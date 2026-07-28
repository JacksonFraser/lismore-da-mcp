"""
Lismore Development Application MCP Server

Provides tools for assisting with Development Applications in the Lismore LGA.
"""

import base64
import json
import math
import shutil
import tempfile
from pathlib import Path
from typing import Any

from mcp.types import Tool, TextContent

# Re-exports. Several names below are not referenced in this module — they are
# imported so that `from lismore_da_mcp.server import X` keeps working for the
# tests and for anything embedding this package, which is where they lived before
# the Phase 2 split. Do not "clean up" an unused import here without checking
# tests/ first; prefer importing from the owning module in new code.
from lismore_da_mcp.app import server
from lismore_da_mcp.config import (
    DOC_CATEGORIES,
    DOCS_DIR,
    LISTABLE_SUFFIXES,
    PUBLIC_MODE,
    SEARCHABLE_SUFFIXES,
    SEE_TEMPLATE_PATH,
)
from lismore_da_mcp.landuse import canonical_use, classify_land_use, match_land_use
from lismore_da_mcp.vocabulary import (
    DEFINITION_SYNONYMS,
    MINOR_DEVELOPMENT_SYNONYMS,
    PARKING_SYNONYMS,
    SEE_SECTION_SYNONYMS,
    resolve,
    unresolved_error,
)
from lismore_da_mcp.transport import _RateLimitMiddleware, build_http_app, run, run_http
from lismore_da_mcp.see.fill import fill_see_pdf
from lismore_da_mcp.see.generate import generate_see_form_data
from lismore_da_mcp.see.fields import (
    PURPOSE_WRITTEN_SEE_HEADINGS,
    RESIDENTIAL_ZONES,
    SEE_COMMENT_FIELDS,
    SEE_FORM_FIELDS,
    SEE_QUESTIONS,
    SEE_TEMPLATE_SCOPE,
)
from lismore_da_mcp.see.layout import (
    CHECKBOX_GLYPHS,
    SEE_LAYOUT_EXPECTED,
    _answer_boxes,
    _checkbox_rects,
    see_layout,
)
from lismore_da_mcp.see.parsers import (
    estimate_parking_requirement,
    parse_land_identifier,
    parse_street_address,
)
from lismore_da_mcp.search import (
    STOPWORDS,
    search_all,
    _query_tokens,
    _score_lines,
    extract_document_section,
    extract_pdf_section,
    extract_text_section,
    find_document,
    list_available_documents,
    search_document,
    search_pdf,
    search_text_file,
    searchable_documents,
)

# Planning data lives in data/ so a transcription can be checked against the LEP
# or DCP without reading the server. Re-exported here because tools, tests and
# any external caller have always imported these from this module.
from lismore_da_mcp.data.contacts import CONTACT_INFO
from lismore_da_mcp.data.definitions import (
    CATCHALL_TERM,
    LAND_USE_DEFINITIONS,
    LAND_USE_HIERARCHY,
)
from lismore_da_mcp.data.fees import DA_FEE_BRACKETS, DA_FEE_SCHEDULE_YEAR
from lismore_da_mcp.data.flood import FLOOD_PLANNING
from lismore_da_mcp.data.parking import PARKING_RATES
from lismore_da_mcp.data.referrals import REFERRAL_REQUIREMENTS
from lismore_da_mcp.data.see_templates import SEE_TEMPLATES
from lismore_da_mcp.data.standards import RESIDENTIAL_STANDARDS
from lismore_da_mcp.data.zones import ZONES



# ============================================================================
# Fee Calculation
# ============================================================================

def calculate_da_fee(development_cost: float) -> dict:
    """Calculate DA fee based on estimated development cost."""
    for upper, base, per_thousand, floor in DA_FEE_BRACKETS:
        if development_cost <= upper:
            # Schedule 4 charges the increment "for each $1,000, or part $1,000,
            # by which estimated cost exceeds" the bracket floor — so a partial
            # thousand is charged as a whole one. Interpolating linearly here
            # under-charged every cost that wasn't a round number of thousands.
            excess = max(0.0, development_cost - floor)
            fee = base + per_thousand * math.ceil(excess / 1000)
            break

    cost_estimate_requirement = "Applicant estimate"
    if development_cost > 100000:
        cost_estimate_requirement = "Qualified person estimate"
    if development_cost > 3000000:
        cost_estimate_requirement = "Registered Quantity Surveyor report"

    return {
        "estimated_fee": round(fee, 2),
        "development_cost": development_cost,
        "cost_estimate_requirement": cost_estimate_requirement,
        "fee_schedule_year": DA_FEE_SCHEDULE_YEAR,
        "note": "This is the statutory DA lodgement fee only. Additional fees may apply for advertising, referrals, long service levy, and Section 7.11 contributions.",
        "currency_warning": (
            f"Calculated from the {DA_FEE_SCHEDULE_YEAR} EP&A Regulation Schedule 4 scale. "
            "Statutory fees are re-set each July — confirm against Council's current fees and "
            "charges before relying on this figure."
        ),
    }




# ============================================================================
# PDF Search Functions
# ============================================================================




























# ============================================================================
# SEE PDF Form Configuration
# ============================================================================


# The blank template carries no AcroForm fields, so answers have to be drawn
# onto the page. Rather than hardcode coordinates — which were consistently a
# few dozen points out, so text landed on top of the printed labels and outside
# the boxes — the geometry is read out of the template at fill time:
#
#   * every answer box is a white-filled rectangle drawn over the grey form
#   * every tick box is a Wingdings empty-square glyph
#
# Fields below reference those by page plus index in reading order (top to
# bottom, then left to right). If Council reissues the form with a different
# layout the indices still resolve to real boxes, and SEE_LAYOUT_EXPECTED makes
# a change in box/checkbox counts fail loudly instead of silently misplacing text.












# ---------------------------------------------------------------------------
# Land use classification
# ---------------------------------------------------------------------------
# Child terms and the broader parent categories they fall under. If a parent is
# permitted in a zone, so is everything beneath it.










# ---------------------------------------------------------------------------
# The form's Yes/No questions
# ---------------------------------------------------------------------------
# Every one of these is a declaration the applicant signs as true on page 7, so
# none of them is answered unless the answer was supplied or is entailed by
# something that was. Keys match the SEE_FORM_FIELDS prefixes ("<key>_yes"/"_no").



























# ============================================================================
# MCP Tool Definitions
# ============================================================================

TOOLS: list[Tool] = [
        Tool(
            name="get_parking_rates",
            description="Get off-street parking requirements for a development type in Lismore. Supply floor_area_sqm, num_employees and spaces_provided to also get the indicative number of spaces required and any shortfall to be addressed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "development_type": {
                        "type": "string",
                        "description": "Type of development (e.g., 'dwelling_house', 'restaurant', 'shop', 'office', 'warehouse')"
                    },
                    "floor_area_sqm": {
                        "type": "number",
                        "description": "Optional. Floor area the rate applies to, in square metres."
                    },
                    "num_employees": {
                        "type": "integer",
                        "description": "Optional. Number of employees, for rates with a staff component."
                    },
                    "spaces_provided": {
                        "type": "integer",
                        "description": "Optional. Spaces provided on site, to calculate the shortfall."
                    }
                },
                "required": ["development_type"]
            }
        ),
        Tool(
            name="get_zone_info",
            description="Get information about a zoning classification in Lismore LEP 2012, including objectives, permitted uses, and development standards.",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_code": {
                        "type": "string",
                        "description": "Zone code (e.g., 'R1', 'R2', 'R3', 'B2', 'B3', 'IN1', 'RU5')"
                    }
                },
                "required": ["zone_code"]
            }
        ),
        Tool(
            name="calculate_da_fees",
            description="Calculate the Development Application lodgement fee based on estimated development cost.",
            inputSchema={
                "type": "object",
                "properties": {
                    "development_cost": {
                        "type": "number",
                        "description": "Estimated cost of development works in dollars"
                    }
                },
                "required": ["development_cost"]
            }
        ),
        Tool(
            name="get_flood_requirements",
            description="Get flood planning requirements for development in Lismore, including floor level requirements and exemptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "development_type": {
                        "type": "string",
                        "description": "Type of development: 'residential', 'commercial', or 'cbd'"
                    }
                },
                "required": ["development_type"]
            }
        ),
        Tool(
            name="get_contact_info",
            description="Get Lismore City Council contact information, including duty planner availability and key URLs.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_dcp",
            description="Search Lismore's planning documents (DCP chapters, LEP documents and text extracts, forms, fee schedules, and the NSW exempt-development fact sheets) for specific provisions, requirements, or keywords. Matches on significant terms in the query, not just the exact phrase, so multi-word conceptual queries still surface partial matches. Each hit reports the file plus a location — a page number for PDFs, a line number for text extracts — that read_dcp_section accepts directly.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term or phrase to find in DCP documents"
                    },
                    "chapter": {
                        "type": "string",
                        "description": "Optional: specific chapter to search (e.g., 'chapter-1', 'chapter-7', 'nimbin')"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="read_dcp_section",
            description="Read a section from any planning document — a DCP chapter, an LEP text extract, a form, a fee schedule, or an exempt-development fact sheet. Use list_documents for filenames.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chapter": {
                        "type": "string",
                        "description": "Document filename or a fragment of it (e.g., 'chapter-7-off-street-carparking.pdf', 'lep-2012-nsw-full.txt', 'fences')"
                    },
                    "start_page": {
                        "type": "integer",
                        "description": "Starting page number, or starting line number for .txt documents (default: 1)"
                    },
                    "end_page": {
                        "type": "integer",
                        "description": "Ending page number, or ending line number for .txt documents (optional; .txt defaults to a 200-line window)"
                    }
                },
                "required": ["chapter"]
            }
        ),
        Tool(
            name="list_documents",
            description="List all available planning documents (DCP chapters, LEP documents and text extracts, forms, fee schedules, exempt-development fact sheets), with how each is addressed by read_dcp_section.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_da_checklist",
            description="Get a checklist of required documents for a Development Application based on development type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "development_type": {
                        "type": "string",
                        "description": "Type of development (e.g., 'dwelling', 'commercial', 'subdivision', 'change_of_use')"
                    }
                },
                "required": ["development_type"]
            }
        ),
        Tool(
            name="list_parking_types",
            description="List all development types that have parking rate information available.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_zones",
            description="List all zone codes available in Lismore LEP 2012.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_definition",
            description="Get the Standard Instrument LEP definition of a land-use term (e.g. 'retail premises' vs 'food and drink premises' vs 'shop'), including related terms. Use this to work out which defined use a proposal actually falls under before checking zone permissibility.",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Land-use term to look up (e.g. 'retail premises', 'food and drink premises', 'shop', 'home business')"
                    }
                },
                "required": ["term"]
            }
        ),
        Tool(
            name="check_permissibility",
            description="Check if a specific land use is permitted in a specific zone. Returns whether the use is permitted without consent, permitted with consent, prohibited, or not found. Essential first step for any DA - confirms the proposal is actually permissible.",
            inputSchema={
                "type": "object",
                "properties": {
                    "land_use": {
                        "type": "string",
                        "description": "The proposed land use (e.g., 'restaurant or cafe', 'dwelling house', 'warehouse', 'shop top housing')"
                    },
                    "zone_code": {
                        "type": "string",
                        "description": "Zone code (e.g., 'R1', 'E2', 'MU1')"
                    }
                },
                "required": ["land_use", "zone_code"]
            }
        ),
        Tool(
            name="get_setback_requirements",
            description="Get setback requirements for residential development. Returns front, side, and rear setback requirements based on dwelling type and lot configuration.",
            inputSchema={
                "type": "object",
                "properties": {
                    "setback_type": {
                        "type": "string",
                        "description": "Type of setback: 'front', 'side', 'rear', or 'all'"
                    },
                    "development_type": {
                        "type": "string",
                        "description": "Optional: 'single_storey', 'two_storey', 'corner_lot', 'battle_axe'"
                    }
                },
                "required": ["setback_type"]
            }
        ),
        Tool(
            name="check_referrals",
            description="Check what external agency referrals (integrated development approvals) may be required for a development. Returns triggers and required documents for each potential referral authority.",
            inputSchema={
                "type": "object",
                "properties": {
                    "development_characteristics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of development characteristics, e.g., ['bushfire_prone', 'near_waterway', 'heritage_item', 'significant_traffic', 'vegetation_clearing', 'industrial']"
                    }
                },
                "required": ["development_characteristics"]
            }
        ),
        Tool(
            name="get_see_template",
            description="Get Statement of Environmental Effects (SEE) section template with prompts for what to include. Returns structured guidance for writing each section of an SEE.",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "SEE section: 'site_description', 'proposal_description', 'planning_framework', 'environmental_impacts', 'mitigation_measures', 'section_4_15_matters', or 'all'"
                    }
                },
                "required": ["section"]
            }
        ),
        Tool(
            name="get_residential_standards",
            description="Get residential development standards from DCP Chapter 1, including site coverage, private open space, landscaping, and car parking design requirements.",
            inputSchema={
                "type": "object",
                "properties": {
                    "standard_type": {
                        "type": "string",
                        "description": "Type of standard: 'site_coverage', 'private_open_space', 'landscaping', 'car_parking_design', 'building_height', or 'all'. Defaults to 'all'."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="list_definitions",
            description="List all available land-use definitions in the system. Use this to see what terms have definitions available before calling get_definition.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="generate_see_draft",
            description="Generate a draft Statement of Environmental Effects (SEE) document based on proposal details. Automatically pulls in zone information, parking requirements, flood planning, and other relevant data to create a structured SEE ready for review and refinement.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_address": {
                        "type": "string",
                        "description": "Street address of the property"
                    },
                    "lot_dp": {
                        "type": "string",
                        "description": "Lot and DP number (e.g., 'Lot 1 DP 123456')"
                    },
                    "zone_code": {
                        "type": "string",
                        "description": "Zone code (e.g., 'E2', 'R1', 'MU1')"
                    },
                    "site_area_sqm": {
                        "type": "number",
                        "description": "Site area in square metres"
                    },
                    "existing_use": {
                        "type": "string",
                        "description": "Current/existing use of the property"
                    },
                    "proposed_use": {
                        "type": "string",
                        "description": "Proposed land use (e.g., 'restaurant or cafe', 'shop', 'dwelling house')"
                    },
                    "development_type": {
                        "type": "string",
                        "description": "Type of development: 'new_building', 'alteration', 'change_of_use', 'fitout'"
                    },
                    "floor_area_sqm": {
                        "type": "number",
                        "description": "Gross floor area of the proposal in square metres"
                    },
                    "building_description": {
                        "type": "string",
                        "description": "Description of proposed works (e.g., 'Internal fitout for cafe with kitchen, counter, and 8-seat dining area')"
                    },
                    "hours_of_operation": {
                        "type": "string",
                        "description": "Proposed hours of operation (e.g., '7am-4pm Monday to Saturday')"
                    },
                    "num_employees": {
                        "type": "integer",
                        "description": "Number of employees"
                    },
                    "num_customers": {
                        "type": "integer",
                        "description": "Maximum number of customers/patrons at any time"
                    },
                    "estimated_cost": {
                        "type": "number",
                        "description": "Estimated cost of development works in dollars"
                    },
                    "is_flood_affected": {
                        "type": "boolean",
                        "description": "Is the property within the flood planning area?"
                    },
                    "is_heritage": {
                        "type": "boolean",
                        "description": "Is the property a heritage item or in a heritage conservation area?"
                    },
                    "existing_parking_spaces": {
                        "type": "integer",
                        "description": "Number of existing on-site parking spaces (0 if none)"
                    },
                    "applicant_name": {
                        "type": "string",
                        "description": "Name of the applicant"
                    }
                },
                "required": ["property_address", "zone_code", "proposed_use", "development_type", "floor_area_sqm"]
            }
        ),
        Tool(
            name="preview_see_form",
            description="Preview exactly what will be written into the official Lismore SEE PDF, including every tick. Shows the questions still unanswered and any issue that blocks the form being generated. Review this before calling fill_see_pdf.",
            inputSchema={
                "type": "object",
                "properties": {
                    "applicant_name": {
                        "type": "string",
                        "description": "Full name of the applicant"
                    },
                    "minor_development_type": {
                        "type": "string",
                        "enum": ["dwelling_single_storey", "residential_addition_single_storey", "ancillary_residential_structure", "strata_subdivision"],
                        "description": "REQUIRED. Which of the four development types this Council template covers. Anything outside this list (commercial work, change of use, multi-storey) cannot use this form - build a purpose-written SEE with generate_see_draft instead."
                    },
                    "property_address": {
                        "type": "string",
                        "description": "Full street address, e.g. '45 Keen Street, Lismore NSW 2480'. Prefer the separate unit/street_number/street/suburb fields where the address has a shop or unit number."
                    },
                    "unit": {
                        "type": "string",
                        "description": "Tenancy identifier if any, e.g. 'Shop 3', 'Unit 2'"
                    },
                    "street_number": {
                        "type": "string",
                        "description": "Street number only, e.g. '88' or '5-7'"
                    },
                    "street": {
                        "type": "string",
                        "description": "Street name only, e.g. 'Keen Street'"
                    },
                    "suburb": {
                        "type": "string",
                        "description": "Suburb only, without NSW or postcode"
                    },
                    "building_name": {
                        "type": "string",
                        "description": "Building name, if known"
                    },
                    "lot_dp": {
                        "type": "string",
                        "description": "Land identifier as text, e.g. 'Lot 12 DP 758651' or 'SP 12345'. Prefer lot/plan_type/plan_number. The form is not generated without a plan number."
                    },
                    "lot": {
                        "type": "string",
                        "description": "Lot number on its own"
                    },
                    "plan_type": {
                        "type": "string",
                        "enum": ["DP", "SP", "CP"],
                        "description": "Deposited, Strata or Community plan"
                    },
                    "plan_number": {
                        "type": "string",
                        "description": "Plan number on its own, e.g. '758651'"
                    },
                    "section": {
                        "type": "string",
                        "description": "Section number, if the land has one"
                    },
                    "zone_code": {
                        "type": "string",
                        "description": "Zone code under Lismore LEP 2012, e.g. 'R1', 'E2'. Employment zones replaced the B-series codes in 2023."
                    },
                    "proposed_use": {
                        "type": "string",
                        "description": "Proposed land use, e.g. 'dwelling house', 'shed'"
                    },
                    "development_type": {
                        "type": "string",
                        "description": "Type: 'new_building', 'alteration', 'change_of_use', 'fitout'"
                    },
                    "floor_area_sqm": {
                        "type": "number",
                        "description": "Floor area in square metres"
                    },
                    "building_description": {
                        "type": "string",
                        "description": "Description of the proposed works, in the applicant's own words. Used verbatim as the description of development."
                    },
                    "site_description": {
                        "type": "string",
                        "description": "Physical description of the site: shape, slope, vegetation, waterways"
                    },
                    "surrounding_context": {
                        "type": "string",
                        "description": "Land uses and development on surrounding land"
                    },
                    "existing_use": {
                        "type": "string",
                        "description": "Present and previous use of the site"
                    },
                    "hours_of_operation": {
                        "type": "string",
                        "description": "Proposed operating hours, where the use has any"
                    },
                    "num_employees": {
                        "type": "integer",
                        "description": "Number of employees"
                    },
                    "num_customers": {
                        "type": "integer",
                        "description": "Maximum customers at any time"
                    },
                    "estimated_cost": {
                        "type": "number",
                        "description": "Estimated cost of works in dollars"
                    },
                    "is_flood_affected": {
                        "type": "boolean",
                        "description": "Is the site flood prone? Omit if unknown - the tick is then left blank rather than guessed."
                    },
                    "is_bushfire_prone": {
                        "type": "boolean",
                        "description": "Is the site bushfire prone? Omit if unknown."
                    },
                    "is_heritage": {
                        "type": "boolean",
                        "description": "Is the site a heritage item under LEP 2012 Schedule 5? Omit if unknown."
                    },
                    "in_heritage_conservation_area": {
                        "type": "boolean",
                        "description": "Is the site within a heritage conservation area? Omit if unknown."
                    },
                    "internal_works_only": {
                        "type": "boolean",
                        "description": "True if the works are wholly internal. Lets the excavation and vegetation questions be answered from that fact."
                    },
                    "parking_spaces_provided": {
                        "type": "integer",
                        "description": "Off-street parking spaces provided on site. Compared against the DCP Chapter 7 rate so any shortfall is stated."
                    },
                    "stormwater_to_council_system": {
                        "type": "boolean",
                        "description": "True if stormwater goes to the Council drainage system; false if disposed of another way (describe it in comments.stormwater_details)."
                    },
                    "answers": {
                        "type": "object",
                        "description": "The applicant's answers to the form's Yes/No questions, as {question_key: true|false}. Any question left out stays blank on the form and is returned in unanswered_questions - these are declarations signed as true, so they are never filled in on the applicant's behalf. Keys: zone_objectives, dcp_accordance, visually_prominent, inconsistent_streetscape, out_of_character, inconsistent_land_use, setback_variation, privacy_issues, overshadowing, acoustic_issues, views_impact, legal_access, increase_traffic, additional_access, parking_addressed, utilities_available, air_pollution, water_pollution, noise_impacts, excavation, erosion, contamination, sustainable, heritage_impact, aboriginal, remove_vegetation, threatened_species, effluent, trade_waste, hazardous_waste, rainwater_tanks, overland_risks, economic_social, crime_prevention, permissible."
                    },
                    "comments": {
                        "type": "object",
                        "description": "Free text for the form's comment boxes, as {field: text}. Keys: hazards_comments, constraints, surrounding_land_use, planning_comments, context_comment, privacy_comments, access_comments, environmental_comments, flora_comments, waste_comments, social_comments, other_matters, stormwater_details, traffic_amount."
                    }
                },
                "required": ["applicant_name", "property_address", "lot_dp", "zone_code", "proposed_use", "development_type", "floor_area_sqm", "minor_development_type"]
            }
        ),
        Tool(
            name="fill_see_pdf",
            description="Fill the official Lismore SEE PDF form and save it. Refuses proposals outside the template's 'Minor Development Only' scope, and refuses to write a blank land identifier. Questions the applicant has not answered are left blank and reported rather than guessed. Run preview_see_form first.",
            inputSchema={
                "type": "object",
                "properties": {
                    "applicant_name": {
                        "type": "string",
                        "description": "Full name of the applicant"
                    },
                    "minor_development_type": {
                        "type": "string",
                        "enum": ["dwelling_single_storey", "residential_addition_single_storey", "ancillary_residential_structure", "strata_subdivision"],
                        "description": "REQUIRED. Which of the four development types this Council template covers. Anything outside this list (commercial work, change of use, multi-storey) cannot use this form - build a purpose-written SEE with generate_see_draft instead."
                    },
                    "property_address": {
                        "type": "string",
                        "description": "Full street address, e.g. '45 Keen Street, Lismore NSW 2480'. Prefer the separate unit/street_number/street/suburb fields where the address has a shop or unit number."
                    },
                    "unit": {
                        "type": "string",
                        "description": "Tenancy identifier if any, e.g. 'Shop 3', 'Unit 2'"
                    },
                    "street_number": {
                        "type": "string",
                        "description": "Street number only, e.g. '88' or '5-7'"
                    },
                    "street": {
                        "type": "string",
                        "description": "Street name only, e.g. 'Keen Street'"
                    },
                    "suburb": {
                        "type": "string",
                        "description": "Suburb only, without NSW or postcode"
                    },
                    "building_name": {
                        "type": "string",
                        "description": "Building name, if known"
                    },
                    "lot_dp": {
                        "type": "string",
                        "description": "Land identifier as text, e.g. 'Lot 12 DP 758651' or 'SP 12345'. Prefer lot/plan_type/plan_number. The form is not generated without a plan number."
                    },
                    "lot": {
                        "type": "string",
                        "description": "Lot number on its own"
                    },
                    "plan_type": {
                        "type": "string",
                        "enum": ["DP", "SP", "CP"],
                        "description": "Deposited, Strata or Community plan"
                    },
                    "plan_number": {
                        "type": "string",
                        "description": "Plan number on its own, e.g. '758651'"
                    },
                    "section": {
                        "type": "string",
                        "description": "Section number, if the land has one"
                    },
                    "zone_code": {
                        "type": "string",
                        "description": "Zone code under Lismore LEP 2012, e.g. 'R1', 'E2'. Employment zones replaced the B-series codes in 2023."
                    },
                    "proposed_use": {
                        "type": "string",
                        "description": "Proposed land use, e.g. 'dwelling house', 'shed'"
                    },
                    "development_type": {
                        "type": "string",
                        "description": "Type: 'new_building', 'alteration', 'change_of_use', 'fitout'"
                    },
                    "floor_area_sqm": {
                        "type": "number",
                        "description": "Floor area in square metres"
                    },
                    "building_description": {
                        "type": "string",
                        "description": "Description of the proposed works, in the applicant's own words. Used verbatim as the description of development."
                    },
                    "site_description": {
                        "type": "string",
                        "description": "Physical description of the site: shape, slope, vegetation, waterways"
                    },
                    "surrounding_context": {
                        "type": "string",
                        "description": "Land uses and development on surrounding land"
                    },
                    "existing_use": {
                        "type": "string",
                        "description": "Present and previous use of the site"
                    },
                    "hours_of_operation": {
                        "type": "string",
                        "description": "Proposed operating hours, where the use has any"
                    },
                    "num_employees": {
                        "type": "integer",
                        "description": "Number of employees"
                    },
                    "num_customers": {
                        "type": "integer",
                        "description": "Maximum customers at any time"
                    },
                    "estimated_cost": {
                        "type": "number",
                        "description": "Estimated cost of works in dollars"
                    },
                    "is_flood_affected": {
                        "type": "boolean",
                        "description": "Is the site flood prone? Omit if unknown - the tick is then left blank rather than guessed."
                    },
                    "is_bushfire_prone": {
                        "type": "boolean",
                        "description": "Is the site bushfire prone? Omit if unknown."
                    },
                    "is_heritage": {
                        "type": "boolean",
                        "description": "Is the site a heritage item under LEP 2012 Schedule 5? Omit if unknown."
                    },
                    "in_heritage_conservation_area": {
                        "type": "boolean",
                        "description": "Is the site within a heritage conservation area? Omit if unknown."
                    },
                    "internal_works_only": {
                        "type": "boolean",
                        "description": "True if the works are wholly internal. Lets the excavation and vegetation questions be answered from that fact."
                    },
                    "parking_spaces_provided": {
                        "type": "integer",
                        "description": "Off-street parking spaces provided on site. Compared against the DCP Chapter 7 rate so any shortfall is stated."
                    },
                    "stormwater_to_council_system": {
                        "type": "boolean",
                        "description": "True if stormwater goes to the Council drainage system; false if disposed of another way (describe it in comments.stormwater_details)."
                    },
                    "answers": {
                        "type": "object",
                        "description": "The applicant's answers to the form's Yes/No questions, as {question_key: true|false}. Any question left out stays blank on the form and is returned in unanswered_questions - these are declarations signed as true, so they are never filled in on the applicant's behalf. Keys: zone_objectives, dcp_accordance, visually_prominent, inconsistent_streetscape, out_of_character, inconsistent_land_use, setback_variation, privacy_issues, overshadowing, acoustic_issues, views_impact, legal_access, increase_traffic, additional_access, parking_addressed, utilities_available, air_pollution, water_pollution, noise_impacts, excavation, erosion, contamination, sustainable, heritage_impact, aboriginal, remove_vegetation, threatened_species, effluent, trade_waste, hazardous_waste, rainwater_tanks, overland_risks, economic_social, crime_prevention, permissible."
                    },
                    "comments": {
                        "type": "object",
                        "description": "Free text for the form's comment boxes, as {field: text}. Keys: hazards_comments, constraints, surrounding_land_use, planning_comments, context_comment, privacy_comments, access_comments, environmental_comments, flora_comments, waste_comments, social_comments, other_matters, stormwater_details, traffic_amount."
                    },
                    "output_filename": {
                        "type": "string",
                        "description": "Output filename only — any path component is stripped. When running locally over stdio, saved to documents/output/; when served publicly over HTTP, returned inline as base64 and never written to disk. Default: 'SEE_filled.pdf'"
                    }
                },
                "required": ["applicant_name", "property_address", "lot_dp", "zone_code", "proposed_use", "development_type", "floor_area_sqm", "minor_development_type"]
            }
        ),
]

TOOL_SCHEMAS = {tool.name: tool.inputSchema for tool in TOOLS}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return TOOLS


def validate_arguments(name: str, arguments: dict) -> dict | None:
    """Check arguments against the tool's own schema. Returns an error payload, or None if valid.

    Handlers read arguments with .get() and sensible-looking defaults, which means a
    misspelt or omitted argument used to produce a confident wrong answer rather than
    an error — an empty land_use reported 'permitted without consent'. Refuse instead.
    """
    schema = TOOL_SCHEMAS.get(name)
    if schema is None:
        return {"error": f"Unknown tool: {name}", "available_tools": sorted(TOOL_SCHEMAS)}

    properties = schema.get("properties", {})
    unknown = sorted(k for k in arguments if k not in properties)
    if unknown:
        return {
            "error": "Unrecognised argument(s): " + ", ".join(unknown),
            "accepted_arguments": sorted(properties),
            "note": "Unrecognised arguments are not guessed at. Re-send the call using the names above.",
        }

    missing = [
        key for key in schema.get("required", [])
        if arguments.get(key) is None
        or (isinstance(arguments[key], str) and not arguments[key].strip())
    ]
    if missing:
        return {
            "error": "Missing or empty required argument(s): " + ", ".join(missing),
            "required_arguments": schema.get("required", []),
        }

    return None


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    argument_error = validate_arguments(name, arguments)
    if argument_error:
        return [TextContent(type="text", text=json.dumps(argument_error, indent=2))]

    if name == "get_parking_rates":
        requested = arguments.get("development_type", "")
        match = resolve(requested, PARKING_RATES, PARKING_SYNONYMS)
        if match:
            dev_type = match.key
            result = PARKING_RATES[dev_type]
            response = {
                "development_type": dev_type,
                "parking_spaces": result["spaces"],
                "rate_description": result["rate"],
                "source": "Lismore DCP Chapter 7 - Off-Street Carparking",
                "note": "Rates may vary by location. Check specific DCP provisions for exact requirements."
            }
            if match.how != "exact":
                response["interpreted_as"] = (
                    f"Read '{requested}' as '{dev_type}'. If that is not the use you meant, "
                    "call again with a term from list_parking_types."
                )

            # Turn the rate into a number where the inputs allow it, so a shortfall
            # gets stated rather than left as an exercise for the reader.
            estimate = estimate_parking_requirement(
                result["spaces"],
                arguments.get("floor_area_sqm", 0) or 0,
                arguments.get("num_employees", 0) or 0,
            )
            if estimate:
                provided = arguments.get("spaces_provided")
                estimate["spaces_provided"] = provided
                if provided is not None:
                    shortfall = max(0, estimate["spaces_required"] - provided)
                    estimate["shortfall"] = shortfall
                    estimate["advice"] = (
                        f"A shortfall of {shortfall} space(s) must be justified in the SEE — "
                        "on-street or public parking nearby is an argument for a variation, not evidence of compliance."
                        if shortfall else "The rate is met by the spaces provided."
                    )
                response["calculation"] = estimate

            return [TextContent(type="text", text=json.dumps(response, indent=2))]
        else:
            # No rate for this use. Say so rather than offering the closest
            # string — a hairdresser given warehouse rates is a wrong answer,
            # not a helpful approximation.
            error = unresolved_error(requested, match, "parking rate", PARKING_RATES)
            error["note"] = (
                "Chapter 7 sets rates by land use category, so an unlisted business usually "
                "falls under a broader term (a hairdresser is generally 'shop' or "
                "'business premises'). Confirm the correct category with Council rather than "
                "assuming the nearest-sounding one."
            )
            return [TextContent(type="text", text=json.dumps(error, indent=2))]

    elif name == "get_zone_info":
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
                    "available_zones": list(ZONES.keys())
                }, indent=2)
            )]

    elif name == "calculate_da_fees":
        cost = arguments.get("development_cost", 0)
        result = calculate_da_fee(float(cost))
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "get_flood_requirements":
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

    elif name == "get_contact_info":
        return [TextContent(
            type="text",
            text=json.dumps(CONTACT_INFO, indent=2)
        )]

    elif name == "search_dcp":
        query = arguments.get("query", "")
        chapter = arguments.get("chapter", "")

        if not DOCS_DIR.exists():
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Documents directory not found"})
            )]

        # Searches all planning document categories, not just dcp/ — a query about
        # e.g. flood clauses, exempt development or heritage schedules may only be
        # answerable from lep/, exempt-development/ or forms/. Uses the FTS index
        # when present and falls back to a full scan when it isn't.
        top_results = search_all(query, chapter)

        if not top_results:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "results": [],
                    "message": "No matches found. Try different search terms."
                }, indent=2)
            )]

        # Drop the internal ranking score before returning.
        for r in top_results:
            r.pop("score", None)

        return [TextContent(
            type="text",
            text=json.dumps({
                "query": query,
                "results": top_results
            }, indent=2)
        )]

    elif name == "read_dcp_section":
        chapter = arguments.get("chapter", "")
        start_page = arguments.get("start_page", 1)
        end_page = arguments.get("end_page")

        # Resolve across every category, not just dcp/ — search_dcp can return a hit in
        # lep/ or exempt-development/, and there was previously no way to open it.
        doc_path = find_document(chapter)

        if not doc_path:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Document '{chapter}' not found",
                    "available": [str(p.relative_to(DOCS_DIR)) for p in searchable_documents()]
                }, indent=2)
            )]

        text = extract_document_section(doc_path, start_page, end_page)
        return [TextContent(
            type="text",
            text=text
        )]

    elif name == "list_documents":
        docs = list_available_documents()
        return [TextContent(
            type="text",
            text=json.dumps({"documents": docs}, indent=2)
        )]

    elif name == "get_da_checklist":
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

    elif name == "list_parking_types":
        return [TextContent(
            type="text",
            text=json.dumps({
                "available_development_types": list(PARKING_RATES.keys()),
                "categories": {
                    "residential": ["dwelling_house", "dual_occupancy", "multi_dwelling_housing", "residential_flat_building", "secondary_dwelling", "boarding_house"],
                    "commercial": ["shop", "retail", "office", "business_premises", "restaurant", "cafe", "take_away", "medical_centre", "hotel", "motel"],
                    "industrial": ["industry", "warehouse", "bulky_goods"],
                    "other": ["childcare_centre", "place_of_worship", "gym"]
                }
            }, indent=2)
        )]

    elif name == "list_zones":
        # Filter out legacy zones that just redirect
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

    elif name == "get_definition":
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

    elif name == "check_permissibility":
        land_use = arguments["land_use"].strip()
        zone_code = arguments["zone_code"].upper().strip()

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

    elif name == "get_setback_requirements":
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

    elif name == "check_referrals":
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

    elif name == "get_see_template":
        section = arguments.get("section", "all").lower()

        if section == "all":
            result = {
                "see_template": SEE_TEMPLATES,
                "usage": "Use these headings and prompts to structure your Statement of Environmental Effects",
                "source": "Based on EP&A Regulation Schedule 1 and Lismore Council requirements"
            }
        else:
            match = resolve(section, SEE_TEMPLATES, SEE_SECTION_SYNONYMS)
            if match:
                result = {
                    "section": match.key,
                    "template": SEE_TEMPLATES[match.key],
                    "source": "Based on EP&A Regulation Schedule 1 and Lismore Council requirements"
                }
                if match.how != "exact":
                    result["interpreted_as"] = f"Read '{section}' as section '{match.key}'."
            else:
                result = unresolved_error(section, match, "SEE section", SEE_TEMPLATES)

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_residential_standards":
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

    elif name == "list_definitions":
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

    elif name == "generate_see_draft":
        # Extract all inputs
        property_address = arguments.get("property_address", "[ADDRESS NOT PROVIDED]")
        lot_dp = arguments.get("lot_dp", "[LOT/DP NOT PROVIDED]")
        zone_code = arguments.get("zone_code", "").upper()
        site_area = arguments.get("site_area_sqm", "[NOT PROVIDED]")
        existing_use = arguments.get("existing_use", "Vacant/Unknown")
        proposed_use = arguments.get("proposed_use", "")
        development_type = arguments.get("development_type", "")
        floor_area = arguments.get("floor_area_sqm", 0)
        building_description = arguments.get("building_description", "[NOT PROVIDED]")
        hours = arguments.get("hours_of_operation", "[NOT PROVIDED]")
        num_employees = arguments.get("num_employees")
        num_customers = arguments.get("num_customers")
        employees_line = num_employees if num_employees is not None else "[NOT PROVIDED]"
        customers_line = num_customers if num_customers is not None else "[NOT PROVIDED]"
        estimated_cost = arguments.get("estimated_cost", 0)
        is_flood = arguments.get("is_flood_affected", False)
        is_heritage = arguments.get("is_heritage", False)
        existing_parking = arguments.get("existing_parking_spaces", 0)
        applicant_name = arguments.get("applicant_name", "[APPLICANT NAME]")

        # Get zone information
        zone_info = ZONES.get(zone_code, {})
        zone_name = zone_info.get("name", "Unknown Zone")
        zone_objectives = zone_info.get("objectives", [])

        # Permissibility from the shared classifier, so this draft and
        # check_permissibility can't disagree about the same land use
        proposed_use_lower = proposed_use.lower().strip()
        classification = classify_land_use(proposed_use, zone_info, zone_code)
        if not classification:
            permissibility, permissibility_detail = "Unknown", ""
        elif classification["permissible"] is True:
            permissibility = "Permitted with consent"
            permissibility_detail = classification["statement"]
        elif classification["permissible"] is False:
            permissibility = "Prohibited"
            permissibility_detail = classification["statement"]
        else:
            permissibility = "To be confirmed"
            permissibility_detail = classification["statement"]

        # Get parking requirements
        parking_key = proposed_use_lower.replace(" ", "_").replace("or_", "")
        if "cafe" in parking_key or "restaurant" in parking_key:
            parking_key = "cafe"
        parking_info = PARKING_RATES.get(parking_key, PARKING_RATES.get("restaurant", {}))
        parking_rate = parking_info.get("rate", "Refer to DCP Chapter 7")

        # Calculate required parking
        if floor_area and "10m" in str(parking_info.get("spaces", "")):
            required_parking = max(1, int(floor_area / 10))
        else:
            required_parking = "[CALCULATE BASED ON DCP]"

        traffic_scale = (
            "minimal" if isinstance(num_customers, (int, float)) and num_customers <= 20
            else "moderate" if isinstance(num_customers, (int, float))
            else "[TO BE ASSESSED]"
        )

        # Get flood info
        flood_info = FLOOD_PLANNING if is_flood else None

        # Calculate DA fee
        fee_info = calculate_da_fee(estimated_cost) if estimated_cost else {"estimated_fee": None}
        # Either may legitimately be unknown at draft stage, so format defensively
        # instead of applying a currency format to a placeholder string.
        cost_line = f"${estimated_cost:,.2f}" if estimated_cost else "[TO BE PROVIDED]"
        fee = fee_info.get("estimated_fee")
        fee_line = f"${fee:,.2f}" if isinstance(fee, (int, float)) else "[CALCULATE ONCE COST OF WORKS IS KNOWN]"

        # Development type description
        dev_type_desc = {
            "new_building": "Construction of a new building",
            "alteration": "Alterations and additions to existing building",
            "change_of_use": "Change of use of existing premises",
            "fitout": "Internal fitout of existing premises"
        }.get(development_type, development_type)

        # Build the SEE document
        see_document = f"""
================================================================================
                    STATEMENT OF ENVIRONMENTAL EFFECTS
================================================================================

Prepared for: {applicant_name}
Property: {property_address}
Date: [INSERT DATE]

================================================================================
1. INTRODUCTION
================================================================================

This Statement of Environmental Effects (SEE) has been prepared in support of a
Development Application for {dev_type_desc.lower()} at {property_address}.

The proposal seeks consent for {proposed_use} within an existing {existing_use.lower()}
premises.

================================================================================
2. SITE DESCRIPTION
================================================================================

2.1 Property Details
--------------------
Address:            {property_address}
Legal Description:  {lot_dp}
Site Area:          {site_area} m²
Zone:               {zone_code} - {zone_name}

2.2 Existing Development
------------------------
The site currently contains {existing_use.lower() if existing_use != "Vacant/Unknown" else "a vacant premises"}.

2.3 Surrounding Context
-----------------------
The site is located within the {zone_name} zone. The surrounding area is
characterised by {"commercial and retail uses typical of the Lismore CBD" if zone_code == "E2" else "uses consistent with the " + zone_name + " zone"}.

[APPLICANT TO ADD: Description of adjoining properties and streetscape]

================================================================================
3. PROPOSED DEVELOPMENT
================================================================================

3.1 Development Overview
------------------------
Development Type:   {dev_type_desc}
Proposed Use:       {proposed_use.title()}
Floor Area:         {floor_area} m²

3.2 Description of Works
------------------------
{building_description}

3.3 Operational Details
-----------------------
Hours of Operation: {hours}
Number of Employees: {employees_line}
Maximum Customers:  {customers_line}

3.4 Estimated Cost
------------------
Cost of Works:      {cost_line}
DA Lodgement Fee:   {fee_line}

================================================================================
4. PLANNING FRAMEWORK ASSESSMENT
================================================================================

4.1 Lismore Local Environmental Plan 2012
------------------------------------------

4.1.1 Zoning
The site is zoned {zone_code} - {zone_name} under Lismore LEP 2012.

Zone Objectives:
{chr(10).join(f"• {obj}" for obj in zone_objectives[:3]) if zone_objectives else "[REFER TO LEP]"}

4.1.2 Permissibility
{permissibility_detail if permissibility_detail else f"The proposed {proposed_use} is {permissibility.lower()} in Zone {zone_code}."}

Development consent is required for this proposal.

4.1.3 Development Standards
Height:             {"Not applicable - no external works" if development_type in ["change_of_use", "fitout"] else "[CHECK HEIGHT MAP]"}
Floor Space Ratio:  {"Not applicable - no increase in GFA" if development_type in ["change_of_use", "fitout"] else "[CHECK FSR MAP]"}

{"4.1.4 Clause 5.21 - Flood Planning" if is_flood else ""}
{"The site is within the flood planning area. The proposal:" if is_flood else ""}
{"• Does not increase the intensity of use significantly" if is_flood else ""}
{"• Maintains existing floor levels" if is_flood else ""}
{"• Does not impede flood flows" if is_flood else ""}
{"[APPLICANT: Confirm floor level relative to Flood Planning Level]" if is_flood else ""}

{"4.1.5 Heritage" if is_heritage else ""}
{"The property is identified as a heritage item / within a heritage conservation area." if is_heritage else ""}
{"The proposal involves internal works only with no impact on heritage significance." if is_heritage else ""}
{"[APPLICANT: Prepare Heritage Impact Statement if external works proposed]" if is_heritage else ""}

4.2 Lismore Development Control Plan
-------------------------------------

4.2.1 Chapter 2 - Commercial Development
The proposal is consistent with the objectives of commercial development in the
Lismore CBD, providing active street frontage and contributing to the vitality
of the commercial centre.

4.2.2 Chapter 7 - Off-Street Car Parking
Parking Requirement: {parking_rate}
Required Spaces:     {required_parking}
Existing Spaces:     {existing_parking}
{"Parking Compliance: The existing parking provision is adequate for the proposed use." if existing_parking >= (required_parking if isinstance(required_parking, int) else 0) else "Parking Shortfall: [APPLICANT TO ADDRESS - consider CBD location, shared parking, contribution in lieu]"}

4.3 State Environmental Planning Policies
-----------------------------------------
The proposal has been assessed against relevant SEPPs. No SEPPs preclude the
granting of consent.

================================================================================
5. ENVIRONMENTAL IMPACT ASSESSMENT
================================================================================

5.1 Visual Impact
-----------------
{"The proposal involves internal works only with no change to the external appearance of the building. There is no adverse visual impact." if development_type in ["change_of_use", "fitout"] else "[ASSESS VISUAL IMPACT OF PROPOSED WORKS]"}

5.2 Traffic and Parking
-----------------------
The proposed {proposed_use.lower()} will generate {traffic_scale} traffic movements
consistent with the commercial nature of the area.

The site is located within the Lismore CBD with access to {"on-street parking, " if zone_code == "E2" else ""}public
transport, and pedestrian connections.

5.3 Noise and Amenity
---------------------
The proposed hours of operation ({hours}) are consistent with
the commercial character of the area. {"No amplified music or entertainment is proposed." if "cafe" in proposed_use.lower() or "restaurant" in proposed_use.lower() else ""}

Noise impacts will be limited to {"normal cafe/restaurant operations including customer conversation and kitchen equipment" if "cafe" in proposed_use.lower() or "restaurant" in proposed_use.lower() else "normal business operations"}.

5.4 Waste Management
--------------------
{"Food waste and general waste will be stored in appropriate bins within the premises and collected by a licensed waste contractor." if "cafe" in proposed_use.lower() or "restaurant" in proposed_use.lower() or "food" in proposed_use.lower() else "Waste will be managed in accordance with Council requirements."}

5.5 Stormwater and Drainage
---------------------------
{"No changes to existing stormwater or drainage arrangements." if development_type in ["change_of_use", "fitout"] else "[APPLICANT TO ADDRESS STORMWATER MANAGEMENT]"}

================================================================================
6. SECTION 4.15 MATTERS FOR CONSIDERATION
================================================================================

(a)(i) Environmental Planning Instruments
The proposal is consistent with Lismore LEP 2012. The use is permissible
with consent in the {zone_code} zone.

(a)(ii) Draft Environmental Planning Instruments
No draft EPIs affect this application.

(a)(iii) Development Control Plans
The proposal is consistent with the relevant provisions of Lismore DCP.

(a)(iiia) Planning Agreements
Not applicable.

(a)(iv) Regulations
The proposal complies with the EP&A Regulation 2021.

(b) Likely Impacts
The proposal will have positive economic impacts through job creation and
service provision. Environmental impacts are minimal given the {"internal nature of the works" if development_type in ["change_of_use", "fitout"] else "scale and nature of the proposal"}.

(c) Suitability of the Site
The site is suitable for the proposed development, being located within a
{"commercial centre with supporting infrastructure" if zone_code == "E2" else "zone that permits the proposed use"}.

(d) Submissions
To be addressed following public exhibition (if required).

(e) Public Interest
The proposal is in the public interest as it:
• Provides employment opportunities
• Contributes to the {"vitality of the CBD" if zone_code == "E2" else "local economy"}
• Is consistent with the objectives of the zone
• Has minimal environmental impact

================================================================================
7. CONCLUSION
================================================================================

This Statement of Environmental Effects demonstrates that the proposed
{proposed_use.lower()} at {property_address} is appropriate and warrants
the granting of development consent.

The proposal:
• Is permissible in the {zone_code} - {zone_name} zone
• Complies with the relevant provisions of Lismore LEP 2012
• Is consistent with Lismore Development Control Plan
• Will have minimal environmental impact
• Is in the public interest

It is requested that Council approve this Development Application.

================================================================================
                              END OF DOCUMENT
================================================================================

NOTES FOR APPLICANT:
--------------------
1. Replace all [BRACKETED TEXT] with actual information
2. Attach required plans and supporting documents
3. Verify all information before lodgement
4. Consult Duty Planner if uncertain about any requirements
   - Available: Tuesdays and Thursdays, 8:30am-10:30am
   - Location: Corporate Centre, Goonellabah
   - Phone: (02) 6625 0500

Generated by: Lismore DA MCP Server
"""

        return [TextContent(
            type="text",
            text=see_document
        )]

    elif name in ("preview_see_form", "fill_see_pdf"):
        shared_keys = (
            "applicant_name", "property_address", "lot_dp", "zone_code", "proposed_use",
            "development_type", "floor_area_sqm", "minor_development_type",
            "building_description", "site_description", "surrounding_context", "existing_use",
            "hours_of_operation", "num_employees", "num_customers", "estimated_cost",
            "is_flood_affected", "is_bushfire_prone", "is_heritage", "in_heritage_conservation_area",
            "internal_works_only", "parking_spaces_provided", "stormwater_to_council_system",
            "unit", "street_number", "street", "suburb", "building_name",
            "lot", "plan_type", "plan_number", "section", "answers", "comments",
        )
        kwargs = {key: arguments[key] for key in shared_keys if key in arguments}
        result = generate_see_form_data(**kwargs)

        form_data = result["fields"]
        unanswered = result["unanswered_questions"]
        blocking = result["blocking_issues"]

        # The form cannot be written while a scope or identification issue stands.
        if blocking:
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "blocking_issues": blocking,
                "purpose_written_see_headings": (
                    PURPOSE_WRITTEN_SEE_HEADINGS
                    if any("Minor Development Only" in issue for issue in blocking) else None
                ),
                "template_scope": SEE_TEMPLATE_SCOPE,
                "next_step": "Resolve the issues above, or use generate_see_draft to build a purpose-written SEE.",
            }, indent=2))]

        summary = {
            "applicant": form_data["applicant_name"],
            "premises": " ".join(p for p in (
                form_data["address_number"], form_data["street_name"], form_data["suburb"]) if p),
            "land": " ".join(p for p in (
                f"Lot {form_data['lot']}" if form_data["lot"] else "",
                # the form's box is labelled DP, so a deposited plan carries no prefix there
                f"DP {form_data['dp']}" if form_data["dp"].isdigit() else form_data["dp"]) if p),
            "development_type": arguments.get("minor_development_type"),
            "questions_answered": len(SEE_QUESTIONS) - len([q for q in unanswered if q["key"] in SEE_QUESTIONS]),
            "questions_total": len(SEE_QUESTIONS),
        }

        if name == "preview_see_form":
            # Every field that will be written, so review sees exactly what the PDF gets.
            ticks = {
                key: ("Yes" if form_data.get(f"{key}_yes") else "No" if form_data.get(f"{key}_no") else "— unanswered")
                for key in SEE_QUESTIONS
            }
            for key, label in (("flooding", "flooding"), ("bushfire_prone", "bushfire prone"),
                               ("stormwater_council", "stormwater to Council system")):
                value = form_data.get(key)
                ticks[label] = "Yes" if value else "No" if value is False else "— unanswered"

            return [TextContent(type="text", text=json.dumps({
                "summary": summary,
                "text_fields": {
                    key: value for key, value in form_data.items()
                    if not key.endswith(("_yes", "_no")) and isinstance(value, str) and value
                },
                "empty_text_fields": [
                    key for key, value in form_data.items()
                    if not key.endswith(("_yes", "_no")) and isinstance(value, str) and not value
                ],
                "tick_boxes": ticks,
                "derived_answers": result["derived_answers"],
                "unanswered_questions": unanswered,
                "parking": result["parking"],
                "required_documents": result["required_documents"],
                "next_step": (
                    "Collect answers to the unanswered questions and re-send them in `answers`/`comments`, "
                    "then call fill_see_pdf. Unanswered questions are left blank on the form."
                ),
            }, indent=2))]

        # --- fill_see_pdf ------------------------------------------------------
        # Sanitize unconditionally: .name strips any directory components (including
        # absolute paths and ../ traversal), so this can only ever resolve to a bare
        # filename inside the directory we choose below.
        output_filename = Path(arguments.get("output_filename") or "SEE_filled.pdf").name
        if not output_filename or output_filename in (".", ".."):
            output_filename = "SEE_filled.pdf"
        if not output_filename.endswith(".pdf"):
            output_filename += ".pdf"

        tmp_dir: Path | None = None
        if PUBLIC_MODE:
            tmp_dir = Path(tempfile.mkdtemp(prefix="see_"))
            output_path = tmp_dir / output_filename
        else:
            output_dir = DOCS_DIR / "output"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / output_filename

        fill_result = fill_see_pdf(form_data, output_path)
        if not fill_result["success"]:
            if tmp_dir is not None:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": fill_result.get("error", "Failed to fill PDF."),
                "template_path": str(SEE_TEMPLATE_PATH),
            }, indent=2))]

        notes = [
            "Answer every blank question by hand before lodging — blanks are questions, not answers of 'No'",
            "Sign and date the declaration on page 7",
            "Lodge via NSW Planning Portal",
        ]
        if fill_result["overflowed_fields"]:
            notes.insert(0, (
                "Text longer than the printed box, trimmed to fit: "
                + ", ".join(fill_result["overflowed_fields"])
                + ". Continue it on an attachment; page 1's supporting-information box has been ticked."
            ))
        if fill_result["unresolved_fields"]:
            notes.insert(0, (
                "No box could be located in the template for: "
                + ", ".join(fill_result["unresolved_fields"])
                + " — complete these by hand."
            ))
        if fill_result["template_layout_changed"]:
            notes.insert(0, (
                "WARNING: the template's layout no longer matches what this tool expects ("
                + "; ".join(fill_result["template_layout_changed"])
                + "). Check every field position before lodging."
            ))

        response = {
            "success": True,
            "summary": summary,
            "unanswered_questions": unanswered,
            "derived_answers": result["derived_answers"],
            "required_documents": result["required_documents"],
            "parking": result["parking"],
            "notes": notes,
        }

        if tmp_dir is not None:
            pdf_bytes = output_path.read_bytes()
            shutil.rmtree(tmp_dir, ignore_errors=True)
            response["pdf_base64"] = base64.b64encode(pdf_bytes).decode("ascii")
            response["output_filename"] = output_filename
            notes.insert(0, "PDF returned inline as base64 (pdf_base64) — decode and save it yourself; nothing is kept on the server.")
        else:
            response["output_path"] = str(output_path)

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ============================================================================
# Server Entry Point
# ============================================================================

def main():
    """Main entry point. MCP_TRANSPORT=http serves over Streamable HTTP; anything else (or
    unset) keeps the original stdio behavior used by local .mcp.json setups."""
    if PUBLIC_MODE:
        run_http()
    else:
        import asyncio
        asyncio.run(run())


if __name__ == "__main__":
    main()
