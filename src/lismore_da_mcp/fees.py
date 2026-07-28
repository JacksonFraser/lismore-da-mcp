"""DA lodgement fee, from the EP&A Regulation Schedule 4 scale."""

import math

from lismore_da_mcp.data.fees import DA_FEE_BRACKETS, DA_FEE_SCHEDULE_YEAR


def calculate_da_fee(development_cost: float) -> dict:
    """Calculate DA fee based on estimated development cost."""
    for upper, base, per_thousand, floor in DA_FEE_BRACKETS:
        if development_cost <= upper:
            # Schedule 4 charges the increment "for each $1,000, or part $1,000,
            # by which estimated cost exceeds" the bracket floor — so a partial
            # thousand is charged as a whole one. Interpolating linearly here
            # under-charged every cost that wasn't a round number of thousands.
            excess = max(0.0, development_cost - floor)
            fee = base + per_thousand * math.ceil(excess / 1000)
            break

    cost_estimate_requirement = "Applicant estimate"
    if development_cost > 100000:
        cost_estimate_requirement = "Qualified person estimate"
    if development_cost > 3000000:
        cost_estimate_requirement = "Registered Quantity Surveyor report"

    return {
        "estimated_fee": round(fee, 2),
        "development_cost": development_cost,
        "cost_estimate_requirement": cost_estimate_requirement,
        "fee_schedule_year": DA_FEE_SCHEDULE_YEAR,
        "note": "This is the statutory DA lodgement fee only. Additional fees may apply for advertising, referrals, long service levy, and Section 7.11 contributions.",
        "currency_warning": (
            f"Calculated from the {DA_FEE_SCHEDULE_YEAR} EP&A Regulation Schedule 4 scale. "
            "Statutory fees are re-set each July — confirm against Council's current fees and "
            "charges before relying on this figure."
        ),
    }
