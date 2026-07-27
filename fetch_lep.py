#!/usr/bin/env python3
"""Fetch Lismore LEP 2012 content using Playwright to bypass bot protection."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

DOCS_DIR = Path(__file__).parent / "documents" / "lep"

async def fetch_page(url: str, output_file: str, wait_time: int = 3):
    """Fetch a page and save its content."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        print(f"Fetching: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Initial load issue: {e}, trying to get content anyway...")

        await asyncio.sleep(wait_time)

        text_content = await page.evaluate("document.body.innerText")

        output_path = DOCS_DIR / output_file
        output_path.write_text(text_content, encoding="utf-8")
        print(f"Saved to: {output_path} ({len(text_content)} chars)")

        await browser.close()
        return text_content


async def fetch_rtf_download(url: str, output_file: str):
    """Fetch an RTF file."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        print(f"Downloading: {url}")

        # Set up download handling
        async with page.expect_download() as download_info:
            await page.goto(url)

        download = await download_info.value
        output_path = DOCS_DIR / output_file
        await download.save_as(output_path)
        print(f"Saved to: {output_path}")

        await browser.close()


async def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch specific zone land use tables from AustLII
    zone_pages = [
        # Zone R1 - General Residential
        ("https://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/nsw/consol_reg/llep2012310/s2.3.html", "zone-r1-land-use-table.txt"),
        # Dictionary
        ("https://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/nsw/consol_reg/llep2012310/sch7.html", "lep-dictionary.txt"),
        # Schedule 5 - Heritage
        ("https://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/nsw/consol_reg/llep2012310/sch5.html", "schedule-5-heritage.txt"),
        # Part 4 - Development Standards
        ("https://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/nsw/consol_reg/llep2012310/s4.1.html", "part-4-development-standards.txt"),
        # Clause 5.21 Flood Planning
        ("https://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/nsw/consol_reg/llep2012310/s5.21.html", "clause-5.21-flood-planning.txt"),
    ]

    for url, output in zone_pages:
        try:
            await fetch_page(url, output)
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    # Try to get the plain text download of the full LEP
    try:
        print("\nTrying to download full LEP text file...")
        # AustLII plain text link
        await fetch_page(
            "http://www.austlii.edu.au/cgi-bin/download.cgi/download/au/legis/nsw/consol_reg/llep2012310.txt",
            "lep-2012-full.txt",
            wait_time=5
        )
    except Exception as e:
        print(f"Could not download full text: {e}")


if __name__ == "__main__":
    asyncio.run(main())
