"""Zone lookups, permissibility and land use definitions."""

import json

from mcp.types import TextContent

from lismore_da_mcp.addresses import lookup_constraints
from lismore_da_mcp.addresses import lookup_zone
from lismore_da_mcp.data.definitions import LAND_USE_DEFINITIONS
from lismore_da_mcp.data.zones import ZONES
from lismore_da_mcp.landuse import NOT_A_LAND_USE
from lismore_da_mcp.landuse import canonical_use
from lismore_da_mcp.landuse import classify_land_use
from lismore_da_mcp.registry import tool
from lismore_da_mcp.vocabulary import DEFINITION_SYNONYMS
from lismore_da_mcp.vocabulary import resolve
from lismore_da_mcp.vocabulary import unresolved_error


@tool(
    name='get_zone_info',
    description='Get information about a zoning classification in Lismore LEP 2012, including objectives, permitted uses, and development standards.',
    properties={
        'zone_code': {'type': 'string', 'description': "Zone code under Lismore LEP 2012, e.g. 'R2', 'E2', 'MU1', 'RU5'. The B and IN series were retired in 2023 — they still resolve, but they redirect."},
    },
    required=['zone_code'],
)
def get_zone_info(arguments: dict):
    zone_code = arguments.get("zone_code", "").upper()
    if zone_code in ZONES:
        return [TextContent(
            type="text",
            text=json.dumps({
                "zone_code": zone_code,
                **ZONES[zone_code],
                "source": "Lismore LEP 2012"
            }, indent=2)
        )]
    else:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Zone '{zone_code}' not found",
                # Current zones only. Offering the six retired B/IN entries here
                # invited the caller to pick one — they exist to redirect a code
                # someone already has, not to be chosen from a menu.
                "available_zones": [k for k in ZONES if "redirect_to" not in ZONES[k]]
            }, indent=2)
        )]


@tool(
    name='lookup_zone_by_address',
    description=(
        'Find the LEP zone that applies to a street address. Use this first when the applicant '
        'knows their address but not their zone code — several tools require zone_code and this '
        'is the only thing that derives it. Needs a street number and a suburb or postcode. '
        'Live lookup against NSW Government mapping; if it is unavailable the tool says so '
        'rather than guessing.'
    ),
    properties={
        'address': {'type': 'string', 'description': "Street address, e.g. '12 Keen Street, Lismore' or '43 Oliver Avenue Goonellabah 2480'"},
    },
    required=['address'],
)
def lookup_zone_by_address(arguments: dict):
    result = lookup_zone(arguments["address"].strip())

    # The state map can carry a code this server holds no land use table for —
    # a deferred area, or a zone Lismore's LEP does not use. Saying so here is
    # better than the caller passing it to check_permissibility and getting a
    # bare "zone not found" with no explanation of where the code came from.
    unknown = [
        z["zone_code"] for z in result.get("zones", [])
        if z["zone_code"] not in ZONES
    ]
    if unknown:
        result["zones_not_held_by_this_server"] = unknown
        result["note"] = (
            f"The zoning map returned {', '.join(unknown)}, which has no land use table in "
            "this server's copy of Lismore LEP 2012. The zone is real — confirm the "
            "applicable controls with the Duty Planner."
        )

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@tool(
    name='lookup_site_constraints',
    description=(
        'Check what constrains a property, by address: maximum building height, minimum lot size, '
        'heritage listing, bushfire prone land and flood mapping. Use this instead of asking the '
        'applicant whether their site is heritage or bushfire affected — they usually do not know. '
        'Note that the state flood layer holds no Lismore data, so this cannot rule flooding out; '
        'it says so in the result.'
    ),
    properties={
        'address': {'type': 'string', 'description': "Street address, e.g. '12 Keen Street, Lismore'"},
    },
    required=['address'],
)
def lookup_site_constraints(arguments: dict):
    result = lookup_constraints(arguments["address"].strip())
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@tool(
    name='list_zones',
    description='List all zone codes available in Lismore LEP 2012.',
    properties={},
)
def list_zones(arguments: dict):
    active_zones = {code: info["name"] for code, info in ZONES.items() if "redirect_to" not in info}
    return [TextContent(
        type="text",
        text=json.dumps({
            "zones": active_zones,
            "categories": {
                "residential": ["R1", "R2", "R3", "R5"],
                "employment": ["E1", "E2", "E3", "E4"],
                "mixed_use": ["MU1"],
                "rural": ["RU5"],
                "special_purpose": ["SP2"],
                "recreation": ["RE1", "RE2"],
                "conservation": ["C1", "C2", "C3"],
                "waterways": ["W1"],
                "legacy_codes": ["B1", "B2", "B3", "B4", "IN1", "IN2"]
            },
            "note": "Zone codes changed in April 2022 under Standard Instrument amendments. Legacy B/IN codes redirect to new E/MU zones."
        }, indent=2)
    )]


@tool(
    name='check_permissibility',
    description='Check if a specific land use is permitted in a specific zone. Returns whether the use is permitted without consent, permitted with consent, prohibited, or not found. Essential first step for any DA - confirms the proposal is actually permissible.',
    properties={
        'land_use': {'type': 'string', 'description': "The proposed land use (e.g., 'restaurant or cafe', 'dwelling house', 'warehouse', 'shop top housing')"},
        'zone_code': {'type': 'string', 'description': "Zone code (e.g., 'R1', 'E2', 'MU1')"},
    },
    required=['land_use', 'zone_code'],
)
def check_permissibility(arguments: dict):
    land_use = arguments["land_use"].strip()
    zone_code = arguments["zone_code"].upper().strip()

    if canonical_use(land_use) in {canonical_use(term) for term in NOT_A_LAND_USE}:
        return [TextContent(type="text", text=json.dumps({
            "error": f"{land_use!r} describes the work, not a land use.",
            "why": (
                "The LEP land use table answers one question: may this *use* operate on this "
                "land. It says nothing about whether the work is a new building, a fit-out or "
                "a change of use. Asked this way it falls through to the table's catch-all and "
                "would report 'likely permitted with consent' — a confident answer to a "
                "question you did not ask."
            ),
            "ask_instead": (
                "Check the use you want to operate. For a café in a vacant shop, ask about "
                "'restaurant or cafe' — not 'change of use'."
            ),
            "for_a_change_of_use_also_check": [
                "Whether consent is needed at all. Some changes of use between similar "
                "commercial uses are exempt or complying development under the Codes SEPP. "
                "This tool reads the LEP land use table only and cannot tell you — put it to "
                "Council's free Duty Planner before you pay a lodgement fee.",
                "Existing use rights, if the current lawful use is no longer permissible in "
                "the zone — these can allow it to continue or change. Also a Duty Planner "
                "question; it turns on the history of the site, which nothing here knows.",
                "Contamination. Moving to a more sensitive use — a workshop becoming a café "
                "or a child care centre — can require a Preliminary Site Investigation even "
                "with no building work.",
                "Parking. The requirement is assessed against the new use; get_parking_rates "
                "gives the rate and any shortfall, and any credit for the previous use is "
                "argued in the SEE.",
                "get_da_checklist with 'change of use' lists the documents.",
            ],
            "zone_code": zone_code,
        }, indent=2))]

    redirect_note = None
    if zone_code in ZONES and "redirect_to" in ZONES[zone_code]:
        new_zone = ZONES[zone_code]["redirect_to"]
        redirect_note = f"Zone {zone_code} has been replaced by {new_zone}. Checked against {new_zone}."
        zone_code = new_zone

    if zone_code not in ZONES:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"Zone \'{zone_code}\' not found",
                "available_zones": [k for k in ZONES if "redirect_to" not in ZONES[k]]
            }, indent=2)
        )]

    zone = ZONES[zone_code]
    classification = classify_land_use(land_use, zone, zone_code)

    # Map the classification onto the verdicts this tool has always returned.
    verdicts = {
        ("exact", True): "permitted",
        ("hierarchy", True): "permitted_with_consent",
        ("exact", False): "prohibited",
        ("hierarchy", False): "prohibited",
    }
    permissibility = "unknown"
    if classification["match_type"] == "catchall":
        permissibility = "likely_permitted_with_consent" if classification["permissible"] is None else "likely_prohibited"
    elif classification["match_type"] == "approximate":
        permissibility = "likely_prohibited" if classification["category"] == "prohibited" else "uncertain"
    elif classification["matched_use"]:
        in_without = any(
            canonical_use(u) == canonical_use(classification["matched_use"])
            for u in zone.get("permitted_without_consent", [])
        )
        if classification["permissible"] is False:
            permissibility = "prohibited"
        else:
            permissibility = "permitted_without_consent" if in_without else "permitted_with_consent"
    elif classification["match_type"] == "none":
        permissibility = "not_found"

    result = {
        "land_use": land_use,
        "zone_code": zone_code,
        "zone_name": zone["name"],
        "permissibility": permissibility,
        "detail": classification["statement"],
        "matched_use": classification["matched_use"],
        "match_type": classification["match_type"],
    }
    if redirect_note:
        result["redirect_note"] = redirect_note
    if permissibility == "permitted_with_consent":
        result["next_steps"] = "A Development Application is required for this use."
    elif permissibility == "prohibited":
        result["advice"] = "This use cannot be approved in this zone. Consider an alternative zone or use."
    elif permissibility in ("uncertain", "not_found", "likely_permitted_with_consent", "likely_prohibited"):
        result["advice"] = "Confirm the exact land use term with the Council Duty Planner before relying on this."
        all_uses = zone.get("permitted_without_consent", []) + zone.get("permitted_with_consent", [])
        words = [w for w in canonical_use(land_use).split() if len(w) > 3]
        similar = [u for u in all_uses if any(w in canonical_use(u) for w in words)]
        if similar:
            result["similar_uses"] = similar[:5]

    # This tool reads the LEP land use table and nothing else. A State
    # Environmental Planning Policy can permit a use the table omits, and
    # prevails over the LEP where they conflict — most commonly for secondary
    # dwellings ("granny flats"), which are absent from several Lismore
    # residential tables but are generally permissible with consent under the
    # Housing SEPP. Without this note, a catch-all miss reads as a settled "no".
    if permissibility in ("likely_prohibited", "prohibited", "not_found"):
        result["scope_of_this_answer"] = (
            "Based on the Lismore LEP 2012 land use table only. State Environmental "
            "Planning Policies (Housing, Exempt and Complying Development Codes, "
            "Transport and Infrastructure, Primary Production) can independently permit "
            "a use that the LEP table does not list, and prevail over the LEP where they "
            "conflict. A use shown here as prohibited may still have a SEPP pathway — "
            "secondary dwellings are the common example. Check with the Duty Planner "
            "before treating this as a refusal."
        )

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@tool(
    name='get_definition',
    description="Get the Standard Instrument LEP definition of a land-use term (e.g. 'retail premises' vs 'food and drink premises' vs 'shop'), including related terms. Use this to work out which defined use a proposal actually falls under before checking zone permissibility.",
    properties={
        'term': {'type': 'string', 'description': "Land-use term to look up (e.g. 'retail premises', 'food and drink premises', 'shop', 'home business')"},
    },
    required=['term'],
)
def get_definition(arguments: dict):
    raw_term = arguments.get("term", "")
    match = resolve(raw_term, LAND_USE_DEFINITIONS, DEFINITION_SYNONYMS)

    if match:
        entry = LAND_USE_DEFINITIONS[match.key]
        result = {
            **entry,
            "source": "Standard Instrument (Local Environmental Plans) Order 2006 — Dictionary, as carried into Lismore LEP 2012",
            "caveat": "Paraphrased for readability. Definitions can be amended — verify against the current Lismore LEP 2012 Dictionary before relying on this for a formal submission."
        }
        if match.how != "exact":
            # The planning term is often not the word the applicant used, and
            # which term applies decides permissibility — so name the swap.
            result["interpreted_as"] = (
                f"'{raw_term}' is not itself a defined term; answered with "
                f"'{entry['term']}', the Standard Instrument term it usually corresponds to. "
                "Use that term in a DA, and confirm it fits your proposal."
            )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    error = unresolved_error(raw_term, match, "definition", LAND_USE_DEFINITIONS)
    error["note"] = (
        "Only terms with a Standard Instrument definition are listed. Everyday words for "
        "building elements (deck, shed, fence) are not separately defined — they are "
        "assessed as part of the development they belong to."
    )
    return [TextContent(type="text", text=json.dumps(error, indent=2))]


@tool(
    name='list_definitions',
    description='List all available land-use definitions in the system. Use this to see what terms have definitions available before calling get_definition.',
    properties={},
)
def list_definitions(arguments: dict):
    definitions_list = [
        {"key": k, "term": v["term"]}
        for k, v in LAND_USE_DEFINITIONS.items()
    ]
    categories = {
        "retail_commercial": ["retail_premises", "food_and_drink_premises", "shop", "restaurant_or_cafe", "take_away_food_and_drink_premises", "business_premises", "commercial_premises", "neighbourhood_shop"],
        "home_based": ["home_business", "home_occupation"],
        "residential": ["dwelling_house", "dual_occupancy", "secondary_dwelling", "multi_dwelling_housing", "residential_flat_building", "attached_dwellings", "shop_top_housing", "boarding_house"],
        "industrial": ["light_industries", "general_industries", "warehouse_or_distribution_centre", "vehicle_repair_station"],
        "community_recreation": ["recreation_facility_indoor", "community_facility", "centre_based_child_care_facility"],
        "accommodation": ["hotel_or_motel_accommodation", "bed_and_breakfast_accommodation"],
    }
    return [TextContent(
        type="text",
        text=json.dumps({
            "available_definitions": definitions_list,
            "categories": categories,
            "total_count": len(definitions_list),
            "usage": "Use get_definition with any term key to get the full definition"
        }, indent=2)
    )]
