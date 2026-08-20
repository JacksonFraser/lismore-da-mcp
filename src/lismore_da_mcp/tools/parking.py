"""Off-street parking rates (DCP Chapter 7)."""

import json

from mcp.types import TextContent

from lismore_da_mcp.data.parking import CBD_FIXED_RATE
from lismore_da_mcp.data.parking import COUNTABLE
from lismore_da_mcp.data.parking import COUNTABLE_DESCRIPTIONS
from lismore_da_mcp.data.parking import DISABILITY_PARKING
from lismore_da_mcp.data.parking import PARKING_RATES
from lismore_da_mcp.registry import tool
from lismore_da_mcp.parking import cbd_location as _location
from lismore_da_mcp.parking import cbd_spaces
from lismore_da_mcp.parking import estimate_spaces
from lismore_da_mcp.parking import shortfall_options
from lismore_da_mcp.parking import uses_schedule_1_in_cbd
from lismore_da_mcp.vocabulary import PARKING_SYNONYMS
from lismore_da_mcp.vocabulary import resolve
from lismore_da_mcp.vocabulary import unresolved_error

# The countables, as schema properties, generated from the same dict the
# estimator reads. Ten of the twelve had no argument at all, so a rate that
# counted practitioners or children could never be given them — see the note on
# COUNTABLE. Generating these means adding a countable to a rate cannot silently
# fail to be askable. ROADMAP.md S3.
_COUNTABLE_PROPERTIES = {
    argument: {
        'type': 'number' if argument.endswith('_sqm') else 'integer',
        'description': 'Optional. ' + COUNTABLE_DESCRIPTIONS[argument],
        'minimum': 0,
    }
    for argument in COUNTABLE.values()
}


@tool(
    name='get_parking_rates',
    description='Get off-street parking requirements for a development type in Lismore, and what can be done about a shortfall. Supply floor_area_sqm, spaces_provided and whatever the rate counts (employees, seats, practitioners, children, beds, rooms) for the number of spaces required and any shortfall. A rate whose terms are not all supplied returns no number and says which argument to send — a part of the sum is not a lower bound. IMPORTANT: the Lismore CBD is assessed under a different rate from the rest of the LGA, so supply `location` — without it both readings are returned and neither is the answer.',
    properties={
        'development_type': {'type': 'string', 'description': "Type of development (e.g., 'dwelling_house', 'restaurant', 'shop', 'office', 'warehouse')"},
        'location': {'type': 'string', 'description': "Optional but important. 'cbd' if the site is inside the Lismore CBD as defined on Map 1 of DCP Chapter 7, or 'outside_cbd'. Inside the CBD a fixed rate of 3.3 spaces/100m2 GFA replaces the Schedule 1 rate for non-residential uses, and it is usually far lower. Do not guess — the E2 zone is close to the CBD boundary but is not the same line."},
        'floor_area_sqm': {'type': 'number', 'description': 'Optional. Floor area the rate applies to, in square metres.', 'minimum': 0},
        **_COUNTABLE_PROPERTIES,
        'spaces_provided': {'type': 'integer', 'description': 'Optional. Spaces provided on site, to calculate the shortfall.', 'minimum': 0},
        'existing_gfa_sqm': {'type': 'number', 'description': 'Optional, CBD only. Gross floor area of the existing building on the site. A CBD site being redeveloped or changing use earns a deemed parking credit under DCP 7.7.3.4 which is often most of the requirement, and it is not applied unless this is supplied.', 'minimum': 0},
        'existing_spaces_on_site': {'type': 'integer', 'description': 'Optional, CBD only. Parking spaces physically provided on the existing site. Subtracted from the deemed credit under the DCP 7.7.3.4 formula.', 'minimum': 0},
    },
    required=['development_type'],
)
def get_parking_rates(arguments: dict):
    requested = arguments.get("development_type", "")
    in_cbd = _location(arguments.get("location"))
    match = resolve(requested, PARKING_RATES, PARKING_SYNONYMS)
    if match:
        dev_type = match.key
        result = PARKING_RATES[dev_type]
        response = {
            "development_type": dev_type,
            "parking_spaces": result["spaces"],
            "rate_description": result["rate"],
            "dcp_land_use": result.get("dcp_use"),
            "source": result.get("source", "Lismore DCP Chapter 7 - Off-Street Carparking"),
            "note": "Rates may vary by location. Check specific DCP provisions for exact requirements."
        }
        if result.get("note"):
            response["what_to_check"] = result["note"]
        if match.how != "exact":
            response["interpreted_as"] = (
                f"Read '{requested}' as '{dev_type}'. If that is not the use you meant, "
                "call again with a term from list_parking_types."
            )

        # Which rate even applies. Schedule 1 is the rate *outside* the CBD
        # (§7.7.2); inside it a fixed 3.3/100m² replaces it for everything
        # except residential and tourist accommodation (§7.7.3.1). Answering a
        # CBD business off Schedule 1 overstates its requirement several times
        # over, which is what this tool did until now.
        floor_area = arguments.get("floor_area_sqm") or None
        schedule_1_applies_anyway = uses_schedule_1_in_cbd(dev_type)

        # Every countable the rates can ask for, not the two that had arguments.
        schedule_1 = estimate_spaces(
            result,
            floor_area,
            # `.get()` without `or 0` — an absent argument stays None so the rate
            # declines, and a supplied 0 stays 0 so it counts as zero.
            {key: arguments.get(argument) for key, argument in COUNTABLE.items()},
        )
        cbd = None if schedule_1_applies_anyway else cbd_spaces(
            floor_area,
            arguments.get("existing_gfa_sqm") or None,
            arguments.get("existing_spaces_on_site") or 0,
        )

        if in_cbd is True and not schedule_1_applies_anyway:
            estimate = cbd
            # The headline fields have to describe the rate actually being
            # applied, or the response contradicts its own calculation.
            response["rate_description"] = CBD_FIXED_RATE["verbatim"]
            response["parking_spaces"] = "3.3 per 100m² GFA (fixed CBD rate)"
            response["source"] = CBD_FIXED_RATE["source"]
            response["schedule_1_rate_not_applied"] = (
                f"Schedule 1 would give '{result['rate']}', but Schedule 1 is the rate for "
                "development outside the Lismore CBD (DCP 7.7.2). Inside the CBD the fixed "
                "rate above replaces it."
            )
        elif in_cbd is True:
            estimate = schedule_1
            response["cbd_treatment"] = (
                f"'{dev_type}' is residential or tourist and visitor accommodation, which "
                "DCP 7.7.3.1 exception (i) keeps on the Schedule 1 rate even inside the CBD. "
                "The fixed 3.3/100m² CBD rate does not apply to it."
            )
        else:
            estimate = schedule_1

        if (in_cbd is None and cbd is not None and schedule_1 is not None
                and schedule_1["spaces_required"] is not None):
            # Neither figure is the answer until the site is placed. Presenting
            # both, rather than defaulting, is the same discipline the
            # contributions catchment follows — a silent default here is a
            # wrong number in a business's plans.
            response["which_rate_applies"] = {
                "unresolved": "You have not said whether the site is inside the Lismore CBD, "
                              "and the two rates give different answers. Neither figure below "
                              "is the answer until that is settled.",
                "outside_the_cbd": f"{schedule_1['spaces_required']} space(s) — Schedule 1 "
                                   f"(DCP 7.7.2).",
                "inside_the_cbd": f"{cbd['spaces_required']} space(s) — the fixed rate of 3.3 "
                                  f"spaces/100m² GFA (DCP 7.7.3.1)"
                                  + ("." if arguments.get("existing_gfa_sqm")
                                     else ", before any deemed parking credit for an existing "
                                          "building, which would reduce it further."),
                "how_to_settle_it": "The CBD is the area shown on Map 1 of DCP Chapter 7, which "
                                    "is a map image and cannot be read by this tool. Check it "
                                    "with Council or the Duty Planner, then call again with "
                                    "location='cbd' or location='outside_cbd'.",
            }

        if estimate:
            estimate["applies"] = (
                "inside the Lismore CBD" if in_cbd is True
                else "outside the Lismore CBD" if in_cbd is False
                else "location not stated — see which_rate_applies"
            )
            provided = arguments.get("spaces_provided")
            estimate["spaces_provided"] = provided
            if provided is not None and estimate["spaces_required"] is not None:
                gap = max(0, estimate["spaces_required"] - provided)
                estimate["shortfall"] = gap
                estimate["advice"] = (
                    f"A shortfall of {gap} space(s) has to be addressed in the SEE. It does "
                    "not necessarily have to be built — see addressing_the_shortfall."
                    if gap else "The rate is met by the spaces provided."
                )
                if gap:
                    # The point of PLAN.md 2.2: a shortfall is a decision with
                    # named options in the DCP, not just a number to justify.
                    response["addressing_the_shortfall"] = shortfall_options(
                        gap, bool(in_cbd), dev_type)
            response["calculation"] = estimate
        elif result.get("spec") is None:
            response["no_calculation"] = (
                "This rate cannot be turned into a number from the inputs given — read "
                "rate_description and what_to_check. Guessing a space count here is worse "
                "than not giving one."
            )

        if arguments.get("spaces_provided"):
            response["accessible_parking"] = DISABILITY_PARKING

        return [TextContent(type="text", text=json.dumps(response, indent=2))]
    else:
        # No rate for this use. Say so rather than offering the closest
        # string — a hairdresser given warehouse rates is a wrong answer,
        # not a helpful approximation.
        error = unresolved_error(requested, match, "parking rate", PARKING_RATES)
        error["note"] = (
            "Chapter 7 sets rates by land use category, so an unlisted business usually "
            "falls under a broader term (a hairdresser is generally 'shop' or "
            "'business premises'). Confirm the correct category with Council rather than "
            "assuming the nearest-sounding one."
        )
        return [TextContent(type="text", text=json.dumps(error, indent=2))]


@tool(
    name='list_parking_types',
    description='List all development types that have parking rate information available.',
    properties={},
)
def list_parking_types(arguments: dict):
    return [TextContent(
        type="text",
        text=json.dumps({
            "available_development_types": list(PARKING_RATES.keys()),
            "categories": {
                "residential": ["dwelling_house", "dual_occupancy", "multi_dwelling_housing", "residential_flat_building", "secondary_dwelling", "boarding_house"],
                "commercial": ["shop", "retail", "office", "business_premises", "restaurant", "cafe", "take_away", "medical_centre", "hotel", "motel"],
                "industrial": ["industry", "warehouse", "bulky_goods"],
                "other": ["childcare_centre", "place_of_worship", "gym"]
            }
        }, indent=2)
    )]
