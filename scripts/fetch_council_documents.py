#!/usr/bin/env python3
"""Fetch Lismore City Council planning documents with Playwright.

See SCRAPER.md for why a browser is needed (plain HTTP is refused at the edge),
and for the LEP 2000 / LEP 2012 trap that decides which of two identically-named
chapters you actually want.

Every download is validated before it is kept: it must be a real PDF whose first
page contains text. Anything that fails is deleted rather than left on disk —
fifteen error pages were once committed under names promising real content, and
because the document tools search PDF text, junk surfaces as an answer to a
planning question.

    uv sync --extra scraping
    .venv/bin/playwright install chromium
    .venv/bin/python scripts/fetch_council_documents.py [--dry-run]

Downloading is only half the job. Open each new file, confirm it is what its
name claims and carries no private information, then record it in
documents/DOCUMENT_INDEX.md.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from council_sources import DOCUMENTS, USER_AGENT  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent / "documents"



def validate(path: Path) -> str | None:
    """Return a reason the file is unusable, or None if it looks like a real PDF."""
    if not path.exists():
        return "no file written"
    size = path.stat().st_size
    if size < 2000:
        return f"suspiciously small ({size} bytes)"
    if path.read_bytes()[:5] != b"%PDF-":
        return "not a PDF (an error page saves just as happily as a document)"
    try:
        import fitz
    except ImportError:
        return None  # structural checks above still passed
    try:
        with fitz.open(path) as doc:
            if doc.page_count == 0:
                return "PDF has no pages"
            # Look across the opening pages, not just the first. Council
            # publications routinely lead with a wholly graphical cover that
            # extracts as zero characters — checking page 1 alone rejected the
            # genuine 60-page 2026-27 fees schedule on the first run of this
            # script.
            pages = [doc[i].get_text().strip() for i in range(min(5, doc.page_count))]
    except Exception as exc:                                  # noqa: BLE001
        return f"unreadable PDF ({type(exc).__name__})"

    text = "\n".join(pages)
    if len(text) < 200:
        return (f"almost no text in the first {len(pages)} page(s) — "
                "may be a scan, a stub, or an error page")
    lowered = text.lower()
    if "access denied" in lowered or "page not found" in lowered:
        return "content is an error page"
    return None


async def fetch(dry_run: bool) -> int:
    from playwright.async_api import async_playwright

    pending = []
    for url, category, filename in DOCUMENTS:
        target = DOCS / category / filename
        if target.exists():
            print(f"  have    {category}/{filename}")
        else:
            pending.append((url, category, filename, target))

    if not pending:
        print("\nNothing to fetch.")
        return 0
    print(f"\n{len(pending)} to fetch:")
    for _, category, filename, _ in pending:
        print(f"  want    {category}/{filename}")
    if dry_run:
        print("\n--dry-run: nothing downloaded.")
        return 0

    kept, rejected = [], []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        ctx = await browser.new_context(user_agent=USER_AGENT, accept_downloads=True)
        page = await ctx.new_page()
        for url, category, filename, target in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            print(f"\n  fetching {category}/{filename}")
            try:
                # The PDF is served as a download rather than rendered, so the
                # navigation itself raises; the download event is the payload.
                async with page.expect_download(timeout=120000) as info:
                    try:
                        await page.goto(url, timeout=120000)
                    except Exception:
                        pass
                download = await info.value
                await download.save_as(target)
            except Exception as exc:                          # noqa: BLE001
                print(f"    FAILED  {type(exc).__name__}: {str(exc)[:110]}")
                rejected.append((filename, "download failed"))
                target.unlink(missing_ok=True)
                continue

            problem = validate(target)
            if problem:
                print(f"    REJECTED  {problem} — deleting")
                target.unlink(missing_ok=True)
                rejected.append((filename, problem))
            else:
                kb = target.stat().st_size // 1024
                print(f"    ok      {kb} KB")
                kept.append(f"{category}/{filename}")
        await browser.close()

    print(f"\n{'=' * 60}\nkept {len(kept)}, rejected {len(rejected)}")
    for name in kept:
        print(f"  + {name}")
    for name, why in rejected:
        print(f"  - {name}: {why}")
    if kept:
        print(
            "\nNow: open each file and confirm it is what its name claims and carries no\n"
            "private information, then add it to documents/DOCUMENT_INDEX.md.\n"
            "Nothing under documents/ is private — it is all committed and published."
        )
    return 1 if rejected else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="list what would be fetched, download nothing")
    sys.exit(asyncio.run(fetch(parser.parse_args().dry_run)))
