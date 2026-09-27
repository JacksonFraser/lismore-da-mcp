"""The tools that take an applicant's name stay off the public transport.

ROADMAP.md A4. `fill_see_pdf`, `preview_see_form` and `generate_see_draft`
take a named applicant's details, and the public server is an open,
unauthenticated endpoint with no terms and no privacy policy. None of the three
had ever been called by anyone real, so the privacy design around them was
well-built and entirely unexercised. Switching them off there closes the only
place applicant PII could enter the system, and costs nothing today.

Local (stdio) behaviour must not change: that is where these tools are used.
"""

import asyncio
import json

import pytest

from lismore_da_mcp import config
from lismore_da_mcp.registry import registered
from lismore_da_mcp.server import call_tool, list_tools

PII_TOOLS = {"fill_see_pdf", "preview_see_form", "generate_see_draft"}

# Enough to pass validation, so the stdio test proves the handler ran.
DRAFT_ARGS = {
    "property_address": "12 Keen Street, Lismore",
    "zone_code": "E2",
    "proposed_use": "restaurant or cafe",
    "development_type": "change_of_use",
    "floor_area_sqm": 80,
    "applicant_name": "A Person",
}


@pytest.fixture
def public(monkeypatch):
    monkeypatch.setattr(config, "PUBLIC_MODE", True)


def _names(tools):
    return {t.name for t in tools}


def test_exactly_the_applicant_name_tools_are_local_only():
    """Pinned as a set, both ways: a new tool taking an applicant's name must
    be marked, and nothing else is hidden from the public server by accident.
    The rule it encodes is the argument, so it is checked against the schemas
    rather than only against a list."""
    local_only = {n for n, t in registered().items() if t.local_only}
    assert local_only == PII_TOOLS
    takes_a_name = {n for n, t in registered().items()
                    if "applicant_name" in t.schema["properties"]}
    assert takes_a_name <= local_only


def test_public_server_does_not_list_them(public):
    listed = _names(asyncio.run(list_tools()))
    assert not listed & PII_TOOLS
    assert listed == set(registered()) - PII_TOOLS


def test_stdio_still_lists_them(monkeypatch):
    monkeypatch.setattr(config, "PUBLIC_MODE", False)
    assert PII_TOOLS <= _names(asyncio.run(list_tools()))


@pytest.mark.parametrize("name", sorted(PII_TOOLS))
def test_public_call_is_refused_clearly(public, name):
    """A client with a stale tool list can still call one. The refusal says
    the tool exists and where it runs — "unknown tool" would read as a typo —
    and comes before argument validation, so nothing the caller sent is
    examined and they are not asked to fix arguments for a tool they cannot
    use."""
    result = json.loads(asyncio.run(call_tool(name, dict(DRAFT_ARGS)))[0].text)
    assert result["error"] == "not_available_on_the_public_server"
    assert result["tool"] == name
    assert "locally" in result["detail"]
    assert "A Person" not in json.dumps(result)


def test_public_refusal_precedes_validation(public):
    result = json.loads(asyncio.run(call_tool("fill_see_pdf", {"bogus": 1}))[0].text)
    assert result["error"] == "not_available_on_the_public_server"


def test_other_tools_still_answer_publicly(public):
    result = json.loads(asyncio.run(call_tool(
        "check_permissibility", {"zone_code": "E2", "land_use": "shop"}))[0].text)
    assert result["permissibility"] == "permitted_with_consent"


def test_stdio_still_runs_them(monkeypatch):
    monkeypatch.setattr(config, "PUBLIC_MODE", False)
    text = asyncio.run(call_tool("generate_see_draft", dict(DRAFT_ARGS)))[0].text
    assert "not_available_on_the_public_server" not in text
    assert "A Person" in text


def test_refusal_is_logged_as_its_own_outcome(public, caplog):
    """Not as invalid_arguments, which is the usability signal. A count of
    these is the evidence that would justify exposing the tools publicly."""
    with caplog.at_level("INFO"):
        asyncio.run(call_tool("fill_see_pdf", dict(DRAFT_ARGS)))
    lines = [r.getMessage() for r in caplog.records if "tool=fill_see_pdf" in r.getMessage()]
    assert lines and "outcome=local_only" in lines[-1]
    assert "A Person" not in caplog.text
