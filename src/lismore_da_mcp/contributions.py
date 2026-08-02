"""Turning the Section 7.11 rates into a number for a specific proposal.

PLAN.md item 2.1. The contribution, not the lodgement fee, is usually the
largest single line in a commercial DA — an 80m2 cafe fitout attracts a
lodgement fee of a few hundred dollars and a contribution around $16,000 — so
this is the calculation a business most needs and least expects.

Two things here are load-bearing and easy to get wrong later:

**The catchment is never assumed.** Rates differ by catchment and for retail the
rural rate is the higher of the two, so defaulting to urban would understate a
rural proposal by 20%. Without a stated catchment every figure is returned.

**A change of use is charged on the increase, not the total** (plan section
2.7). A shop becoming a cafe is retail premises either way and may attract
nothing at all; an office becoming a cafe steps from 1.6 to 7 peak vehicle trips
per 100m2 and attracts most of the full rate. Getting this wrong in the
pessimistic direction talks a viable business out of a tenancy, and in the
optimistic direction leaves it with an unbudgeted consent condition.
"""

from lismore_da_mcp.data.contributions import (
    CATCHMENT_NOTE,
    CATCHMENTS,
    DEVELOPMENT_TYPE_RATES,
    EXISTING_DEVELOPMENT_ALLOWANCE,
    HIERARCHY_TO_TYPE,
    INDEXATION,
    OTHER_DEVELOPMENT,
    PLAN_NAME,
)
from lismore_da_mcp.data.definitions import LAND_USE_HIERARCHY
from lismore_da_mcp.landuse import canonical_use

# What each Table E2 base is counted in, and the argument that supplies it.
BASE_UNITS = {
    "100m2 GFA": ("gross_floor_area_m2", 100.0, "m2 of gross floor area"),
    "Dwelling": ("dwellings", 1.0, "dwellings"),
    "Bed / Site": ("beds_or_sites", 1.0, "beds or sites"),
}


def resolve_development_type(term: str) -> tuple[str | None, str | None]:
    """Map a proposed use onto a Table E2 row.

    Returns (key, how_it_matched). Resolution goes through LAND_USE_HIERARCHY,
    the same table check_permissibility uses, so "cafe" reaches retail premises
    via food and drink premises without this module enumerating every business
    that might open in Lismore.
    """
    if not term:
        return None, None

    target = canonical_use(term)

    # A Table E2 key or plan name, given directly.
    for key, entry in DEVELOPMENT_TYPE_RATES.items():
        if target in (canonical_use(key), canonical_use(entry["plan_name"])):
            return key, "exact"

    for hierarchy_term, key in HIERARCHY_TO_TYPE.items():
        if canonical_use(hierarchy_term) == target:
            return key, "exact"

    # Otherwise walk up the land use hierarchy to the first term Table E2 covers.
    for parent in LAND_USE_HIERARCHY.get(target, []):
        parent_canonical = canonical_use(parent)
        for hierarchy_term, key in HIERARCHY_TO_TYPE.items():
            if canonical_use(hierarchy_term) == parent_canonical:
                return key, f"via '{parent}'"

    return None, None


def _units(entry: dict, counts: dict) -> tuple[float | None, str]:
    """How many chargeable units the proposal has, in the base Table E2 uses."""
    argument, divisor, described = BASE_UNITS[entry["base"]]
    supplied = counts.get(argument)
    if supplied is None or supplied <= 0:
        return None, argument
    return supplied / divisor, described


def _rates(entry: dict, catchment: str | None) -> dict:
    if catchment:
        return {catchment: entry["rates"][catchment]}
    return dict(entry["rates"])


def estimate_contribution(
    term: str,
    counts: dict,
    catchment: str | None = None,
    existing_use: str | None = None,
    existing_counts: dict | None = None,
) -> dict:
    """Estimate the Section 7.11 contribution for a proposal.

    `counts` carries whichever of gross_floor_area_m2 / dwellings / beds_or_sites
    the development type is charged on. `existing_use` triggers the section 2.7
    allowance for the development already lawfully on the site.
    """
    result: dict = {
        "plan": PLAN_NAME,
        "indexation": INDEXATION,
    }

    if catchment and catchment not in CATCHMENTS:
        return {
            **result,
            "error": f"Unknown catchment '{catchment}'.",
            "catchments": list(CATCHMENTS),
        }

    key, how = resolve_development_type(term)
    if key is None:
        return {
            **result,
            "development_type": term,
            "contribution": None,
            "why_not": OTHER_DEVELOPMENT,
            "listed_development_types": [e["plan_name"] for e in DEVELOPMENT_TYPE_RATES.values()],
        }

    entry = DEVELOPMENT_TYPE_RATES[key]
    result["development_type"] = entry["plan_name"]
    result["charged_per"] = entry["base"]
    if how != "exact":
        result["interpreted_as"] = (
            f"'{term}' is charged as '{entry['plan_name']}' {how} in the LEP land use "
            "hierarchy. If Council classifies it differently the rate changes — retail is "
            "the highest non-residential rate in the plan, so this is worth confirming."
        )
    if entry.get("note"):
        result["what_to_know"] = entry["note"]

    units, described = _units(entry, counts)
    if units is None:
        return {
            **result,
            "contribution": None,
            "why_not": (
                f"This use is charged per {entry['base']}. Supply {described} to get a "
                "figure — the rates below are per unit."
            ),
            "rate_per_unit": _rates(entry, catchment),
        }

    rates = _rates(entry, catchment)
    gross = {name: round(rate * units, 2) for name, rate in rates.items()}
    result["units"] = round(units, 4)
    result["units_described"] = described
    result["rate_per_unit"] = rates
    result["contribution"] = gross

    # Section 2.7 — the allowance for what is already lawfully on the site.
    if existing_use:
        existing_key, existing_how = resolve_development_type(existing_use)
        allowance: dict = {"section": EXISTING_DEVELOPMENT_ALLOWANCE["section"]}
        if existing_key is None:
            allowance["allowed"] = None
            allowance["why_not"] = (
                f"'{existing_use}' does not map to a development type in Table E2, so the "
                "allowance cannot be quantified here. Council assesses it — see "
                "what_you_must_do."
            )
        else:
            existing_entry = DEVELOPMENT_TYPE_RATES[existing_key]
            # A change of use in the same tenancy keeps the same floor area unless
            # the caller says otherwise, which is the ordinary case.
            existing_units, _ = _units(existing_entry, existing_counts or counts)
            if existing_units is None:
                allowance["allowed"] = None
                allowance["why_not"] = (
                    f"The previous use is charged per {existing_entry['base']}, which was "
                    "not supplied."
                )
            else:
                existing_rates = _rates(existing_entry, catchment)
                credit = {
                    name: round(rate * existing_units, 2)
                    for name, rate in existing_rates.items()
                }
                net = {
                    name: round(max(0.0, gross[name] - credit[name]), 2)
                    for name in gross
                }
                allowance["existing_development_type"] = existing_entry["plan_name"]
                if existing_how != "exact":
                    allowance["existing_interpreted_as"] = (
                        f"'{existing_use}' read as '{existing_entry['plan_name']}' {existing_how}"
                    )
                if existing_counts is None:
                    allowance["assumption"] = (
                        "The previous use is taken to occupy the same floor area as the "
                        "proposal, which is the ordinary case for a change of use in an "
                        "existing tenancy. Supply the previous floor area if it differed."
                    )
                allowance["allowance"] = credit
                result["net_contribution"] = net
                if all(value == 0 for value in net.values()):
                    allowance["effect"] = (
                        "The previous use generated at least as much demand as the "
                        "proposal, so on these figures no contribution is payable. That is "
                        "a conclusion to put to Council with evidence, not to assume."
                    )
                else:
                    allowance["effect"] = (
                        "The contribution is charged on the increase in demand only. The "
                        "net figures above are what to budget."
                    )
        allowance["existing_lawful_development"] = (
            EXISTING_DEVELOPMENT_ALLOWANCE["existing_lawful_development"]
        )
        allowance["what_you_must_do"] = EXISTING_DEVELOPMENT_ALLOWANCE["what_you_must_do"]
        result["existing_development_allowance"] = allowance
    elif entry["demand"] == "non_residential":
        result["ask_about_the_allowance"] = (
            "If this is a change of use, the contribution is charged on the *increase* in "
            "demand over the use already lawfully on the site (section 2.7) — call again "
            "with the previous use to see the difference. It is often the whole bill."
        )

    if not catchment:
        result["catchment"] = CATCHMENT_NOTE

    result["pro_rata_note"] = (
        "Table E2 states the rate per unit; this applies it pro rata to the area or count "
        "given. Council performs the assessment and can reach a different figure, "
        "particularly on how gross floor area is measured."
    )
    return result
