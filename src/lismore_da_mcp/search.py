"""Full-text search and section extraction over the documents/ tree.

PDFs are addressed by page and .txt extracts by line; every result carries a
`location` string that read_dcp_section accepts either way.
"""

from pathlib import Path

import fitz  # PyMuPDF

from lismore_da_mcp.config import (
    DOC_CATEGORIES,
    DOCS_DIR,
    LISTABLE_SUFFIXES,
    SEARCHABLE_SUFFIXES,
)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "into", "is", "it", "of", "on", "or", "that", "the", "to", "was",
    "what", "when", "where", "will", "with",
}

def _query_tokens(query: str) -> list[str]:
    """Break a query into significant lowercase tokens (drops stopwords/short words)."""
    words = "".join(c if c.isalnum() else " " for c in query.lower()).split()
    tokens = [w for w in words if len(w) >= 3 and w not in STOPWORDS]
    return tokens or words  # fall back to raw words if everything got filtered out

def _score_lines(lines: list[str], tokens: list[str], query: str) -> list[tuple[int, int, list[str], str]]:
    """Score each line by how many distinct query tokens it contains.

    Returns (index, score, matched_terms, context) for every line that matched at
    least one token. Requiring the full phrase verbatim would return nothing for a
    query like "food and drink premises change of use"; scoring by token count still
    ranks a full-phrase line highest while surfacing lines covering only part of the
    concept.
    """
    hits = []
    for i, line in enumerate(lines):
        line_lower = line.lower()
        matched = [t for t in tokens if t in line_lower]
        if not matched:
            continue

        score = len(matched)
        if query.lower() in line_lower:
            score += len(tokens)  # exact-phrase bonus, still just a ranking boost

        start = max(0, i - 2)
        end = min(len(lines), i + 3)
        context = '\n'.join(lines[start:end])
        hits.append((i, score, matched, context.strip()[:500]))
    return hits

def search_pdf(pdf_path: Path, query: str, max_results: int = 5) -> list[dict]:
    """Search a PDF for text matching the query, scored per line."""
    tokens = _query_tokens(query)
    if not tokens:
        return []

    scored = []
    try:
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            lines = doc[page_num].get_text().split('\n')
            for _, score, matched, context in _score_lines(lines, tokens, query):
                scored.append({
                    "score": score,
                    "matched_terms": matched,
                    "page": page_num + 1,
                    "location": f"page {page_num + 1}",
                    "context": context,
                    "file": pdf_path.name
                })

        doc.close()
    except Exception as e:
        return [{"error": str(e)}]

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:max_results]

def search_text_file(text_path: Path, query: str, max_results: int = 5) -> list[dict]:
    """Search a plain-text document, reporting line numbers where a PDF reports pages.

    read_dcp_section takes the same line numbers as its start/end range for .txt files,
    so a hit here can be opened directly.
    """
    tokens = _query_tokens(query)
    if not tokens:
        return []

    try:
        lines = text_path.read_text(encoding="utf-8", errors="replace").split('\n')
    except Exception as e:
        return [{"error": str(e)}]

    scored = [
        {
            "score": score,
            "matched_terms": matched,
            "line": i + 1,
            "location": f"line {i + 1}",
            "context": context,
            "file": text_path.name
        }
        for i, score, matched, context in _score_lines(lines, tokens, query)
    ]

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:max_results]

def search_document(path: Path, query: str, max_results: int = 5) -> list[dict]:
    """Search one document, dispatching on file type."""
    if path.suffix.lower() == ".txt":
        return search_text_file(path, query, max_results)
    return search_pdf(path, query, max_results)

def searchable_documents(chapter: str = "") -> list[Path]:
    """Every searchable document across all categories, optionally filtered by filename."""
    paths = []
    for subdir in DOC_CATEGORIES:
        subdir_path = DOCS_DIR / subdir
        if not subdir_path.exists():
            continue
        for path in sorted(subdir_path.iterdir()):
            if path.suffix.lower() not in SEARCHABLE_SUFFIXES:
                continue
            if chapter and chapter.lower() not in path.name.lower():
                continue
            paths.append(path)
    return paths

def find_document(name: str) -> Path | None:
    """Locate a document by filename or filename fragment, across all categories."""
    candidates = [
        path for path in searchable_documents()
        if name.lower() in path.name.lower()
    ]
    if not candidates:
        return None
    # Prefer an exact filename match over a fragment match ('chapter-1' would
    # otherwise resolve by directory order rather than by what was asked for).
    for path in candidates:
        if path.name.lower() == name.lower():
            return path
    return candidates[0]

def extract_pdf_section(pdf_path: Path, start_page: int = 1, end_page: int = None) -> str:
    """Extract text from specific pages of a PDF."""
    try:
        doc = fitz.open(pdf_path)
        if end_page is None:
            end_page = len(doc)

        text = ""
        for page_num in range(start_page - 1, min(end_page, len(doc))):
            page = doc[page_num]
            text += f"\n--- Page {page_num + 1} ---\n"
            text += page.get_text()

        doc.close()
        return text[:10000]  # Limit output size
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_section(text_path: Path, start_line: int = 1, end_line: int = None) -> str:
    """Extract a line range from a plain-text document.

    Text extracts have no pages, so read_dcp_section's start/end are read as line
    numbers here — matching the line numbers search_text_file reports.
    """
    try:
        lines = text_path.read_text(encoding="utf-8", errors="replace").split('\n')
        if end_line is None:
            end_line = min(len(lines), max(start_line, 1) + 199)  # default window

        selected = lines[max(start_line, 1) - 1:min(end_line, len(lines))]
        header = f"--- {text_path.name}, lines {start_line}-{min(end_line, len(lines))} of {len(lines)} ---\n"
        return (header + '\n'.join(selected))[:10000]
    except Exception as e:
        return f"Error reading text file: {e}"

def extract_document_section(path: Path, start: int = 1, end: int = None) -> str:
    """Read a section of one document — pages for PDFs, lines for text extracts."""
    if path.suffix.lower() == ".txt":
        return extract_text_section(path, start, end)
    return extract_pdf_section(path, start, end)

def list_available_documents() -> list[dict]:
    """List all available documents in the documents directory."""
    documents = []

    if DOCS_DIR.exists():
        for subdir in DOC_CATEGORIES:
            subdir_path = DOCS_DIR / subdir
            if subdir_path.exists():
                for file in sorted(subdir_path.iterdir()):
                    if file.suffix.lower() in LISTABLE_SUFFIXES:
                        documents.append({
                            "category": subdir,
                            "filename": file.name,
                            "path": str(file.relative_to(DOCS_DIR)),
                            "addressed_by": "line number" if file.suffix.lower() == ".txt" else "page number",
                        })

    return documents
