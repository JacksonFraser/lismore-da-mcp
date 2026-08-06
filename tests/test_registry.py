"""Tool registration.

A tool used to live in three distant places — the TOOLS list, a branch of the
if/elif chain, and the README — with nothing enforcing they agreed. The registry
makes schema and handler one declaration; these tests guard the properties that
used to be maintained by hand.
"""

import re
from pathlib import Path

import pytest

from lismore_da_mcp import registry
from lismore_da_mcp.server import TOOLS

README = Path(__file__).resolve().parent.parent / "README.md"


def readme_tools() -> set[str]:
    """Tool names from the README's tool tables.

    Rows look like `| \\`get_zone_info\\` | ... |`, and only the tool tables put a
    backticked identifier in the first cell.
    """
    rows = re.findall(r"^\|\s*`([a-z_]+)`\s*\|", README.read_text(), re.MULTILINE)
    return set(rows)


class TestRegistration:
    def test_registry_and_readme_agree(self):
        """The count used to be written out as a literal here, in the README and
        in a test docstring, so adding a tool meant editing three unrelated files
        and CI failed on the two you forgot — it caught out three separate
        changes on 2026-08-01 alone (PLAN.md Housekeeping). The registry already
        knows how many tools there are; the README is the thing worth checking
        against it, because it is the part a human maintains."""
        registered = set(registry.registered())
        assert registered == readme_tools(), (
            "README tool table and the registry disagree. Missing from the README: "
            f"{sorted(registered - readme_tools())}; listed but not registered: "
            f"{sorted(readme_tools() - registered)}"
        )

    def test_readme_states_the_right_total(self):
        stated = re.search(r"^(\d+) tools in total\.", README.read_text(), re.MULTILINE)
        assert stated, "README no longer states a tool total"
        assert int(stated.group(1)) == len(registry.registered())

    def test_registry_and_tools_list_agree(self):
        assert {t.name for t in TOOLS} == set(registry.registered())

    def test_every_tool_has_a_handler(self):
        assert all(callable(t.handler) for t in registry.registered().values())

    def test_every_tool_has_a_description(self):
        assert [n for n, t in registry.registered().items() if not t.description.strip()] == []

    def test_schema_is_an_object_schema(self):
        for name, t in registry.registered().items():
            assert t.schema["type"] == "object", name
            assert isinstance(t.schema["properties"], dict), name

    def test_order_is_declaration_order(self):
        """Clients see tools in this order, so it should be stable and reviewable
        rather than dependent on iteration order elsewhere."""
        assert [t.name for t in TOOLS] == list(registry.registered())


class TestDecoratorRefusesBadDeclarations:
    """Registration errors surface at import, not on the call that needed them."""

    def test_duplicate_name_rejected(self):
        with pytest.raises(ValueError, match="already registered"):
            registry.tool(name="get_zone_info", description="x")(lambda a: None)

    def test_required_argument_must_be_declared(self):
        with pytest.raises(ValueError, match="not declared"):
            registry.tool(
                name="a_brand_new_tool",
                description="x",
                properties={"present": {"type": "string"}},
                required=["absent"],
            )(lambda a: None)


class TestValidation:
    """Moved from server.py with the dispatcher; behaviour must not have changed."""

    def test_unknown_tool(self):
        error = registry.validate_arguments("no_such_tool", {})
        assert "Unknown tool" in error["error"]

    def test_unknown_argument(self):
        error = registry.validate_arguments("get_zone_info", {"zone": "R2"})
        assert "Unrecognised" in error["error"]
        assert "zone_code" in error["accepted_arguments"]

    def test_missing_required(self):
        assert "Missing" in registry.validate_arguments("get_zone_info", {})["error"]

    def test_blank_string_counts_as_missing(self):
        error = registry.validate_arguments(
            "check_permissibility", {"zone_code": "R2", "land_use": "   "}
        )
        assert error is not None

    def test_valid_call_passes(self):
        assert registry.validate_arguments("get_zone_info", {"zone_code": "R2"}) is None

    def test_optional_arguments_may_be_omitted(self):
        assert registry.validate_arguments("get_residential_standards", {}) is None


class TestHandlersAreDirectlyCallable:
    """The point of the split: a handler can be exercised without the dispatcher."""

    def test_handler_returns_content_blocks(self):
        handler = registry.get("get_zone_info").handler
        result = handler({"zone_code": "R2"})
        assert len(result) == 1 and result[0].text

    def test_handler_for_a_no_argument_tool(self):
        assert registry.get("get_contact_info").handler({})[0].text
