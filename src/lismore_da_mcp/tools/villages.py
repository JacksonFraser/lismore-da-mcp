"""The villages: DCP Part B Chapter 6, Nimbin Village."""

import json

from mcp.types import TextContent

from lismore_da_mcp import villages
from lismore_da_mcp.data.nimbin import FLOOD, PRECINCTS
from lismore_da_mcp.registry import tool
from lismore_da_mcp.vocabulary import unresolved_error


@tool(
    name='get_village_requirements',
    description=(
        "Controls for a site in a village (zone RU5). Only Nimbin has a DCP chapter of its "
        "own — Part B Chapter 6, which sets precincts, the uses preferred in each, heritage "
        "controls for Cullen Street and the historic housing, rainwater storage where there is "
        "no reticulated water, and its own flood hazard controls. Pass `village`: RU5 covers "
        "other villages, and for those the tool says what applies instead. The precinct, the "
        "heritage conservation area and the flood hazard are drawn on maps no address can "
        "read, so pass each if known; without one, every option is returned rather than one "
        "guessed. 'Preferred' is not 'permissible' — check_permissibility still decides that."
    ),
    properties={
        'village': {
            'type': 'string',
            'description': (
                "The village the site is in, e.g. 'Nimbin', 'Dunoon', 'Clunes'. Never inferred "
                "from the zone."
            ),
        },
        'precinct': {
            'type': 'string',
            'description': (
                "Optional, Nimbin only, from Figure 2 of the chapter: 'commercial' (Cullen "
                "Street), 'live_work', 'light_industry', 'community', "
                "'residential_character' (the historic housing), "
                "'residential_south_of_sibley' or 'investigation_area' (south of Cecil Street)."
            ),
        },
        'in_heritage_conservation_area': {
            'type': 'boolean',
            'description': (
                "Optional: whether the site is inside the Nimbin Heritage Conservation Area "
                "(Figure 3). Most of the Commercial Precinct and the historic housing is."
            ),
        },
        'flood_hazard': {
            'type': 'string',
            'description': (
                "Optional, from Figure 5: 'extreme', 'high', 'medium' or 'low'."
            ),
        },
        'zone': {
            'type': 'string',
            'description': "Optional LEP zone code. The chapter applies only to land zoned RU5.",
        },
    },
)
def get_village_requirements(arguments: dict):
    precinct_key = hazard_key = None

    if arguments.get("precinct"):
        found = villages.resolve_precinct(arguments["precinct"])
        if not found:
            return _reply(unresolved_error(arguments["precinct"], found, "precinct", PRECINCTS))
        precinct_key = found.key

    if arguments.get("flood_hazard"):
        categories = FLOOD["hazard_categories"]
        found = villages.resolve_flood_hazard(arguments["flood_hazard"])
        if not found:
            return _reply(unresolved_error(arguments["flood_hazard"], found, "flood hazard",
                                           categories))
        hazard_key = found.key

    return _reply(villages.requirements(
        village=arguments.get("village"),
        precinct_key=precinct_key,
        in_hca=arguments.get("in_heritage_conservation_area"),
        hazard_key=hazard_key,
        zone=arguments.get("zone"),
    ))


def _reply(payload: dict):
    return [TextContent(type="text", text=json.dumps(payload, indent=2, ensure_ascii=False))]
