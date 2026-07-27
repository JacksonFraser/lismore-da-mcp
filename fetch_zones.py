#!/usr/bin/env python3
"""Fetch zone land use tables from AustLII."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

DOCS_DIR = Path(__file__).parent / "documents" / "lep"

async def fetch_page(url: str, output_file: str, wait_time: int = 2):
    """Fetch a page and save its content."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        print(f"Fetching: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Load issue: {e}")

        await asyncio.sleep(wait_time)
        text_content = await page.evaluate("document.body.innerText")

        output_path = DOCS_DIR / output_file
        output_path.write_text(text_content, encoding="utf-8")
        print(f"Saved: {output_file} ({len(text_content)} chars)")

        await browser.close()
        return text_content


async def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Each zone's land use table is in a separate "longtitle" page on AustLII
    # The format is: longtitle/{zone-name}
    zones = [
        ("longtitle/zone-r1---general-residential", "zone-R1-general-residential.txt"),
        ("longtitle/zone-r2---low-density-residential", "zone-R2-low-density-residential.txt"),
        ("longtitle/zone-r3---medium-density-residential", "zone-R3-medium-density-residential.txt"),
        ("longtitle/zone-r5---large-lot-residential", "zone-R5-large-lot-residential.txt"),
        ("longtitle/zone-ru5---village", "zone-RU5-village.txt"),
        ("longtitle/zone-e1---local-centre", "zone-E1-local-centre.txt"),
        ("longtitle/zone-e2---commercial-centre", "zone-E2-commercial-centre.txt"),
        ("longtitle/zone-e4---general-industrial", "zone-E4-general-industrial.txt"),
        ("longtitle/zone-mu1---mixed-use", "zone-MU1-mixed-use.txt"),
    ]

    base_url = "https://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/nsw/consol_reg/llep2012310"

    for path, output in zones:
        url = f"{base_url}/{path}"
        try:
            await fetch_page(url, output)
        except Exception as e:
            print(f"Error: {e}")

    # Also try to get the standard instrument dictionary for definitions
    print("\nFetching Standard Instrument definitions...")
    await fetch_page(
        "https://www.legislation.nsw.gov.au/view/html/inforce/current/epi-2006-155a/sch4",
        "standard-instrument-dictionary.txt",
        wait_time=5
    )


if __name__ == "__main__":
    asyncio.run(main())
