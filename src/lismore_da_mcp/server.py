"""
Lismore Development Application MCP Server

Wiring only. Tools live in lismore_da_mcp.tools, one module per domain, each
handler carrying its own schema — see registry.py.

It also re-exports names that used to live here, so older
`from lismore_da_mcp.server import X` imports keep working. New code should
import from the owning module.
"""

import asyncio
import json

import mcp.types as types
from mcp.types import TextContent

# Importing the tools package is what registers every tool.
import lismore_da_mcp.tools  # noqa: F401  (side-effecting import, must come first)
from lismore_da_mcp import config
from lismore_da_mcp.app import server

# --- re-exports (see module docstring) --------------------------------------
from lismore_da_mcp.config import (  # noqa: F401
    DOC_CATEGORIES,
    DOCS_DIR,
    LISTABLE_SUFFIXES,
    PUBLIC_MODE,
    SEARCHABLE_SUFFIXES,
    SEE_TEMPLATE_PATH,
)
from lismore_da_mcp.data.contacts import CONTACT_INFO  # noqa: F401
from lismore_da_mcp.data.definitions import (  # noqa: F401
    CATCHALL_TERM,
    LAND_USE_DEFINITIONS,
    LAND_USE_HIERARCHY,
)
from lismore_da_mcp.data.fees import DA_FEE_BRACKETS, DA_FEE_SCHEDULE_YEAR  # noqa: F401
from lismore_da_mcp.data.flood import FLOOD_AREAS  # noqa: F401
from lismore_da_mcp.data.instruments import (  # noqa: F401
    SUPERSEDED_NOTE,
    instrument_for,
    is_superseded,
)
from lismore_da_mcp.data.parking import PARKING_RATES  # noqa: F401
from lismore_da_mcp.data.referrals import REFERRAL_REQUIREMENTS  # noqa: F401
from lismore_da_mcp.data.see_templates import SEE_TEMPLATES  # noqa: F401
from lismore_da_mcp.data.zones import ZONES  # noqa: F401
from lismore_da_mcp.fees import calculate_da_fee  # noqa: F401
from lismore_da_mcp.landuse import (  # noqa: F401
    canonical_use,
    classify_land_use,
    match_land_use,
)
from lismore_da_mcp.observability import (
    OUTCOME_INVALID_ARGUMENTS,
    OUTCOME_LOCAL_ONLY,
    OUTCOME_OK,
    timed_tool_call,
)
from lismore_da_mcp.registry import (
    local_only_refusal,
    mcp_tools,
    registered,
    resolve_aliases,
    validate_arguments,
)
from lismore_da_mcp.search import (  # noqa: F401
    STOPWORDS,
    _query_tokens,
    _score_lines,
    extract_document_section,
    extract_pdf_section,
    extract_text_section,
    find_document,
    list_available_documents,
    search_all,
    search_document,
    search_pdf,
    search_text_file,
    searchable_documents,
)
from lismore_da_mcp.see.fields import (  # noqa: F401
    PURPOSE_WRITTEN_SEE_HEADINGS,
    RESIDENTIAL_ZONES,
    SEE_COMMENT_FIELDS,
    SEE_FORM_FIELDS,
    SEE_QUESTIONS,
    SEE_TEMPLATE_SCOPE,
)
from lismore_da_mcp.see.fill import fill_see_pdf  # noqa: F401
from lismore_da_mcp.see.generate import generate_see_form_data  # noqa: F401
from lismore_da_mcp.see.layout import (  # noqa: F401
    CHECKBOX_GLYPHS,
    SEE_LAYOUT_EXPECTED,
    _answer_boxes,
    _checkbox_rects,
    see_layout,
)
from lismore_da_mcp.see.parsers import (  # noqa: F401
    parse_land_identifier,
    parse_street_address,
)
from lismore_da_mcp.transport import (  # noqa: F401
    _RateLimitMiddleware,
    build_http_app,
    run,
    run_http,
)


def _tools():
    """The registered tools, as MCP Tool objects."""
    return mcp_tools()


# Kept as module attributes because callers and tests read them directly.
TOOLS = _tools()
TOOL_SCHEMAS = {t.name: t.input_schema for t in TOOLS}


async def list_tools():
    """List available tools — without the local-only ones on the public server."""
    return mcp_tools(public=config.PUBLIC_MODE)


async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
    """Validate arguments, then hand off to the registered handler.

    `arguments` is never passed to the logger (see observability.py).

    Handlers are synchronous and blocking (PDF extraction, SQLite, outbound
    HTTPS), so they run on a worker thread to keep the event loop free. That is
    safe because they share nothing mutable: connections and documents are
    opened per call and the data dicts are read-only.
    """
    with timed_tool_call(name) as outcome:
        # Before validation: the tool is unavailable whatever the arguments, so
        # asking the caller to fix them first would only cost a round trip — and
        # nothing an applicant typed is looked at. Read at call time rather than
        # bound at import, so a test can switch modes.
        registration = registered().get(name)
        if registration and registration.local_only and config.PUBLIC_MODE:
            outcome[0] = OUTCOME_LOCAL_ONLY
            return [TextContent(type="text",
                                text=json.dumps(local_only_refusal(name), indent=2))]

        # Known aliases first (ROADMAP.md A1), so the gate below sees only the
        # tool's own names and refuses everything else exactly as before.
        arguments, argument_error = resolve_aliases(name, arguments)
        argument_error = argument_error or validate_arguments(name, arguments)
        if argument_error:
            outcome[0] = OUTCOME_INVALID_ARGUMENTS
            return [TextContent(type="text", text=json.dumps(argument_error, indent=2))]

        registration = registered()[name]
        result = await asyncio.to_thread(registration.handler, arguments)
        outcome[0] = OUTCOME_OK
        return result


# --- SDK boundary -----------------------------------------------------------
#
# The SDK dispatches to handlers registered against a method name, taking a
# request context and typed params and returning a typed result. The two
# functions above keep their plain shape — a name and a dict in, content blocks
# out — and these adapters translate. That keeps the SDK's shape at one seam
# instead of through every caller and test, which is the seam that moves.


async def _on_call_tool(_context, params: types.CallToolRequestParams) -> types.CallToolResult:
    return types.CallToolResult(content=await call_tool(params.name, params.arguments or {}))


async def _on_list_tools(_context, _params) -> types.ListToolsResult:
    return types.ListToolsResult(tools=await list_tools())


server.add_request_handler("tools/call", types.CallToolRequestParams, _on_call_tool)
server.add_request_handler("tools/list", types.PaginatedRequestParams, _on_list_tools)


# ============================================================================
# Server Entry Point
# ============================================================================

def main():
    """Main entry point. MCP_TRANSPORT=http serves over Streamable HTTP; anything else (or
    unset) keeps the original stdio behavior used by local .mcp.json setups."""
    if PUBLIC_MODE:
        run_http()
    else:
        asyncio.run(run())


if __name__ == "__main__":
    main()
