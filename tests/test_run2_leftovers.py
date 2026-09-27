"""The run-2 leftovers in SCENARIOS.md: carried over from run 1, and the LOW list.

One file for the same reason `test_smaller_defects.py` is one file: these are
held together by provenance — each was found by running `SCENARIOS.md` against
the server — not by subject, and scattered they would read as unrelated
assertions with no record of why anyone checked.

Not here, deliberately: argument aliases (A1) and shared synonym resolution,
including the hairdresser note (A2), which are separate items; zero
`gross_floor_area_m2`, which is fixed in PR #70's change to the same lines; and
implausible inputs, for which no flag could be set without inventing a
threshold no document gives.
"""

import json
import re
from pathlib import Path

import pytest

from lismore_da_mcp.data.zones import RU4_RU6_NOTE, ZONES, ZONES_WITHOUT_A_TABLE
from lismore_da_mcp.readiness import Proposal, _site, open_questions

LEP_TEXT = (Path(__file__).resolve().parent.parent
            / "documents" / "lep" / "lep-2012-nsw-full.txt").read_text()


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


class TestClause522ReachesTheReadinessCheck:
    """A childcare centre at a CBD address was told flood was "not established"
    and nothing about cl 5.22, which reaches past the flood planning area to the
    probable maximum flood for exactly this use. get_flood_requirements raised
    it; the tool that composes the whole application did not."""

    def test_a_childcare_centre_is_told(self, call):
        result = call("check_da_readiness", {
            "proposed_use": "childcare centre", "zone_code": "E2",
            "property_address": "12 Keen Street, Lismore"})
        clause = [f for f in result["outstanding"] if f.get("source") == "LEP 2012 cl 5.22"]
        assert len(clause) == 1
        assert "probable maximum flood" in clause[0]["why"]
        # Not a rejection risk: nothing is known to be wrong, it is a question.
        assert clause[0]["severity"] == "confirm_before_lodging"

    @pytest.mark.parametrize("use", ["centre-based child care facility", "school",
                                     "boarding house"])
    def test_other_sensitive_uses_are_told(self, use):
        findings = _site(Proposal(proposed_use=use))
        assert any(f.get("source") == "LEP 2012 cl 5.22" for f in findings)

    def test_a_shop_is_not(self, call):
        """Over-listing is the rule here, but a finding on every proposal would
        be a standing caveat, and carry no information."""
        result = call("check_da_readiness", {"proposed_use": "shop", "zone_code": "E2"})
        assert not any(f.get("source") == "LEP 2012 cl 5.22" for f in result["outstanding"])


class TestHeritageDoesNotHardenWithAnAddress:
    """Supplying an address made the answer less careful: the state layer's
    "not within a mapped area" became silence, dropping the vicinity rule and
    the conservation area question that the same call raised with no address."""

    def test_through_the_tool_with_an_address(self, call):
        # The canned layer reply for this address is "not within a mapped area".
        result = call("check_da_readiness", {
            "proposed_use": "restaurant or cafe", "zone_code": "E2",
            "property_address": "12 Keen Street, Lismore"})
        assert result["understood_as"]["heritage"] == "no"
        heritage = [f for f in result["outstanding"] if "heritage" in f["finding"].lower()]
        assert heritage and any("vicinity" in f["why"] for f in heritage)
        questions = [q["question"] for q in result["questions_for_council"]]
        assert any("conservation area" in q for q in questions)

    def test_a_mapped_no_still_names_the_vicinity_rule(self):
        findings = _site(Proposal(proposed_use="cafe", zone_code="E2", heritage=False))
        heritage = [f for f in findings if "heritage" in f["finding"].lower()]
        assert heritage, "a mapped 'no' produced no heritage finding at all"
        assert "5.10(5)(c)" in heritage[0]["source"]
        assert heritage[0]["severity"] == "address_in_the_see"

    def test_the_question_survives_a_mapped_no_and_goes_on_a_yes(self):
        def keys(heritage):
            return {q["key"] for q in open_questions(Proposal(proposed_use="cafe",
                                                              heritage=heritage))}
        assert "heritage_status" in keys(False)
        assert "heritage_status" in keys(None)
        assert "heritage_status" not in keys(True)


class TestTheFloodAreaMenuOffersWhatTheSchemaOffers:
    def test_cbd_flood_liable_is_on_the_menu(self, call):
        result = call("get_flood_requirements",
                      {"development_type": "commercial", "flood_area": "not an area"})
        assert "cbd_flood_liable" in result["available_flood_areas"]

    def test_every_menu_item_resolves_and_every_schema_word_is_on_the_menu(self, call):
        from lismore_da_mcp.registry import registered

        described = registered()["get_flood_requirements"].schema["properties"]["flood_area"]
        offered = set(re.findall(r"'([a-z_]+)'", described["description"]))
        menu = set(call("get_flood_requirements", {
            "development_type": "commercial", "flood_area": "zz"})["available_flood_areas"])
        assert offered == menu
        for area in menu:
            answer = call("get_flood_requirements",
                          {"development_type": "commercial", "flood_area": area})
            assert "error" not in answer, area


class TestAZoneLismoreDoesNotUseIsNotAMissingZone:
    """RU4 and C4 were "Zone not found" — which reads as a hole in this
    server's data, when it is a fact about the Plan."""

    @pytest.mark.parametrize("tool,args", [
        ("get_zone_info", {"zone_code": "RU4"}),
        ("check_permissibility", {"zone_code": "C4", "land_use": "dwelling house"}),
    ])
    def test_says_the_plan_has_no_table_for_it(self, call, tool, args):
        result = call(tool, args)
        assert "not found" not in result["error"]
        assert "no land use table" in result["detail"]
        assert "available_zones" in result

    def test_the_cl_4_2_note_is_quoted_for_ru4_and_ru6(self, call):
        for code in ("RU4", "RU6"):
            assert call("get_zone_info", {"zone_code": code})[
                "lep_cl_4_2_note_verbatim"] == RU4_RU6_NOTE
        assert "lep_cl_4_2_note_verbatim" not in call("get_zone_info", {"zone_code": "C4"})

    def test_an_unknown_code_is_still_not_found(self, call):
        assert call("get_zone_info", {"zone_code": "X9"})["error"] == "Zone 'X9' not found"

    @pytest.mark.parametrize("code", sorted(ZONES_WITHOUT_A_TABLE))
    def test_each_name_is_the_leps_and_none_has_a_table(self, code):
        """The names are read from the document, not from memory of the
        Standard Instrument — so only zones the Plan itself mentions are here."""
        assert f"Zone {code} {ZONES_WITHOUT_A_TABLE[code]}" in _flat(LEP_TEXT)
        assert code not in ZONES

    def test_the_note_is_verbatim(self):
        assert RU4_RU6_NOTE in _flat(LEP_TEXT)


class TestTheChecklistAcceptsTheLepsWordsAndSiteWords:
    def test_takeaway_food_premises(self, call):
        assert call("get_da_checklist",
                    {"development_type": "takeaway food premises"})["development_type"] \
            == "commercial"

    def test_heritage_answers_with_what_the_site_adds(self, call):
        """'heritage' is not a kind of development, so it cannot choose a
        checklist — but every checklist carries it, and refusing it hid that."""
        result = call("get_da_checklist", {"development_type": "heritage"})
        assert "error" not in result
        conditions = [c["condition"] for c in result["because_of_that_condition"]]
        assert len(conditions) == 1 and "heritage" in conditions[0]
        assert "may" in json.dumps(result).lower() or "if Council requires" in json.dumps(result)
        assert result["required_documents"]

    @pytest.mark.parametrize("word", ["land", "nuclear reactor"])
    def test_words_that_name_no_condition_are_still_refused(self, call, word):
        assert "error" in call("get_da_checklist", {"development_type": word})

    def test_a_real_type_is_not_shadowed(self, call):
        assert call("get_da_checklist",
                    {"development_type": "signage"})["development_type"] == "signage"
