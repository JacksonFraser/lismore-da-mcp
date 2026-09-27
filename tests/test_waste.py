"""Waste requirements match DCP Chapter 15, and the tool applies them honestly.

ROADMAP.md D2. The checklists named Chapter 15 seven times as prose; the
change-of-use list asked only for "waste storage and collection arrangements"
while §1.3 puts a change of use inside the chapter and §2.1 puts a plan in the
SEE. The audit was written before the data. This pins it, and pins the three
things the tool must never do: leave a change of use out, invent a volume the
chapter calls "Variable", or say nothing about grease.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_waste import (  # noqa: E402
    chapter_text,
    completeness,
    figure_problems,
    generation_rates_from_document,
    headings,
    normalise,
    numbered_items_in,
    rate_table_problems,
    section_slices,
)

from lismore_da_mcp import waste  # noqa: E402
from lismore_da_mcp.data.checklists import DA_CHECKLISTS  # noqa: E402
from lismore_da_mcp.data.waste import FIGURES, GENERATION_RATES, NOT_SET_BY_THIS_CHAPTER, SCOPE, SECTIONS  # noqa: E402
from lismore_da_mcp.readiness import _claims  # noqa: E402
from lismore_da_mcp.server import call_tool  # noqa: E402


@pytest.fixture(scope="module")
def chapter():
    return normalise(chapter_text())


def call(arguments: dict) -> dict:
    return json.loads(asyncio.run(call_tool("get_waste_requirements", arguments))[0].text)


class TestTheAuditPasses:
    def test_audit_script_is_clean(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_waste.py")],
                                capture_output=True, text=True, cwd=ROOT)
        assert result.returncode == 0, result.stdout[-3000:]

    def test_nothing_is_unaccounted_for(self, chapter):
        gaps = completeness(chapter)
        assert all(not v for v in gaps.values()), gaps

    def test_the_structure_it_reads_is_the_whole_chapter(self):
        found = headings()
        assert len(set(found["sections"])) == 27
        assert found["appendices"] == list("ABCDEFGH")

    def test_the_item_counter_actually_counts(self, chapter):
        """Completeness passes vacuously if the counter reads zero everywhere."""
        slices = section_slices(chapter, headings()["sections"])
        assert numbered_items_in(slices["4.3"]) == 21
        assert numbered_items_in(slices["4.2"]) == 27

    def test_appendix_c_rebuilt_from_geometry_matches(self):
        assert rate_table_problems() == []
        assert len(generation_rates_from_document()["rows"]) == len(GENERATION_RATES) == 16


class TestTheAuditCanFail:
    def test_a_figure_that_disagrees_with_its_quote_is_caught(self, chapter):
        doctored = {"x": dict(FIGURES["food_waste_threshold_litres_per_week"], value=250)}
        assert figure_problems(doctored, chapter)

    def test_a_rate_filed_against_the_wrong_row_is_caught(self, monkeypatch):
        """The failure a presence check cannot see: every cell is real, one is
        on the wrong line."""
        from lismore_da_mcp.data import waste as data

        swapped = dict(data.GENERATION_RATES)
        swapped["butcher"] = dict(swapped["butcher"], waste=["240L/100m² floor area/day"])
        monkeypatch.setattr(data, "GENERATION_RATES", swapped)
        assert any("Butcher" in p for p in rate_table_problems())

    def test_the_food_shops_group_ends_where_the_page_ends_it(self):
        groups = generation_rates_from_document()["groups"]
        assert groups["Takeaway food and drink premises"]
        assert groups["Hairdresser/ beauty salon"] is None


class TestWhatTheChapterDoesNotSay:
    @pytest.mark.parametrize("key", NOT_SET_BY_THIS_CHAPTER)
    def test_recorded_absences_are_absent(self, chapter, key):
        for phrase in NOT_SET_BY_THIS_CHAPTER[key]["absent_phrases"]:
            assert normalise(phrase) not in chapter, f"{phrase!r} is in Chapter 15"


class TestChangeOfUse:
    def test_the_chapter_covers_it(self):
        assert "Change of use." in SCOPE["numbered"]["covered"]

    def test_the_tool_says_so(self):
        result = call({"development_type": "cafe", "is_change_of_use": True})
        assert "item 3 of §1.3" in result["does_it_apply"]["your_change_of_use"]
        assert "Statement of Environmental Effects" in result["what_to_lodge"]["in_the_see"]

    def test_the_checklist_asks_for_a_plan_not_just_arrangements(self):
        docs = DA_CHECKLISTS["change_of_use"]["documents"]
        waste_items = [d for d in docs if "waste" in d.lower()]
        assert waste_items and waste_items[0].startswith("Waste management plan")
        assert "get_waste_requirements" in waste_items[0]

    def test_the_document_matcher_still_recognises_it(self):
        entry = next(d for d in DA_CHECKLISTS["change_of_use"]["documents"]
                     if d.startswith("Waste management plan"))
        assert _claims("waste management plan", entry)
        assert _claims("WMP", entry)
        assert not _claims("stormwater management plan", entry)

    def test_no_building_work_drops_the_construction_section(self):
        result = call({"development_type": "cafe", "is_change_of_use": True,
                       "involves_building_work": False})
        assert "construction" not in result["controls"]


class TestFoodBusiness:
    def test_criterion_14_is_surfaced(self):
        food = call({"development_type": "cafe"})["food_waste"]
        assert "240 litres per week" in food["criterion_14"]
        assert "twice weekly" in food["criterion_14"]

    def test_grease_is_said_to_be_outside_the_chapter(self):
        result = call({"development_type": "restaurant"})
        assert "grease" in result["not_covered_by_this_chapter"]["liquid_trade_waste"]
        assert "liquid_trade_waste" in result["not_covered_by_this_chapter"]["where_instead"]

    def test_cafe_estimate_uses_the_per_1_5m2_base(self):
        estimate = call({"development_type": "cafe", "floor_area_m2": 75})["how_much_waste"]
        assert estimate["general_waste"]["litres_per_day"] == 500.0
        assert estimate["recyclables"]["litres_per_day"] == 100.0
        assert "1.5m²" in estimate["read_the_base"]

    def test_weekly_and_bins_only_when_the_inputs_are_given(self):
        bare = call({"development_type": "cafe", "floor_area_m2": 75})["how_much_waste"]
        assert "general_waste_litres_per_week" not in bare
        full = call({"development_type": "cafe", "floor_area_m2": 75, "days_open_per_week": 6,
                     "collections_per_week": 2})["how_much_waste"]
        assert full["general_waste_litres_per_week"] == 3000.0
        assert full["general_waste_between_collections_litres"] == 1500.0
        assert full["bins_to_hold_it"]["1,100L"] == 2
        assert "360L" not in full["bins_to_hold_it"]      # recycling-only in Appendix D


class TestNothingIsInvented:
    def test_variable_stays_variable(self):
        estimate = call({"development_type": "butcher", "floor_area_m2": 100})["how_much_waste"]
        assert estimate["recyclables"]["litres_per_day"] is None
        assert "Variable" in estimate["recyclables"]["why"]

    def test_no_floor_area_no_number(self):
        estimate = call({"development_type": "cafe"})["how_much_waste"]
        assert estimate["general_waste"]["litres_per_day"] is None
        assert estimate["general_waste"]["supply"] == "floor_area_m2"

    def test_non_floor_area_rates_are_not_computed(self):
        estimate = call({"development_type": "pub", "floor_area_m2": 300})["how_much_waste"]
        assert all(cell["litres_per_day"] is None for cell in estimate["general_waste"])

    def test_a_shop_needs_its_floor_area_to_pick_a_row(self):
        assert call({"development_type": "shop"})["how_much_waste"]["premises"] == "shop"
        assert call({"development_type": "shop", "floor_area_m2": 60})["how_much_waste"][
            "premises"] == "Shop less than 100m² floor area"
        assert call({"development_type": "shop", "floor_area_m2": 100})["how_much_waste"][
            "premises"] == "shop"

    def test_an_unknown_premises_is_refused_not_approximated(self):
        result = call({"development_type": "commercial", "premises_type": "bakery"})
        assert "error" in result


class TestParseRate:
    @pytest.mark.parametrize("key", GENERATION_RATES)
    def test_every_non_variable_cell_parses(self, key):
        for stream in ("waste", "recyclables"):
            for cell in GENERATION_RATES[key][stream]:
                assert cell == "Variable" or waste.parse_rate(cell), cell


class TestSections:
    def test_mixed_use_brings_both_residential_and_commercial(self):
        controls = call({"development_type": "shop top housing"})["controls"]
        assert {"mixed_use", "multi_dwelling", "commercial_and_retail"} <= set(controls)

    def test_commercial_carries_all_21_numbered_requirements(self):
        numbered = SECTIONS["commercial_and_retail"]["numbered"]
        assert sum(len(v) for v in numbered.values()) == 21
