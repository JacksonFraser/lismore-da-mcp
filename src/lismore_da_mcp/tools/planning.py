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
from lismore_da_mcp.data.standards import RESIDENTIAL_STANDARDS
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
        "Front setbacks depend on lot configuration and side/rear setbacks on the number of "
        "storeys, so supply those to get the applicable figure rather than every variant."
    ),
    properties={
        'setback_type': {'type': 'string', 'description': "Type of setback: 'front', 'side', 'rear', or 'all'"},
        'storeys': {'type': 'integer', 'description': "Optional: number of storeys proposed. Determines the side and rear setback."},
        'lot_configuration': {'type': 'string', 'description': "Optional: 'standard', 'corner', or 'battle_axe'. Determines the front setback."},
        'development_type': {'type': 'string', 'description': "Deprecated: use storeys and lot_configuration. Accepted as 'single_storey', 'two_storey', 'corner_lot' or 'battle_axe'."},
    },
    required=['setback_type'],
)
def get_setback_requirements(arguments: dict):
    setback_type = arguments.get("setback_type", "all").lower()
    setbacks = RESIDENTIAL_STANDARDS["setbacks"]

    # DCP Chapter 1 applies by development type, not by zone: it covers "building,
    # altering or using land for the construction of residential development,
    # including ancillary structures such as sheds, pools and garages" — wherever
    # that occurs. So there is no zone to filter on, but the scope does need
    # stating, because a caller asking about a shopfront setback would otherwise
    # get residential numbers with nothing to say they do not apply.
    scope = (
        "DCP Chapter 1 controls residential development, including ancillary structures "
        "(sheds, pools, garages), in any zone where such development is permitted. "
        "Commercial setbacks are in Chapter 2 and industrial in Chapter 3."
    )

    storeys = arguments.get("storeys")
    lot_configuration = (arguments.get("lot_configuration") or "").lower().strip()

    # The old single `development_type` conflated two independent things — how
    # many storeys, and what shape the lot is — so a two-storey corner lot could
    # not be expressed at all. Still accepted, mapped onto whichever it meant.
    legacy = (arguments.get("development_type") or "").lower().strip()
    if legacy in ("single_storey", "single storey") and storeys is None:
        storeys = 1
    elif legacy in ("two_storey", "two storey") and storeys is None:
        storeys = 2
    elif legacy in ("corner_lot", "corner") and not lot_configuration:
        lot_configuration = "corner"
    elif legacy in ("battle_axe", "battleaxe") and not lot_configuration:
        lot_configuration = "battle_axe"

    def applicable(kind: str) -> tuple[str | None, str | None, str | None]:
        """(the applicable requirement, why it applies, what input would narrow it)."""
        options = setbacks[kind]
        if kind == "front":
            if lot_configuration == "corner":
                return options.get("corner_lots"), "corner lot", None
            if lot_configuration == "battle_axe":
                return options.get("battle_axe"), "battle-axe lot", None
            if lot_configuration == "standard":
                return options.get("general"), "standard lot", None
            return None, None, "lot_configuration ('standard', 'corner' or 'battle_axe')"
        if kind == "side":
            if storeys is None:
                return None, None, "storeys"
            if storeys <= 1:
                return options.get("single_storey"), "single storey", None
            return options.get("two_storey"), f"{storeys} storeys", None
        if kind == "rear":
            if storeys is None:
                return None, None, "storeys"
            # "Minimum 3m for single storey, 6m for two storey" — return only the
            # half that applies, so a two-storey answer does not lead with the
            # single-storey figure.
            general = options.get("general", "")
            halves = [h.strip() for h in general.split(",")]
            if len(halves) == 2:
                part = halves[0] if storeys <= 1 else halves[1]
            else:
                part = general
            return part, ("single storey" if storeys <= 1 else f"{storeys} storeys"), None
        return None, None, None

    if setback_type == "all":
        kinds = ["front", "side", "rear"]
    elif setback_type in setbacks:
        kinds = [setback_type]
    else:
        return [TextContent(type="text", text=json.dumps({
            "error": f"Setback type '{setback_type}' not found",
            "available_types": ["front", "side", "rear", "all"],
        }, indent=2))]

    answer: dict = {}
    unresolved: list[str] = []
    for kind in kinds:
        requirement, because, needs = applicable(kind)
        entry = {"all_cases": setbacks[kind]}
        if requirement:
            entry["applicable"] = requirement
            entry["because"] = because
        elif needs:
            # Say what is missing rather than picking a default and presenting it
            # as the answer — which is what returning "general" unconditionally did.
            entry["applicable"] = None
            entry["to_narrow_this"] = f"Supply {needs}."
            unresolved.append(kind)
        answer[kind] = entry

    result = {
        "setback_type": setback_type,
        "setbacks": answer if len(kinds) > 1 else answer[kinds[0]],
        "applies_to": scope,
        "source": "Lismore DCP Chapter 1 - Residential Development",
        "note": (
            "Figures are the DCP's standard controls. An established building line, a "
            "building envelope control or a site-specific constraint can displace them, so "
            "confirm against Chapter 1 and the site before relying on a number."
        ),
    }
    if unresolved:
        result["not_determined"] = (
            "No single figure given for: " + ", ".join(unresolved)
            + ". Every case is listed under all_cases."
        )

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


@tool(
    name='get_residential_standards',
    description='Get residential development standards from DCP Chapter 1, including site coverage, private open space, landscaping, and car parking design requirements.',
    properties={
        'standard_type': {'type': 'string', 'description': "Type of standard: 'site_coverage', 'private_open_space', 'landscaping', 'car_parking_design', 'building_height', or 'all'. Defaults to 'all'."},
    },
)
def get_residential_standards(arguments: dict):
    standard_type = arguments.get("standard_type", "all").lower()

    if standard_type == "all":
        result = {
            "residential_standards": RESIDENTIAL_STANDARDS,
            "source": "Lismore DCP Chapter 1 - Residential Development",
            "note": "These are summary guidelines. Always check the full DCP chapter for detailed provisions."
        }
    elif standard_type in RESIDENTIAL_STANDARDS:
        result = {
            "standard_type": standard_type,
            "requirements": RESIDENTIAL_STANDARDS[standard_type],
            "source": "Lismore DCP Chapter 1 - Residential Development"
        }
    elif standard_type == "setbacks":
        result = {
            "standard_type": "setbacks",
            "requirements": RESIDENTIAL_STANDARDS["setbacks"],
            "source": "Lismore DCP Chapter 1 - Residential Development"
        }
    else:
        result = {
            "error": f"Standard type '{standard_type}' not found",
            "available_types": list(RESIDENTIAL_STANDARDS.keys())
        }

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
