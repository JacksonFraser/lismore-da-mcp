"""Lodgement readiness and the pre-lodgement brief — PLAN.md Phase 3.

The thing being prevented is a rejection under EP&A Regulation s39: an
application that is *taken never to have been made*, starting again from zero.
Every ground for it is administrative — a missing document, an unclear
description, an approval not identified — which is exactly why a checklist can
catch them, and why this is the only failure in the DA process a tool can
genuinely prevent.

Two guarantees matter more than the rest and most of what follows is one of
them from a different angle:

  * **A document is never reported as ready unless the applicant said so, in
    words that clearly name it.** A tool that tells someone their lodgement is
    complete when it is not has done worse than nothing.
  * **Nothing is ever reported as "ready to lodge".** Council runs the
    completeness check, and some of its grounds cannot be tested from here.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_readiness import section_39_paragraphs  # noqa: E402
from audit_timing import SOURCE, normalise, walk  # noqa: E402

from lismore_da_mcp.data import readiness as data  # noqa: E402
from lismore_da_mcp.readiness import Proposal, document_gap, open_questions, short_name  # noqa: E402

CBD = "12 Keen Street, Lismore NSW 2480"


def check(call, **kwargs):
    args = {"proposed_use": "cafe", "zone_code": "E2",
            "development_type": "change of use"}
    args.update(kwargs)
    return call("check_da_readiness", args)


def brief(call, **kwargs):
    args = {"proposed_use": "cafe", "zone_code": "E2",
            "development_type": "change of use"}
    args.update(kwargs)
    return call("prepare_prelodgement_brief", args)


def findings(result, severity=None):
    return [f for f in result["outstanding"]
            if severity is None or f["severity"] == severity]


class TestQuotedFromTheRegulation:
    """Same guard as the timing data: this text is a fetched snapshot of
    legislation.nsw.gov.au, so a quote that stops matching means the law was
    amended rather than that a transcription slipped."""

    @pytest.mark.parametrize("group", ["STATUTORY_CONTENT", "REJECTION_GROUNDS",
                                       "REJECTION_WINDOW"])
    def test_every_quote_still_appears(self, group):
        haystack = normalise(SOURCE.read_text())
        for path, quote in walk(getattr(data, group)):
            assert normalise(quote) in haystack, f"{group}.{path} not found in the regulation"

    def test_every_rejection_ground_is_carried(self):
        """A list of five grounds out of six reads as complete and is not.
        s39(1)(c) cannot apply to a Lismore business, so it is marked rather
        than dropped."""
        carried = {e["clause"].removeprefix("s39(1)(").removesuffix(")")
                   for e in data.REJECTION_GROUNDS.values()}
        assert carried == section_39_paragraphs(SOURCE.read_text())
        assert data.REJECTION_GROUNDS["state_significant_incomplete"]["not_applicable_here"]

    def test_the_audit_can_fail(self):
        """A checker that cannot detect a fault manufactures confidence."""
        haystack = normalise(SOURCE.read_text())
        assert normalise("the application is illegible or unclear about the parking") not in haystack


class TestEveryDutyPlannerQuestionIsOneWeDeclinedToAnswer:
    """These are not general advice. Each is a wall some earlier item hit and
    refused to guess past, and the refusal is what makes it worth the free
    fifteen minutes."""

    @pytest.mark.parametrize("entry", data.DUTY_PLANNER_QUESTIONS,
                             ids=[q["key"] for q in data.DUTY_PLANNER_QUESTIONS])
    def test_says_why_it_cannot_be_answered_here(self, entry):
        assert entry["why_we_cannot_answer_it"].strip()
        assert entry["cost_if_unresolved"].strip()
        assert entry["ask_it_as"].strip()

    def test_they_are_ordered_by_cost_not_by_topic(self):
        """The first one can remove the whole application; the last changes a
        design decision. The order is the product — a business with fifteen
        minutes asks from the top."""
        keys = [q["key"] for q in data.DUTY_PLANNER_QUESTIONS]
        assert keys[0] == "codes_sepp_or_existing_use_rights"
        assert keys.index("cbd_boundary") < keys.index("gfa_increase_within_tenancy")


class TestDocumentMatchingIsConservative:
    """The direction of the error is the whole design. Reporting a document as
    missing that the applicant has costs them a moment; reporting one as ready
    that they do not have costs them the lodgement."""

    def test_an_acronym_matches_its_own_document(self):
        """'SEE' shares no word with 'Statement of Environmental Effects', so
        without the synonym table the most universally prepared document in a
        DA is reported missing to anyone who calls it by its name."""
        gap = document_gap(["Statement of Environmental Effects (SEE)"], ["SEE"])
        assert gap["missing"] == []

    @pytest.mark.parametrize("claim,requirement", [
        ("fire safety schedule", "Fire safety upgrade report (commonly required)"),
        ("site plan", "Services layout plan"),
        ("waste management plan", "Stormwater management plan"),
        ("survey plan", "Subdivision layout plan"),
    ])
    def test_documents_sharing_words_are_not_confused(self, claim, requirement):
        """These pairs share most of their words and none of their content.
        Requiring the head noun to agree is what separates them."""
        assert document_gap([requirement], [claim])["missing"] == [requirement]

    def test_words_that_matched_nothing_are_reported_back(self):
        """Dropping them in silence reads as 'that counted'."""
        gap = document_gap(["Site plan (1:100 or 1:200 scale)"], ["site plan", "my lease"])
        assert gap["not_recognised"] == ["my lease"]

    def test_a_match_is_reported_as_a_claim_not_as_verification(self):
        """Nothing here can open a file."""
        gap = document_gap(["Site plan (1:100 or 1:200 scale)"], ["site plan"])
        assert gap["said_to_be_ready"][0]["you_listed"] == ["site plan"]

    def test_the_short_name_drops_the_explanation_not_the_document(self):
        assert short_name("Access report — compliance with the Standards") == "Access report"
        assert short_name("Site plan (1:100 or 1:200 scale)") == "Site plan"


class TestWhatStopsAnApplication:
    """A blocker is not a missing document. These are the three ways a proposal
    is not ready to be worked on at all."""

    def test_a_process_word_as_the_use_is_refused(self, call):
        """'fitout' is not a land use, so permissibility has not been checked —
        and a readiness check that stayed silent about that would be reporting
        on an application nobody had checked could proceed."""
        result = check(call, proposed_use="fitout")
        stops = findings(result, "stop")
        assert stops and "describes the work" in stops[0]["finding"]

    def test_a_prohibited_use_stops_before_the_documents(self, call):
        result = check(call, proposed_use="industry", zone_code="R2")
        assert findings(result, "stop")
        assert result["outstanding"][0]["severity"] == "stop"

    def test_a_prohibited_use_is_not_reported_as_a_settled_refusal(self, call):
        """The land use table is not the whole story: a SEPP can permit what it
        omits and prevails over the LEP."""
        result = check(call, proposed_use="industry", zone_code="R2")
        advice = " ".join(f["do_this"] for f in findings(result, "stop"))
        assert "State Environmental Planning Policy" in advice
        assert "not a settled refusal" in advice

    def test_an_unknown_zone_is_not_worked_around(self, call):
        result = call("check_da_readiness", {"proposed_use": "cafe"})
        stops = findings(result, "stop")
        assert stops and "zone is not known" in stops[0]["finding"]


class TestTheRejectionGroundsAreChecked:
    """s39 is a fourteen-day window on administrative grounds. These are the
    ones a tool can act on.

    Note the split between severities. Sections 25 and 39(1)(a) apply to every
    application, so they are reported as "confirm_before_lodging" rather than as
    deficiencies — emitting them as deficiencies made every proposal ever
    checked come back "not ready", and a warning on every answer carries no
    information. "rejection_risk" is reserved for something actually known to
    be wrong.
    """

    def test_the_approvals_list_is_always_raised(self, call):
        """s25(b) requires the application to *list* the other approvals, and
        s39(1)(d) makes failing to do so a ground to reject. Applicants read
        the field as asking whether they have the approvals, which it does not."""
        result = check(call)
        risks = findings(result, "confirm_before_lodging")
        assert any("list the other approvals" in f["finding"] for f in risks)
        assert result["approvals_to_list_on_the_application"]["clause"] == "s25"
        assert result["approvals_to_list_on_the_application"]["list_these"]

    def test_a_clause_4_6_request_is_required_when_a_standard_is_contravened(self, call):
        result = check(call, contravenes_development_standard=True)
        risks = " ".join(f["finding"] for f in findings(result, "rejection_risk"))
        assert "clause 4.6" in risks

    def test_an_unstated_contravention_is_raised_rather_than_assumed_away(self, call):
        result = check(call)
        assert any("contravenes a development standard" in f["finding"]
                   for f in result["outstanding"])

    def test_basix_carries_its_three_month_expiry(self, call):
        """A certificate obtained early and held while plans were finalised is
        a common way to have a residential DA sent back for a document the
        applicant believes it has."""
        result = check(call, proposed_use="dwelling house", development_type="dwelling",
                       zone_code="R2")
        risks = " ".join(f["finding"] for f in findings(result, "confirm_before_lodging"))
        assert "BASIX" in risks and "three months" in risks

    def test_a_description_of_development_is_drafted_from_the_proposal(self, call):
        """s39(1)(a) — unclear about the consent sought. 'Fitout' names no
        consent; the change of use, the previous use and the components do."""
        result = check(call, existing_use="office")
        drafted = " ".join(f["do_this"] for f in findings(result, "confirm_before_lodging"))
        assert "Change of use from office to cafe" in drafted


class TestFloodIsNeverReportedAsClear:
    """The state Flood Planning Map holds no features for the Lismore LGA, so
    an empty result means the dataset does not cover this council. The CBD was
    inundated in 2022."""

    def test_flood_always_appears(self, call):
        result = check(call, property_address=CBD)
        assert any("lood" in f["finding"] for f in result["outstanding"])

    def test_an_unestablished_flood_status_says_so(self, call):
        result = check(call, property_address=CBD)
        assert result["understood_as"]["flood"] == "not established"
        flood = [f for f in result["outstanding"] if "lood" in f["finding"]][0]
        assert "cannot be ruled out" in flood["finding"]

    def test_the_flood_planning_level_is_always_a_question_for_council(self, call):
        result = check(call, property_address=CBD)
        assert any("Flood Planning Level" in q["question"]
                   for q in result["questions_for_council"])


class TestTheQuestionsFollowTheProposal:
    """Ten questions asked of every proposal would be a form letter. Each is
    raised only where it actually bites."""

    def test_the_cbd_question_disappears_once_the_site_is_placed(self, call):
        raised = [q["question"] for q in check(call)["questions_for_council"]]
        assert any("Map 1" in q for q in raised)
        settled = [q["question"] for q in
                   check(call, location="outside_cbd")["questions_for_council"]]
        assert not any("Map 1" in q for q in settled)

    def test_the_catchment_question_disappears_once_council_has_confirmed_it(self, call):
        assert any("catchment" in q["question"] for q in check(call)["questions_for_council"])
        settled = check(call, catchment="urban")["questions_for_council"]
        assert not any("catchment" in q["question"] for q in settled)

    def test_a_new_building_is_not_asked_the_change_of_use_questions(self):
        questions = {q["key"] for q in open_questions(
            Proposal(proposed_use="cafe", development_type="commercial", in_cbd=False,
                     catchment="urban"))}
        assert "codes_sepp_or_existing_use_rights" not in questions
        assert "existing_use_allowance" not in questions

    def test_a_change_of_use_is_asked_whether_it_needs_a_da_at_all(self):
        """The one question on the list that can remove the entire
        application, so it is asked first."""
        questions = open_questions(Proposal(proposed_use="cafe", existing_use="office"))
        assert questions[0]["key"] == "codes_sepp_or_existing_use_rights"


class TestParkingIsARangeUntilTheSiteIsPlaced:
    """Schedule 1 is the rate outside the CBD; inside it a fixed 3.3/100m²
    replaces it. Picking either would be a number, and the wrong one."""

    def test_both_readings_are_given_when_the_location_is_unknown(self, call):
        parking = check(call, floor_area_sqm=80)["parking"]
        assert "between" in str(parking["spaces_required"])

    def test_one_reading_is_given_once_the_location_is_known(self, call):
        parking = check(call, floor_area_sqm=80, location="cbd")["parking"]
        assert parking["spaces_required"] == 3

    def test_a_shortfall_is_only_asserted_when_both_readings_agree(self, call):
        """With no spaces at all every reading is short; with enough for the
        CBD rate but not Schedule 1, neither answer is available yet."""
        assert check(call, floor_area_sqm=80, spaces_provided=0)["parking"]["shortfall"] is True
        assert check(call, floor_area_sqm=80, spaces_provided=99)["parking"]["shortfall"] is False
        undecided = check(call, floor_area_sqm=80, spaces_provided=5)["parking"]
        assert undecided["shortfall"] is None
        assert "which rate applies" in undecided["note"]

    def test_the_missing_components_are_named(self, call):
        """This tool takes no seat or staff count and the cafe rule adds one
        for each. A partial figure presented as the requirement is the failure
        `estimate_spaces` exists to avoid."""
        parking = check(call, floor_area_sqm=80)["parking"]
        assert "get_parking_rates" in parking["for_the_full_calculation"]


class TestItNeverSaysReady:
    def test_the_best_verdict_is_a_smaller_claim(self, call):
        result = check(call, location="outside_cbd", catchment="urban",
                       contravenes_development_standard=False,
                       documents_prepared=[
                           "development application form", "owner's consent", "SEE",
                           "site plan", "architectural plans", "cost estimate",
                           "description of the existing approved use",
                           "BCA compliance assessment", "fire safety upgrade report",
                           "access upgrade assessment", "car parking assessment",
                           "operating hours", "waste storage", "acoustic report",
                       ])
        assert result["documents"]["missing"] == []
        assert result["verdict"].startswith("Nothing this tool can check is outstanding")
        assert "smaller claim than 'ready'" in result["verdict"]
        assert "completeness check" in result["verdict"]
        # The statutory items still appear — they just no longer masquerade as
        # findings about this particular proposal.
        assert findings(result, "confirm_before_lodging")

    def test_it_says_what_it_did_not_check(self, call):
        unchecked = " ".join(check(call)["not_checked_here"])
        assert "legible" in unchecked
        assert "SEPP" in unchecked


class TestTheBrief:
    """It is printed and carried into a room. Fifteen minutes is the constraint
    the whole document is shaped by."""

    def test_it_is_text_not_json(self, call):
        assert isinstance(brief(call), str)

    def test_it_carries_the_duty_planner_times(self, call):
        text = brief(call)
        assert "Tuesdays and Thursdays" in text
        assert "No appointment needed" in text

    def test_it_says_what_not_to_ask(self, call):
        """A session spent re-deriving the zone is a session wasted. The
        'already answered' section is what makes the fifteen minutes work."""
        text = brief(call, property_address=CBD)
        section = text[text.find("2. ALREADY ANSWERED"):text.find("3. QUESTIONS")]
        assert "E2" in section
        assert "40 days is calendar days" in section

    def test_it_does_not_claim_to_have_settled_what_it_could_not(self, call):
        """With no address there is no zone, and a section claiming otherwise
        would waste the session more surely than saying nothing."""
        text = call("prepare_prelodgement_brief", {"proposed_use": "cafe"})
        section = text[text.find("2. ALREADY ANSWERED"):text.find("3. QUESTIONS")]
        assert "The zone is" not in section

    def test_the_session_holds_five_questions_and_the_rest_are_offered(self, call):
        text = brief(call, existing_use="office", floor_area_sqm=80)
        assert "Q5." in text and "Q6." not in text
        assert "4. IF THERE IS TIME" in text

    def test_every_question_has_somewhere_to_write_the_answer(self, call):
        text = brief(call, existing_use="office")
        assert text.count("Answer: ___") == text.count("   Q")

    def test_it_ends_with_what_to_do_before_lodging_regardless(self, call):
        """The questions are for Council; this part is not contingent on the
        session happening at all."""
        text = brief(call)
        assert "5. BEFORE LODGING, REGARDLESS" in text
        # The section text is wrapped for printing, so the phrase spans a line.
        assert "taken never to have been made" in " ".join(text.split())

    def test_it_fits_a_printed_page(self, call):
        over = [line for line in brief(call, existing_use="office").splitlines()
                if len(line) > 78]
        assert over == [], over


class TestReferralsChangeMoreThanTheDocuments:
    def test_a_referral_extends_the_period_and_creates_a_rejection_risk(self, call):
        result = check(call, development_characteristics=["bushfire_prone"])
        assert "rural_fire_service" in result["referrals"]
        assert "60 days" in result["referrals_change_the_timeline"]
        assert "s39(1)(d)" in result["referrals_change_the_timeline"]

    def test_an_unrecognised_characteristic_is_not_silence(self, call):
        """Dropping it reads as 'no referral required' for a site that may well
        need one."""
        result = check(call, development_characteristics=["asbestos everywhere"])
        assert result["characteristics_not_recognised"]["not_assessed"] == \
            ["asbestos everywhere"]


class TestTheAddressIsShownBack:
    def test_the_matched_address_is_reported_with_the_zone(self, call):
        """A zone read off the wrong property flows straight into a
        permissibility answer and then into an SEE."""
        result = call("check_da_readiness",
                      {"proposed_use": "cafe", "property_address": CBD})
        assert "12 Keen Street Lismore 2480" in result["how_that_was_established"]["zone"]

    def test_a_failed_lookup_says_so_rather_than_proceeding_quietly(self, call, monkeypatch):
        from lismore_da_mcp import addresses

        monkeypatch.setattr(addresses, "_get_json",
                            lambda url, params: (_ for _ in ()).throw(OSError("down")))
        result = call("check_da_readiness",
                      {"proposed_use": "cafe", "property_address": CBD})
        assert result["understood_as"]["zone_code"] is None
        assert findings(result, "stop")
