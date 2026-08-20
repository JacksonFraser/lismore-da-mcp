"""Signage requirements (DCP Chapter 9)."""

import json

from mcp.types import TextContent

from lismore_da_mcp.data.signage import APPLICATION_REQUIREMENTS
from lismore_da_mcp.data.signage import EXISTING_USE_RIGHTS
from lismore_da_mcp.data.signage import SEPP_CURRENCY_WARNING
from lismore_da_mcp.data.signage import SIGNAGE
from lismore_da_mcp.registry import tool
from lismore_da_mcp.signage import is_on_road_reserve
from lismore_da_mcp.signage import pathway
from lismore_da_mcp.signage import relevant_guidelines
from lismore_da_mcp.signage import size_check
from lismore_da_mcp.signage import zone_restriction
from lismore_da_mcp.vocabulary import SIGNAGE_SYNONYMS
from lismore_da_mcp.vocabulary import resolve
from lismore_da_mcp.vocabulary import unresolved_error


@tool(
    name='get_signage_requirements',
    description="Signage requirements for a business in Lismore (DCP Chapter 9). Answers first whether the sign needs an application at all — most shopfront signage is Exempt Development and needs neither a DA nor a CDC — then whether it is prohibited on the site, then the size standard. Supply zone_code and is_heritage for a site-specific answer: signage on a heritage item or in a conservation area is a common refusal point in the CBD.",
    properties={
        'sign_type': {'type': 'string', 'description': "Type of sign. Plain wording works — 'A-frame', 'sandwich board', 'shopfront sign', 'menu board', 'pylon' all resolve. Use list_signage_types to see the full set."},
        'zone_code': {'type': 'string', 'description': "Optional. Zone of the site, e.g. 'E2', 'R1', 'MU1'. Used to test the clause 9.2 prohibition, which applies in residential, open space, waterway and conservation areas."},
        'is_heritage': {'type': 'boolean', 'description': 'Optional. Whether the site is a heritage item or within a heritage conservation area. A heritage area is a prohibited area for advertising regardless of zone, so this is worth establishing — lookup_site_constraints reads it from the NSW heritage layer by address.'},
        'area_sqm': {'type': 'number', 'description': 'Optional. Area of the proposed sign in square metres, to check it against the DCP standard.', 'minimum': 0},
        'height_m': {'type': 'number', 'description': 'Optional. Height of the proposed sign in metres, for pylon and directory board signs.', 'minimum': 0},
    },
    required=['sign_type'],
)
def get_signage_requirements(arguments: dict):
    requested = arguments.get("sign_type", "")
    match = resolve(requested, SIGNAGE, SIGNAGE_SYNONYMS)
    if not match:
        error = unresolved_error(requested, match, "sign type", SIGNAGE)
        error["note"] = (
            "Chapter 9 names sign types by form rather than by trade, so an unlisted term "
            "usually falls under a broader one — a shopfront sign is generally a wall, window "
            "or fascia sign depending on where it is fixed. list_signage_types shows the set "
            "with what each covers."
        )
        return [TextContent(type="text", text=json.dumps(error, indent=2))]

    sign_type = match.key
    entry = SIGNAGE[sign_type]
    is_heritage = arguments.get("is_heritage")

    response = {
        "sign_type": sign_type,
        "dcp_name": entry["dcp_name"],
        "definition": entry["definition"],
        "source": entry["source"],
        # Pathway leads deliberately. Most businesses asking about a sign do not
        # need an application at all, and the size standard is the answer to a
        # question they only have if they do.
        "do_you_need_an_application": pathway(entry),
    }
    if match.how != "exact":
        response["interpreted_as"] = (
            f"Read '{requested}' as '{sign_type}'. If that is not the sign you meant, call "
            "again with a term from list_signage_types."
        )

    response["where_it_can_go"] = zone_restriction(
        sign_type, arguments.get("zone_code"), is_heritage)

    size = size_check(entry, arguments.get("area_sqm"), arguments.get("height_m"))
    if size:
        response["size"] = size
    else:
        # No numeric control for this sign type. Say that outright — including
        # when the caller supplied a measurement, which is precisely when
        # silence would read as a pass. An unstated limit is not an unlimited
        # one, and several of these sign types have only prose in §9.11.
        if entry.get("standard"):
            response["standard"] = entry["standard"]
        response["no_numeric_standard"] = (
            "Chapter 9 sets no size or height limit for this sign type, so it is assessed on "
            "merit against the §9.4 design guidelines rather than measured. An unstated limit "
            "is not an unlimited one."
            + (" A measurement was supplied and has not been assessed against anything."
               if arguments.get("area_sqm") or arguments.get("height_m") else "")
        )

    road_reserve = is_on_road_reserve(sign_type)
    if road_reserve:
        response["road_reserve"] = road_reserve

    response["design_guidelines"] = relevant_guidelines(sign_type, is_heritage)

    if entry.get("note"):
        response["what_to_watch"] = entry["note"]

    if entry["pathway"] in ("consent", "restricted"):
        response["if_you_lodge"] = APPLICATION_REQUIREMENTS

    response["existing_signage_on_the_premises"] = EXISTING_USE_RIGHTS
    response["check_the_sepp_reference"] = SEPP_CURRENCY_WARNING

    return [TextContent(type="text", text=json.dumps(response, indent=2))]


@tool(
    name='list_signage_types',
    description='List the sign types in Lismore DCP Chapter 9, grouped by what approval each needs.',
    properties={},
)
def list_signage_types(arguments: dict):
    grouped: dict[str, list] = {}
    for key, entry in SIGNAGE.items():
        grouped.setdefault(entry["pathway"], []).append({
            "sign_type": key,
            "dcp_name": entry["dcp_name"],
        })

    return [TextContent(type="text", text=json.dumps({
        "by_approval_pathway": {
            "exempt — no application needed if it meets the SEPP criteria":
                grouped.get("exempt", []),
            "complying — a CDC rather than a DA": grouped.get("complying", []),
            "consent — a DA, assessed on merit": grouped.get("consent", []),
            "generally not permissible — read the entry": grouped.get("restricted", []),
        },
        "start_here": "Most shopfront signage — wall, window, fascia, under-awning, top hamper "
                      "— is Exempt Development, so it needs no application at all provided it "
                      "meets the SEPP's criteria. Call get_signage_requirements with the sign "
                      "type, the zone and whether the site is heritage listed before assuming "
                      "a DA is needed.",
        "source": "Lismore DCP Chapter 9 - Signage",
    }, indent=2))]
