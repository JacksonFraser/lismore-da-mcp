#!/usr/bin/env python3
"""Check the server still answers what Council currently publishes.

PLAN.md item 0.4. The three `audit_*.py` scripts check the transcribed data
against the PDFs **in this repository**. Nothing checked that those PDFs are
still the documents Council publishes, so a reissued chapter or an amended fee
schedule would leave every audit green while the server quoted superseded
figures — which is precisely how the fee scale sat two years stale.

This closes that loop, in three passes:

  1. **Re-download** every document with a recorded source URL and compare it
     byte for byte with the committed copy.
  2. **Re-verify the figures** against the freshly downloaded copy — every DA fee
     bracket, Section 7.11 rate, Section 64 charge and parking requirement the
     server would quote. A document can be reissued without any number changing,
     and that distinction is the point: "reissued, figures hold" is a note, while
     "figures differ" is an emergency.
  3. **Crawl** Council's planning pages for PDFs this repo does not carry, so a
     newly published rate sheet or amended chapter surfaces.

It **never writes to `documents/`**. Downloads go to a temp directory and are
discarded. Anything it proposes still has to go through the checks in
SCRAPER.md §8 and a human deciding whether it belongs — a watcher that
auto-commits is a way to publish an error page as a planning answer.

    .venv/bin/python scripts/verify_against_council.py
    .venv/bin/python scripts/verify_against_council.py --no-crawl   # faster
    .venv/bin/python scripts/verify_against_council.py --only fees  # one category

Requires the scraping extra, because lismore.nsw.gov.au returns 403 to plain
HTTP — a browser is the only way in:

    .venv/bin/python -m pip install -e ".[scraping]"
    .venv/bin/playwright install chromium
"""

import argparse
import asyncio
import hashlib
import re
import shutil
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "src"))

from council_sources import (  # noqa: E402
    CRAWL_PAGES,
    DOCUMENTS,
    KNOWN_NOT_CARRIED,
    USER_AGENT,
)

DOCS = ROOT / "documents"


# --------------------------------------------------------------------------
# Which figures live in which document.
#
# These are *derived* from the data modules rather than restated, so this file
# holds no second copy of any number — only the rule for finding one. Adding a
# rate to `data/` therefore adds it to this check automatically.
# --------------------------------------------------------------------------

def money(amount: float) -> str:
    return f"${amount:,.2f}"


def fee_figures() -> list[tuple[str, str]]:
    from lismore_da_mcp.data.fees import (
        DA_FEE_BRACKETS,
        DA_FEE_DWELLING_UNDER_100K,
        DA_FEE_NO_BUILDING_WORK,
        DESIGNATED_DEVELOPMENT_FEE,
        NOTIFICATION_FEES,
        PRESCRIBED_NOTICE_FEES,
    )
    out = [("DA fee bracket base", money(base)) for _, base, _, _ in DA_FEE_BRACKETS]
    out.append(("DA fee, no building work (item 2.7)", money(DA_FEE_NO_BUILDING_WORK)))
    out.append(("DA fee, dwelling under $100k", money(DA_FEE_DWELLING_UNDER_100K)))
    out.append(("designated development fee", money(DESIGNATED_DEVELOPMENT_FEE)))
    out.append(("IT service charge", "0.1% of estimated cost"))
    out += [(f"notification fee ({k})", money(v)) for k, v in NOTIFICATION_FEES.items()]
    out += [(f"prescribed notice ({k})", money(v)) for k, v in PRESCRIBED_NOTICE_FEES.items()]
    return out


def contribution_figures() -> list[tuple[str, str]]:
    from lismore_da_mcp.data.contributions import (
        DEVELOPMENT_TYPE_RATES,
        INFRASTRUCTURE_RATES,
    )
    out = [
        (f"Table E2 {key} ({catchment})", money(rate))
        for key, entry in DEVELOPMENT_TYPE_RATES.items()
        for catchment, rate in entry["rates"].items()
    ]
    out += [
        (f"Table E1 {row['category']} ({row['basis']})", money(row["rates"]["urban"]))
        for row in INFRASTRUCTURE_RATES
    ]
    return out


def dsp_figures() -> list[tuple[str, str]]:
    from lismore_da_mcp.data.contributions import SECTION_64_CHARGES
    return [
        (f"{area} {service}", f"${amount:,}")
        for area, services in SECTION_64_CHARGES.items()
        for service, amount in services.items()
        if amount
    ]


def parking_figures() -> list[tuple[str, str]]:
    from lismore_da_mcp.data.parking import PARKING_RATES
    return [
        (key, entry["rate"])
        for key, entry in PARKING_RATES.items()
        if entry.get("dcp_use")
    ]


# filename → (label, figure-producing function)
FIGURE_CHECKS = {
    "fees-and-charges-2026-27.pdf": ("DA fees and Council charges", fee_figures),
    "section-7.11-contributions-plan-2024-2041.pdf": ("Section 7.11 rates", contribution_figures),
    "development-servicing-plans-water-wastewater.pdf": ("Section 64 charges", dsp_figures),
    "chapter-7-off-street-carparking.pdf": ("Parking rates", parking_figures),
}


def normalise(text: str) -> str:
    """Compare on wording, not typography — the same rule audit_parking_rates uses."""
    text = text.replace("m²", "m2").replace("'", "'").replace("'", "'")
    text = text.replace("–", "-").replace("—", "-")
    return " ".join(text.lower().split())


def pdf_text(path: Path) -> str:
    import fitz

    with fitz.open(path) as doc:
        return normalise(" ".join(doc[i].get_text() for i in range(doc.page_count)))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# Recognising a document this repo already holds under a different filename.
#
# Without this the crawl reports 48 of 59 links as "new", most of them chapters
# already carried under Council's other naming convention, and the report
# becomes something to skim past. The DCP chapters are the bulk of the noise and
# they have a real identity — part, number and LEP edition — so match on that
# rather than on the filename, which differs on both sides for the same document.
# --------------------------------------------------------------------------

def chapter_identity(name: str) -> tuple[str, str, str] | None:
    """(part, chapter number, LEP edition) for a DCP chapter, else None.

    The part separator needs an explicit non-alphanumeric lookahead rather than
    `\\b`: an underscore *is* a word character, so `part_b_chapter_1` failed
    `part[-_ ]?([ab])\\b`, fell through to the Part A default, and matched Part B
    chapter 1 to the Part A chapter 1 file.
    """
    stem = Path(name).stem.lower()
    number = re.search(r"chapter[-_ ]?(\d+[ab]?)", stem)
    if not number:
        return None
    part = re.search(r"part[-_ ]?([ab])(?![a-z0-9])", stem)
    edition = "2000" if "2000" in stem else "2012"
    return (part.group(1) if part else "a", number.group(1), edition)


def similar(a: str, b: str) -> float:
    def clean(name: str) -> str:
        stem = Path(name).stem.lower()
        for noise in ("new-", "new_", "_lep_2012", "_lep_2000", "-lep2012", "-lep2000"):
            stem = stem.replace(noise, "")
        return re.sub(r"[^a-z0-9]+", " ", stem).strip()

    return SequenceMatcher(None, clean(a), clean(b)).ratio()


def already_held(url_name: str, committed: list[Path]) -> Path | None:
    """The committed file this link probably is, or None if it looks genuinely new."""
    identity = chapter_identity(url_name)
    if identity:
        for path in committed:
            if chapter_identity(path.name) == identity:
                return path
        return None
    best = max(committed, key=lambda p: similar(url_name, p.name), default=None)
    return best if best and similar(url_name, best.name) >= 0.65 else None


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------

async def download_all(targets, into: Path) -> dict:
    """Download each target with a browser. Returns filename → path or None."""
    from playwright.async_api import async_playwright

    got = {}
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        ctx = await browser.new_context(user_agent=USER_AGENT, accept_downloads=True)
        page = await ctx.new_page()
        for url, _category, filename in targets:
            target = into / filename
            print(f"  fetching {filename} ...", end="", flush=True)
            try:
                # The PDF is served as a download rather than rendered, so the
                # navigation itself raises; the download event is the payload.
                async with page.expect_download(timeout=180_000) as info:
                    try:
                        await page.goto(url, timeout=180_000)
                    except Exception:
                        pass
                await (await info.value).save_as(target)
                print(f" {target.stat().st_size:,}B")
                got[filename] = target
            except Exception as exc:                              # noqa: BLE001
                print(f" FAILED ({type(exc).__name__})")
                got[filename] = None
        await browser.close()
    return got


async def crawl_pages() -> dict[str, list[tuple[str, str]]]:
    """Every PDF linked from the council index pages."""
    from playwright.async_api import async_playwright

    found = {}
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        ctx = await browser.new_context(user_agent=USER_AGENT)
        page = await ctx.new_page()
        for url in CRAWL_PAGES:
            try:
                await page.goto(url, timeout=90_000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2_500)
                links = await page.eval_on_selector_all(
                    "a[href]",
                    "els => els.map(e => [e.getAttribute('href'), e.textContent.trim()])",
                )
            except Exception as exc:                              # noqa: BLE001
                print(f"  crawl FAILED {url}: {type(exc).__name__}")
                found[url] = []
                continue
            found[url] = [(h, t) for h, t in links if h and ".pdf" in h.lower()]
            print(f"  {len(found[url])} PDF link(s) on {url.rsplit('/', 1)[-1]}")
        await browser.close()
    return found


# --------------------------------------------------------------------------

async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Limit to one category (fees, dcp, lep, business)")
    parser.add_argument("--no-crawl", action="store_true",
                        help="Skip looking for documents we do not have")
    parser.add_argument("--show-superseded", action="store_true",
                        help="Also list the LEP 2000 editions this repo does not carry")
    args = parser.parse_args()

    targets = [d for d in DOCUMENTS if not args.only or d[1] == args.only]
    if not targets:
        print(f"No documents in category {args.only!r}.")
        return 1

    problems: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="lismore-verify-"))
    try:
        print(f"Re-downloading {len(targets)} document(s) Council publishes now...")
        downloaded = await download_all(targets, tmp)

        print("\n--- live document against the committed copy ---")
        changed = []
        for _url, category, filename in targets:
            live = downloaded.get(filename)
            committed = DOCS / category / filename
            if live is None:
                problems.append(f"{filename}: could not be downloaded — is the URL still valid?")
                print(f"  UNREACHABLE  {filename}")
                continue
            if not committed.exists():
                problems.append(f"{filename}: listed in the manifest but not in documents/")
                print(f"  MISSING      {filename} (not in documents/{category}/)")
                continue
            if digest(live) == digest(committed):
                print(f"  IDENTICAL    {filename}")
            else:
                changed.append((filename, category))
                print(f"  DIFFERS      {filename} "
                      f"(live {live.stat().st_size:,}B / repo {committed.stat().st_size:,}B)")

        print("\n--- figures the server quotes, against the live document ---")
        for filename, (label, figures) in FIGURE_CHECKS.items():
            live = downloaded.get(filename)
            if live is None:
                continue
            text = pdf_text(live)
            missing = [(what, value) for what, value in figures()
                       if normalise(value) not in text]
            total = len(figures())
            if missing:
                print(f"  {label}: {total - len(missing)}/{total} verify — "
                      f"{len(missing)} NOT FOUND")
                for what, value in missing:
                    print(f"      missing: {what} = {value}")
                    problems.append(f"{filename}: {what} = {value} is no longer in the "
                                    f"document Council publishes")
            else:
                print(f"  {label}: {total}/{total} verify against the live document")

        for filename, _category in changed:
            if filename not in FIGURE_CHECKS:
                problems.append(
                    f"{filename}: reissued, and nothing here checks its figures. "
                    f"Open it and compare against whatever data/ takes from it."
                )

        if not args.no_crawl:
            print("\n--- documents Council publishes that this repo does not carry ---")
            committed = sorted(p for p in DOCS.rglob("*.pdf") if p.is_file())
            known_urls = {u.rsplit("/", 1)[-1] for u, _c, _f in DOCUMENTS}

            unlisted, superseded, matched = {}, {}, {}
            for _page, links in (await crawl_pages()).items():
                for href, title in links:
                    name = href.rsplit("/", 1)[-1]
                    if name in known_urls or name in KNOWN_NOT_CARRIED:
                        continue
                    held = already_held(name, committed)
                    if held:
                        matched[name] = held
                    elif "2000" in name.lower():
                        # Council publishes both editions side by side. This repo
                        # carries LEP 2012 by policy (SCRAPER.md §6) and only the
                        # few LEP 2000 chapters with no 2012 successor, so listing
                        # every 2000 chapter every run would bury the real finding
                        # among twenty non-findings.
                        superseded[name] = (href, title)
                    else:
                        unlisted[name] = (href, title)

            if unlisted:
                print(f"\n  {len(unlisted)} current document(s) with no local counterpart:")
                for name, (href, title) in sorted(unlisted.items()):
                    print(f"    {title[:72]}")
                    print(f"      {href}")
                print("\n  Not downloaded. Check each against SCRAPER.md §8 before "
                      "fetching, and confirm\n  which LEP edition it is (§6) before "
                      "believing the filename.")
            else:
                print("\n  No current document without a local counterpart.")

            if superseded:
                print(f"\n  {len(superseded)} LEP 2000 edition(s) published but not carried, "
                      f"which is the\n  policy — pass --show-superseded to list them.")
                if args.show_superseded:
                    for name, (href, _title) in sorted(superseded.items()):
                        print(f"    {href}")

            if matched:
                print(f"\n  {len(matched)} link(s) recognised as documents already held, "
                      f"under Council's\n  other naming convention. Their source URL is not "
                      f"in the manifest, so they are\n  not re-verified — add them to "
                      f"council_sources.DOCUMENTS to bring them in:")
                for name, held in sorted(matched.items()):
                    print(f"    {name}\n      -> documents/{held.relative_to(DOCS)}")

            if KNOWN_NOT_CARRIED:
                print("\n  Not reported, decided against previously:")
                for name, why in KNOWN_NOT_CARRIED.items():
                    print(f"    {name}\n      {why}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'=' * 70}")
    if problems:
        print(f"{len(problems)} PROBLEM(S) — the server may be quoting superseded figures:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Every recorded figure still appears in the document Council publishes today.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
