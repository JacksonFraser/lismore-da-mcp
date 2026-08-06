"""How long a DA takes, and what stops the clock (EP&A Regulation 2021)."""

import json

from mcp.types import TextContent

from lismore_da_mcp.registry import tool
from lismore_da_mcp.timing import assessment_period
from lismore_da_mcp.timing import information_request
from lismore_da_mcp.timing import levers
from lismore_da_mcp.timing import the_clock


@tool(
    name='get_assessment_timeline',
    description="How long a DA takes and what stops the clock, from the EP&A Regulation 2021. The 40-day period is a deemed-refusal threshold, not a delivery date: it is when the applicant gains a right to appeal, not when Council must decide. Covers when the clock starts (lodgement, not submission), what stops it (a request for information, but only if made within 25 days), and what undoes it entirely (rejection, which means the DA is taken never to have been made). Use this before a business commits to a fitout or opening date.",
    properties={
        'is_designated': {'type': 'boolean', 'description': 'Optional. Whether the development is designated development (EP&A Regulation Schedule 3 — large-scale or high-impact uses). Makes the period 60 days.'},
        'is_integrated': {'type': 'boolean', 'description': 'Optional. Whether the development is integrated development, meaning it also needs an approval from another agency under one of the Acts listed in EP&A Act section 4.46. Makes the period 60 days. check_referrals indicates whether a proposal is likely to trigger this.'},
        'requires_concurrence': {'type': 'boolean', 'description': "Optional. Whether the development requires another authority's concurrence. Makes the period 60 days."},
        'is_state_significant': {'type': 'boolean', 'description': 'Optional. Whether the development is State significant development. Makes the period 90 days.'},
        'is_crown': {'type': 'boolean', 'description': 'Optional. Whether this is a Crown development application. The period is 70 days.'},
    },
    required=[],
)
def get_assessment_timeline(arguments: dict):
    period = assessment_period(
        is_designated=arguments.get("is_designated"),
        is_integrated=arguments.get("is_integrated"),
        requires_concurrence=arguments.get("requires_concurrence"),
        is_state_significant=arguments.get("is_state_significant"),
        is_crown=arguments.get("is_crown"),
    )

    response = {
        # The correction leads. Quoting the number first and qualifying it
        # afterwards is how "40 days" became a delivery date in the first place.
        "read_this_first": period.pop("what_this_period_actually_is")["plain"],
        **period,
        "the_clock": the_clock(),
        "if_council_asks_for_more_information": information_request(),
        "what_you_control": levers(),
    }

    response["no_date_is_calculated"] = (
        "This deliberately does not turn the period into a calendar date. The count runs from "
        "lodgement, and lodgement is not when you press submit — it is when the Planning "
        "Portal's completeness check passes and the fee is paid, which is neither predictable "
        "nor fully in your hands. A date produced from a submission date would be the one "
        "number a business would most like to have and the one least safe to give."
    )
    response["what_to_tell_a_landlord_or_a_builder"] = (
        "Do not commit to an opening date off the statutory period. Ask Council's Duty Planner "
        "what current turnaround looks like for the kind of DA you are lodging — it is a fair "
        "question, the answer is not in any document, and it is free. Then add the approvals "
        "that come after the consent: the Construction Certificate cannot be applied for until "
        "the consent exists, and the Occupation Certificate gates the opening itself. "
        "get_other_approvals lists those in order."
    )
    response["source"] = (
        "Environmental Planning and Assessment Regulation 2021, Part 4 Division 4 (sections "
        "91-95) and Part 3 (sections 36, 39). Fetched from legislation.nsw.gov.au and checked "
        "by scripts/audit_timing.py."
    )
    return [TextContent(type="text", text=json.dumps(response, indent=2))]
