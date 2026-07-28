"""Calls routed the way a real client makes them.

Every other test invokes `call_tool` directly. The MCP SDK wraps it and runs
`jsonschema.validate(instance=arguments, schema=tool.inputSchema)` **before**
dispatching, so a schema constraint can reject a call that the handler would
have accepted — and no direct-call test can see it.

That is not hypothetical. `minor_development_type` carried an `enum`, so the
synonym resolution added in 3.1/3.2 was dead over HTTP: "shed" was rejected by
schema validation and the handler never ran. Every direct-call test passed. It
was found by trying the tool with curl.
"""

import asyncio
import json

import mcp.types as types
import pytest

import lismore_da_mcp.server  # noqa: F401  (registers the tools)
from lismore_da_mcp.app import server
from lismore_da_mcp.registry import registered

MINIMAL_SEE = {
    "applicant_name": "A Person",
    "property_address": "12 Keen Street, Lismore NSW 2480",
    "lot_dp": "Lot 12 DP 758651",
    "zone_code": "R2",
    "proposed_use": "dwelling house",
    "development_type": "dwelling",
    "floor_area_sqm": 40,
}


def through_sdk(name: str, arguments: dict):
    """Invoke a tool the way a connected client does, schema validation included."""
    handler = server.request_handlers[types.CallToolRequest]
    request = types.CallToolRequest(
        method="tools/call",
        params=types.CallToolRequestParams(name=name, arguments=arguments),
    )
    result = asyncio.run(handler(request)).root
    return result.isError, result.content[0].text


class TestSchemaDoesNotBlockAcceptedInput:
    """A schema constraint stricter than the handler silently disables it."""

    @pytest.mark.parametrize("value", [
        "shed", "carport", "pool", "extension", "single storey dwelling",
        "dwelling_single_storey",
    ])
    def test_plain_wording_reaches_the_handler(self, value):
        is_error, text = through_sdk(
            "preview_see_form", {**MINIMAL_SEE, "minor_development_type": value}
        )
        assert not is_error, text
        assert json.loads(text)["success"] is True

    def test_out_of_scope_is_refused_by_the_handler_not_the_schema(self):
        """The handler's refusal names the valid types and points at
        generate_see_draft; a schema enum error says none of that."""
        is_error, text = through_sdk(
            "preview_see_form", {**MINIMAL_SEE, "minor_development_type": "shopping centre"}
        )
        assert not is_error
        payload = json.loads(text)
        assert payload["success"] is False
        assert "generate_see_draft" in payload["blocking_issues"][0]

    def test_no_tool_declares_an_enum(self):
        """No enums anywhere, deliberately.

        Every handler here normalises or resolves its own inputs and refuses with
        a message that names the valid values and, where relevant, points at the
        right tool instead. A schema enum runs *before* the handler and is
        strictly less capable, so it can only ever reject input the handler would
        have accepted.

        Two bugs came from exactly that:

          * `minor_development_type` had an enum, so "shed" and "carport" were
            rejected and the vocabulary resolution was unreachable over the real
            transport, while every direct-call test passed.
          * `plan_type` had `['DP','SP','CP']`, so `"dp"` was rejected even though
            the parser upper-cases it.

        An earlier version of this test checked a hardcoded list of arguments and
        missed the second one. Ban the construct instead of listing its victims.
        """
        offenders = [
            f"{name}.{argument}"
            for name, tool in registered().items()
            for argument, spec in tool.schema.get("properties", {}).items()
            if "enum" in spec
        ]
        assert offenders == [], (
            "Schema enums gate values before the handler runs. State the valid "
            "values in the description and let the handler resolve and refuse."
        )

    @pytest.mark.parametrize("value", ["DP", "dp", "Dp", "sp"])
    def test_plan_type_case_is_normalised_not_rejected(self, value):
        is_error, text = through_sdk("preview_see_form", {
            **MINIMAL_SEE, "minor_development_type": "shed", "plan_type": value,
        })
        assert not is_error, text


class TestOrdinaryCallsStillWork:
    def test_simple_lookup(self):
        is_error, text = through_sdk("get_zone_info", {"zone_code": "RU1"})
        assert not is_error
        assert json.loads(text)["name"] == "Primary Production"

    def test_unknown_argument_still_refused(self):
        is_error, text = through_sdk("get_zone_info", {"zone": "R2"})
        assert "Unrecognised" in text or is_error

    def test_missing_required_still_refused(self):
        is_error, text = through_sdk("get_zone_info", {})
        assert "Missing" in text or is_error
