"""Waste management requirements (DCP Chapter 15)."""

import json

from mcp.types import TextContent

from lismore_da_mcp import waste
from lismore_da_mcp.data.waste import GENERATION_RATES
from lismore_da_mcp.registry import tool
from lismore_da_mcp.vocabulary import unresolved_error


def _reply(payload: dict):
    return [TextContent(type="text", text=json.dumps(payload, indent=2))]


@tool(
    name='get_waste_requirements',
    description=(
        "What DCP Chapter 15 requires for waste: the Site Waste Minimisation and Management Plan "
        "(SWMMP) that goes in the Statement of Environmental Effects, what it must cover, the "
        "bin storage and collection controls for the development type, and — for a food "
        "business — the rule that 240 litres a week of food waste means twice-weekly collection "
        "or refrigerated storage. The chapter applies to a change of use as well as to building "
        "work. Give premises_type and floor_area_m2 for Appendix C's estimate of how much waste "
        "the premises will produce. Grease and liquid trade waste are outside the chapter."
    ),
    properties={
        'development_type': {
            'type': 'string',
            'description': (
                "What is proposed: 'commercial' (shops, cafés, offices, salons, pubs), "
                "'industrial', 'mixed_use' (incl. shop top housing), 'multi_dwelling' or "
                "'dwellings'. Plain words like 'cafe' or 'warehouse' resolve."
            ),
        },
        'premises_type': {
            'type': 'string',
            'description': (
                "Optional: the Appendix C premises type for a waste estimate — e.g. 'cafe', "
                "'takeaway', 'butcher', 'green grocer', 'supermarket', 'hairdresser', 'office', "
                "'shop', 'showroom', 'pub'. Taken from development_type if that names one."
            ),
        },
        'floor_area_m2': {
            'type': 'number', 'minimum': 0,
            'description': "Optional: floor area, for Appendix C's floor-area rates (and to choose "
                           "between the two shop rows, split at 100m²).",
        },
        'days_open_per_week': {
            'type': 'integer', 'minimum': 1, 'maximum': 7,
            'description': "Optional: trading days per week, to turn the daily rate into the "
                           "weekly figure the SWMMP template asks for.",
        },
        'collections_per_week': {
            'type': 'integer', 'minimum': 1, 'maximum': 14,
            'description': "Optional: planned collections per week, to size bin storage for what "
                           "accumulates between collections.",
        },
        'is_change_of_use': {
            'type': 'boolean',
            'description': "Optional: an existing building changing use. Chapter 15 still applies "
                           "(§1.3).",
        },
        'involves_building_work': {
            'type': 'boolean',
            'description': "Optional: any building work, including a fitout (brings in §3.3). "
                           "Omit if unsure — it is then included.",
        },
        'involves_demolition': {
            'type': 'boolean',
            'description': "Optional: any demolition (brings in §3.2).",
        },
    },
    required=['development_type'],
)
def get_waste_requirements(arguments: dict):
    requested = arguments["development_type"]
    found = waste.resolve_development_type(requested)
    if not found:
        error = unresolved_error(requested, found, "development type", waste.DEVELOPMENT_TYPES)
        error["note"] = ("Chapter 15 has sections for dwellings (4.1), multi dwelling housing "
                         "(4.2), commercial and retail (4.3), mixed use (4.4) and industrial "
                         "(4.5). A café, shop, office or salon is commercial.")
        return _reply(error)

    area = arguments.get("floor_area_m2")
    premises = None
    premises_arg = arguments.get("premises_type")
    if premises_arg:
        premises = waste.resolve_premises(premises_arg, area)
        if premises is None:
            error = unresolved_error(premises_arg, waste.resolve(premises_arg, GENERATION_RATES),
                                     "premises type", GENERATION_RATES)
            error["note"] = ("Appendix C has rates for these premises types only. For anything "
                             "else the SWMMP estimates the volumes itself (§2.3).")
            return _reply(error)
    else:
        premises = waste.resolve_premises(requested, area)

    response = waste.requirements(
        found.key, premises,
        floor_area_m2=area,
        days_open_per_week=arguments.get("days_open_per_week"),
        collections_per_week=arguments.get("collections_per_week"),
        is_change_of_use=arguments.get("is_change_of_use"),
        involves_building_work=arguments.get("involves_building_work"),
        involves_demolition=arguments.get("involves_demolition"),
    )
    if found.how != "exact":
        response["interpreted_as"] = (f"Read '{requested}' as {found.key} (DCP Chapter 15 "
                                      f"§{waste.SECTIONS[found.key]['section']}).")
    return _reply(response)
