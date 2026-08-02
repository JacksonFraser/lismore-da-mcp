"""What a DA costs — the lodgement fee, and the rest of it.

The lodgement fee alone was the answer here until 2026-08-02 (PLAN.md item 2.1),
and it is a small and unrepresentative fraction of what a business pays. See
`estimate_total_cost` below for the composition, and `data/contributions.py` for
the largest part of it.
"""

import math

from lismore_da_mcp.contributions import estimate_contribution
from lismore_da_mcp.data.fees import (
    AMENDED_PLAN_FEE_RATE,
    DA_FEE_BRACKETS,
    DA_FEE_DWELLING_THRESHOLD,
    DA_FEE_DWELLING_UNDER_100K,
    DA_FEE_NO_BUILDING_WORK,
    DA_FEE_SCHEDULE_YEAR,
    INTEGRATED_DEVELOPMENT_FEE,
    IT_SERVICE_CHARGE_RATE,
    NOTIFICATION_FEES,
    UNQUANTIFIED_CHARGES,
    schedule_status,
)
from lismore_da_mcp.data.contributions import (
    DEVELOPMENT_TYPE_RATES,
    DSP_DOLLARS,
    SECTION_64_CHARGES,
    SECTION_64_NOTES,
)


def calculate_da_fee(
    development_cost: float,
    involves_building_work: bool = True,
    is_dwelling: bool = False,
) -> dict:
    """Calculate the DA lodgement fee for an estimated cost of development.

    `involves_building_work=False` selects Schedule 4 item 2.7, the flat fee for
    development "not involving the erection of a building, the carrying out of a
    work, the subdivision of land, or the demolition of a building or work" — a
    pure change of use with no fitout. Priced off the cost brackets with a $0
    cost of works, that application was quoted $153 instead of $395.
    """
    if not involves_building_work:
        fee = DA_FEE_NO_BUILDING_WORK
        basis = (
            "EP&A Regulation Schedule 4 Part 2 Item 2.7 — development not involving the "
            "erection of a building, the carrying out of a work, the subdivision of land, "
            "or the demolition of a building or work. A flat fee, independent of cost."
        )
    elif is_dwelling and development_cost <= DA_FEE_DWELLING_THRESHOLD:
        fee = DA_FEE_DWELLING_UNDER_100K
        basis = (
            f"Council's fixed fee for a dwelling of ${DA_FEE_DWELLING_THRESHOLD:,} or "
            "less. Above that the cost brackets apply."
        )
    else:
        basis = "EP&A Regulation Schedule 4 Part 2 Item 2.1, by estimated cost of development."
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

    result = {
        "estimated_fee": round(fee, 2),
        "development_cost": development_cost,
        "basis": basis,
        "cost_estimate_requirement": cost_estimate_requirement,
        "fee_schedule_year": DA_FEE_SCHEDULE_YEAR,
        "note": (
            "This is the statutory DA lodgement fee only — it is not what the development "
            "will cost to approve. The parts and budget_at_least figures alongside this "
            "carry the rest."
        ),
        "currency_warning": (
            f"Calculated from the {DA_FEE_SCHEDULE_YEAR} EP&A Regulation Schedule 4 scale. "
            "Statutory fees are re-set each July — confirm against Council's current fees and "
            "charges before relying on this figure."
        ),
    }

    # Only present when the scale is actually behind, so it means something when
    # it appears. The standing caveat above was already on every answer while
    # the scale sat two years stale, which is exactly why nobody noticed.
    stale = schedule_status()
    if stale:
        result["⚠️ FEE SCHEDULE OUT OF DATE"] = stale

    return result


def estimate_total_cost(
    development_cost: float,
    development_type: str | None = None,
    counts: dict | None = None,
    catchment: str | None = None,
    existing_use: str | None = None,
    involves_building_work: bool = True,
    is_dwelling: bool = False,
) -> dict:
    """Everything Council will charge, with the parts named and the gaps stated.

    The lodgement fee is a fraction of it. For an 80m2 cafe the fee is a few
    hundred dollars and the Section 7.11 contribution is around $16,000, and a
    business that budgets the first and then meets the second is exactly the
    business "having issues with Council" this repo exists for.

    Everything quantifiable is summed into `budget_at_least`; everything that
    genuinely cannot be quantified from the documents in this repo is listed
    rather than estimated, because a made-up figure in a budget is worse than a
    named unknown.
    """
    lodgement = calculate_da_fee(development_cost, involves_building_work, is_dwelling)

    # p32: "Information & Technology Service Charge — 0.1% of estimated cost",
    # on every DA. Never mentioned in any discussion of DA fees.
    it_charge = round(development_cost * IT_SERVICE_CHARGE_RATE, 2)

    parts: dict = {
        "da_lodgement_fee": {
            "amount": lodgement["estimated_fee"],
            "basis": lodgement["basis"],
        },
        "information_technology_service_charge": {
            "amount": it_charge,
            "basis": f"{IT_SERVICE_CHARGE_RATE:.1%} of estimated cost of development, on "
                     "every DA and CDC.",
        },
        "advertising_and_notification": {
            "amounts": dict(NOTIFICATION_FEES),
            "basis": (
                "Council's Community Engagement Strategy fee, additional to the DA fee. "
                "Which tier applies is Council's call under its Community Participation "
                "Plan, so all are shown. Most business DAs that are notified at all fall "
                "in 'expected' or 'moderate'."
            ),
        },
    }

    known_total = lodgement["estimated_fee"] + it_charge
    included = ["da_lodgement_fee", "information_technology_service_charge"]

    # Section 7.11 — usually the largest number on this page.
    if development_type:
        contribution = estimate_contribution(
            development_type,
            counts or {},
            catchment=catchment,
            existing_use=existing_use,
        )
        parts["section_7_11_contributions"] = contribution
        payable = contribution.get("net_contribution") or contribution.get("contribution")
        if payable and catchment and catchment in payable:
            known_total += payable[catchment]
            included.append("section_7_11_contributions")
        elif payable:
            parts["section_7_11_contributions"]["not_added_to_total"] = (
                "The contribution differs by catchment and no catchment was given, so it "
                "is not included in budget_at_least. Add the figure for your catchment."
            )
    else:
        retail = DEVELOPMENT_TYPE_RATES["retail_premises"]["rates"]["urban"]
        parts["section_7_11_contributions"] = {
            "amount": None,
            "why_not": (
                "Supply development_type (and floor area, dwellings or beds) to get this. "
                "It is normally the largest single charge on a commercial DA — retail "
                f"premises are charged ${retail:,.2f} per 100m2 of floor area in the urban "
                "catchment, against a lodgement fee in the hundreds."
            ),
        }

    parts["section_64_water_and_wastewater"] = {
        "amount": None,
        "rates_per_ET": {area: dict(services) for area, services in SECTION_64_CHARGES.items()},
        "rates_are_in": f"{DSP_DOLLARS} dollars, indexed to Sydney CPI each 1 July since.",
        **SECTION_64_NOTES,
    }

    parts["integrated_development"] = {
        "amounts": dict(INTEGRATED_DEVELOPMENT_FEE),
        "basis": (
            "Only if the DA is integrated development — needing an approval from a state "
            "agency as well as consent. The per-body amount is charged for each agency the "
            "application goes to, so run check_referrals: every referral it reports is a "
            f"possible extra ${INTEGRATED_DEVELOPMENT_FEE['per_approval_body']:,.0f}."
        ),
    }

    return {
        "budget_at_least": round(known_total, 2),
        "what_that_covers": included,
        "what_it_leaves_out": [key for key in parts if key not in included],
        "parts": parts,
        "not_estimated": UNQUANTIFIED_CHARGES,
        "amended_plans": (
            f"If plans are amended after lodgement in a way that triggers renotification, "
            f"Council charges {AMENDED_PLAN_FEE_RATE:.0%} of the original DA fee again, plus "
            "the notification fee. Getting the application right the first time is cheaper "
            "than the fee schedule makes it look, and far cheaper in time."
        ),
        "caveat": (
            "Indicative only. Council issues the actual figures, and the contribution is "
            "calculated at determination and payable as a condition of consent. Ask the "
            "Duty Planner for a contributions estimate before you sign a lease — it is free "
            "and it is the single most useful question a business can ask."
        ),
    }
