"""Tool surface: schemas, validation, and one valid call per tool.

The point of the smoke pass is that the structural refactor in IMPROVEMENT_PLAN
Phase 2 has something to move against — every tool reachable, returning parseable
output, with schema and handler in agreement.
"""

import json

import pytest

from lismore_da_mcp.server import TOOLS, TOOL_SCHEMAS, ZONES, validate_arguments

TOOL_NAMES = sorted(t.name for t in TOOLS)

# One valid argument set per tool. Kept explicit rather than generated, so that a
# renamed argument breaks a test instead of being silently accommodated.
VALID_ARGS = {
    "get_parking_rates": {"development_type": "restaurant"},
    "get_zone_info": {"zone_code": "R2"},
    "calculate_da_fees": {"development_cost": 250000},
    "get_flood_requirements": {"development_type": "residential"},
    "get_contact_info": {},
    "search_dcp": {"query": "setback", "chapter": "chapter-1"},
    "read_dcp_section": {"chapter": "chapter-7-off-street-carparking.pdf", "start_page": 1, "end_page": 1},
    "list_documents": {},
    "get_da_checklist": {"development_type": "dwelling"},
    "list_parking_types": {},
    "list_zones": {},
    "get_definition": {"term": "dwelling house"},
    "check_permissibility": {"zone_code": "R2", "land_use": "dwelling houses"},
    "get_setback_requirements": {"setback_type": "front"},
    "check_referrals": {"development_characteristics": ["bushfire"]},
    "get_see_template": {"section": "site_description"},
    "get_residential_standards": {"standard_type": "site_coverage"},
    "list_definitions": {},
    "generate_see_draft": {
        "property_address": "12 Keen Street, Lismore NSW 2480",
        "zone_code": "R2",
        "proposed_use": "dwelling house",
        "development_type": "dwelling",
        "floor_area_sqm": 180,
    },
    "preview_see_form": {
        "applicant_name": "A Person",
        "minor_development_type": "dwelling_single_storey",
        "property_address": "12 Keen Street, Lismore NSW 2480",
        "lot_dp": "Lot 12 DP 758651",
        "zone_code": "R2",
        "proposed_use": "dwelling house",
        "development_type": "dwelling",
        "floor_area_sqm": 180,
    },
    # fill_see_pdf writes a file; covered separately so it can clean up after itself.
}


class TestRegistry:
    def test_every_tool_has_a_schema(self):
        assert set(TOOL_SCHEMAS) == set(TOOL_NAMES)

    def test_no_duplicate_tool_names(self):
        names = [t.name for t in TOOLS]
        assert len(names) == len(set(names))

    def test_every_tool_has_a_description(self):
        assert [t.name for t in TOOLS if not (t.description or "").strip()] == []

    def test_required_arguments_are_declared_properties(self):
        for tool in TOOLS:
            props = set(tool.inputSchema.get("properties", {}))
            required = set(tool.inputSchema.get("required", []))
            assert required <= props, f"{tool.name}: {required - props} required but not declared"

    def test_smoke_coverage_is_complete(self):
        """Fails when a tool is added without a smoke case."""
        uncovered = set(TOOL_NAMES) - set(VALID_ARGS) - {"fill_see_pdf"}
        assert uncovered == set()


class TestValidation:
    def test_unknown_tool_rejected(self):
        error = validate_arguments("no_such_tool", {})
        assert error and "Unknown tool" in error["error"]

    def test_unknown_argument_rejected(self):
        error = validate_arguments("get_zone_info", {"zone": "R2"})
        assert error and "Unrecognised" in error["error"]
        assert "zone_code" in error["accepted_arguments"]

    def test_missing_required_rejected(self):
        error = validate_arguments("get_zone_info", {})
        assert error and "Missing" in error["error"]

    def test_empty_string_treated_as_missing(self):
        """A blank land_use once produced 'permitted without consent'."""
        error = validate_arguments("check_permissibility", {"zone_code": "R2", "land_use": "   "})
        assert error is not None

    def test_valid_arguments_accepted(self):
        assert validate_arguments("get_zone_info", {"zone_code": "R2"}) is None


class TestSmoke:
    @pytest.mark.parametrize("name", sorted(VALID_ARGS))
    def test_tool_returns_without_raising(self, call, name):
        result = call(name, VALID_ARGS[name])
        assert result not in (None, "", {})

    @pytest.mark.parametrize("name", sorted(VALID_ARGS))
    def test_tool_reports_no_error_for_valid_input(self, call, name):
        result = call(name, VALID_ARGS[name])
        if isinstance(result, dict):
            assert "error" not in result, f"{name}: {result.get('error')}"

    @pytest.mark.parametrize("name", sorted(VALID_ARGS))
    def test_output_is_json_serialisable(self, call, name):
        json.dumps(call(name, VALID_ARGS[name]))


class TestZoneData:
    def test_listed_zones_all_resolve(self, call):
        listed = call("list_zones")
        codes = listed["zones"] if isinstance(listed, dict) and "zones" in listed else listed
        codes = [z["zone_code"] if isinstance(z, dict) else z for z in codes]
        for code in codes:
            assert call("get_zone_info", {"zone_code": code}), code

    def test_retired_codes_redirect_rather_than_fail(self, call):
        result = call("get_zone_info", {"zone_code": "B3"})
        assert result.get("redirect_to") == "E2"

    def test_case_insensitive(self, call):
        assert call("get_zone_info", {"zone_code": "r2"})["zone_code"] == "R2"

    @pytest.mark.parametrize("zone", ["RU1", "RU2", "RU3", "RU4", "RU6", "R4", "E5", "C4", "SP1", "W2"])
    @pytest.mark.xfail(strict=True, reason="zone absent from ZONES; IMPROVEMENT_PLAN 1.1")
    def test_all_lep_zones_present(self, zone):
        assert zone in ZONES


class TestKnownGaps:
    """Pinned as xfail so Phase 1 and 3 have executable targets."""

    @pytest.mark.xfail(strict=True, reason="unknown types get a generic checklist; IMPROVEMENT_PLAN 1.6")
    def test_checklist_refuses_nonsense(self, call):
        assert "error" in call("get_da_checklist", {"development_type": "nuclear reactor"})

    @pytest.mark.xfail(strict=True, reason="exact-token matching; IMPROVEMENT_PLAN 3.1")
    @pytest.mark.parametrize("term", ["coffee shop", "child care centre"])
    def test_parking_accepts_common_synonyms(self, call, term):
        assert "error" not in call("get_parking_rates", {"development_type": term})

    @pytest.mark.xfail(strict=True, reason="section keys are snake_case only; IMPROVEMENT_PLAN 3.1")
    def test_see_template_accepts_spaces(self, call):
        assert "error" not in call("get_see_template", {"section": "site description"})

    @pytest.mark.xfail(strict=True, reason="LEP-only reasoning ignores SEPPs; IMPROVEMENT_PLAN 1.3")
    def test_catchall_prohibition_mentions_sepps(self, call):
        result = call("check_permissibility", {"zone_code": "R2", "land_use": "secondary dwelling"})
        assert "sepp" in json.dumps(result).lower()

    @pytest.mark.xfail(strict=True, reason="success key absent on happy path; IMPROVEMENT_PLAN 3.5")
    def test_preview_see_form_always_reports_success(self, call):
        assert "success" in call("preview_see_form", VALID_ARGS["preview_see_form"])
