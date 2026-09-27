"""Heritage requirements (DCP Chapter 12 and LEP 2012 cl 5.10)."""

import json

from mcp.types import TextContent

from lismore_da_mcp import heritage
from lismore_da_mcp.data.heritage import CONSERVATION_AREAS
from lismore_da_mcp.registry import tool
from lismore_da_mcp.vocabulary import unresolved_error


@tool(
    name='get_heritage_requirements',
    description=(
        "What DCP Chapter 12 and LEP 2012 cl 5.10 ask of a proposal on or near heritage land: "
        "whether the work needs consent under cl 5.10, the Chapter 12 design guidelines for "
        "the work described (signage, shopfront, repaint, roof, extension, fences…), the "
        "precinct policies of the conservation area, what Council may ask for, and the cl "
        "5.10(10) pathway for a use the zone prohibits. Heritage status is never guessed: "
        "pass `heritage_status` if you know it, or get every case side by side. "
        "lookup_site_constraints can confirm a listing but cannot clear one; `address` checks "
        "LEP Schedule 5 offline for a listing at or near it."
    ),
    properties={
        'heritage_status': {
            'type': 'string',
            'description': (
                "Optional, and never guessed if omitted: 'heritage_item', 'conservation_area', "
                "'item_in_conservation_area', 'vicinity' (near a listed item or area) or "
                "'none_known'. From a s10.7 planning certificate, the LEP Heritage Map, or "
                "lookup_site_constraints when it reports the site as affected."
            ),
        },
        'conservation_area': {
            'type': 'string',
            'description': (
                "Optional. Which heritage conservation area, for its precinct policies: "
                "'Dalley Street', 'Eltham', 'Girards Hill', 'St Andrew's', 'Spinks Park/Civic "
                "Precinct', 'St Carthage's' or 'Nimbin'. Naming one states that the site is "
                "within it."
            ),
        },
        'works': {
            'type': 'array',
            'items': {'type': 'string'},
            'description': (
                "Optional. What is being done, in your own words — 'new shopfront sign', "
                "'repaint facade', 'replace windows', 'rear extension', 'front fence', "
                "'internal fitout'. Selects the Chapter 12 guidelines; omit for all of them."
            ),
        },
        'is_change_of_use': {
            'type': 'boolean',
            'description': (
                "True if an existing building is changing use. cl 5.10(2) lists works rather "
                "than uses, and cl 5.10(10) can allow a prohibited use in a heritage item."
            ),
        },
        'address': {
            'type': 'string',
            'description': (
                "Optional, e.g. '180 Molesworth Street, Lismore'. Searched offline against LEP "
                "Schedule 5 for a listing at that address or on the same street. A match is "
                "evidence; no match clears nothing, and the status is still yours to supply."
            ),
        },
    },
)
def get_heritage_requirements(arguments: dict):
    status_arg = arguments.get("heritage_status")
    area_arg = arguments.get("conservation_area")

    status = None
    if status_arg:
        resolved = heritage.resolve_status(status_arg)
        if not resolved:
            error = unresolved_error(status_arg, resolved, "heritage status", heritage.STATUSES)
            error["if_you_do_not_know"] = (
                "Omit heritage_status and every case comes back side by side. "
                + heritage.STATE_LAYER_CONFIRMS_BUT_CANNOT_CLEAR["how_to_settle_it"]
            )
            return [TextContent(type="text", text=json.dumps(error, indent=2))]
        status = resolved.key

    area_key = None
    if area_arg:
        area = heritage.resolve_conservation_area(area_arg)
        if not area:
            error = unresolved_error(area_arg, area, "conservation area", CONSERVATION_AREAS)
            error["note"] = (
                "Lismore LEP 2012 Schedule 5 Part 2 lists seven heritage conservation areas. A "
                "site outside all seven may still be a heritage item or near one."
            )
            return [TextContent(type="text", text=json.dumps(error, indent=2))]
        area_key = area.key

    # A named conservation area is the caller stating the site is in one; it is
    # not an inference. But it cannot contradict a stated status.
    if area_key:
        if status is None:
            status = "conservation_area"
        elif status == "heritage_item":
            status = "item_in_conservation_area"
        elif status in ("vicinity", "none_known"):
            return [TextContent(type="text", text=json.dumps({
                "error": f"heritage_status '{status_arg}' says the site is not in a conservation "
                         f"area, but conservation_area names "
                         f"{CONSERVATION_AREAS[area_key]['lep_name']}.",
                "note": "Supply one or the other. If the site is near the area rather than in "
                        "it, use heritage_status 'vicinity' without conservation_area.",
            }, indent=2))]

    response = heritage.requirements(
        status, area_key,
        works=arguments.get("works") or [],
        is_change_of_use=bool(arguments.get("is_change_of_use", False)),
    )
    if status_arg:
        response["heritage_status_asked_for"] = status_arg
    if area_arg:
        response["conservation_area_asked_for"] = area_arg
    if arguments.get("address"):
        response["schedule_5_cross_check"] = heritage.schedule_5_cross_check(arguments["address"])
    return [TextContent(type="text", text=json.dumps(response, indent=2))]
