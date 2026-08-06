#!/usr/bin/env python3
"""Fetch the EP&A Regulation 2021 provisions that govern DA assessment time.

PLAN.md item 2.5. Nothing in `documents/` said anything about how long a DA
takes or what stops the clock — the one item in Phase 2 whose source was not
already in the repo. The periods are set by the Environmental Planning and
Assessment Regulation 2021, so this fetches it rather than transcribing them
from memory, which is exactly the failure mode PLAN.md 0.3 documents.

legislation.nsw.gov.au returns 403 to plain HTTP and sits behind a Cloudflare
challenge, hence Playwright and the `scraping` extra. Same shape as
`fetch_lep_full.py`.

**Read what this produces before committing it.** These scripts save whatever
the server returned, including challenge pages and error bodies — fifteen such
files were once committed to `documents/lep/` under names promising real
content. `verify()` below refuses to write anything that does not contain the
provisions being sought, which is the check that was missing then.

    uv sync --extra scraping
    .venv/bin/python scripts/fetch_epa_regulation.py
"""

import asyncio
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "documents" / "legislation"
OUT_FILE = OUT_DIR / "epa-regulation-2021-assessment-periods.txt"

# The "whole" view, because the default paginates by part and the provisions
# wanted here are spread across several. Note the SL number: the regulation is
# 2021 No 759, and 0642 (a first guess) is a live page for something else
# entirely — the verify() check below is what caught that.
URL = "https://legislation.nsw.gov.au/view/whole/html/inforce/current/sl-2021-0759"

# Phrases that must appear for the fetch to be considered real content rather
# than a challenge page. Chosen from the provisions actually being sought.
REQUIRED = [
    "deemed refusal",
    "additional information",
]

CHALLENGE_MARKERS = ["Just a moment", "Enable JavaScript", "Attention Required",
                     "Access denied", "cf-browser-verification"]


async def fetch(url: str) -> str:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => false});")

        print(f"fetching {url}")
        try:
            response = await page.goto(url, wait_until="networkidle", timeout=90000)
            print(f"  status {response.status if response else 'unknown'}")
        except Exception as exc:                                      # noqa: BLE001
            print(f"  initial load: {exc}")

        for attempt in range(4):
            content = await page.content()
            if not any(marker in content for marker in CHALLENGE_MARKERS):
                break
            print(f"  challenge page, waiting ({attempt + 1}/4)...")
            await asyncio.sleep(8)

        text = await page.evaluate("() => document.body.innerText")
        await browser.close()
        return text


def verify(text: str) -> list[str]:
    """Reasons this content should not be written. Empty means it is usable."""
    problems = []
    if any(marker in text for marker in CHALLENGE_MARKERS):
        problems.append("still a Cloudflare challenge or access-denied page")
    if len(text) < 20000:
        problems.append(f"suspiciously short ({len(text)} chars) for this regulation")
    for phrase in REQUIRED:
        if phrase.lower() not in text.lower():
            problems.append(f"does not contain {phrase!r}")
    return problems


def main() -> int:
    text = asyncio.run(fetch(URL))
    problems = verify(text)
    if problems:
        print("\nNOT WRITING — the fetch did not return usable content:")
        for problem in problems:
            print(f"  - {problem}")
        print(f"\nFirst 400 chars:\n{text[:400]!r}")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    header = (
        f"Environmental Planning and Assessment Regulation 2021 (NSW)\n"
        f"Source: {URL}\n"
        f"Retrieved by scripts/fetch_epa_regulation.py\n"
        f"{'=' * 70}\n\n"
    )
    OUT_FILE.write_text(header + text)
    print(f"\nwrote {OUT_FILE} ({len(text):,} chars)")

    # Show what was found, so the operator can see it is the right document
    # rather than trusting the length check.
    for phrase in REQUIRED:
        for match in re.finditer(re.escape(phrase), text, re.I):
            excerpt = " ".join(text[max(0, match.start() - 120):match.start() + 200].split())
            print(f"\n  [{phrase}] ...{excerpt}...")
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
