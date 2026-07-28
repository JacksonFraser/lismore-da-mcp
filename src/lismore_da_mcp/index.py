"""SQLite FTS5 index over the documents/ tree.

Without an index every query re-extracts text from all 41 documents — 902 PDF
pages, ~2.1M characters — which measured 7.4s locally and 16-26s on the hosted
free tier. That is almost entirely PyMuPDF extraction; the line scoring itself is
noise. So the index stores the extracted text and nothing else clever.

Segments are stored at exactly the granularity the scorer already works on:

  * one row per page for a PDF
  * one row per file for a .txt extract

which is how search_pdf and search_text_file split text today. The index narrows
which segments get scored; `_score_lines` then runs unchanged on the stored text,
so results are identical to a full scan — a line can only score above zero if its
segment contains at least one query token, and that is exactly what FTS5 returns.

Uses the stdlib `sqlite3`; no new dependency.
"""

import os
import sqlite3
from pathlib import Path

import fitz  # PyMuPDF

from lismore_da_mcp.config import DOCS_DIR

# Ephemeral on Render, which is fine — it is rebuilt at deploy time by the build
# command configured in the Render dashboard (see render.yaml for why the
# dashboard rather than the Blueprint). If that step is ever removed, search
# still answers: lookup() returns None and the caller falls back to a full scan.
# There is no lazy rebuild — a first request should not pay an ~8s build.
INDEX_PATH = Path(
    os.environ.get("LISMORE_SEARCH_INDEX", str(DOCS_DIR.parent / ".search-index.sqlite3"))
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS segments USING fts5(
    file, category, kind, number UNINDEXED, body
);
"""


def fingerprint(paths) -> str:
    """Identity of the corpus, so a changed documents/ tree forces a rebuild.

    Name and size rather than mtime: a fresh git checkout rewrites mtimes and
    would otherwise trigger a needless rebuild on every deploy.
    """
    return "|".join(f"{p.name}:{p.stat().st_size}" for p in sorted(paths))


def _segments(path: Path):
    """Yield (kind, number, text) for one document."""
    if path.suffix.lower() == ".txt":
        yield "file", 0, path.read_text(encoding="utf-8", errors="replace")
        return
    doc = fitz.open(path)
    try:
        for page_num in range(len(doc)):
            yield "page", page_num + 1, doc[page_num].get_text()
    finally:
        doc.close()


def build_index(paths, index_path: Path = None, force: bool = False) -> dict:
    """Build or refresh the index. Returns a summary dict."""
    index_path = index_path or INDEX_PATH
    want = fingerprint(paths)

    if not force and index_path.exists():
        try:
            with sqlite3.connect(index_path) as conn:
                have = conn.execute(
                    "SELECT value FROM meta WHERE key = 'fingerprint'"
                ).fetchone()
            if have and have[0] == want:
                return {"status": "current", "path": str(index_path)}
        except sqlite3.Error:
            pass  # corrupt or half-written — fall through and rebuild

    index_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = index_path.with_suffix(".building")
    tmp.unlink(missing_ok=True)

    rows = 0
    with sqlite3.connect(tmp) as conn:
        conn.executescript(SCHEMA)
        for path in paths:
            category = path.parent.name
            for kind, number, text in _segments(path):
                if not text.strip():
                    continue
                conn.execute(
                    "INSERT INTO segments (file, category, kind, number, body)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (path.name, category, kind, number, text),
                )
                rows += 1
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('fingerprint', ?)", (want,)
        )
    # Atomic swap, so a concurrent reader never sees a partial index.
    tmp.replace(index_path)
    return {"status": "built", "segments": rows, "documents": len(paths), "path": str(index_path)}


def _match_expression(tokens: list[str]) -> str:
    """OR of the query tokens as FTS5 prefix terms.

    Tokens arrive from _query_tokens already reduced to alphanumerics, but they
    are quoted regardless so an FTS5 operator can never be smuggled in via the
    query string.

    Prefix (`house*`) rather than exact, because the scorer this feeds matches
    substrings: it counts "house" as present in "houses" and "housing", which a
    plain token match would miss and so silently drop real results. Prefix
    matching recovers those.

    It does not recover a token that merely *contains* a query term — "house"
    inside "warehouse" or "townhouse". Those are matched by a full scan and not
    by the index, which is the one place indexed and unindexed search differ.
    Losing them is an improvement rather than a regression: a query for "house"
    surfacing "warehouse" is a false positive nobody asked for. See
    tests/test_index.py, which pins this.
    """
    return " OR ".join('"' + t.replace('"', '""') + '"*' for t in tokens)


def lookup(tokens: list[str], chapter: str = "", index_path: Path = None):
    """Candidate segments for these tokens, or None if there is no usable index.

    Returns (file, category, kind, number, body) tuples. Returning None rather
    than raising lets the caller fall back to a full scan.
    """
    index_path = index_path or INDEX_PATH
    if not tokens or not index_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{index_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        sql = "SELECT file, category, kind, number, body FROM segments WHERE segments MATCH ?"
        params = [_match_expression(tokens)]
        if chapter:
            sql += " AND file LIKE ?"
            params.append(f"%{chapter}%")
        return conn.execute(sql, params).fetchall()
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def index_status(index_path: Path = None) -> dict:
    index_path = index_path or INDEX_PATH
    if not index_path.exists():
        return {"present": False, "path": str(index_path)}
    try:
        with sqlite3.connect(index_path) as conn:
            segments = conn.execute("SELECT count(*) FROM segments").fetchone()[0]
        return {"present": True, "segments": segments, "path": str(index_path)}
    except sqlite3.Error as e:
        return {"present": False, "error": str(e), "path": str(index_path)}


def main() -> None:
    """Entry point for building the index at deploy time."""
    from lismore_da_mcp.search import searchable_documents

    print(build_index(searchable_documents(), force=True))


if __name__ == "__main__":
    main()
