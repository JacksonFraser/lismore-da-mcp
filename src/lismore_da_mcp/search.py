"""Full-text search and section extraction over the documents/ tree.

PDFs are addressed by page and .txt extracts by line; every result carries a
`location` string that read_dcp_section accepts either way.
"""

from pathlib import Path

import fitz  # PyMuPDF

from lismore_da_mcp.observability import record_document_error

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
    except (OSError, RuntimeError, ValueError) as e:
        # A document that cannot be read contributes no hits. Returning an error
        # dict here put it into the result list, where it sorted as a scoreless
        # "hit" and could be handed to the caller with no file or context. The
        # failure belongs in the log, not in the answer.
        record_document_error("search", pdf_path.name, type(e).__name__, str(e))
        return []

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
    except OSError as e:
        record_document_error("search", text_path.name, type(e).__name__, str(e))
        return []

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

def search_all(
    query: str, chapter: str = "", max_results: int = 10, per_document: int = 5
) -> list[dict]:
    """Search every document, using the FTS index when one is available.

    Falls back to a full scan when the index is missing or unreadable, so the
    server still answers — just slowly — rather than failing. Results are the
    same either way: the index only narrows which segments get scored, and a line
    can only score above zero if its segment contains a query token.
    """
    tokens = _query_tokens(query)
    if not tokens:
        return []

    from lismore_da_mcp.index import lookup

    candidates = lookup(tokens, chapter)
    if candidates is None:
        results = []
        for path in searchable_documents(chapter):
            results.extend(search_document(path, query))
        results.sort(key=lambda r: r.get("score", 0), reverse=True)
        return [annotate_instrument(r) for r in results[:max_results]]

    # FTS5 returns matching segments in its own order. Scores tie constantly —
    # every hit on a single-token query scores 1 — so the order candidates are
    # visited decides which survive the per-document cap and the global top-N.
    # Sort into the same order a full scan walks them (documents as
    # searchable_documents lists them, then page/segment number) so the two paths
    # cannot disagree.
    document_order = {p.name: i for i, p in enumerate(searchable_documents(chapter))}
    candidates = sorted(
        candidates,
        key=lambda row: (document_order.get(row[0], len(document_order)), row[3]),
    )

    per_file: dict[str, list[dict]] = {}
    for file_name, _category, kind, number, body in candidates:
        for i, score, matched, context in _score_lines(body.split("\n"), tokens, query):
            if kind == "page":
                where = {"page": number, "location": f"page {number}"}
            else:
                where = {"line": i + 1, "location": f"line {i + 1}"}
            per_file.setdefault(file_name, []).append(
                {"score": score, "matched_terms": matched, **where,
                 "context": context, "file": file_name}
            )

    # A full scan caps each document at `per_document` hits before ranking
    # globally, which keeps one large document from filling every slot — the LEP
    # text alone would otherwise take 9 of 10 for a query like "acid sulfate
    # soils". Reproduced here so the index changes speed and nothing else.
    results = []
    for file_name in per_file:
        hits = per_file[file_name]
        hits.sort(key=lambda r: r["score"], reverse=True)
        results.extend(hits[:per_document])

    results.sort(key=lambda r: r.get("score", 0), reverse=True)
    return [annotate_instrument(r) for r in results[:max_results]]


def annotate_instrument(result: dict) -> dict:
    """Tag a search hit with the planning instrument it comes from.

    The DCP has parallel chapters for LEP 2012 and LEP 2000 land, and they were
    previously indistinguishable in results — so a superseded setback could be
    quoted as a current control.
    """
    from lismore_da_mcp.data.instruments import (
        instrument_for,
        is_superseded,
        superseded_note_for,
    )

    file_name = result.get("file", "")
    category = ""
    for path in searchable_documents():
        if path.name == file_name:
            category = path.parent.name
            break

    result["instrument"] = instrument_for(file_name, category)
    if is_superseded(file_name):
        result["superseded"] = superseded_note_for(file_name)
    return result


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

# Output cap. A DCP chapter can run to hundreds of pages, and returning all of it
# would swamp the caller's context for no benefit.
MAX_SECTION_CHARS = 10000


def _truncate(text: str, resume_hint: str) -> str:
    """Cap the output, saying so and how to get the rest.

    Cutting silently at 10,000 characters left a reader with no way to know
    content was dropped, let alone where it stopped — so a provision continuing
    past the cut simply looked absent.
    """
    if len(text) <= MAX_SECTION_CHARS:
        return text
    return (
        text[:MAX_SECTION_CHARS]
        + f"\n\n--- TRUNCATED at {MAX_SECTION_CHARS} characters. "
        + resume_hint
        + " ---"
    )


def extract_pdf_section(pdf_path: Path, start_page: int = 1, end_page: int = None) -> str:
    """Extract text from specific pages of a PDF."""
    try:
        doc = fitz.open(pdf_path)
        if end_page is None:
            end_page = len(doc)

        text = ""
        last_page = start_page
        for page_num in range(start_page - 1, min(end_page, len(doc))):
            page = doc[page_num]
            text += f"\n--- Page {page_num + 1} ---\n"
            text += page.get_text()
            if len(text) <= MAX_SECTION_CHARS:
                last_page = page_num + 1

        doc.close()
        return _truncate(
            text,
            f"Content continues past page {last_page}. Request a later page range "
            f"(e.g. start_page={last_page}) to read on.",
        )
    except (OSError, RuntimeError, ValueError) as e:
        # The caller asked for this document by name, so the error is the answer
        # to their question — unlike search, where it would masquerade as a hit.
        record_document_error("read", pdf_path.name, type(e).__name__, str(e))
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

        first = max(start_line, 1)
        last = min(end_line, len(lines))
        selected = lines[first - 1:last]
        header = f"--- {text_path.name}, lines {first}-{last} of {len(lines)} ---\n"
        body = header + '\n'.join(selected)

        # Report the line the caller can resume from, rather than the requested
        # end — which is what they would otherwise assume they had received.
        if len(body) > MAX_SECTION_CHARS:
            consumed = body[:MAX_SECTION_CHARS].count("\n")
            resume = first + max(consumed - 1, 0)
            return _truncate(
                body,
                f"Content continues at line {resume} of {len(lines)}. "
                f"Request start_line={resume} to read on.",
            )
        return body
    except OSError as e:
        record_document_error("read", text_path.name, type(e).__name__, str(e))
        return f"Error reading text file: {e}"

def extract_document_section(path: Path, start: int = 1, end: int = None) -> str:
    """Read a section of one document — pages for PDFs, lines for text extracts."""
    if path.suffix.lower() == ".txt":
        return extract_text_section(path, start, end)
    return extract_pdf_section(path, start, end)

def list_available_documents() -> list[dict]:
    """List all available documents in the documents directory."""
    documents = []

    from lismore_da_mcp.data.instruments import instrument_for, is_superseded

    if DOCS_DIR.exists():
        for subdir in DOC_CATEGORIES:
            subdir_path = DOCS_DIR / subdir
            if subdir_path.exists():
                for file in sorted(subdir_path.iterdir()):
                    if file.suffix.lower() in LISTABLE_SUFFIXES:
                        entry = {
                            "category": subdir,
                            "filename": file.name,
                            "path": str(file.relative_to(DOCS_DIR)),
                            "addressed_by": "line number" if file.suffix.lower() == ".txt" else "page number",
                            "instrument": instrument_for(file.name, subdir),
                        }
                        if is_superseded(file.name):
                            entry["superseded"] = True
                        documents.append(entry)

    return documents
