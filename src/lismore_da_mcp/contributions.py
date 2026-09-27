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
from lismore_da_mcp.interpretations import cite_all
from lismore_da_mcp.landuse import canonical_use, lep_term_for

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
    key, how, _ = _resolve(term)
    return key, how


def _resolve(term: str) -> tuple[str | None, str | None, str | None]:
    """As resolve_development_type, plus the HIERARCHY_TO_TYPE term that decided it.

    Which term decided it is what says whether a registered reading was relied
    on: 'food and drink premises' reaching the retail row, or 'warehouse or
    distribution centre' reaching the industry row, is a judgement, where 'shop'
    reaching retail premises is not.
    """
    if not term:
        return None, None, None

    target = canonical_use(term)

    # A Table E2 key or plan name, given directly.
    for key, entry in DEVELOPMENT_TYPE_RATES.items():
        if target in (canonical_use(key), canonical_use(entry["plan_name"])):
            return key, "exact", None

    for hierarchy_term, key in HIERARCHY_TO_TYPE.items():
        if canonical_use(hierarchy_term) == target:
            return key, "exact", hierarchy_term

    # Otherwise walk up the land use hierarchy to the first term Table E2 covers.
    for parent in LAND_USE_HIERARCHY.get(target, []):
        parent_canonical = canonical_use(parent)
        for hierarchy_term, key in HIERARCHY_TO_TYPE.items():
            if canonical_use(hierarchy_term) == parent_canonical:
                return key, f"via '{parent}'", hierarchy_term

    return None, None, None


# The Table E2 rows reached through a registered reading rather than by name.
# ROADMAP.md B1 — data/interpretations.py carries each one's alternative.
_READING_FOR_TERM = {
    "food and drink premises": "food_and_drink_charged_as_retail",
    "warehouse or distribution centre": "warehouse_charged_as_industry",
}


def _units(entry: dict, counts: dict) -> tuple[float | None, str]:
    """How many chargeable units the proposal has, in the base Table E2 uses.

    `None` means not supplied and `0` means zero — a previous use with no floor
    area is how a caller says the area is new (ROADMAP.md T1). The schema's
    `minimum: 0` keeps negatives out before this is reached.
    """
    argument, divisor, described = BASE_UNITS[entry["base"]]
    supplied = counts.get(argument)
    if supplied is None:
        return None, argument
    return supplied / divisor, described


def _same_use(proposed: str, existing: str) -> bool:
    """Whether the previous use is the proposal's own use, not a different one.

    Compared as the LEP term each word stands for, so "Restaurants or cafes" and
    "restaurant or cafe" match, and so do an everyday word and the term A2 maps
    it to. Two different uses on the same Table E2 row — shop and cafe — are not
    the same use: that is a change of use, and the same-area default is right
    for it.
    """
    def term(word: str) -> str:
        mapped = lep_term_for(word)
        return canonical_use(mapped["term"] if mapped else word)

    return term(proposed) == term(existing)


def _rates(entry: dict, catchment: str | None) -> dict:
    if catchment:
        return {catchment: entry["rates"][catchment]}
    return dict(entry["rates"])


def _existing_use_allowance(
    result: dict,
    readings: list[str],
    term: str,
    entry: dict,
    gross: dict,
    counts: dict,
    catchment: str | None,
    existing_use: str,
    existing_counts: dict | None,
) -> dict:
    """Section 2.7: the allowance for the development already lawfully on the site.

    Sets `result["net_contribution"]` where a net can be stated, and appends any
    registered reading the net relies on to `readings`.
    """
    existing_key, existing_how = resolve_development_type(existing_use)
    allowance: dict = {"section": EXISTING_DEVELOPMENT_ALLOWANCE["section"]}
    if existing_key is None:
        allowance["allowed"] = None
        allowance["why_not"] = (
            f"'{existing_use}' does not map to a development type in Table E2, so the "
            "allowance cannot be quantified here. Council assesses it — see "
            "what_you_must_do."
        )
    elif existing_counts is None and _same_use(term, existing_use):
        # The same use, previous size not stated. The same-area default would
        # mean nothing new was built, so the net would be $0 by construction —
        # which is how DA 2024/198's new 14m² of bar area, charged $2,805.67 by
        # Council, was answered $0 (ROADMAP.md T1). The net lies between nil
        # and the gross; only the previous floor area says where.
        existing_entry = DEVELOPMENT_TYPE_RATES[existing_key]
        argument = BASE_UNITS[existing_entry["base"]][0]
        allowance["existing_development_type"] = existing_entry["plan_name"]
        allowance["allowed"] = None
        allowance["supply"] = f"existing_{argument}"
        allowance["at_most"] = gross
        allowance["why_not"] = (
            f"The previous use is the same use as the proposal, so the contribution is "
            f"charged only on what is added. Supply existing_{argument}: what the use "
            f"had before this application, or 0 for an area that is entirely new to it. "
            f"The net is between nil and the at_most figure, which is the charge if "
            f"all of it is new."
        )
        result["net_contribution"] = None
    else:
        existing_entry = DEVELOPMENT_TYPE_RATES[existing_key]
        # A change of use in the same tenancy keeps the same floor area unless
        # the caller says otherwise, which is the ordinary case.
        existing_units, _ = _units(
            existing_entry, counts if existing_counts is None else existing_counts)
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
            if existing_entry["demand"] != entry["demand"]:
                readings.append("allowance_netted_as_totals")
            if existing_counts is None:
                readings.append("allowance_same_floor_area")
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
    return allowance


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

    key, how, decided_by = _resolve(term)
    readings: list[str] = []
    if decided_by in _READING_FOR_TERM:
        readings.append(_READING_FOR_TERM[decided_by])
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
        if readings:
            result["readings_relied_on"] = cite_all(readings)
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
    if entry["base"] == "100m2 GFA" and units != int(units):
        readings.append("contribution_pro_rata")
    if key == "tourist_accommodation" and catchment != "urban":
        readings.append("tourist_rural_published_figure")
    result["units"] = round(units, 4)
    result["units_described"] = described
    result["rate_per_unit"] = rates
    result["contribution"] = gross

    # Section 2.7 — the allowance for what is already lawfully on the site.
    if existing_use:
        allowance = _existing_use_allowance(
            result, readings, term, entry, gross, counts, catchment, existing_use, existing_counts)
        result["existing_development_allowance"] = allowance
    elif entry["demand"] == "non_residential":
        result["ask_about_the_allowance"] = (
            "If this is a change of use, the contribution is charged on the *increase* in "
            "demand over the use already lawfully on the site (section 2.7) — call again "
            "with the previous use to see the difference. It is often the whole bill."
        )

    if not catchment:
        result["catchment"] = CATCHMENT_NOTE

    if readings:
        result["readings_relied_on"] = cite_all(readings)

    result["pro_rata_note"] = (
        "Table E2 states the rate per unit; this applies it pro rata to the area or count "
        "given. Council performs the assessment and can reach a different figure, "
        "particularly on how gross floor area is measured."
    )
    return result
