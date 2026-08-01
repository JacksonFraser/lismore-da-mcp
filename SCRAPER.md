# Retrieving documents from the Lismore City Council website

How to get planning documents off `lismore.nsw.gov.au`, and the traps that have already cost time.
Written 2026-08-01 after a full scan of the site; the specifics below were verified that day.

**Read `documents/DOCUMENT_INDEX.md` and the "Documents and privacy" section of `CLAUDE.md`
before committing anything you download.** This file covers *how to fetch*; those cover *what is
allowed into the repo*, which is a separate and stricter question.

---

## 1. Plain HTTP does not work. Use Playwright.

Every unadorned request is refused at the edge:

```bash
curl https://www.lismore.nsw.gov.au/robots.txt
# <TITLE>Access Denied</TITLE> ... Reference #18.24672817...
```

`robots.txt`, `sitemap.xml` and `sitemap` are all blocked the same way, so **there is no sitemap to
work from** — discovery has to be done by crawling.

A headless browser with a normal desktop user agent is served normally:

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.launch()
    ctx = await browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
    page = await ctx.new_page()
    await page.goto(url, wait_until="networkidle", timeout=30000)
```

Setup:

```bash
uv sync --extra scraping          # playwright + httpx, kept out of the deployed image
.venv/bin/playwright install chromium
```

This is the same reason `fetch_lep.py`, `fetch_zones.py` and `fetch_exempt_development.py` exist —
`legislation.nsw.gov.au`, `austlii.edu.au` and `planning.nsw.gov.au` block automated fetches too.
Follow their shape for anything new.

## 2. Wait for `networkidle`, not `domcontentloaded`

The site runs on OpenCities and renders its content and link lists with JavaScript. With
`wait_until="domcontentloaded"` you get a partial DOM and will silently miss most links — the
Business section looked nearly empty on the first pass for exactly this reason. Use
`wait_until="networkidle"`, or `domcontentloaded` plus an explicit `wait_for_timeout`.

## 3. There is no usable search endpoint

`/Search?q=trade+waste` redirects to `Page-Not-Found`. Do not build discovery on it. Navigate by
path, and confirm a path exists by checking `response.status` before crawling it.

## 4. Guessing paths mostly fails — check status codes first

Section naming is not what you would guess. Verified 2026-08-01:

| Path | |
|---|---|
| `/Business` | ✅ |
| `/Business/Food-businesses-in-Lismore` | ✅ |
| `/Building-and-planning/Development-Applications` | ✅ |
| `/Building-and-planning/Strategic-planning` | ✅ |
| `/Building-and-planning/Strategic-planning/Developer-contributions` | ✅ |
| `/Building-and-planning/Strategic-planning/Local-Environmental-Plans-and-DCPs` | ✅ |
| `/Business-and-economy`, `/Development`, `/Environment`, `/Doing-business` | ❌ 404 |
| `/Households/Water`, `/Households/Water-and-sewer` | ❌ 404 |

Note the DA area is reached at two names — `/Development-Applications` links onward to
`/Development-Applications-in-Lismore`, which is where the sub-pages live.

## 5. Filter `?oc_lang=` or your crawl will never end

Every page is emitted with a query-string variant for ~40 languages
(`?oc_lang=af`, `?oc_lang=ar`, …). They are the same page. Drop any URL containing `oc_lang`
before queueing it, and strip `#fragments`, or the frontier grows without bound.

## 6. ⚠️ The biggest trap: LEP 2000 and LEP 2012 chapters sit side by side

The DCP page lists **both** the current LEP 2012 chapters and the superseded LEP 2000 ones, often
with **identical link text**. "Heritage Conservation", "Waste Minimisation" and "Off Street
Carparking" each appear twice. Selecting by link text alone will get you the wrong one about half
the time — and a superseded chapter that looks authoritative is worse than no chapter.

Tell them apart by filename, not by link text:

| Filename signal | Instrument |
|---|---|
| `new-` prefix, and/or `_lep_2012` | **LEP 2012 — current** |
| `_lep_2000` | **LEP 2000 — superseded for most land** |

```
new-part_a_chapter_8_flood_prone_lands_lep_2012.pdf   ← current
part_a_chapter_8_flood_prone_land_lep_2000.pdf        ← superseded
```

Both signals agreed on every chapter observed. The repo already models this distinction — see
`data/instruments.py` and `SUPERSEDED_NOTE` — so anything added must be filed so that
`instrument_for()` classifies it correctly.

## 7. PDF URLs

Documents live under `/files/assets/public/...`, frequently with a version segment (`/v/1/`, `/v/5/`).
Some links are wrapped in a redirector (`?url=https%3A%2F%2F...`) — unwrap and URL-decode those
before fetching. Link text usually carries the size, e.g. `Signage(PDF, 510KB)`, which is a useful
sanity check against what you actually downloaded.

## 8. ⚠️ Verify every file before committing it

**This has gone wrong before.** Fifteen files were once committed to `documents/lep/` under names
promising real content, and were actually 403 bodies and Cloudflare challenge pages; they had to be
deleted (recorded in `documents/DOCUMENT_INDEX.md`). Because the document tools search `.txt` and
PDF content, junk surfaces as an *answer to a planning question* — which is the worst possible
place for it.

A scraper saves whatever the server returned. Check, at minimum:

```bash
file documents/dcp/new-file.pdf          # must say "PDF document"
ls -la documents/dcp/new-file.pdf        # compare against the size in the link text
.venv/bin/python -c "
import fitz, sys
d = fitz.open(sys.argv[1])
print(d.page_count, 'pages')
print(d[0].get_text()[:400])              # must be the document, not 'Access Denied'
" documents/dcp/new-file.pdf
```

Then **open it** and confirm it is the document you meant and contains no private information —
`_quarantined/README.md` records a third party's real signed SEE that was mistaken for a blank
template. Everything under `documents/` is committed and therefore published.

Finally, record it in `documents/DOCUMENT_INDEX.md` with its source URL and retrieval date.

## 9. Be a good citizen

This is a public council site serving the community. Crawl gently: a small page cap, sequential
requests rather than parallel bursts, and a real user agent. Everything here is public information
published for exactly this purpose, but there is no reason to be expensive about collecting it.

---

## Worked example

`fetch_council_documents.py` at the repo root applies all of the above: it fetches a declared list
of (url, category, filename), skips anything already present, validates that each download is a
real PDF whose first page contains text, and deletes anything that fails rather than leaving it on
disk. Run it, read its report, inspect the new files, then update `DOCUMENT_INDEX.md` by hand.

```bash
uv sync --extra scraping
.venv/bin/playwright install chromium
.venv/bin/python fetch_council_documents.py          # add --dry-run to list without downloading
```
