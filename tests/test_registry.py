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


class TestArgumentAliases:
    """ROADMAP.md A1. Run 2 of SCENARIOS.md sent five natural spellings of
    arguments the server has — floor area, cost, zone — and all five were
    refused. Rewrite what we know, refuse what we do not, never default."""

    @staticmethod
    def dispatch(tool, arguments):
        import asyncio
        import json

        from lismore_da_mcp.server import call_tool

        text = asyncio.run(call_tool(tool, arguments))[0].text
        try:
            return json.loads(text)
        except ValueError:
            return {"text": text}

    @pytest.mark.parametrize("tool,arguments", [
        # The five RB-01 calls, verbatim.
        ("calculate_da_fees", {"cost_of_works": 50000, "floor_area": 80, "development_type": "cafe"}),
        ("get_parking_rates", {"development_type": "cafe", "floor_area": 80}),
        ("get_setback_requirements", {"setback_type": "front", "zone_code": "R1"}),
        ("generate_see_draft", {"property_address": "12 Keen Street, Lismore NSW 2480", "zone": "E2",
                                "proposed_use": "cafe", "development_type": "change of use",
                                "floor_area_sqm": 80}),
        ("calculate_da_fees", {"estimated_cost": 50000, "floor_area_sqm": 80, "development_type": "cafe"}),
    ])
    def test_the_spellings_run_2_sent_are_accepted(self, tool, arguments):
        result = self.dispatch(tool, arguments)
        assert "Unrecognised" not in str(result.get("error", "")), result

    def test_every_alias_lands_on_the_argument_the_tool_declares(self):
        """Every tool, every concept it has an argument for, every alias it does
        not itself declare — each renamed to that one argument."""
        checked = 0
        for tool, schema in registry.schemas().items():
            properties = schema.get("properties", {})
            for concept in registry.ARGUMENT_CONCEPTS.values():
                target = registry._alias_target(tool, properties, concept)
                if target is None:
                    continue
                assert target in properties
                for alias in concept["aliases"] - set(properties):
                    resolved, error = registry.resolve_aliases(tool, {alias: 1})
                    assert error is None and resolved == {target: 1}, (tool, alias, resolved)
                    checked += 1
        assert checked > 100, "the aliases are not being exercised"

    def test_an_alias_never_shadows_a_tools_own_argument(self):
        """The collision guard. A name a tool declares is that tool's argument,
        whatever it means elsewhere — 'zone' is the setbacks tool's own."""
        for tool, schema in registry.schemas().items():
            properties = schema.get("properties", {})
            for concept in registry.ARGUMENT_CONCEPTS.values():
                for alias in concept["aliases"] & set(properties):
                    resolved, _ = registry.resolve_aliases(tool, {alias: 1})
                    assert resolved == {alias: 1}, (tool, alias)

    def test_no_alias_belongs_to_two_concepts(self):
        seen = {}
        for name, concept in registry.ARGUMENT_CONCEPTS.items():
            for alias in concept["aliases"]:
                assert alias not in seen, f"{alias!r} is in both {seen.get(alias)!r} and {name!r}"
                seen[alias] = name

    def test_every_target_is_a_real_argument(self):
        declared = {p for s in registry.schemas().values() for p in s.get("properties", {})}
        for name, concept in registry.ARGUMENT_CONCEPTS.items():
            for target in concept["targets"]:
                assert target in declared, (name, target)
            for tool in concept.get("development_type_in", ()):
                assert "development_type" in registry.schemas()[tool]["properties"]

    @pytest.mark.parametrize("name", [
        "area_sqm",                 # signage: the sign's area, not a floor area
        "existing_spaces_on_site",  # parking: feeds the CBD credit, not spaces provided
        "existing_parking_spaces",
        "development_type",         # the use in two tools, "what you are doing" in others
        "site_area_sqm",
    ])
    def test_names_that_mean_different_things_are_not_aliases(self, name):
        assert all(name not in c["aliases"] for c in registry.ARGUMENT_CONCEPTS.values())

    def test_signage_does_not_take_a_floor_area_as_its_area(self):
        result = self.dispatch("get_signage_requirements",
                               {"sign_type": "wall sign", "floor_area": 80})
        assert "Unrecognised argument(s): floor_area" in result["error"]

    def test_an_unknown_argument_is_still_refused_the_same_way(self):
        result = self.dispatch("get_zone_info", {"colour": "R2"})
        assert result["error"] == "Unrecognised argument(s): colour"
        assert "zone_code" in result["accepted_arguments"]

    def test_two_names_with_different_values_are_refused(self):
        result = self.dispatch("calculate_da_fees", {"development_cost": 1000, "cost": 2000})
        assert "both give development_cost" in result["error"]

    def test_two_names_with_the_same_value_are_one_argument(self):
        result = self.dispatch("calculate_da_fees", {"development_cost": 1000, "cost": 1000})
        assert "error" not in result
