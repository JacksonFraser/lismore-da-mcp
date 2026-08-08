"""Flood controls match DCP Chapter 8, and the tool applies them honestly.

PLAN.md item 0.5. What this replaced was not a transcription: it asserted a
500mm freeboard where §8.2 says 300mm three times, described levels as "1% AEP"
in a chapter that says "1 in 100 year ARI" throughout, and carried a
"CBD Development Exemption Precinct" and a "2090 climate change level (~13.4m)"
that appear in no document in this repository.

`TestFreeboardIsThreeHundred` and `TestTheInventedProvisionsAreGone` pin the
specific errors, because a regression should name the fault rather than show a
diff. The rest holds the shape the chapter actually has: controls per flood
hazard area, the §8.3 change-of-use exemption, and an area that is never
guessed.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_flood import chapter_text, normalise  # noqa: E402

from lismore_da_mcp import flood  # noqa: E402
from lismore_da_mcp.data.flood import (  # noqa: E402
    ARI_500_OFFSET_M, CHANGE_OF_USE_EXEMPT, DEFINITIONS, FLOOD_AREAS,
    FREEBOARD_MM, LEP_FLOOD_CLAUSES, SCOPE)


@pytest.fixture(scope="module")
def chapter():
    return normalise(chapter_text())


class TestFreeboardIsThreeHundred:
    """The error that motivated the item. 200mm is the difference between a
    compliant slab and a non-compliant one."""

    def test_freeboard_constant(self):
        assert FREEBOARD_MM == 300

    def test_freeboard_is_in_the_chapter(self, chapter):
        assert "the freeboard adopted for the purposes of this plan is 300mm" in chapter

    def test_five_hundred_appears_nowhere_in_the_data(self):
        """The old value. It must not survive anywhere, including in prose."""
        for name, value in vars(__import__(
                "lismore_da_mcp.data.flood", fromlist=["x"])).items():
            if name.startswith("_"):
                continue
            assert "500mm" not in repr(value), f"{name} still carries a 500mm freeboard"

    def test_the_chapter_never_says_500mm_freeboard(self, chapter):
        assert "500mm" not in chapter

    def test_fpl_is_calculated_from_the_freeboard(self):
        fpl = flood.flood_planning_level()
        assert fpl["freeboard_mm"] == 300
        assert "300mm" in fpl["how_calculated"]
        assert "1 in 100 year ARI" in fpl["how_calculated"]


class TestTheInventedProvisionsAreGone:
    """Four claims in the old file that no document in this repo supports."""

    @pytest.mark.parametrize("phrase", [
        "1% AEP", "2090", "13.4", "Exemption Precinct", "proposed_fpl",
    ])
    def test_phrase_absent_from_the_data(self, phrase):
        module = __import__("lismore_da_mcp.data.flood", fromlist=["x"])
        blob = repr({k: v for k, v in vars(module).items() if not k.startswith("_")})
        assert phrase.lower() not in blob.lower(), (
            f"'{phrase}' is back in data/flood.py. It appears in neither DCP Chapter 8 nor "
            f"LEP 2012 — if it comes from a real Council policy, carry that policy first.")

    @pytest.mark.parametrize("phrase", ["1% aep", "exemption precinct", "2090"])
    def test_phrase_absent_from_the_chapter(self, chapter, phrase):
        assert phrase not in chapter


class TestEveryControlIsInTheChapter:
    """The audit, run as a test, so CI enforces it."""

    def test_audit_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "audit_flood.py")],
            capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr

    @pytest.mark.parametrize("key", sorted(DEFINITIONS))
    def test_definition_appears_verbatim(self, key, chapter):
        assert normalise(DEFINITIONS[key]["verbatim"]) in chapter

    @pytest.mark.parametrize("key", sorted(FLOOD_AREAS))
    def test_area_definition_appears_verbatim(self, key, chapter):
        assert normalise(FLOOD_AREAS[key]["definition_verbatim"]) in chapter

    def test_the_change_of_use_sentence_is_real(self, chapter):
        assert normalise(SCOPE["change_of_use_verbatim"]) in chapter


class TestTheAuditCanFail:
    """A checker that cannot detect a fault manufactures confidence rather than
    providing it — the rule `test_zone_transcription.py` set in item 0.2."""

    def test_a_drifted_quote_is_caught(self, chapter):
        drifted = DEFINITIONS["freeboard"]["verbatim"].replace("300mm", "500mm")
        assert normalise(drifted) not in chapter

    def test_a_paraphrase_is_caught(self, chapter):
        paraphrase = "Commercial development must have 25% of its floor area above the flood level"
        assert normalise(paraphrase) not in chapter

    def test_the_uncarried_control_scan_finds_a_removed_control(self, chapter):
        """Drop a control from a copy of the data and the scan must notice."""
        from audit_flood import controls_not_carried

        import copy
        gutted = copy.deepcopy(FLOOD_AREAS)
        gutted["flood_fringe"]["controls"]["commercial"]["requirements"] = []
        missed = controls_not_carried(chapter, gutted, [])
        assert missed, "removing a control left the scan reporting nothing missing"


class TestControlsDifferByArea:
    """The reason a single 'commercial requirement' was wrong four times in
    five."""

    def test_high_flood_risk_commercial_needs_a_mezzanine(self):
        reqs = FLOOD_AREAS["high_flood_risk"]["controls"]["commercial"]["requirements"]
        assert any("mezzanine" in r for r in reqs)

    def test_flood_fringe_commercial_does_not(self):
        reqs = FLOOD_AREAS["flood_fringe"]["controls"]["commercial"]["requirements"]
        assert not any("mezzanine" in r for r in reqs)

    def test_low_flood_risk_has_no_controls(self):
        assert FLOOD_AREAS["low_flood_risk"]["controls"] == {}

    def test_floodway_prohibits_regardless_of_development_type(self):
        for dev_type in flood.DEVELOPMENT_TYPES:
            answer = flood.controls_for("floodway", dev_type)
            assert "prohibition_verbatim" in answer
            assert "no new buildings or structures of any type" in \
                answer["prohibition_verbatim"].lower()

    def test_industrial_keeps_the_hollingworth_creek_split(self):
        answer = flood.controls_for("high_flood_risk", "industrial")
        assert isinstance(answer["requirements"], dict)
        assert len(answer["requirements"]) == 2

    def test_the_small_works_exemption_is_only_in_the_flood_fringe(self):
        """§8.6.4(2) exempts work under $50,000; §8.5.4(2) does not."""
        assert "all_developments_exemption" in FLOOD_AREAS["flood_fringe"]
        assert "all_developments_exemption" not in FLOOD_AREAS["high_flood_risk"]


class TestChangeOfUse:
    """§8.3, and the most valuable sentence in the chapter for this audience."""

    def test_a_cbd_cafe_fitout_is_not_held_to_the_commercial_controls(self):
        answer = flood.controls_for("flood_fringe", "commercial", is_change_of_use=True)
        assert answer["change_of_use_exemption"]["applies"] is True
        assert "requirements" not in answer, (
            "the controls were returned as applicable alongside the exemption that lifts them")
        assert "would_apply_to_new_development" in answer

    def test_new_development_still_gets_the_controls(self):
        answer = flood.controls_for("flood_fringe", "commercial", is_change_of_use=False)
        assert "requirements" in answer
        assert "change_of_use_exemption" not in answer

    def test_residential_is_not_exempt(self):
        """§8.3 lifts the commercial and industrial controls only."""
        answer = flood.controls_for("flood_fringe", "residential", is_change_of_use=True)
        assert "change_of_use_exemption" not in answer
        assert "requirements" in answer

    def test_the_exemption_pairs_match_the_sentence(self):
        assert CHANGE_OF_USE_EXEMPT == {
            (area, dev)
            for area in ("high_flood_risk", "flood_fringe", "cbd_flood_liable")
            for dev in ("commercial", "industrial")
        }

    def test_the_exemption_does_not_lift_the_lep(self):
        answer = flood.controls_for("flood_fringe", "commercial", is_change_of_use=True)
        still = " ".join(answer["change_of_use_exemption"]["still_applies"])
        assert "5.21" in still

    def test_an_unexempted_area_says_nothing_about_it(self):
        answer = flood.controls_for("low_flood_risk", "commercial", is_change_of_use=True)
        assert "change_of_use_exemption" not in answer


class TestTheAreaIsNeverGuessed:
    """Map 1 is a bitmap. Same discipline as the CBD parking boundary."""

    def test_no_area_returns_every_area(self):
        answer = flood.requirements("commercial")
        assert answer["flood_area"] == "not established"
        assert len(answer["controls_by_area"]) == len(FLOOD_AREAS)

    def test_no_area_says_none_of_them_is_the_answer(self):
        answer = flood.requirements("commercial")
        assert "None of these is your requirement yet" in answer["what_this_means"]
        assert answer["why_not_established"]["how_to_settle"]

    def test_the_zone_is_named_as_not_a_proxy(self):
        answer = flood.requirements("commercial")
        assert "E2" in answer["why_not_established"]["not_a_proxy"]

    def test_cbd_resolves_to_the_flood_fringe_controls(self):
        assert flood.resolve_flood_area("cbd").key == "flood_fringe"
        assert flood.resolve_flood_area("cbd_flood_liable").key == "flood_fringe"
        assert flood.is_cbd_flood_liable("cbd") is True
        assert flood.is_cbd_flood_liable("flood_fringe") is False

    def test_business_words_resolve_to_commercial(self):
        for term in ("cafe", "coffee shop", "hairdresser", "office", "gym"):
            assert flood.resolve_development_type(term).key == "commercial"

    def test_an_unknown_development_type_is_refused(self):
        assert not flood.resolve_development_type("nuclear reactor")


class TestTheLepIsAlwaysCarried:
    def test_both_clauses_are_returned(self):
        answer = flood.requirements("commercial", "flood_fringe")
        assert set(answer["lep_2012"]) == {"5.21", "5.22"}

    def test_5_21_is_described_as_a_bar_not_a_standard(self):
        assert "must not be granted" in LEP_FLOOD_CLAUSES["5.21"]["verbatim"]
        answer = flood.requirements("commercial", "flood_fringe")
        assert "not a standard to design to" in answer["over_the_dcp"]

    def test_the_state_mapping_gap_is_always_stated(self):
        for args in [("commercial", None), ("residential", "low_flood_risk")]:
            answer = flood.requirements(*args)
            assert "no data for the Lismore LGA" in answer["automated_mapping"]


class TestNumbersAgreeWithTheirSource:
    def test_the_500_year_offset(self, chapter):
        assert ARI_500_OFFSET_M == 1.03
        assert f"add {ARI_500_OFFSET_M}m to the 1 in 100 year ari flood level" in chapter

    def test_every_stored_page_reference_exists(self):
        """The chapter is 11 pages. A citation past the end is a transcription
        that was never opened."""
        pages = []
        for entry in list(DEFINITIONS.values()) + list(FLOOD_AREAS.values()):
            pages += entry.get("pages", [])
            if "page" in entry:
                pages.append(entry["page"])
        assert pages
        assert all(1 <= p <= 11 for p in pages), pages

    def test_every_area_cites_a_section(self):
        for key, area in FLOOD_AREAS.items():
            assert re.fullmatch(r"8\.\d", area["section"]), key
