"""Tool surface: schemas, validation, and one valid call per tool.

The point of the smoke pass is that the structural refactor in IMPROVEMENT_PLAN
Phase 2 has something to move against — every tool reachable, returning parseable
output, with schema and handler in agreement.
"""

import json

import pytest

from lismore_da_mcp.server import TOOLS, TOOL_SCHEMAS, ZONES, validate_arguments

TOOL_NAMES = sorted(t.name for t in TOOLS)

# The zones that have a land use table in Lismore LEP 2012, read off the LEP text
# (documents/lep/lep-2012-nsw-full.txt). This is the authoritative set for this LGA.
LISMORE_ZONES = [
    "RU1", "RU2", "RU3", "RU5",
    "R1", "R2", "R3", "R5",
    "E1", "E2", "E3", "E4", "MU1",
    "SP2", "RE1", "RE2",
    "C1", "C2", "C3",
    "W1", "W2",
]

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

    @pytest.mark.parametrize("zone", LISMORE_ZONES)
    def test_every_lismore_zone_present(self, zone):
        """The 21 zones with a land use table in Lismore LEP 2012.

        Derived from the LEP text itself, not from the Standard Instrument: RU4,
        RU6, R4, E5, C4 and SP1 exist in the Standard Instrument and are
        name-checked in passing by LEP clauses, but have no land use table here
        and do not apply in this LGA. Do not add them.
        """
        assert zone in ZONES

    @pytest.mark.parametrize("zone", LISMORE_ZONES)
    def test_every_zone_has_a_land_use_table(self, zone):
        entry = ZONES[zone]
        assert entry.get("name")
        assert entry.get("permitted_with_consent") or entry.get("permitted_without_consent")
        assert entry.get("prohibited"), f"{zone} has no prohibition, not even the catch-all"

    def test_no_zones_beyond_lismore_and_legacy_redirects(self):
        """Guards against re-adding Standard Instrument zones that Lismore doesn't use."""
        unexpected = {
            code for code in ZONES
            if code not in LISMORE_ZONES and not ZONES[code].get("redirect_to")
        }
        assert unexpected == set()


class TestKnownGaps:
    """Pinned as xfail so Phase 1 and 3 have executable targets."""

    def test_checklist_refuses_nonsense(self, call):
        result = call("get_da_checklist", {"development_type": "nuclear reactor"})
        assert "error" in result
        assert result["recognised_types"]
        # Still tells the caller what every DA needs, rather than refusing outright.
        assert result["documents_required_for_every_da"]

    @pytest.mark.parametrize("dev_type", ["dwelling", "commercial", "subdivision", "change_of_use"])
    def test_checklist_still_answers_known_types(self, call, dev_type):
        result = call("get_da_checklist", {"development_type": dev_type})
        assert "error" not in result
        assert result["additional_for_type"]

    @pytest.mark.parametrize("term,expected", [
        ("coffee shop", "cafe"),                  # synonym
        ("child care centre", "childcare_centre"),  # word-boundary difference
        ("takeaway", "take_away"),                # squashed
        ("granny flat", "secondary_dwelling"),    # applicant's word for a planning term
        ("doctors surgery", "medical_centre"),
        ("Restaurant", "restaurant"),             # case only
    ])
    def test_parking_accepts_common_phrasing(self, call, term, expected):
        result = call("get_parking_rates", {"development_type": term})
        assert "error" not in result, result.get("error")
        assert result["development_type"] == expected

    def test_parking_says_when_it_reinterpreted(self, call):
        """A silent swap would hide that the rate is for a different use."""
        result = call("get_parking_rates", {"development_type": "coffee shop"})
        assert "coffee shop" in result["interpreted_as"]

    def test_parking_exact_match_carries_no_note(self, call):
        assert "interpreted_as" not in call("get_parking_rates", {"development_type": "cafe"})

    def test_see_template_accepts_spaces(self, call):
        assert "error" not in call("get_see_template", {"section": "site description"})

    def test_catchall_prohibition_mentions_sepps(self, call):
        """A use missing from the LEP table may still have a SEPP pathway; the
        answer must not read as a settled refusal. IMPROVEMENT_PLAN 1.3."""
        result = call("check_permissibility", {"zone_code": "R2", "land_use": "secondary dwelling"})
        assert "sepp" in json.dumps(result).lower()
        assert "secondary dwelling" in result["scope_of_this_answer"].lower()

    def test_permitted_answers_carry_no_sepp_caveat(self, call):
        """The caveat belongs on refusals only — adding it everywhere would dilute it."""
        result = call("check_permissibility", {"zone_code": "R2", "land_use": "dwelling houses"})
        assert "scope_of_this_answer" not in result

    @pytest.mark.xfail(strict=True, reason="success key absent on happy path; IMPROVEMENT_PLAN 3.5")
    def test_preview_see_form_always_reports_success(self, call):
        assert "success" in call("preview_see_form", VALID_ARGS["preview_see_form"])
