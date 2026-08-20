"""Flood, setbacks, residential standards, referrals, checklists and contacts."""

import json

from mcp.types import TextContent

from lismore_da_mcp.data.checklists import (
    CONDITIONAL_DOCUMENTS,
    DA_CHECKLISTS,
    UNIVERSAL_DOCUMENTS,
)
from lismore_da_mcp import flood
from lismore_da_mcp.data.contacts import CONTACT_INFO
from lismore_da_mcp.data.flood import FLOOD_AREAS
from lismore_da_mcp.data.referrals import CHARACTERISTIC_TRIGGERS
from lismore_da_mcp.data.referrals import REFERRAL_REQUIREMENTS
from lismore_da_mcp import standards
from lismore_da_mcp.registry import tool
from lismore_da_mcp.vocabulary import CHECKLIST_SYNONYMS
from lismore_da_mcp.vocabulary import resolve
from lismore_da_mcp.vocabulary import unresolved_error


@tool(
    name='get_flood_requirements',
    description=(
        "Flood controls from DCP Chapter 8 and LEP 2012 cl 5.21. The controls differ by flood "
        "hazard area — Floodway, High Flood Risk, Flood Fringe (which includes the CBD Flood "
        "Liable area), Low Flood Risk, and rural land — so pass `flood_area` if you know it. "
        "It cannot be worked out from an address or a zone. Pass `is_change_of_use` for a "
        "business taking over existing premises: §8.3 lifts the commercial and industrial "
        "controls entirely in that case."
    ),
    properties={
        'development_type': {
            'type': 'string',
            'description': (
                "What is being built or done: 'residential', 'commercial' or 'industrial'. "
                "Business uses (cafe, shop, office, gym) all resolve to commercial — Chapter 8 "
                "has no finer categories."
            ),
        },
        'flood_area': {
            'type': 'string',
            'description': (
                "Optional, and never guessed if omitted: 'floodway', 'high_flood_risk', "
                "'flood_fringe', 'cbd_flood_liable', 'low_flood_risk' or 'rural'. From Council's "
                "Map 1, a s10.7 certificate, or the Duty Planner."
            ),
        },
        'is_change_of_use': {
            'type': 'boolean',
            'description': (
                "True if an existing building is changing use rather than new development being "
                "built. Changes which controls apply — see DCP §8.3."
            ),
        },
    },
    required=['development_type'],
)
def get_flood_requirements(arguments: dict):
    dev_type = arguments.get("development_type", "")
    area_arg = arguments.get("flood_area")
    is_change_of_use = bool(arguments.get("is_change_of_use", False))

    resolved = flood.resolve_development_type(dev_type)
    if not resolved:
        return [TextContent(type="text", text=json.dumps(
            unresolved_error(dev_type, resolved, "development type",
                             flood.DEVELOPMENT_TYPES), indent=2))]

    area_key = None
    if area_arg:
        area = flood.resolve_flood_area(area_arg)
        if not area:
            error = unresolved_error(area_arg, area, "flood area", FLOOD_AREAS)
            error["how_to_find_it"] = flood.AREA_NOT_INFERABLE["how_to_settle"]
            return [TextContent(type="text", text=json.dumps(error, indent=2))]
        area_key = area.key

    response = flood.requirements(resolved.key, area_key, is_change_of_use)
    if area_arg:
        response["flood_area_asked_for"] = area_arg
        if flood.is_cbd_flood_liable(area_arg):
            response["cbd_flood_liable"] = (
                "The CBD Flood Liable area is its own category on Map 1, and DCP §8.3 gives it "
                "the same planning controls as the Flood Fringe Area. The controls below are "
                "the ones that apply to it."
            )

    return [TextContent(
        type="text",
        text=json.dumps(response, indent=2)
    )]


@tool(
    name='get_setback_requirements',
    description=(
        "Setback requirements for residential development from Lismore DCP Chapter 1. "
        "The front setback is set by zone — 6m in R1/R2/R3/RU5, 15m in RU1/R5/E3, 28m on an "
        "RMS road — so supply the zone. Chapter 1 sets no side or rear setback for an ordinary "
        "lot; those are answered by performance criteria, and this tool says so rather than "
        "inventing a figure."
    ),
    properties={
        'setback_type': {'type': 'string', 'description': "Type of setback: 'front', 'side', 'rear', or 'all'"},
        'zone': {'type': 'string', 'description': "The LEP zone code, which determines the front setback: R1, R2, R3, RU5, RU1, R5 or E3. lookup_zone_by_address derives it from an address."},
        'lot_configuration': {'type': 'string', 'description': "Optional: 'standard' or 'corner'. A corner allotment has a 3m secondary road setback."},
        'fronts_rms_road': {'type': 'boolean', 'description': "Optional, and only relevant in RU1, R5 and E3: whether the site fronts an RMS road, which raises the setback from 15m to 28m."},
        'storeys': {'type': 'integer', 'description': "Accepted but not used: Chapter 1 sets no setback by storey. Supply zone instead.", 'minimum': 1},
        'development_type': {'type': 'string', 'description': "Accepted but not used: superseded by zone and lot_configuration."},
    },
    required=['setback_type'],
)
def get_setback_requirements(arguments: dict):
    result = standards.setbacks(
        arguments.get("setback_type", "all"),
        arguments.get("zone"),
        arguments.get("lot_configuration"),
        arguments.get("fronts_rms_road"),
    )

    # The old schema asked for storeys and lot configuration and never for the
    # zone, so a caller carrying those arguments forward is asking a question
    # this chapter does not answer that way. Say it, rather than ignoring them.
    if arguments.get("storeys") is not None or arguments.get("development_type"):
        result["about_the_arguments_you_passed"] = (
            "storeys and development_type do not determine any setback in Chapter 1 — an earlier "
            "version of this tool said they did, using figures that are not in the chapter. The "
            "front setback comes from the zone; side and rear are performance-based."
        )

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@tool(
    name='get_residential_standards',
    description=(
        "Residential development standards from DCP Chapter 1 — open space and landscaping, "
        "density, privacy, earthworks, car parking, fences, service areas, solar access — plus "
        "the housing types with their own provisions (small lot housing, secondary dwellings, "
        "shop top housing, expanded dwellings) and the Lismore Health Precinct. Chapter 1 is "
        "written as Performance Criteria with Acceptable Solutions, so a figure is a "
        "deemed-to-comply safe harbour, not a limit."
    ),
    properties={
        'standard_type': {
            'type': 'string',
            'description': (
                "What to return: an element ('open_space_and_landscaping', 'density', "
                "'building_height', 'visual_privacy', 'acoustic_privacy', 'earthworks', "
                "'car_parking', 'fences', 'service_areas_and_waste', 'orientation_and_shade', "
                "'on_site_sewage', 'setbacks'), a housing type ('small_lot_housing', "
                "'secondary_dwelling', 'shop_top_housing', 'expanded_dwelling', "
                "'adaptable_housing', 'rural_dual_occupancy'), 'health_precinct', or 'all'. "
                "Plain words resolve — 'site coverage', 'privacy', 'granny flat', 'driveway'."
            ),
        },
    },
)
def get_residential_standards(arguments: dict):
    wanted = arguments.get("standard_type") or "all"

    if str(wanted).strip().lower() == "all":
        result = standards.everything()
        result["source"] = "Lismore DCP Chapter 1 - Residential Development"
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    resolved = standards.resolve_topic(wanted)
    if not resolved:
        error = unresolved_error(wanted, resolved, "standard type", standards.STANDARD_TOPICS)
        error["also_accepted"] = "all"
        return [TextContent(type="text", text=json.dumps(error, indent=2))]

    result = standards.topic(resolved.key)
    result["source"] = "Lismore DCP Chapter 1 - Residential Development"
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@tool(
    name='check_referrals',
    description='Check what external agency referrals (integrated development approvals) may be required for a development. Returns triggers and required documents for each potential referral authority.',
    properties={
        'development_characteristics': {'type': 'array', 'items': {'type': 'string'}, 'description': "List of development characteristics, e.g., ['bushfire_prone', 'near_waterway', 'heritage_item', 'significant_traffic', 'vegetation_clearing', 'industrial']"},
    },
    required=['development_characteristics'],
)
def check_referrals(arguments: dict):
    characteristics = arguments.get("development_characteristics", [])
    char_to_referral = CHARACTERISTIC_TRIGGERS

    triggered_referrals = {}
    unrecognised = []
    for char in characteristics:
        char_lower = char.lower().replace(" ", "_")
        matched = False
        for key, referral in char_to_referral.items():
            if key in char_lower:
                matched = True
                if referral not in triggered_referrals:
                    triggered_referrals[referral] = REFERRAL_REQUIREMENTS.get(referral, {})
        if not matched:
            unrecognised.append(char)

    response = {
        "triggered_referrals": triggered_referrals,
        "characteristics_checked": characteristics,
        "warning": "This is indicative only. Council will confirm all referral requirements at lodgement."
    }
    if not triggered_referrals:
        response["message"] = "No referrals triggered by the characteristics provided"
    # An unrecognised characteristic used to be dropped in silence, which read as
    # "no referral required" for a site that may well need one.
    if unrecognised:
        response["unrecognised_characteristics"] = unrecognised
        response["available_triggers"] = sorted(char_to_referral)
        response["note"] = (
            "The characteristics above were not recognised and have NOT been assessed. "
            "Re-send them using the available triggers, or treat them as unchecked."
        )

    return [TextContent(type="text", text=json.dumps(response, indent=2))]


@tool(
    name='get_da_checklist',
    description='Get the documents a Development Application must include, for a given kind of development. An incomplete lodgement is not assessed — the clock does not start — so this is the cheapest place for a business to avoid losing weeks.',
    properties={
        'development_type': {'type': 'string', 'description': "What you are doing — plain words are fine: 'change of use', 'cafe', 'fitout', 'shop', 'office', 'industrial', 'signage', 'subdivision', 'dwelling'."},
    },
    required=['development_type'],
)
def get_da_checklist(arguments: dict):
    requested = arguments.get("development_type", "")
    match = resolve(requested, DA_CHECKLISTS, CHECKLIST_SYNONYMS)

    if not match:
        # Say what is not known rather than returning the universal list, which
        # made 'nuclear reactor' and 'spaceship' look like recognised types with
        # a considered answer behind them.
        error = unresolved_error(requested, match, "checklist", DA_CHECKLISTS)
        error["documents_required_for_every_da"] = UNIVERSAL_DOCUMENTS
        error["note"] = (
            "Only the types above have type-specific requirements. Every DA needs the "
            "documents listed here regardless of type."
        )
        return [TextContent(type="text", text=json.dumps(error, indent=2))]

    key = match.key
    entry = DA_CHECKLISTS[key]
    response = {
        "development_type": key,
        "what_this_covers": entry["label"],
        "required_documents": UNIVERSAL_DOCUMENTS,
        "additional_for_type": entry["documents"],
        "conditional_documents": CONDITIONAL_DOCUMENTS,
        "lodgement": (
            "Lodged via the NSW Planning Portal: "
            "https://www.planningportal.nsw.gov.au/onlineDA. The DA is not legally lodged "
            "until it passes Council's completeness check and the fee is paid — an "
            "incomplete lodgement does not start the assessment clock."
        ),
    }
    if entry.get("commonly_missed"):
        response["commonly_missed"] = entry["commonly_missed"]
    if entry.get("note"):
        response["before_you_lodge"] = entry["note"]
    if entry.get("also_see"):
        other = DA_CHECKLISTS[entry["also_see"]]
        response["also_see"] = (
            f"{entry['also_see']} — {other['label']}. Call get_da_checklist again with that "
            "type if it fits your proposal better."
        )
    if match.how != "exact":
        response["interpreted_as"] = (
            f"Read '{requested}' as '{key}' ({entry['label']}). If that is not the kind of "
            "development you meant, call again with a type from the list."
        )
    return [TextContent(type="text", text=json.dumps(response, indent=2))]


@tool(
    name='get_contact_info',
    description='Get Lismore City Council contact information, including duty planner availability and key URLs.',
    properties={},
)
def get_contact_info(arguments: dict):
    return [TextContent(
        type="text",
        text=json.dumps(CONTACT_INFO, indent=2)
    )]
