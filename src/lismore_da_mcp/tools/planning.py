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
    description='Get setback requirements for residential development. Returns front, side, and rear setback requirements based on dwelling type and lot configuration.',
    properties={
        'setback_type': {'type': 'string', 'description': "Type of setback: 'front', 'side', 'rear', or 'all'"},
        'development_type': {'type': 'string', 'description': "Optional: 'single_storey', 'two_storey', 'corner_lot', 'battle_axe'"},
    },
    required=['setback_type'],
)
def get_setback_requirements(arguments: dict):
    setback_type = arguments.get("setback_type", "all").lower()
    dev_type = arguments.get("development_type", "").lower()

    setbacks = RESIDENTIAL_STANDARDS["setbacks"]

    if setback_type == "all":
        result = {
            "setbacks": setbacks,
            "source": "Lismore DCP Chapter 1 - Residential Development",
            "note": "These are general guidelines. Site-specific assessment required. Check DCP Chapter 1 for full provisions."
        }
    elif setback_type in setbacks:
        result = {
            "setback_type": setback_type,
            "requirements": setbacks[setback_type],
            "source": "Lismore DCP Chapter 1 - Residential Development"
        }
        if dev_type and dev_type in setbacks[setback_type]:
            result["specific_requirement"] = setbacks[setback_type][dev_type]
    else:
        result = {
            "error": f"Setback type '{setback_type}' not found",
            "available_types": ["front", "side", "rear", "all"]
        }

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
