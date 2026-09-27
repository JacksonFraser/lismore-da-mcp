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
    .venv/bin/python scripts/verify_against_council.py --json r.json --issue-body b.md

Exit status: 0 clean, 1 drift, 3 unverified (something could not be fetched and
nothing else was wrong), 4 the verifier itself failed, 2 a usage error. Drift
outranks unverified. A quarterly GitHub Actions workflow runs this and opens an
issue on anything but 0 — a different issue for "could not fetch" than for
drift, because Council's bot protection may refuse CI runners.

Requires the scraping extra, because lismore.nsw.gov.au returns 403 to plain
HTTP — a browser is the only way in:

    .venv/bin/python -m pip install -e ".[scraping]"
    .venv/bin/playwright install chromium
"""

import argparse
import asyncio
import hashlib
import json
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

# The exit code is a contract: .github/workflows/verify-against-council.yml
# decides whether to open an issue, and which, from it (and from --json, which
# carries the same status). "Could not fetch" has its own code because Council's
# site blocks automated clients and may block CI runners outright — a blocked
# run must not read as drift, and must not read as clean. 2 is left to argparse,
# which uses it for a usage error.
EXIT_CLEAN = 0          # every document fetched, every figure found
EXIT_DRIFT = 1          # a figure is gone, or a document changed that nothing checks
EXIT_UNVERIFIED = 3     # no drift found, but something could not be fetched
EXIT_ERROR = 4          # the verifier itself failed; nothing is known

STATUS_CLEAN, STATUS_DRIFT = "clean", "drift"
STATUS_UNVERIFIED, STATUS_ERROR = "unverified", "error"

# Consecutive failed downloads after which the rest are not attempted.
GIVE_UP_AFTER = 3


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
    # The curly quotes are spelled as escapes because this line once held two
    # straight-to-straight no-ops — the curly characters had been lost in an
    # edit — and every parking rate containing "manager's" reported as drift.
    text = text.replace("m²", "m2").replace("’", "'").replace("‘", "'")
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

async def download_all(targets, into: Path, give_up_after: int = GIVE_UP_AFTER) -> dict:
    """Download each target with a browser.

    Returns filename → (path, None) on success or (None, reason) on failure. A
    download that is not a PDF is a failure, not a document: Council's site sits
    behind bot protection, and a challenge page saved as `fees-and-charges.pdf`
    would otherwise differ from the committed copy and contain none of its
    figures — a block reported as drift.

    After `give_up_after` consecutive failures the rest are skipped rather than
    each waiting out its own three-minute timeout. That many in a row is the
    site refusing this machine, not a run of moved documents, and on a CI
    runner it is the difference between a nine-minute answer and an hour.
    """
    from playwright.async_api import async_playwright

    got: dict[str, tuple[Path | None, str | None]] = {}
    consecutive = 0
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        ctx = await browser.new_context(user_agent=USER_AGENT, accept_downloads=True)
        page = await ctx.new_page()
        for url, _category, filename in targets:
            if give_up_after and consecutive >= give_up_after:
                got[filename] = (None, f"not attempted — the previous {consecutive} downloads "
                                       f"all failed, which looks like the site refusing "
                                       f"this machine")
                continue
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
            except Exception as exc:                              # noqa: BLE001
                print(f" FAILED ({type(exc).__name__})")
                got[filename] = (None, f"download failed ({type(exc).__name__})")
                consecutive += 1
                continue
            if not looks_like_pdf(target):
                print(" NOT A PDF")
                got[filename] = (None, "the site served something that is not a PDF — "
                                       "most likely an error or bot-challenge page")
                target.unlink(missing_ok=True)
                consecutive += 1
                continue
            print(f" {target.stat().st_size:,}B")
            got[filename] = (target, None)
            consecutive = 0
        await browser.close()
    return got


async def crawl_pages() -> dict[str, list[tuple[str, str]] | None]:
    """Every PDF linked from the council index pages; None for a page that failed."""
    from playwright.async_api import async_playwright

    found: dict[str, list[tuple[str, str]] | None] = {}
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
                found[url] = None
                continue
            found[url] = [(h, t) for h, t in links if h and ".pdf" in h.lower()]
            print(f"  {len(found[url])} PDF link(s) on {url.rsplit('/', 1)[-1]}")
        await browser.close()
    return found


# --------------------------------------------------------------------------
# The verdict. Kept apart from the fetching so it can be tested without a
# browser, because it is the part a scheduled run's issue is decided by.
# --------------------------------------------------------------------------

def looks_like_pdf(path: Path) -> bool:
    """A PDF starts with `%PDF-`; an HTML challenge page saved as .pdf does not."""
    try:
        with path.open("rb") as handle:
            return handle.read(5) == b"%PDF-"
    except OSError:
        return False


def verdict(report: dict) -> tuple[str, int]:
    """(status, exit code) for a finished run.

    Drift outranks everything: a figure missing from a document that *was*
    fetched is a finding however many others could not be. Otherwise anything
    not fetched means clean cannot be claimed — a blocked run is reported as
    unverified, never as clean and never as drift.
    """
    if report["drift"]:
        return STATUS_DRIFT, EXIT_DRIFT
    if report["unreachable"] or (report.get("crawl") or {}).get("failed_pages"):
        return STATUS_UNVERIFIED, EXIT_UNVERIFIED
    return STATUS_CLEAN, EXIT_CLEAN


def issue_body(report: dict) -> str:
    """Markdown for the issue a scheduled run opens or updates."""
    status = report["status"]
    lines = []
    if status == STATUS_DRIFT:
        lines += [
            "**Council publishes something different from what this server quotes.**",
            "",
            "`scripts/verify_against_council.py` re-downloaded Council's documents and at "
            "least one figure the server quotes is no longer in the document Council "
            "publishes today. Nothing has been changed in the repository.",
        ]
    elif status == STATUS_UNVERIFIED:
        lines += [
            "**The check could not reach Council, so nothing was verified.**",
            "",
            "This is not drift and it is not a clean result. Council's site returns 403 to "
            "plain HTTP and may block CI runners outright; if every document is listed "
            "below, that is the likely cause. Run the script from a normal connection:",
            "",
            "```",
            '.venv/bin/python -m pip install -e ".[scraping]" && .venv/bin/playwright install chromium',
            ".venv/bin/python scripts/verify_against_council.py",
            "```",
        ]
    elif status == STATUS_CLEAN:
        lines += ["Every recorded figure still appears in the document Council publishes today."]
    else:
        lines += [f"The verifier stopped with an error: {report.get('error', 'unknown')}"]

    if report["drift"]:
        lines += ["", "### Findings", ""]
        lines += [f"- {problem}" for problem in report["drift"]]
    if report["unreachable"]:
        lines += ["", f"### Not fetched ({len(report['unreachable'])})", ""]
        lines += [f"- `{u['file']}` — {u['reason']}" for u in report["unreachable"]]
    crawl = report.get("crawl") or {}
    if crawl.get("failed_pages"):
        lines += ["", "### Index pages that could not be crawled", ""]
        lines += [f"- {url}" for url in crawl["failed_pages"]]
    if report["reissued"]:
        lines += ["", "### Reissued, figures hold", ""]
        lines += [f"- `{name}`" for name in report["reissued"]]
    if crawl.get("unlisted"):
        lines += ["", "### Published by Council, not carried here", ""]
        lines += [f"- [{d['title'][:72] or d['name']}]({d['href']})" for d in crawl["unlisted"]]

    lines += [
        "",
        "---",
        "Before changing anything: open the live document, confirm the change is real, and "
        "put any new PDF through SCRAPER.md §8 and `/check-documents`. Update `data/` from the "
        "document, re-run the matching `scripts/audit_*.py`, and never edit stored text just "
        "to make a check pass. This run wrote nothing to `documents/`.",
    ]
    return "\n".join(lines) + "\n"


async def run(args) -> dict:
    """Do the work and return the report; print the human-readable account as it goes."""
    targets = [d for d in DOCUMENTS if not args.only or d[1] == args.only]
    report: dict = {
        "checked": len(targets),
        "identical": [],
        "reissued": [],
        "unreachable": [],
        "drift": [],
        "figures": {},
        "crawl": None,
    }

    tmp = Path(tempfile.mkdtemp(prefix="lismore-verify-"))
    try:
        print(f"Re-downloading {len(targets)} document(s) Council publishes now...")
        downloaded = await download_all(targets, tmp, give_up_after=args.give_up_after)

        print("\n--- live document against the committed copy ---")
        changed = []
        for _url, category, filename in targets:
            live, reason = downloaded.get(filename, (None, "not attempted"))
            committed = DOCS / category / filename
            if not committed.exists():
                report["drift"].append(
                    f"{filename}: listed in the manifest but not in documents/")
                print(f"  MISSING      {filename} (not in documents/{category}/)")
                continue
            if live is None:
                report["unreachable"].append({"file": filename, "reason": reason})
                print(f"  UNREACHABLE  {filename} — {reason}")
                continue
            if digest(live) == digest(committed):
                report["identical"].append(filename)
                print(f"  IDENTICAL    {filename}")
            else:
                changed.append(filename)
                print(f"  DIFFERS      {filename} "
                      f"(live {live.stat().st_size:,}B / repo {committed.stat().st_size:,}B)")

        print("\n--- figures the server quotes, against the live document ---")
        for filename, (label, figures) in FIGURE_CHECKS.items():
            live, _reason = downloaded.get(filename, (None, None))
            if live is None:
                continue
            text = pdf_text(live)
            expected = figures()
            missing = [(what, value) for what, value in expected
                       if normalise(value) not in text]
            report["figures"][filename] = {
                "label": label, "total": len(expected), "missing": missing}
            if missing:
                print(f"  {label}: {len(expected) - len(missing)}/{len(expected)} verify — "
                      f"{len(missing)} NOT FOUND")
                for what, value in missing:
                    print(f"      missing: {what} = {value}")
                    report["drift"].append(f"{filename}: {what} = {value} is no longer in "
                                           f"the document Council publishes")
            else:
                print(f"  {label}: {len(expected)}/{len(expected)} verify against the live "
                      f"document")

        for filename in changed:
            if filename not in FIGURE_CHECKS:
                report["drift"].append(
                    f"{filename}: reissued, and nothing here checks its figures. "
                    f"Open it and compare against whatever data/ takes from it."
                )
            elif not report["figures"][filename]["missing"]:
                report["reissued"].append(filename)

        if not args.no_crawl:
            report["crawl"] = await crawl(args)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return report


async def crawl(args) -> dict:
    print("\n--- documents Council publishes that this repo does not carry ---")
    committed = sorted(p for p in DOCS.rglob("*.pdf") if p.is_file())
    known_urls = {u.rsplit("/", 1)[-1] for u, _c, _f in DOCUMENTS}

    failed_pages = []
    unlisted, superseded, matched = {}, {}, {}
    for page, links in (await crawl_pages()).items():
        if links is None:
            failed_pages.append(page)
            continue
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
        for _name, (href, title) in sorted(unlisted.items()):
            print(f"    {title[:72]}")
            print(f"      {href}")
        print("\n  Not downloaded. Check each against SCRAPER.md §8 before "
              "fetching, and confirm\n  which LEP edition it is (§6) before "
              "believing the filename.")
    elif not failed_pages:
        print("\n  No current document without a local counterpart.")

    if superseded:
        print(f"\n  {len(superseded)} LEP 2000 edition(s) published but not carried, "
              f"which is the\n  policy — pass --show-superseded to list them.")
        if args.show_superseded:
            for _name, (href, _title) in sorted(superseded.items()):
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

    return {
        "failed_pages": failed_pages,
        "unlisted": [{"name": n, "href": h, "title": t}
                     for n, (h, t) in sorted(unlisted.items())],
        "matched": {n: str(p.relative_to(DOCS)) for n, p in sorted(matched.items())},
        "superseded": sorted(superseded),
    }


def write_outputs(report: dict, args) -> None:
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2, default=str) + "\n")
    if args.issue_body:
        Path(args.issue_body).write_text(issue_body(report))


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", help="Limit to one category (fees, dcp, lep, business)")
    parser.add_argument("--no-crawl", action="store_true",
                        help="Skip looking for documents we do not have")
    parser.add_argument("--show-superseded", action="store_true",
                        help="Also list the LEP 2000 editions this repo does not carry")
    parser.add_argument("--json", metavar="PATH",
                        help="Also write the result as JSON (status, findings, what was "
                             "not fetched) — what the scheduled workflow reads")
    parser.add_argument("--issue-body", metavar="PATH",
                        help="Also write a Markdown issue body describing the result")
    parser.add_argument("--give-up-after", type=int, default=GIVE_UP_AFTER, metavar="N",
                        help=f"Stop trying after N consecutive failed downloads "
                             f"(default {GIVE_UP_AFTER}; 0 never gives up)")
    args = parser.parse_args(argv)

    if args.only and not any(d[1] == args.only for d in DOCUMENTS):
        parser.error(f"no documents in category {args.only!r}")

    try:
        report = await run(args)
    except Exception as exc:                                      # noqa: BLE001
        # An uncaught exception would exit 1, which is the drift code — so a
        # missing browser or a bug here would open a drift issue. It is its
        # own status instead.
        import traceback
        traceback.print_exc()
        report = {"checked": 0, "identical": [], "reissued": [], "unreachable": [],
                  "drift": [], "figures": {}, "crawl": None,
                  "status": STATUS_ERROR, "exit_code": EXIT_ERROR,
                  "error": f"{type(exc).__name__}: {exc}"}
        write_outputs(report, args)
        return EXIT_ERROR

    report["status"], report["exit_code"] = verdict(report)
    write_outputs(report, args)

    print(f"\n{'=' * 70}")
    if report["status"] == STATUS_DRIFT:
        print(f"{len(report['drift'])} PROBLEM(S) — the server may be quoting superseded "
              f"figures:")
        for problem in report["drift"]:
            print(f"  - {problem}")
    if report["unreachable"]:
        print(f"{len(report['unreachable'])} document(s) could not be fetched, so they were "
              f"not verified.")
    if report["status"] == STATUS_UNVERIFIED:
        print("UNVERIFIED — nothing above is drift, but this is not a clean result either.")
    elif report["status"] == STATUS_CLEAN:
        print("Every recorded figure still appears in the document Council publishes today.")
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
