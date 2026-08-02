#!/usr/bin/env python3
"""Fetch NSW DPE 'rules for exempt development' fact sheets using Playwright.

Mirrors the pattern in fetch_lep.py (same directory). These are the small, stable state-wide
SEPP fact sheets that cover the most common "do I need a DA?" questions
(decks, fences, sheds, carports), so they're cached locally rather than
re-fetched from government sites on every query.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

DOCS_DIR = Path(__file__).resolve().parent.parent / "documents" / "exempt-development"

FACT_SHEETS = [
    (
        "https://www.planning.nsw.gov.au/sites/default/files/2023-02/balconies-decks-patios-pergolas-terraces-and-verandahs-rules-for-exempt-development.pdf",
        "balconies-decks-patios-pergolas-terraces-verandahs.pdf",
    ),
    (
        "https://www.planning.nsw.gov.au/sites/default/files/2023-02/fences-rules-for-exempt-and-complying-development.pdf",
        "fences.pdf",
    ),
    (
        "https://www.planning.nsw.gov.au/sites/default/files/2023-02/carports-and-garages-rules-for-exempt-development.pdf",
        "carports-and-garages.pdf",
    ),
    (
        "https://www.planning.nsw.gov.au/sites/default/files/2023-02/cabanas-cubby-houses-ferneries-garden-sheds-gazebos-and-greenhouses-rules-for-exempt-development.pdf",
        "cabanas-cubby-houses-sheds-gazebos-greenhouses.pdf",
    ),
    (
        "https://www.planning.nsw.gov.au/sites/default/files/2023-02/driveways-hardstands-pathways-and-paving-rules-for-exempt-development.pdf",
        "driveways-hardstands-pathways-paving.pdf",
    ),
    (
        "https://www.planning.nsw.gov.au/sites/default/files/2023-02/understanding-exempt-development.pdf",
        "understanding-exempt-development.pdf",
    ),
]


async def fetch_pdf(context, url: str, output_file: str):
    output_path = DOCS_DIR / output_file
    response = await context.request.get(url)
    if response.ok:
        body = await response.body()
        output_path.write_bytes(body)
        print(f"Saved: {output_path} ({len(body)} bytes)")
    else:
        print(f"FAILED ({response.status}): {url}")


async def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        for url, output in FACT_SHEETS:
            try:
                await fetch_pdf(context, url, output)
            except Exception as e:
                print(f"Error fetching {url}: {e}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
