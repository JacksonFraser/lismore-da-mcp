"""Assessment periods and the clock, against the EP&A Regulation 2021.

PLAN.md item 2.5, and the only Phase 2 item whose source was not already in the
repo. The regulation was fetched rather than written from memory, and doing that
immediately contradicted this repository's own knowledge base: CLAUDE.md said
"40 business days", the regulation says "40 days".

The tests below are mostly about what is said *around* the number. A bare "40
days" is worse than no answer — it reads as a delivery date, and it is a
deemed-refusal threshold.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_timing import SOURCE, normalise, walk  # noqa: E402

from lismore_da_mcp.data import timing as data  # noqa: E402
from lismore_da_mcp.timing import assessment_period  # noqa: E402


@pytest.fixture(scope="module")
def regulation():
    if not SOURCE.exists():
        pytest.skip(f"{SOURCE} not present — run scripts/fetch_epa_regulation.py")
    return normalise(SOURCE.read_text())


class TestQuotesAreInTheRegulation:
    """Same guarantee the parking rates and signage standards get. This one
    additionally guards against the law changing underneath us: the text is
    fetched from legislation.nsw.gov.au, so a mismatch means an amendment."""

    @pytest.mark.parametrize("group_name", [
        "ASSESSMENT_PERIODS", "WHAT_THE_PERIOD_ACTUALLY_IS", "CLOCK_START",
        "CLOCK_STOPS", "INFORMATION_REQUESTS", "REJECTION",
    ])
    def test_group_quotes_appear_verbatim(self, group_name, regulation):
        for label, quote in walk(getattr(data, group_name)):
            assert normalise(quote) in regulation, (
                f"{group_name}.{label} is no longer in the regulation verbatim. This text is "
                "fetched from legislation.nsw.gov.au — a mismatch most likely means the "
                "regulation was amended. Read the current provision before editing."
            )

    def test_rejection_quotes_appear_verbatim(self, regulation):
        assert normalise(data.REJECTION["grounds_verbatim"]) in regulation
        assert normalise(data.REJECTION["consequence_verbatim"]) in regulation

    @pytest.mark.parametrize("key", sorted(data.ASSESSMENT_PERIODS))
    def test_the_number_matches_its_own_quote(self, key):
        """The figure and the words are transcribed separately, so check they
        agree rather than trusting either alone."""
        import re
        entry = data.ASSESSMENT_PERIODS[key]
        assert re.search(rf"\b{entry['days']} days\b", entry["verbatim"])


class TestItIsDaysNotBusinessDays:
    """The finding that came out of reading the source, and the reason this item
    was worth doing from the regulation rather than from memory."""

    def test_the_standard_period_is_40_calendar_days(self):
        assert data.ASSESSMENT_PERIODS["standard"]["days"] == 40

    def test_the_regulation_distinguishes_the_two(self, regulation):
        """"Business days" appears in the regulation where it is meant, so the
        bare "days" in s91 is the drafter's distinction, not an inference."""
        assert "business days" in regulation
        assert "the assessment period is 40 days for all other development applications" \
            in regulation

    def test_the_answer_says_calendar_days_explicitly(self, call):
        result = call("get_assessment_timeline", {})
        assert "calendar days" in result["these_are_calendar_days"]
        assert "business days" in result["these_are_calendar_days"]

    def test_the_knowledge_base_no_longer_claims_business_days(self):
        """CLAUDE.md said "40 business days" and was wrong. It is loaded as
        context in every session, so leaving it would have the agent contradict
        its own tool."""
        text = (ROOT / "CLAUDE.md").read_text()
        assessment = text[text.find("### Assessment Timeframe"):]
        assessment = assessment[:assessment.find("\n## ")]
        assert "Standard: 40 business days" not in assessment
        assert "40 calendar days" in assessment or "**40 days** (calendar)" in assessment


class TestThePeriodIsNotADeliveryDate:
    def test_the_correction_leads_the_answer(self, call):
        """Quoting the number first and qualifying it afterwards is how "40
        days" became a delivery date in the first place."""
        result = call("get_assessment_timeline", {})
        assert list(result)[0] == "read_this_first"
        assert "appeal right rather than an outcome" in result["read_this_first"]

    def test_it_says_a_deemed_refusal_is_not_a_refusal(self, call):
        result = call("get_assessment_timeline", {})
        assert "does not mean the DA has been refused" in result["read_this_first"]

    def test_no_calendar_date_is_produced(self, call):
        """The count runs from lodgement, which the applicant does not control.
        A date from a submission date would be the number most wanted and least
        safe to give."""
        result = call("get_assessment_timeline", {})
        assert "deliberately does not turn the period into a calendar date" in \
            result["no_date_is_calculated"]


class TestTheRightPeriodIsSelected:
    @pytest.mark.parametrize("flags,expected", [
        ({}, 40),
        ({"is_designated": True}, 60),
        ({"is_integrated": True}, 60),
        ({"requires_concurrence": True}, 60),
        ({"is_crown": True}, 70),
        ({"is_state_significant": True}, 90),
    ])
    def test_period_by_kind_of_development(self, flags, expected):
        assert assessment_period(**flags)["assessment_period_days"] == expected

    def test_the_longest_applicable_period_wins(self):
        """A proposal can be several of these at once."""
        assert assessment_period(is_state_significant=True, is_designated=True,
                                 is_integrated=True)["assessment_period_days"] == 90

    def test_the_default_is_the_shortest_period_and_says_what_lengthens_it(self, call):
        """Unstated flags give the tightest timeline rather than a comfortable
        one, and the answer names the triggers that would extend it."""
        result = call("get_assessment_timeline", {})
        assert result["assessment_period_days"] == 40
        assert "60 days" in result["what_would_lengthen_it"]
        assert "check_referrals" in result["what_would_lengthen_it"]

    def test_a_longer_period_does_not_carry_the_lengthening_note(self, call):
        result = call("get_assessment_timeline", {"is_integrated": True})
        assert "what_would_lengthen_it" not in result


class TestWhatStopsTheClock:
    def test_the_25_day_limit_is_surfaced(self, call):
        """The least-known provision in this area and the reason the item is
        worth a tool: a request after day 25 does not stop the clock at all."""
        result = call("get_assessment_timeline", {})
        limit = result["the_clock"]["when_it_stops"]["the_25_day_limit"]
        assert "s94(3)" in limit["clause"]
        assert "within 25 days" in limit["provision"]
        assert "does not stop it" in limit["in_practice"]

    def test_the_clock_starts_at_lodgement_not_submission(self, call):
        result = call("get_assessment_timeline", {})
        start = result["the_clock"]["when_it_starts"]
        assert "Lodged, not submitted" in start["in_practice"]
        assert "completeness check" in start["in_practice"]

    def test_rejection_is_reported_as_undoing_not_delaying(self, call):
        """"Taken never to have been made" is the phrase that matters. A
        business hearing "rejected" thinks "delayed"."""
        result = call("get_assessment_timeline", {})
        never = result["the_clock"]["when_it_never_starts"]
        assert "taken never to have been made" in never["consequence"]
        assert "starts over from zero" in never["in_practice"]
        assert "fee comes back in full" in never["the_fee_comes_back"]

    def test_silence_on_an_information_request_is_flagged_as_a_decision(self, call):
        result = call("get_assessment_timeline", {})
        silence = result["if_council_asks_for_more_information"][
            "missing_the_deadline_is_not_neutral"]
        assert "s36(5)" in silence["clause"]
        assert "not a neutral delay" in silence["in_practice"]
        assert "ask for it before the deadline" in silence["in_practice"]

    def test_the_applicant_is_told_what_cannot_be_demanded_at_da_stage(self, call):
        """s36(2) is a genuine limit and applicants do not know they have it."""
        result = call("get_assessment_timeline", {})
        limit = result["if_council_asks_for_more_information"][
            "what_cannot_be_demanded_at_da_stage"]
        assert "construction certificate" in limit["provision"].lower()
        assert "worth a polite question" in limit["in_practice"]


class TestWhatTheApplicantControls:
    def test_every_lever_names_the_cost_of_missing_it(self, call):
        """The item's actual brief: which of a business's own omissions cost it
        weeks."""
        result = call("get_assessment_timeline", {})
        assert result["what_you_control"]
        for lever in result["what_you_control"]:
            assert lever["lever"] and lever["costs_if_missed"] and lever["how"]

    def test_lodging_something_complete_is_the_first_lever(self, call):
        result = call("get_assessment_timeline", {})
        first = result["what_you_control"][0]
        assert "taken never to have been made" in first["costs_if_missed"]
        assert "get_da_checklist" in first["how"]

    def test_it_hands_off_to_the_approvals_that_follow_the_consent(self, call):
        """The consent is not the end of the timeline — the CC cannot start
        before it and the OC gates the opening."""
        result = call("get_assessment_timeline", {})
        assert "get_other_approvals" in result["what_to_tell_a_landlord_or_a_builder"]
        assert "Occupation Certificate" in result["what_to_tell_a_landlord_or_a_builder"]
