"""Work out which non-DA approvals a proposal needs.

The selection is deliberately generous. Listing an approval that turns out not
to apply costs a business one sentence of reading; omitting one costs it weeks,
and the whole point of PLAN.md 2.4 is that these are the things businesses get
caught by. So where a trigger is uncertain, it is included and the uncertainty
is stated — the inverse of how permissibility or a fee figure is handled, where
a confident wrong answer is the danger.
"""

from lismore_da_mcp.data.approvals import APPROVALS
from lismore_da_mcp.data.approvals import BY_ACTIVITY
from lismore_da_mcp.data.approvals import SEQUENCE
from lismore_da_mcp.data.approvals import TIMING

# Words in a proposed use that imply food handling. Kept broad on purpose: a
# business that turns out not to handle food loses nothing by reading the food
# entries, and "we only do coffee" is still a food business under the Food Act.
FOOD_WORDS = (
    "cafe", "café", "restaurant", "take away", "takeaway", "food", "bakery", "baker",
    "kitchen", "caterer", "catering", "pub", "hotel", "bar", "brewery", "distillery",
    "butcher", "deli", "grocer", "juice", "coffee", "ice cream", "patisserie",
    "canteen", "kiosk", "brewpub", "winery", "cellar door",
)

ALCOHOL_WORDS = (
    "pub", "hotel", "bar", "brewery", "distillery", "winery", "cellar door", "bottle shop",
    "liquor", "tavern", "club", "brewpub",
)

# Uses where a licensed venue is plausible but not implied. A restaurant may or
# may not serve alcohol, and guessing either way is worse than asking.
MAYBE_ALCOHOL_WORDS = ("restaurant", "cafe", "café", "bistro", "function")


def _matches(text: str, words) -> bool:
    return any(word in text for word in words)


def relevant(proposed_use: str = "", building_work: bool | None = None,
             serves_alcohol: bool | None = None, outdoor_dining: bool | None = None,
             connected_to_sewer: bool | None = None,
             works_in_road_reserve: bool | None = None) -> tuple[list[str], list[dict]]:
    """The approvals this proposal probably needs, plus what could not be settled.

    Returns (keys in sequence order, unresolved questions). A question is only
    raised where the answer changes which approvals apply and the caller has not
    supplied it — an unresolved trigger still gets its approval listed, marked
    as conditional, rather than dropped.
    """
    use = (proposed_use or "").lower().strip()
    selected: set[str] = set(BY_ACTIVITY["any_commercial"])
    unresolved: list[dict] = []

    is_food = _matches(use, FOOD_WORDS)
    if is_food:
        selected.update(BY_ACTIVITY["food"])

    if serves_alcohol is True or (serves_alcohol is None and _matches(use, ALCOHOL_WORDS)):
        selected.update(BY_ACTIVITY["alcohol"])
    elif serves_alcohol is None and _matches(use, MAYBE_ALCOHOL_WORDS):
        selected.update(BY_ACTIVITY["alcohol"])
        unresolved.append({
            "question": "Will the business serve alcohol?",
            "why_it_matters": "A liquor licence is issued by Liquor & Gaming NSW, not Council, "
                              "and generally cannot be applied for until development consent "
                              "exists. It adds time after the DA rather than running alongside "
                              "it, so it belongs in the opening date from the start.",
            "listed_anyway": "liquor_licence",
        })

    # Building work is assumed unless ruled out. A change of use with no works
    # is possible but uncommon, and the cost of wrongly omitting the CC and OC
    # is an unlawful start or a delayed opening.
    if building_work is not False:
        selected.update(BY_ACTIVITY["building_work"])
        if building_work is None:
            unresolved.append({
                "question": "Does the proposal involve any building work, including an "
                            "internal fitout?",
                "why_it_matters": "A Construction Certificate and an Occupation Certificate "
                                  "are required for building work and neither can be issued "
                                  "before the development consent exists. Almost every fitout "
                                  "counts.",
                "listed_anyway": "construction_certificate, occupation_certificate",
            })

    if outdoor_dining is True or (outdoor_dining is None and is_food):
        selected.update(BY_ACTIVITY["outdoor_dining"])
        if outdoor_dining is None:
            unresolved.append({
                "question": "Will there be tables or chairs on the footpath?",
                "why_it_matters": "A temporary footpath dining permit is fee-free and is "
                                  "applied for through Service NSW rather than Council. "
                                  "Anything permanent falls outside that policy, carries an "
                                  "annual per-square-metre licence fee, and may become "
                                  "enclosed floor area that generates a parking requirement.",
                "listed_anyway": "outdoor_dining_permit",
            })

    if connected_to_sewer is False:
        selected.update(BY_ACTIVITY["unsewered"])
        # Trade waste is an approval to discharge *to the sewer*. On an
        # unsewered site there is nothing to discharge to, and the load goes to
        # the on-site system instead. This is the one place the generous rule
        # is wrong: listing it here would not be over-inclusive, it would point
        # a business at the wrong approval entirely.
        selected.discard("liquid_trade_waste")
        selected.discard("section_68_approval")
    elif connected_to_sewer is None:
        selected.update(BY_ACTIVITY["sewer_connection"])
        if is_food:
            unresolved.append({
                "question": "Is the premises connected to reticulated sewer?",
                "why_it_matters": "If it is not, an on-site sewage management approval is "
                                  "needed and a commercial kitchen generates far more load "
                                  "than a dwelling — on an unsewered site this is the "
                                  "constraint most likely to stop the proposal, and it needs a "
                                  "consultant's site assessment.",
                "listed_anyway": "section_68_approval",
            })
    else:
        selected.update(BY_ACTIVITY["sewer_connection"])

    if works_in_road_reserve:
        selected.update(BY_ACTIVITY["road_reserve"])

    ordered = [key for key in SEQUENCE if key in selected]
    return ordered, unresolved


def describe(key: str) -> dict:
    """One approval, with its timing spelled out rather than left as a code."""
    entry = APPROVALS[key]
    described = {
        "approval": entry["name"],
        "issued_by": entry["issued_by"],
        "legislation": entry["legislation"],
        "when": TIMING[entry["timing"]],
        "triggered_by": entry["triggered_by"],
    }
    if entry.get("what_it_is"):
        described["what_it_is"] = entry["what_it_is"]
    if entry.get("fee"):
        described["fee"] = entry["fee"]
    if entry.get("fee_source"):
        described["fee_source"] = entry["fee_source"]
    if entry.get("gotcha"):
        described["watch_out_for"] = entry["gotcha"]
    return described


def by_timing(keys: list[str]) -> dict:
    """Group the selection by when it has to happen.

    A flat list of fifteen approvals is a wall. What a business needs is the
    handful that have to happen before it lodges, and the handful it cannot
    start until the consent arrives.
    """
    order = ["before_da", "with_da", "after_consent", "before_work", "before_opening",
             "ongoing"]
    grouped: dict[str, list[str]] = {}
    for key in keys:
        grouped.setdefault(APPROVALS[key]["timing"], []).append(APPROVALS[key]["name"])
    return {TIMING[stage]: grouped[stage] for stage in order if stage in grouped}
