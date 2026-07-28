"""Flood, setbacks, residential standards, referrals, checklists and contacts."""

import json

from mcp.types import TextContent

from lismore_da_mcp.data.contacts import CONTACT_INFO
from lismore_da_mcp.data.flood import FLOOD_PLANNING
from lismore_da_mcp.data.referrals import REFERRAL_REQUIREMENTS
from lismore_da_mcp.data.standards import RESIDENTIAL_STANDARDS
from lismore_da_mcp.registry import tool


@tool(
    name='get_flood_requirements',
    description='Get flood planning requirements for development in Lismore, including floor level requirements and exemptions.',
    properties={
        'development_type': {'type': 'string', 'description': "Type of development: 'residential', 'commercial', or 'cbd'"},
    },
    required=['development_type'],
)
def get_flood_requirements(arguments: dict):
    dev_type = arguments.get("development_type", "").lower()

    response = {
        "flood_planning_level": FLOOD_PLANNING["flood_planning_level"],
        "proposed_fpl": FLOOD_PLANNING["proposed_fpl"],
        "advice": FLOOD_PLANNING["advice"]
    }

    if "residential" in dev_type:
        response["requirement"] = FLOOD_PLANNING["residential_requirement"]
    elif "commercial" in dev_type or "industrial" in dev_type:
        response["requirement"] = FLOOD_PLANNING["commercial_requirement"]
    elif "cbd" in dev_type:
        response["cbd_exemption"] = FLOOD_PLANNING["cbd_exemption"]
    else:
        response["residential_requirement"] = FLOOD_PLANNING["residential_requirement"]
        response["commercial_requirement"] = FLOOD_PLANNING["commercial_requirement"]
        response["cbd_exemption"] = FLOOD_PLANNING["cbd_exemption"]

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

    # Map characteristics to referral authorities
    char_to_referral = {
        "bushfire": "rural_fire_service",
        "bushfire_prone": "rural_fire_service",
        "fire": "rural_fire_service",
        "heritage": "heritage_council",
        "state_heritage": "heritage_council",
        "industrial": "epa",
        "waste": "epa",
        "extractive": "epa",
        "traffic": "transport_nsw",
        "classified_road": "transport_nsw",
        "waterway": "natural_resources_access_regulator",
        "near_waterway": "natural_resources_access_regulator",
        "riparian": "natural_resources_access_regulator",
        "vegetation": "biodiversity_conservation",
        "vegetation_clearing": "biodiversity_conservation",
        "threatened_species": "biodiversity_conservation",
        "flood": "council_flood_assessment",
        "flooding": "council_flood_assessment",
        "flood_prone": "council_flood_assessment",
        "inundation": "council_flood_assessment",
    }

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
    description='Get a checklist of required documents for a Development Application based on development type.',
    properties={
        'development_type': {'type': 'string', 'description': "Type of development (e.g., 'dwelling', 'commercial', 'subdivision', 'change_of_use')"},
    },
    required=['development_type'],
)
def get_da_checklist(arguments: dict):
    dev_type = arguments.get("development_type", "").lower()
    # Keywords the branches below actually test for, surfaced so a rejected
    # call can name them instead of leaving the caller to guess.
    DA_CHECKLIST_TYPES = {
        "dwelling", "residential", "commercial", "subdivision", "change_of_use",
    }

    base_documents = [
        "Development Application form (via NSW Planning Portal)",
        "Owner's consent (if not the owner)",
        "Statement of Environmental Effects (SEE)",
        "Site plan (1:100 or 1:200 scale)",
        "Architectural plans (1:100 or 1:200 scale)",
        "Cost of Development Works estimate"
    ]

    additional = []

    if "dwelling" in dev_type or "residential" in dev_type:
        additional = [
            "BASIX Certificate",
            "Shadow diagrams (if 2+ storeys)",
            "Privacy assessment",
            "Landscape plan"
        ]
    elif "commercial" in dev_type:
        additional = [
            "Traffic impact assessment (if significant traffic generation)",
            "Acoustic report (if noise-generating use)",
            "Waste management plan",
            "BCA compliance report",
            "Fire safety schedule"
        ]
    elif "subdivision" in dev_type:
        additional = [
            "Survey plan",
            "Subdivision layout plan",
            "Services layout plan",
            "Stormwater management plan",
            "Road layout and pavement design"
        ]
    elif "change_of_use" in dev_type:
        additional = [
            "BCA compliance assessment",
            "Fire safety upgrade report (if required)",
            "Parking assessment"
        ]

    # Nothing matched, so there is no type-specific advice to give. Returning the
    # generic list anyway made 'nuclear reactor' and 'spaceship' look like
    # recognised development types with a considered answer behind them.
    if not additional:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"No checklist available for development type '{dev_type}'.",
                "recognised_types": sorted(DA_CHECKLIST_TYPES),
                "note": (
                    "Only the types above have type-specific document requirements. "
                    "Every DA needs the standard documents listed under "
                    "'documents_required_for_every_da' regardless of type."
                ),
                "documents_required_for_every_da": base_documents,
            }, indent=2)
        )]

    conditional = [
        {"condition": "If flood-affected land", "document": "Flood Risk Assessment"},
        {"condition": "If heritage item or near heritage", "document": "Heritage Impact Statement"},
        {"condition": "If vegetation removal required", "document": "Vegetation Management Plan"},
        {"condition": "If contamination suspected", "document": "Contamination Assessment"},
        {"condition": "If on-site sewage", "document": "On-site Sewage Management Report"},
        {"condition": "If Clause 4.6 variation needed", "document": "Clause 4.6 Variation Request"}
    ]

    return [TextContent(
        type="text",
        text=json.dumps({
            "development_type": dev_type,
            "required_documents": base_documents,
            "additional_for_type": additional,
            "conditional_documents": conditional,
            "lodgement": "All applications must be lodged via NSW Planning Portal: https://www.planningportal.nsw.gov.au/onlineDA"
        }, indent=2)
    )]


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
