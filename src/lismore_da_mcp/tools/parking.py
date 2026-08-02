"""Off-street parking rates (DCP Chapter 7)."""

import json

from mcp.types import TextContent

from lismore_da_mcp.data.parking import PARKING_RATES
from lismore_da_mcp.registry import tool
from lismore_da_mcp.parking import estimate_spaces
from lismore_da_mcp.vocabulary import PARKING_SYNONYMS
from lismore_da_mcp.vocabulary import resolve
from lismore_da_mcp.vocabulary import unresolved_error


@tool(
    name='get_parking_rates',
    description='Get off-street parking requirements for a development type in Lismore. Supply floor_area_sqm, num_employees and spaces_provided to also get the indicative number of spaces required and any shortfall to be addressed.',
    properties={
        'development_type': {'type': 'string', 'description': "Type of development (e.g., 'dwelling_house', 'restaurant', 'shop', 'office', 'warehouse')"},
        'floor_area_sqm': {'type': 'number', 'description': 'Optional. Floor area the rate applies to, in square metres.'},
        'num_employees': {'type': 'integer', 'description': 'Optional. Number of employees, for rates with a staff component.'},
        'seats': {'type': 'integer', 'description': 'Optional. Seats, for rates based on seating (restaurants, places of worship, function centres).'},
        'spaces_provided': {'type': 'integer', 'description': 'Optional. Spaces provided on site, to calculate the shortfall.'},
    },
    required=['development_type'],
)
def get_parking_rates(arguments: dict):
    requested = arguments.get("development_type", "")
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

        # Turn the rate into a number where the inputs allow it, so a shortfall
        # gets stated rather than left as an exercise for the reader.
        estimate = estimate_spaces(
            result,
            arguments.get("floor_area_sqm") or None,
            {
                "employees": arguments.get("num_employees") or 0,
                "seats": arguments.get("seats") or 0,
            },
        )
        if estimate:
            provided = arguments.get("spaces_provided")
            estimate["spaces_provided"] = provided
            if provided is not None:
                shortfall = max(0, estimate["spaces_required"] - provided)
                estimate["shortfall"] = shortfall
                estimate["advice"] = (
                    f"A shortfall of {shortfall} space(s) must be justified in the SEE — "
                    "on-street or public parking nearby is an argument for a variation, not evidence of compliance."
                    if shortfall else "The rate is met by the spaces provided."
                )
            response["calculation"] = estimate
        elif result.get("spec") is None:
            response["no_calculation"] = (
                "This rate cannot be turned into a number from the inputs given — read "
                "rate_description and what_to_check. Guessing a space count here is worse "
                "than not giving one."
            )

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
