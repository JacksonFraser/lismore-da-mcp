"""Search and read the planning document library."""

import json

from mcp.types import TextContent

from lismore_da_mcp.config import DOCS_DIR
from lismore_da_mcp.data.instruments import superseded_note_for
from lismore_da_mcp.data.instruments import is_superseded
from lismore_da_mcp.registry import tool
from lismore_da_mcp.search import extract_document_section
from lismore_da_mcp.search import find_document
from lismore_da_mcp.search import list_available_documents
from lismore_da_mcp.search import search_all
from lismore_da_mcp.search import searchable_documents


@tool(
    name='search_dcp',
    description="Search Lismore's planning documents (DCP chapters, LEP documents and text extracts, forms, fee schedules, and the NSW exempt-development fact sheets) for specific provisions, requirements, or keywords. Matches on significant terms in the query, not just the exact phrase, so multi-word conceptual queries still surface partial matches. Each hit reports the file plus a location — a page number for PDFs, a line number for text extracts — that read_dcp_section accepts directly.",
    properties={
        'query': {'type': 'string', 'description': 'Search term or phrase to find in DCP documents'},
        'chapter': {'type': 'string', 'description': "Optional: specific chapter to search (e.g., 'chapter-1', 'chapter-7', 'nimbin')"},
    },
    required=['query'],
)
def search_dcp(arguments: dict):
    query = arguments.get("query", "")
    chapter = arguments.get("chapter", "")

    if not DOCS_DIR.exists():
        return [TextContent(
            type="text",
            text=json.dumps({"error": "Documents directory not found"})
        )]

    # Searches all planning document categories, not just dcp/ — a query about
    # e.g. flood clauses, exempt development or heritage schedules may only be
    # answerable from lep/, exempt-development/ or forms/. Uses the FTS index
    # when present and falls back to a full scan when it isn't.
    top_results = search_all(query, chapter)

    if not top_results:
        return [TextContent(
            type="text",
            text=json.dumps({
                "query": query,
                "results": [],
                "message": "No matches found. Try different search terms."
            }, indent=2)
        )]

    # Drop the internal ranking score before returning.
    for r in top_results:
        r.pop("score", None)

    return [TextContent(
        type="text",
        text=json.dumps({
            "query": query,
            "results": top_results
        }, indent=2)
    )]


@tool(
    name='read_dcp_section',
    description='Read a section from any planning document — a DCP chapter, an LEP text extract, a form, a fee schedule, or an exempt-development fact sheet. Use list_documents for filenames.',
    properties={
        'chapter': {'type': 'string', 'description': "Document filename or a fragment of it (e.g., 'chapter-7-off-street-carparking.pdf', 'lep-2012-nsw-full.txt', 'fences')"},
        'start_page': {'type': 'integer', 'description': 'Starting page number, or starting line number for .txt documents (default: 1)'},
        'end_page': {'type': 'integer', 'description': 'Ending page number, or ending line number for .txt documents (optional; .txt defaults to a 200-line window)'},
    },
    required=['chapter'],
)
def read_dcp_section(arguments: dict):
    chapter = arguments.get("chapter", "")
    start_page = arguments.get("start_page", 1)
    end_page = arguments.get("end_page")

    # Resolve across every category, not just dcp/ — search_dcp can return a hit in
    # lep/ or exempt-development/, and there was previously no way to open it.
    doc_path = find_document(chapter)

    if not doc_path:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Document '{chapter}' not found",
                "available": [str(p.relative_to(DOCS_DIR)) for p in searchable_documents()]
            }, indent=2)
        )]

    text = extract_document_section(doc_path, start_page, end_page)
    # A reader who opens a chapter directly gets no search result to carry the
    # warning, so it goes on the content itself.
    if is_superseded(doc_path.name):
        text = f"⚠️ SUPERSEDED FOR MOST LAND — {superseded_note_for(doc_path.name)}\n\n{text}"
    return [TextContent(
        type="text",
        text=text
    )]


@tool(
    name='list_documents',
    description='List all available planning documents (DCP chapters, LEP documents and text extracts, forms, fee schedules, exempt-development fact sheets), with how each is addressed by read_dcp_section.',
    properties={},
)
def list_documents(arguments: dict):
    docs = list_available_documents()
    return [TextContent(
        type="text",
        text=json.dumps({"documents": docs}, indent=2)
    )]
