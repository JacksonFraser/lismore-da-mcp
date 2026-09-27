"""Nimbin Village — DCP Part B Chapter 6 — and the villages generally.

ROADMAP D3. A fresh transcription, so the audit runs here in all four
directions and each is shown failing: quotes that stop matching, a preferred
use, heading, criterion or figure the data does not carry, a figure invented in
the guidance, and an absence that stops being absent.

The tool's rules are pinned too, and the first matters most: RU5 is not
Nimbin. Nothing here infers the village, the precinct, the heritage area or
the flood hazard — all four are images or facts no address gives.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import audit_nimbin as audit  # noqa: E402

from lismore_da_mcp import villages  # noqa: E402
from lismore_da_mcp.data import nimbin  # noqa: E402
from lismore_da_mcp.readiness import Proposal, open_questions  # noqa: E402


@pytest.fixture(scope="module")
def lines():
    return audit.body_lines()


@pytest.fixture(scope="module")
def haystack(lines):
    return audit.joined(lines)


@pytest.fixture(scope="module")
def introduction():
    return audit.document_text(audit.INTRODUCTION_PDF)


class TestTheAuditIsClean:
    def test_quotes_are_in_the_chapter(self, haystack, introduction):
        assert audit.presence_problems(haystack, introduction) == []

    def test_every_heading_is_carried_or_explained(self, lines):
        assert audit.heading_problems(lines) == []

    def test_every_preferred_use_list_matches(self, lines):
        assert audit.preferred_use_problems(lines) == []

    def test_every_live_work_criterion_is_carried(self, lines):
        assert audit.live_work_problems(lines) == []

    def test_every_figure_is_carried(self, haystack):
        assert audit.figure_problems(haystack) == []

    def test_no_figure_is_invented(self, haystack):
        assert audit.invention_problems(haystack) == []

    def test_the_absences_hold(self, haystack):
        assert audit.absence_problems(haystack) == []


class TestTheDocumentIsReadNotListed:
    """Counts pinned so a parser that silently stops finding things cannot
    pass as clean."""

    def test_headings(self, lines):
        found = audit.section_headings(lines)
        assert len(found) == 28
        assert {"2.4", "3.1.4.1", "2.6.2"} <= set(found)
        # Street addresses at the start of a line are not headings.
        assert "7" not in found and "81" not in found

    def test_preferred_use_lists(self, lines):
        lists = audit.preferred_land_use_lists(lines)
        assert len(lists) == 7
        assert "Restaurants or cafes" in lists[4]
        # A use wrapped over two lines is one use.
        assert any(u.startswith("Recreation facilities (indoor and outdoor)") and
                   u.endswith("surrounding area") for u in lists[6])

    def test_live_work_labels(self, lines):
        assert audit.live_work_labels(lines)[:2] == ["P1", "A1.1"]
        assert len(audit.live_work_labels(lines)) == 18

    def test_every_figure_occurrence_is_found(self, haystack):
        assert len(audit.FIGURE.findall(haystack)) == 12


class TestTheAuditCanFail:
    def test_an_altered_quote(self, monkeypatch, haystack, introduction):
        monkeypatch.setitem(nimbin.WATER_SUPPLY, "verbatim", "Nimbin has plenty of water.")
        assert audit.presence_problems(haystack, introduction)

    def test_a_dropped_preferred_use(self, monkeypatch, lines):
        precinct = dict(nimbin.PRECINCTS["commercial"])
        precinct["preferred_land_uses"] = [u for u in precinct["preferred_land_uses"]
                                           if u != "Markets"]
        monkeypatch.setitem(nimbin.PRECINCTS, "commercial", precinct)
        problems = audit.preferred_use_problems(lines)
        assert any("'markets' is in the chapter" in p for p in problems), problems

    def test_an_invented_preferred_use(self, monkeypatch, lines):
        precinct = dict(nimbin.PRECINCTS["commercial"])
        precinct["preferred_land_uses"] = [*precinct["preferred_land_uses"], "Pubs"]
        monkeypatch.setitem(nimbin.PRECINCTS, "commercial", precinct)
        problems = audit.preferred_use_problems(lines)
        assert any("'pubs' is in the data" in p for p in problems), problems

    def test_an_unexplained_heading(self, monkeypatch, lines):
        fewer = {k: v for k, v in nimbin.SECTIONS_NOT_CARRIED.items() if k != "2.6.2"}
        monkeypatch.setattr(nimbin, "SECTIONS_NOT_CARRIED", fewer)
        assert any("§2.6.2" in p for p in audit.heading_problems(lines))

    def test_a_dropped_live_work_criterion(self, monkeypatch, lines):
        precinct = dict(nimbin.PRECINCTS["live_work"])
        precinct["criteria"] = {k: v for k, v in precinct["criteria"].items() if k != "A3.2"}
        monkeypatch.setitem(nimbin.PRECINCTS, "live_work", precinct)
        assert any("A3.2" in p for p in audit.live_work_problems(lines))

    def test_an_uncarried_figure(self, monkeypatch, haystack):
        precinct = dict(nimbin.PRECINCTS["live_work"])
        precinct["criteria"] = {k: v for k, v in precinct["criteria"].items() if k != "A1.1"}
        monkeypatch.setitem(nimbin.PRECINCTS, "live_work", precinct)
        assert any("'6m'" in p for p in audit.figure_problems(haystack))

    def test_an_invented_figure_in_the_guidance(self, monkeypatch, haystack):
        """Chapter 8's 300mm is the figure most likely to leak in here."""
        flood = dict(nimbin.FLOOD, why_it_matters="Floor levels are the FPL plus 300mm.")
        monkeypatch.setattr(nimbin, "FLOOD", flood)
        assert any("'300mm'" in p for p in audit.invention_problems(haystack))

    def test_an_absence_that_stops_being_absent(self, haystack):
        assert audit.absence_problems(haystack + " maximum site coverage 50%")


class TestTheVillageIsNeverInferred:
    def test_without_a_village_it_says_the_chapter_may_not_apply(self, call):
        answer = call("get_village_requirements", {})
        assert answer["chapter_applies"] == "only if the site is in Nimbin"
        assert "zone does not settle it" in answer["which_village"]

    def test_zone_ru5_alone_does_not_make_it_nimbin(self, call):
        answer = call("get_village_requirements", {"zone": "RU5"})
        assert answer["chapter_applies"] == "only if the site is in Nimbin"

    @pytest.mark.parametrize("village", ["Dunoon", "Clunes", "Bexhill"])
    def test_another_village_is_told_what_applies_instead(self, call, village):
        answer = call("get_village_requirements", {"village": village})
        assert answer["chapter_applies"] is False
        assert "repealed" in answer["why"]
        assert any("check_permissibility" in step for step in answer["what_applies_instead"])

    def test_nimbin_is_recognised_however_it_is_written(self):
        assert villages.is_nimbin("Nimbin Village") and villages.is_nimbin(" nimbin ")

    def test_a_non_ru5_site_in_nimbin_is_outside_the_chapter(self, call):
        answer = call("get_village_requirements", {"village": "Nimbin", "zone": "E1"})
        assert answer["chapter_applies"] is False


class TestThePrecinctIsNeverInferred:
    def test_without_a_precinct_every_precinct_is_summarised(self, call):
        answer = call("get_village_requirements", {"village": "Nimbin"})
        assert set(answer["precincts"]) == set(nimbin.PRECINCTS)
        assert "precinct" not in answer
        assert "Figure 2" in answer["which_precinct"]

    def test_a_precinct_returns_its_full_controls(self, call):
        answer = call("get_village_requirements", {"village": "Nimbin", "precinct": "Cullen Street"})
        assert answer["precinct"]["name"] == "Commercial Precinct"
        assert "Restaurants or cafes" in answer["precinct"]["preferred_land_uses"]
        assert "precincts" not in answer

    def test_an_unknown_precinct_is_refused_not_guessed(self, call):
        answer = call("get_village_requirements", {"village": "Nimbin", "precinct": "downtown"})
        assert "error" in answer
        assert "commercial" in answer["available_precincts"]

    def test_preferred_is_never_presented_as_permissible(self, call):
        answer = call("get_village_requirements", {"village": "Nimbin", "precinct": "commercial"})
        assert "permits (with consent)" in answer["preferred_is_not_permissible"]["quoted"]
        assert "no suitable land" in answer["non_preferred_uses"]["quoted"]
        assert any("check_permissibility" in step for step in answer["next_steps"])

    def test_live_work_carries_every_criterion(self, call):
        answer = call("get_village_requirements", {"village": "Nimbin", "precinct": "live_work"})
        table = answer["precinct"]["performance_criteria_and_acceptable_solutions"]
        assert table["A1.1"] == "A1.1 Buildings are setback 6m from the front boundary."
        assert table["P5"].endswith("without being visually obtrusive.")


class TestHeritageAndFloodAreNeverInferred:
    def test_unknown_heritage_status_keeps_the_controls_with_their_condition(self, call):
        answer = call("get_village_requirements", {"village": "Nimbin", "precinct": "commercial"})
        hca = answer["precinct"]["heritage_conservation_area"]
        assert "Figure 3" in hca["applies_if"]
        assert any("murals is not permitted without consent" in c for c in hca["controls"])

    def test_outside_the_conservation_area_the_controls_are_left_out(self, call):
        answer = call("get_village_requirements", {
            "village": "Nimbin", "precinct": "commercial", "in_heritage_conservation_area": False})
        assert "omitted" in answer["precinct"]["heritage_conservation_area"]

    def test_inside_it_no_condition_is_attached(self, call):
        answer = call("get_village_requirements", {
            "village": "Nimbin", "precinct": "commercial", "in_heritage_conservation_area": True})
        assert "applies_if" not in answer["precinct"]["heritage_conservation_area"]

    def test_without_a_hazard_every_category_is_returned(self, call):
        flood = call("get_village_requirements", {"village": "Nimbin"})["flood"]
        assert set(flood["hazard_categories"]) == {"extreme", "high", "medium", "low"}
        assert "1m freeboard" in flood["about"][0]

    def test_the_figure_4_misprint_is_pointed_out_where_it_matters(self, call):
        high = call("get_village_requirements", {"village": "Nimbin", "flood_hazard": "high"})
        low = call("get_village_requirements", {"village": "Nimbin", "flood_hazard": "low"})
        assert "Figure 5" in high["flood"]["source_text_note"]
        assert "source_text_note" not in low["flood"]


class TestTheDutyPlannerIsAsked:
    """The tool declines to place a site; the refusal must become a question."""

    def test_an_ru5_proposal_gets_the_question(self):
        keys = {q["key"] for q in open_questions(Proposal(proposed_use="cafe", zone_code="RU5"))}
        assert "nimbin_precinct" in keys

    def test_other_zones_do_not(self):
        keys = {q["key"] for q in open_questions(Proposal(proposed_use="cafe", zone_code="E2"))}
        assert "nimbin_precinct" not in keys
