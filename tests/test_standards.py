"""Residential standards match DCP Chapter 1, and the tool applies them honestly.

PLAN.md item 0.6, the companion to item 0.5's flood work. These were the two
data files Phase 0 never audited. Of roughly nineteen figures in the old
`data/standards.py`, two were recognisably from Chapter 1 and the rest were
invented — the giveaway being that each collided with an unrelated number
somewhere in the document, which is what made them look researched.

`TestTheInventedFiguresAreGone` pins the specific ones. The rest holds the shape
the chapter has: Performance Criteria with Acceptable Solutions, a front setback
decided by zone, and three questions the chapter simply does not answer.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_standards import chapter_text, normalise  # noqa: E402

from lismore_da_mcp import standards  # noqa: E402
from lismore_da_mcp.data.standards import (  # noqa: E402
    DEFINITIONS, ELEMENTS, HEALTH_PRECINCT, HOUSING_TYPES, HOW_THIS_CHAPTER_WORKS,
    NOT_SET_BY_THIS_CHAPTER)


@pytest.fixture(scope="module")
def chapter():
    return normalise(chapter_text())


class TestTheInventedFiguresAreGone:
    """Each of these was in the old file and is in no part of Chapter 1."""

    @pytest.mark.parametrize("phrase", [
        "4.5m to articulated facade",
        "1.5m for walls with no major openings",
        "5m from access handle boundary",
        "45° angle from boundary",
        "Maximum 50% (higher densities",
        "Minimum 15% of site as deep soil",
        "Maximum 50% of building frontage width",
        "Maximum 3m for single dwelling, 5.5m for dual crossover",
        "8.5m or 2 storeys, whichever is less",
        "Minimum 80m² with minimum dimension 5m",
    ])
    def test_not_in_the_data(self, phrase):
        module = __import__("lismore_da_mcp.data.standards", fromlist=["x"])
        blob = repr({k: v for k, v in vars(module).items() if not k.startswith("_")})
        assert phrase not in blob, f"{phrase!r} is back in data/standards.py"

    @pytest.mark.parametrize("phrase", [
        "articulated facade", "access handle", "battle axe", "battle-axe",
        "dual crossover", "deep soil zone shall", "maximum site coverage",
    ])
    def test_not_in_the_chapter_either(self, chapter, phrase):
        assert normalise(phrase) not in chapter

    def test_the_real_open_space_figure_kept_its_conditions(self):
        """80m² is real; the 5m dimension and the missing lot-size condition
        were not."""
        pos = ELEMENTS["open_space_and_landscaping"]["private_open_space"]
        entry = pos["detached dwelling on a lot under 400m2"]
        assert entry["primary_area"] == "80m2"
        assert entry["primary_dimension"] == "2.5m"
        assert pos["detached dwelling on a lot over 400m2"]["primary_area"] is None

    def test_the_real_09m_kept_its_scope(self):
        """0.9m is real, and is small lot housing's side setback only."""
        a26_3 = HOUSING_TYPES["small_lot_housing"]["acceptable_solutions"]["A26.3"]
        assert "0.9 metres" in a26_3
        setback_solutions = ELEMENTS["setbacks"]["acceptable_solutions"]
        assert not any("0.9" in v for v in setback_solutions.values())


class TestEveryQuoteIsInTheChapter:
    def test_audit_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_standards.py")],
            capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr

    @pytest.mark.parametrize("key", sorted(DEFINITIONS))
    def test_definition_appears_verbatim(self, key, chapter):
        assert normalise(DEFINITIONS[key]) in chapter

    @pytest.mark.parametrize("key", sorted(ELEMENTS))
    def test_every_acceptable_solution_appears_verbatim(self, key, chapter):
        for ref, text in ELEMENTS[key].get("acceptable_solutions", {}).items():
            assert normalise(text) in chapter, f"{key} {ref}"

    def test_the_front_setbacks_are_real(self, chapter):
        solutions = ELEMENTS["setbacks"]["acceptable_solutions"]
        assert "setback 6m from the boundary fronting the street in zones r1, r2, r3 and ru5" \
            in normalise(solutions["A1.1"])
        assert normalise(solutions["A1.4"]) in chapter
        assert normalise(solutions["A1.5"]) in chapter


class TestTheAuditCanFail:
    def test_a_drifted_figure_is_caught(self, chapter):
        drifted = ELEMENTS["setbacks"]["acceptable_solutions"]["A1.1"].replace("6m", "4.5m")
        assert normalise(drifted) not in chapter

    def test_the_absence_check_would_catch_a_reinvented_figure(self, chapter):
        """The inverse check is the one that matters for this file: a presence
        check only ever looks at what is stored, so it is blind to invention."""
        real = "setback 15m from the boundary fronting the street"
        assert normalise(real) in chapter, "sanity: the absence check can find things"
        assert normalise("setback 4.5m from the boundary fronting the street") not in chapter

    def test_the_uncarried_solution_scan_notices_a_removed_control(self, chapter):
        from audit_standards import solutions_not_carried

        assert solutions_not_carried(chapter, set()), \
            "with nothing carried, the scan should report the chapter's solutions as missing"


class TestWhatTheChapterDoesNotSet:
    """Three questions applicants ask constantly that Chapter 1 has no figure
    for. Each had an invented one."""

    @pytest.mark.parametrize("key", ["side_setback", "rear_setback", "site_coverage",
                                     "deep_soil_percentage", "battle_axe_lots",
                                     "garage_and_driveway_widths"])
    def test_each_is_answered_rather_than_left_blank(self, key):
        answer = standards.absent(key)
        assert answer["the_dcp_sets_no_figure"] is True
        assert answer["what_the_chapter_says"]
        assert NOT_SET_BY_THIS_CHAPTER[key]["previously_claimed"]

    def test_side_setback_points_at_the_performance_criterion(self):
        answer = standards.setbacks("side")
        assert answer["side"]["the_dcp_sets_no_figure"] is True
        assert "A4.2" in answer["side"]["performance_criterion"]
        assert "A26.3" in answer["side"]["small_lot_housing"]

    def test_site_coverage_explains_the_40_percent_instead(self):
        answer = standards.topic("open_space_and_landscaping")
        assert "40%" in answer["site_coverage"]["what_the_chapter_says"]

    def test_deep_soil_says_the_table_is_an_image(self):
        answer = standards.absent("deep_soil_percentage")
        assert "image" in answer["what_the_chapter_says"]


class TestFrontSetbackComesFromTheZone:
    @pytest.mark.parametrize("zone,expected", [
        ("R1", "6m"), ("R2", "6m"), ("R3", "6m"), ("RU5", "6m"),
        ("RU1", "15m"), ("R5", "15m"), ("E3", "15m"),
    ])
    def test_by_zone(self, zone, expected):
        assert standards.front_setback(zone)["applicable"] == expected

    def test_rms_road_raises_it_to_28m(self):
        assert standards.front_setback("R5", fronts_rms_road=True)["applicable"] == "28m"

    def test_rms_road_is_flagged_when_unanswered(self):
        assert "check_this" in standards.front_setback("R5")

    def test_rms_is_not_offered_where_it_does_not_apply(self):
        """A1.5 reaches RU1, R5 and E3 only."""
        assert "check_this" not in standards.front_setback("R2")
        assert standards.front_setback("R2", fronts_rms_road=True)["applicable"] == "6m"

    def test_corner_lots_get_the_secondary_figure(self):
        answer = standards.front_setback("R1", lot_configuration="corner")
        assert "3m" in answer["applicable"]

    def test_without_a_zone_no_figure_is_picked(self):
        answer = standards.front_setback()
        assert answer["applicable"] is None
        assert len(answer["by_zone"]) == 7
        assert "nine metres" in answer["why"]

    def test_an_unknown_zone_says_so(self):
        answer = standards.front_setback("E2")
        assert answer["applicable"] is None
        assert "zone_not_recognised" in answer

    def test_e3_is_carried_even_though_it_is_a_business_zone(self):
        assert "E3" in ELEMENTS["setbacks"]["front_setback_by_zone"]
        assert standards.front_setback("E3")["applicable"] == "15m"


class TestAcceptableSolutionsAreSafeHarbours:
    """§1.3. Reporting a figure as a limit forecloses an argument the chapter
    expressly invites."""

    def test_the_chapter_says_so_verbatim(self, chapter):
        assert normalise(HOW_THIS_CHAPTER_WORKS["alternative_verbatim"]) in chapter

    def test_every_answer_carries_the_caveat(self):
        assert "not a maximum or a minimum" in standards.HOW_TO_READ_A_FIGURE
        for name in ("open_space_and_landscaping", "fences", "car_parking"):
            assert "how_to_read_this" in standards.topic(name)
        assert "how_to_read_this" in standards.front_setback("R1")


class TestTopicResolution:
    @pytest.mark.parametrize("term,expected", [
        ("site coverage", "open_space_and_landscaping"),
        ("private_open_space", "open_space_and_landscaping"),
        ("car_parking_design", "car_parking"),
        ("driveway", "car_parking"),
        ("granny flat", "secondary_dwelling"),
        ("privacy", "visual_privacy"),
        ("retaining walls", "earthworks"),
        ("shop top", "shop_top_housing"),
        ("health precinct", "health_precinct"),
    ])
    def test_plain_words_resolve(self, term, expected):
        assert standards.resolve_topic(term).key == expected

    def test_the_old_tools_vocabulary_still_works(self):
        """site_coverage, private_open_space, landscaping and car_parking_design
        were the previous schema's enum. They must not simply error."""
        for old in ("site_coverage", "private_open_space", "landscaping",
                    "car_parking_design", "building_height"):
            assert standards.resolve_topic(old)

    def test_an_unknown_topic_is_refused(self):
        assert not standards.resolve_topic("nuclear reactor")


class TestChapterCoverage:
    def test_every_element_carries_a_section_and_page(self):
        for key, element in ELEMENTS.items():
            assert element["section"].startswith("4."), key
            assert 1 <= element["page"] <= 56, key

    def test_the_health_precinct_separation_table_is_carried(self):
        rows = HEALTH_PRECINCT["building_separation"]["rows"]
        assert rows["Up to 16m (5 storeys)"]["non_habitable_rooms"] == "4.5m"

    def test_the_secondary_dwelling_cap_cannot_be_varied(self):
        """The one development standard in the chapter clause 4.6 cannot reach."""
        entry = HOUSING_TYPES["secondary_dwelling"]
        assert "4.6(8)(c)" in entry["cannot_be_varied_verbatim"]

    def test_the_sepp_65_citation_is_flagged_not_relied_on(self):
        assert "repealed" in HEALTH_PRECINCT["sepp_65_note"]
