"""
Lismore Development Application MCP Server

Wiring only. Tools live in lismore_da_mcp.tools, one module per domain, each
handler carrying its own schema — see registry.py.

This module also re-exports a good deal of the package so that
`from lismore_da_mcp.server import X` keeps working for the tests and for
anything embedding this package, which is where these names lived before the
Phase 2 and 2.3 splits. Prefer importing from the owning module in new code.
"""

import json

from mcp.types import TextContent

from lismore_da_mcp.app import server
from lismore_da_mcp.observability import (
    OUTCOME_INVALID_ARGUMENTS,
    OUTCOME_OK,
    configure_logging,
    timed_tool_call,
)
from lismore_da_mcp.registry import mcp_tools, registered, validate_arguments

# Importing the tools package is what registers every tool.
import lismore_da_mcp.tools  # noqa: F401  (side-effecting import, must come first)

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
from lismore_da_mcp.data.flood import FLOOD_PLANNING  # noqa: F401
from lismore_da_mcp.data.instruments import (  # noqa: F401
    SUPERSEDED_NOTE,
    instrument_for,
    is_superseded,
)
from lismore_da_mcp.data.parking import PARKING_RATES  # noqa: F401
from lismore_da_mcp.data.referrals import REFERRAL_REQUIREMENTS  # noqa: F401
from lismore_da_mcp.data.see_templates import SEE_TEMPLATES  # noqa: F401
from lismore_da_mcp.data.standards import RESIDENTIAL_STANDARDS  # noqa: F401
from lismore_da_mcp.data.zones import ZONES  # noqa: F401
from lismore_da_mcp.fees import calculate_da_fee  # noqa: F401
from lismore_da_mcp.landuse import (  # noqa: F401
    canonical_use,
    classify_land_use,
    match_land_use,
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
    estimate_parking_requirement,
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
TOOL_SCHEMAS = {t.name: t.inputSchema for t in TOOLS}


@server.list_tools()
async def list_tools():
    """List available tools."""
    return mcp_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Validate arguments, then hand off to the registered handler.

    `arguments` is never passed to the logger — several tools carry an
    applicant's name and address. See observability.py.
    """
    with timed_tool_call(name) as outcome:
        argument_error = validate_arguments(name, arguments)
        if argument_error:
            outcome[0] = OUTCOME_INVALID_ARGUMENTS
            return [TextContent(type="text", text=json.dumps(argument_error, indent=2))]

        registration = registered()[name]
        result = registration.handler(arguments)
        outcome[0] = OUTCOME_OK
        return result


# ============================================================================
# Server Entry Point
# ============================================================================

def main():
    """Main entry point. MCP_TRANSPORT=http serves over Streamable HTTP; anything else (or
    unset) keeps the original stdio behavior used by local .mcp.json setups."""
    if PUBLIC_MODE:
        run_http()
    else:
        import asyncio
        asyncio.run(run())


if __name__ == "__main__":
    main()
