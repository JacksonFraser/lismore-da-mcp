"""Paths and runtime configuration shared across the package."""

import os
from pathlib import Path

# Path to documents directory
DOCS_DIR = Path(__file__).parent.parent.parent / "documents"

# Served publicly over HTTP. Generated files carry applicant details, so in this
# mode they go to a per-request temp dir and are returned inline, never kept.
PUBLIC_MODE = os.environ.get("MCP_TRANSPORT", "stdio").lower() == "http"

# Every category the document tools search and list. A directory missing from
# here is unreachable through any tool.
DOC_CATEGORIES = ["dcp", "lep", "forms", "fees", "exempt-development", "business",
                  "legislation"]

# .txt because parts of the LEP only exist here as scraped text extracts.
# Everything under documents/ is searched as real content, so check a new file
# is not a scraper error page before adding it (scripts/check_documents.py).
SEARCHABLE_SUFFIXES = {".pdf", ".txt"}

LISTABLE_SUFFIXES = {".pdf", ".txt", ".xls", ".xlsx"}

# Path to the blank SEE PDF template
SEE_TEMPLATE_PATH = DOCS_DIR / "forms" / "statement-of-environmental-effects-minor-development.pdf"
