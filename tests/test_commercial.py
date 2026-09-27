"""Commercial design controls match DCP Chapter 2, and the tool applies them honestly.

ROADMAP.md D1. Chapter 2 is the one DCP chapter written for the businesses this
server is for, and it was reachable only through keyword search. The audit was
written before the data; this pins both, and pins the three things the selector
must never do — infer the precinct, apply building design rules to a change of
use, or present a missed figure as a failure rather than a variation.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_commercial import (  # noqa: E402
    FIGURE_CAPTION, chapter_text, figure_problems, headings, introduction_text,
    invented_structure, normalise, not_carried)

from lismore_da_mcp import commercial  # noqa: E402
from lismore_da_mcp.data.commercial import (  # noqa: E402
    FIGURES, HOW_TO_READ_THIS_CHAPTER, NOT_SET_BY_THIS_CHAPTER, PART_A, TABLE_B1)
from lismore_da_mcp.registry import registered  # noqa: E402
from lismore_da_mcp.server import call_tool  # noqa: E402


@pytest.fixture(scope="module")
def chapter():
    return normalise(FIGURE_CAPTION.sub(" ", chapter_text()))


def call(arguments: dict) -> dict:
    return json.loads(asyncio.run(call_tool("get_commercial_requirements", arguments))[0].text)


class TestTheAuditPasses:
    def test_audit_script_is_clean(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_commercial.py")],
            capture_output=True, text=True, cwd=ROOT)
        assert result.returncode == 0, result.stdout[-3000:]

    def test_every_section_subheading_and_label_is_accounted_for(self):
        assert not_carried() == {"sections": [], "subheadings": [], "table_labels": []}

    def test_nothing_is_claimed_that_the_chapter_does_not_have(self):
        assert invented_structure() == {"sections": [], "subheadings": [], "table_labels": []}

    def test_the_structure_read_off_the_document_is_the_whole_chapter(self):
        """If typography detection silently breaks, completeness passes on
        nothing. Pin what it reads today."""
        found = headings()
        assert len(set(found["sections"])) == 17          # A.1-A.13, B.1-B.4
        assert len(set(found["subheadings"])) == 16
        assert len(set(found["table_labels"])) == 34     # P1-P11 and 23 A labels


class TestTheAuditCanFail:
    """An audit that cannot fail proves nothing."""

    def test_a_paraphrase_is_caught(self, chapter):
        paraphrase = "No external wall may exceed 14m in length in the CBD."
        assert normalise(paraphrase) not in chapter

    def test_a_figure_that_disagrees_with_its_quote_is_caught(self, chapter):
        doctored = {"wall": dict(FIGURES["cbd_external_wall_max_m"], value=15)}
        assert figure_problems(doctored, chapter)

    def test_a_figure_missing_from_its_quote_is_caught(self, chapter):
        doctored = {"wall": dict(FIGURES["cbd_external_wall_max_m"], as_written="16m")}
        assert figure_problems(doctored, chapter)


class TestWhatTheChapterDoesNotSay:
    @pytest.mark.parametrize("key", NOT_SET_BY_THIS_CHAPTER)
    def test_recorded_absences_are_absent(self, chapter, key):
        for phrase in NOT_SET_BY_THIS_CHAPTER[key]["absent_phrases"]:
            assert normalise(phrase) not in chapter, f"{phrase!r} is in Chapter 2"

    def test_the_chapter_never_mentions_a_change_of_use(self, chapter):
        assert "change of use" not in chapter

    def test_there_is_no_chapter_1_style_reading_rule(self, chapter):
        """Which is why the reading rule is quoted from the DCP Introduction."""
        assert "alternatively, council may be prepared to approve" not in chapter
        assert normalise(HOW_TO_READ_THIS_CHAPTER["variations_verbatim"]) in normalise(
            introduction_text())

    def test_the_14m_wall_rule_is_chapter_2s(self, chapter):
        """CLAUDE.md Part 2 once attributed it to Chapter 1, where it is absent."""
        assert "14m in length" in chapter


class TestPrecinctIsNeverInferred:
    def test_the_schema_has_no_address_or_zone(self):
        schema = registered()["get_commercial_requirements"].schema
        assert not {"address", "zone", "zone_code", "property_address"} & set(schema["properties"])

    def test_without_a_precinct_both_parts_come_back_with_the_question(self):
        result = call({})
        assert "part_a_cbd" in result and "part_b_brewster_street" in result
        assert "Map 1 or Map 2" in result["which_precinct"]["ask_it_as"]

    def test_neither_says_the_chapter_does_not_apply(self):
        result = call({"precinct": "neither"})
        assert result["applies"] is False
        assert "part_a_cbd" not in result

    def test_nimbin_is_neither(self):
        assert call({"precinct": "Nimbin"})["applies"] is False


class TestChangeOfUse:
    """The commonest business DA. Chapter 2 is written for buildings."""

    def test_no_design_rules_are_presented_as_binding(self):
        part_a = call({"precinct": "cbd", "work_type": "change of use"})["part_a_cbd"]
        assert "controls" not in part_a
        assert "never mentions a change of use" in part_a["scope"]
        assert set(part_a["if_you_change_the_outside"]) == set(commercial.EXTERNAL_WORK_TOPICS)

    def test_the_wall_rule_is_not_applied_to_a_fitout(self):
        part_a = call({"precinct": "cbd", "work_type": "fitout",
                       "external_wall_length_m": 30})["part_a_cbd"]
        assert part_a["external_wall_length"]["applies"] is False

    def test_part_b_is_scoped_the_same_way(self):
        part_b = call({"precinct": "brewster_street",
                       "work_type": "change_of_use_only"})["part_b_brewster_street"]
        assert "table_b1" not in part_b
        assert "signage" in part_b["if_you_change_the_outside"]


class TestPartA:
    def test_new_building_gets_infill_and_site_analysis_but_not_additions(self):
        controls = call({"precinct": "cbd", "work_type": "new_building"})["part_a_cbd"]["controls"]
        assert "new_buildings" in controls and "site_analysis" in controls
        assert "additions_to_existing_buildings" not in controls

    def test_alterations_get_a9_but_not_the_site_analysis(self):
        controls = call({"precinct": "cbd",
                         "work_type": "new shopfront"})["part_a_cbd"]["controls"]
        assert "additions_to_existing_buildings" in controls
        assert "site_analysis" not in controls

    def test_awnings_resolves_to_weather_protection(self):
        part_a = call({"precinct": "cbd", "topic": "awnings"})["part_a_cbd"]
        assert list(part_a["controls"]) == ["weather_protection"]
        assert "must be integral" in part_a["controls"]["weather_protection"]["verbatim"]

    def test_a_long_wall_is_a_variation_not_a_failure(self):
        check = call({"precinct": "cbd", "work_type": "new_building",
                      "external_wall_length_m": 20})["part_a_cbd"]["external_wall_length"]
        assert check["within_the_figure"] is False
        assert "600mm" in check["what_to_do"]
        assert "fail" not in json.dumps(check).lower()

    def test_heritage_adds_the_heritage_section(self):
        part_a = call({"precinct": "cbd", "topic": "colour", "is_heritage": True})["part_a_cbd"]
        assert "heritage_buildings" in part_a["controls"]
        assert "may" in part_a["heritage"]

    def test_every_part_a_entry_says_what_work_it_is_for(self):
        for key, entry in PART_A.items():
            assert set(entry["applies_to"]) <= {"new_building", "alterations_or_additions"}, key


class TestPartB:
    def test_low_building_drops_the_taller_rows(self):
        part_b = call({"precinct": "brewster_street", "work_type": "new_building",
                       "levels": 2})["part_b_brewster_street"]
        assert "taller_buildings_site_area" not in part_b["table_b1"]
        assert "taller_buildings_site_area" in part_b["rows_not_applying"]

    def test_unknown_levels_keeps_them_and_says_why(self):
        part_b = call({"precinct": "brewster_street"})["part_b_brewster_street"]
        assert "taller_buildings_site_area" in part_b["table_b1"]
        assert any("levels" in u for u in part_b["included_because_not_ruled_out"])

    def test_small_site_is_argued_against_p8(self):
        checks = call({"precinct": "brewster_street", "work_type": "new_building",
                       "levels": 3, "site_area_m2": 900})["part_b_brewster_street"][
            "against_your_figures"]
        assert checks["site_area"]["within_the_figure"] is False
        assert "P8" in checks["site_area"]["what_to_do"]

    def test_separation_up_to_11_5m(self):
        checks = call({"precinct": "brewster_street", "levels": 3, "building_height_m": 11,
                       "adjoins_r2_zone": True})["part_b_brewster_street"]["against_your_figures"]
        assert checks["separation"]["habitable_rooms_and_balconies_m"] == 6
        assert checks["separation"]["non_habitable_rooms_m"] == 3

    def test_above_11_5m_the_table_has_no_row_and_nothing_is_invented(self):
        sep = call({"precinct": "brewster_street", "levels": 4, "building_height_m": 14,
                    "adjoins_r2_zone": True})["part_b_brewster_street"][
            "against_your_figures"]["separation"]
        assert "habitable_rooms_and_balconies_m" not in sep
        assert "sets no separation" in sep["no_row_for_this_height"]

    def test_the_table_b1_figures_are_the_chapters(self):
        a1 = TABLE_B1["street_setbacks"]["acceptable_solutions"]
        assert "6 metres" in a1["A1.1"] and "4m from the secondary road" in a1["A1.2"]


class TestReadiness:
    def test_e2_new_building_raises_the_precinct_question(self):
        from lismore_da_mcp.readiness import Proposal, open_questions

        p = Proposal(proposed_use="shop", development_type="new building", zone_code="E2")
        assert "commercial_design_precinct" in [q["key"] for q in open_questions(p)]

    def test_change_of_use_does_not_spend_the_fifteen_minutes_on_it(self):
        from lismore_da_mcp.readiness import Proposal, open_questions

        p = Proposal(proposed_use="cafe", development_type="change of use", zone_code="E2",
                     existing_use="shop")
        assert "commercial_design_precinct" not in [q["key"] for q in open_questions(p)]

    def test_other_zones_are_untouched(self):
        from lismore_da_mcp.readiness import Proposal, open_questions

        p = Proposal(proposed_use="shop", development_type="new building", zone_code="E1")
        assert "commercial_design_precinct" not in [q["key"] for q in open_questions(p)]
