"""Commercial design controls (DCP Chapter 2)."""

import json

from mcp.types import TextContent

from lismore_da_mcp import commercial
from lismore_da_mcp.data.commercial import PART_A
from lismore_da_mcp.registry import tool
from lismore_da_mcp.vocabulary import unresolved_error


def _reply(payload: dict):
    return [TextContent(type="text", text=json.dumps(payload, indent=2))]


@tool(
    name='get_commercial_requirements',
    description=(
        "Design controls for commercial buildings from Lismore DCP Chapter 2: weather protection "
        "and awnings, shopfronts, heritage, signage, the 14m blank wall rule and the site analysis "
        "in the Lismore CBD (Part A, Map 1), and the Performance Criteria table for Brewster "
        "Street in the Health Precinct (Part B, Map 2). Pass `precinct` if known — it cannot be "
        "worked out from an address or a zone, and without it both parts are returned. Pass "
        "`work_type`: the chapter is written for new and renovating buildings and never mentions "
        "a change of use, so a change of use with no external work is answered with that scope "
        "rather than a list of design rules."
    ),
    properties={
        'precinct': {
            'type': 'string',
            'description': (
                "Optional, and never guessed if omitted: 'cbd' (Chapter 2 Map 1), "
                "'brewster_street' (Map 2, the Health Precinct) or 'neither'. From the maps in "
                "the chapter or the Duty Planner. Chapter 2's Map 1 is not the Chapter 7 CBD "
                "parking boundary."
            ),
        },
        'work_type': {
            'type': 'string',
            'description': (
                "Optional: 'new_building', 'alterations_or_additions' (a new shopfront, awning, "
                "facade or extension counts) or 'change_of_use_only' (no external work)."
            ),
        },
        'topic': {
            'type': 'string',
            'description': (
                "Optional: narrow Part A to one topic — e.g. 'awnings', 'shopfront', 'heritage', "
                "'signage', 'colour', 'windows', 'disabled access', 'height', 'setback'."
            ),
        },
        'is_heritage': {
            'type': 'boolean',
            'description': "Optional: the site is a heritage item, or in or near a conservation "
                           "area. lookup_site_constraints reads the mapped heritage layer.",
        },
        'is_corner': {
            'type': 'boolean',
            'description': "Optional: the site is a corner allotment.",
        },
        'external_wall_length_m': {
            'type': 'number',
            'minimum': 0,
            'description': "Optional, CBD: the longest straight run of external wall, checked "
                           "against the 14m figure.",
        },
        'levels': {
            'type': 'integer',
            'minimum': 1,
            'description': "Optional, Brewster Street: number of levels. At 3 or more the taller "
                           "building rows of Table B1 apply.",
        },
        'site_area_m2': {
            'type': 'number',
            'minimum': 0,
            'description': "Optional, Brewster Street: site area, checked against the 1200m² "
                           "Acceptable Solution for taller buildings.",
        },
        'building_height_m': {
            'type': 'number',
            'minimum': 0,
            'description': "Optional, Brewster Street: building height, for the A10 separation "
                           "table beside the R2 zone.",
        },
        'adjoins_r2_zone': {
            'type': 'boolean',
            'description': "Optional, Brewster Street: the site adjoins the R2 Low Density "
                           "Residential zone.",
        },
    },
)
def get_commercial_requirements(arguments: dict):
    precinct = work_type = topic = None

    if arguments.get("precinct"):
        found = commercial.resolve_precinct(arguments["precinct"])
        if not found:
            error = unresolved_error(arguments["precinct"], found, "precinct",
                                     commercial.PRECINCT_KEYS)
            error["how_to_find_it"] = (
                "Chapter 2 applies on its Map 1 (the Lismore CBD) and Map 2 (Brewster Street). "
                "Neither can be read from an address. Omit precinct to get both parts."
            )
            return _reply(error)
        precinct = found.key

    if arguments.get("work_type"):
        found = commercial.resolve_work_type(arguments["work_type"])
        if not found:
            return _reply(unresolved_error(arguments["work_type"], found, "work type",
                                           commercial.WORK_TYPES))
        work_type = found.key

    if arguments.get("topic"):
        found = commercial.resolve_topic(arguments["topic"])
        if not found:
            return _reply(unresolved_error(arguments["topic"], found, "topic", PART_A))
        topic = found.key

    response = commercial.requirements(
        precinct, work_type, topic,
        is_heritage=arguments.get("is_heritage"),
        is_corner=arguments.get("is_corner"),
        external_wall_length_m=arguments.get("external_wall_length_m"),
        levels=arguments.get("levels"),
        site_area_m2=arguments.get("site_area_m2"),
        building_height_m=arguments.get("building_height_m"),
        adjoins_r2_zone=arguments.get("adjoins_r2_zone"),
    )
    return _reply(response)
