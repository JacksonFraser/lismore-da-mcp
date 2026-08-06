"""Work out the assessment period for a proposal, and model the clock.

The arithmetic here is trivial; the judgement is in what gets said around it.
A bare "40 days" is worse than no answer, because it reads as a delivery date
and it is not one — it is the point at which a deemed refusal, and so an appeal
right, arises. Every path through this module carries that distinction.

Nothing here converts a period into a calendar date. The regulation counts days
from lodgement, and lodgement is not a date the applicant controls or can
predict: it happens when the Portal's completeness check passes and the fee is
paid. Producing "your DA will be determined on 14 October" from a submission
date would be inventing the one number a business would most like to have.
"""

from lismore_da_mcp.data.timing import ASSESSMENT_PERIODS
from lismore_da_mcp.data.timing import CLOCK_START
from lismore_da_mcp.data.timing import CLOCK_STOPS
from lismore_da_mcp.data.timing import INFORMATION_REQUESTS
from lismore_da_mcp.data.timing import REJECTION
from lismore_da_mcp.data.timing import WHAT_THE_APPLICANT_CONTROLS
from lismore_da_mcp.data.timing import WHAT_THE_PERIOD_ACTUALLY_IS

# Which of the s91 periods a proposal falls into. Checked longest-first,
# because a proposal can be several of these at once — integrated development
# that also requires concurrence is still 60 days, and State significant
# development that happens to be designated is 90.
_ORDER = ["state_significant", "crown", "designated_or_integrated", "standard"]


def assessment_period(is_designated: bool | None = None,
                      is_integrated: bool | None = None,
                      requires_concurrence: bool | None = None,
                      is_state_significant: bool | None = None,
                      is_crown: bool | None = None) -> dict:
    """The applicable period under s91, with the provision that sets it.

    Unstated flags are treated as false. That is safe in the direction that
    matters: the standard 40 days is the *shortest* period, so an unflagged
    proposal is told the tightest timeline rather than a comfortable one, and
    the result names the triggers that would lengthen it.
    """
    if is_state_significant:
        key = "state_significant"
    elif is_crown:
        key = "crown"
    elif is_designated or is_integrated or requires_concurrence:
        key = "designated_or_integrated"
    else:
        key = "standard"

    entry = ASSESSMENT_PERIODS[key]
    result = {
        "assessment_period_days": entry["days"],
        "applies_to": entry["applies_to"],
        "provision": entry["verbatim"],
        "clause": f"EP&A Regulation 2021 {entry['clause']}",
        "these_are_calendar_days": (
            "The regulation says 'days', not 'business days' — it uses 'business days' "
            "elsewhere where it means them. So this is calendar days, including weekends and "
            "public holidays. Forty calendar days is under six weeks, not the eight that 'forty "
            "business days' would imply."
        ),
        "what_this_period_actually_is": WHAT_THE_PERIOD_ACTUALLY_IS,
    }

    if key == "standard":
        result["what_would_lengthen_it"] = (
            "This is the fallback period, and it assumes the proposal is not designated "
            "development, not integrated development, and does not require another agency's "
            "concurrence. Any of those makes it 60 days. check_referrals will say whether a "
            "proposal triggers an external referral, which is the usual route into integrated "
            "development."
        )
    return result


def the_clock() -> dict:
    """When the period starts, stops and restarts."""
    return {
        "when_it_starts": {
            "provision": CLOCK_START["verbatim"],
            "clause": f"EP&A Regulation 2021 {CLOCK_START['clause']}",
            "in_practice": CLOCK_START["plain"],
        },
        "when_it_stops": {
            "provision": CLOCK_STOPS["verbatim"],
            "clause": f"EP&A Regulation 2021 {CLOCK_STOPS['clause']}",
            # The single least-known thing in this whole area, and it changes
            # what a delay is worth to each side.
            "the_25_day_limit": {
                "provision": CLOCK_STOPS["the_25_day_limit"]["verbatim"],
                "clause": f"EP&A Regulation 2021 {CLOCK_STOPS['the_25_day_limit']['clause']}",
                "in_practice": CLOCK_STOPS["the_25_day_limit"]["plain"],
            },
            "if_the_da_was_referred": {
                "provision": CLOCK_STOPS["referral_authority_requests"]["verbatim"],
                "clause": "EP&A Regulation 2021 "
                          f"{CLOCK_STOPS['referral_authority_requests']['clause']}",
                "in_practice": CLOCK_STOPS["referral_authority_requests"]["plain"],
            },
        },
        "when_it_never_starts": {
            "provision": REJECTION["grounds_verbatim"],
            "clause": f"EP&A Regulation 2021 {REJECTION['clause']}",
            "consequence": REJECTION["consequence_verbatim"],
            "in_practice": REJECTION["plain"],
            "the_fee_comes_back": REJECTION["fee_is_refunded"]["plain"],
            "it_can_be_reviewed": REJECTION["review_right"]["plain"],
        },
    }


def information_request() -> dict:
    """What a request for further information is, and the two traps in it."""
    return {
        "what_it_is": INFORMATION_REQUESTS["power"]["verbatim"],
        "read_this_number_first": {
            "provision": INFORMATION_REQUESTS["what_the_request_must_say"]["verbatim"],
            "clause": "EP&A Regulation 2021 "
                      f"{INFORMATION_REQUESTS['what_the_request_must_say']['clause']}",
            "in_practice": INFORMATION_REQUESTS["what_the_request_must_say"]["plain"],
        },
        "missing_the_deadline_is_not_neutral": {
            "provision": INFORMATION_REQUESTS["silence_counts_as_refusing"]["verbatim"],
            "clause": "EP&A Regulation 2021 "
                      f"{INFORMATION_REQUESTS['silence_counts_as_refusing']['clause']}",
            "in_practice": INFORMATION_REQUESTS["silence_counts_as_refusing"]["plain"],
        },
        "what_cannot_be_demanded_at_da_stage": {
            "provision": INFORMATION_REQUESTS["what_they_cannot_ask_for"]["verbatim"],
            "clause": "EP&A Regulation 2021 "
                      f"{INFORMATION_REQUESTS['what_they_cannot_ask_for']['clause']}",
            "in_practice": INFORMATION_REQUESTS["what_they_cannot_ask_for"]["plain"],
        },
    }


def levers() -> list[dict]:
    """What the applicant controls, which is the point of the item."""
    return WHAT_THE_APPLICANT_CONTROLS
