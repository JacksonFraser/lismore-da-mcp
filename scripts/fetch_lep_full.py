#!/usr/bin/env python3
"""Fetch full LEP text by handling Cloudflare challenge with Playwright."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

DOCS_DIR = Path(__file__).resolve().parent.parent / "documents" / "lep"

async def fetch_with_cf_bypass(url: str, output_file: str):
    """Fetch URL handling Cloudflare challenge."""
    async with async_playwright() as p:
        # Use non-headless to better handle Cloudflare
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )

        page = await context.new_page()

        # Remove webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
        """)

        print(f"Fetching: {url}")

        try:
            response = await page.goto(url, wait_until="networkidle", timeout=60000)
            print(f"Initial response status: {response.status if response else 'None'}")
        except Exception as e:
            print(f"Initial load: {e}")

        # Wait for Cloudflare challenge to complete
        print("Waiting for Cloudflare challenge...")
        await asyncio.sleep(8)

        # Check if we need to wait more
        content = await page.content()
        if "Just a moment" in content or "Enable JavaScript" in content:
            print("Still on challenge page, waiting more...")
            await asyncio.sleep(10)

        # Get final content
        text_content = await page.evaluate("document.body.innerText")

        # If it's a download link, handle download
        if ".txt" in url or "download" in url:
            # Try to get text content
            if len(text_content) < 1000:
                # Might be a file download - try response body
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    if response:
                        body = await response.body()
                        text_content = body.decode('utf-8', errors='ignore')
                except Exception as e:
                    print(f"Download attempt: {e}")

        output_path = DOCS_DIR / output_file
        output_path.write_text(text_content, encoding="utf-8")
        print(f"Saved: {output_file} ({len(text_content)} chars)")

        # Show first 500 chars
        print(f"Preview: {text_content[:500]}...")

        await browser.close()
        return text_content


async def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Try the NSW Legislation site which might be easier
    urls = [
        # NSW Legislation full view
        ("https://legislation.nsw.gov.au/view/whole/html/inforce/current/epi-2013-0066", "lep-2012-nsw-full.txt"),
    ]

    for url, output in urls:
        try:
            await fetch_with_cf_bypass(url, output)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
