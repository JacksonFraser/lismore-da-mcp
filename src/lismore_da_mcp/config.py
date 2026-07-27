"""Paths and runtime configuration shared across the package."""

import os
from pathlib import Path

# Path to documents directory
DOCS_DIR = Path(__file__).parent.parent.parent / "documents"

# When served over the public Streamable HTTP transport (MCP_TRANSPORT=http), tools that
# generate files must not persist them to shared local disk — one caller's output (which can
# contain another person's name/address) must never be readable by another caller. In this mode
# fill_see_pdf writes to a per-request temp dir, returns the file inline, and deletes it
# immediately instead of writing into the shared documents/output/ tree.
PUBLIC_MODE = os.environ.get("MCP_TRANSPORT", "stdio").lower() == "http"

# Every category the document tools search and list. `exempt-development` holds the
# state-wide NSW DPE fact sheets used for "do I need a DA?" questions; leaving it out
# meant those PDFs shipped with the repo but were unreachable through any tool.
DOC_CATEGORIES = ["dcp", "lep", "forms", "fees", "exempt-development"]

# .txt is included because parts of the LEP only exist here as text extracts
# (legislation.nsw.gov.au and austlii both 403 automated fetches, so they were
# scraped once via Playwright). Note that anything under documents/ is assumed to be
# real content: files that were actually scraper failures — 404 pages, Cloudflare
# challenges — were removed rather than filtered at search time, because a search hit
# quoting a bot-verification page is worse than no hit. Check any new .txt before
# adding it.
SEARCHABLE_SUFFIXES = {".pdf", ".txt"}

LISTABLE_SUFFIXES = {".pdf", ".txt", ".xls", ".xlsx"}

# Path to the blank SEE PDF template
SEE_TEMPLATE_PATH = DOCS_DIR / "forms" / "statement-of-environmental-effects-minor-development.pdf"
