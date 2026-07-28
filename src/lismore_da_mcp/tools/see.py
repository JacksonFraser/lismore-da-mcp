"""Statement of Environmental Effects: guidance, drafting and the official form."""

from pathlib import Path
import base64
import json
import shutil
import tempfile

from mcp.types import TextContent

from lismore_da_mcp.config import DOCS_DIR
from lismore_da_mcp.config import PUBLIC_MODE
from lismore_da_mcp.config import SEE_TEMPLATE_PATH
from lismore_da_mcp.data.flood import FLOOD_PLANNING
from lismore_da_mcp.data.parking import PARKING_RATES
from lismore_da_mcp.data.see_templates import SEE_TEMPLATES
from lismore_da_mcp.data.zones import ZONES
from lismore_da_mcp.fees import calculate_da_fee
from lismore_da_mcp.landuse import classify_land_use
from lismore_da_mcp.registry import tool
from lismore_da_mcp.see.fields import PURPOSE_WRITTEN_SEE_HEADINGS, SEE_QUESTIONS
from lismore_da_mcp.see.fields import SEE_TEMPLATE_SCOPE
from lismore_da_mcp.see.fill import fill_see_pdf
from lismore_da_mcp.see.generate import generate_see_form_data
from lismore_da_mcp.vocabulary import SEE_SECTION_SYNONYMS
from lismore_da_mcp.vocabulary import resolve
from lismore_da_mcp.vocabulary import unresolved_error


@tool(
    name='get_see_template',
    description='Get Statement of Environmental Effects (SEE) section template with prompts for what to include. Returns structured guidance for writing each section of an SEE.',
    properties={
        'section': {'type': 'string', 'description': "SEE section: 'site_description', 'proposal_description', 'planning_framework', 'environmental_impacts', 'mitigation_measures', 'section_4_15_matters', or 'all'"},
    },
    required=['section'],
)
def get_see_template(arguments: dict):
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


@tool(
    name='generate_see_draft',
    description='Generate a draft Statement of Environmental Effects (SEE) document based on proposal details. Automatically pulls in zone information, parking requirements, flood planning, and other relevant data to create a structured SEE ready for review and refinement.',
    properties={
        'property_address': {'type': 'string', 'description': 'Street address of the property'},
        'lot_dp': {'type': 'string', 'description': "Lot and DP number (e.g., 'Lot 1 DP 123456')"},
        'zone_code': {'type': 'string', 'description': "Zone code (e.g., 'E2', 'R1', 'MU1')"},
        'site_area_sqm': {'type': 'number', 'description': 'Site area in square metres'},
        'existing_use': {'type': 'string', 'description': 'Current/existing use of the property'},
        'proposed_use': {'type': 'string', 'description': "Proposed land use (e.g., 'restaurant or cafe', 'shop', 'dwelling house')"},
        'development_type': {'type': 'string', 'description': "Type of development: 'new_building', 'alteration', 'change_of_use', 'fitout'"},
        'floor_area_sqm': {'type': 'number', 'description': 'Gross floor area of the proposal in square metres'},
        'building_description': {'type': 'string', 'description': "Description of proposed works (e.g., 'Internal fitout for cafe with kitchen, counter, and 8-seat dining area')"},
        'hours_of_operation': {'type': 'string', 'description': "Proposed hours of operation (e.g., '7am-4pm Monday to Saturday')"},
        'num_employees': {'type': 'integer', 'description': 'Number of employees'},
        'num_customers': {'type': 'integer', 'description': 'Maximum number of customers/patrons at any time'},
        'estimated_cost': {'type': 'number', 'description': 'Estimated cost of development works in dollars'},
        'is_flood_affected': {'type': 'boolean', 'description': 'Is the property within the flood planning area?'},
        'is_heritage': {'type': 'boolean', 'description': 'Is the property a heritage item or in a heritage conservation area?'},
        'existing_parking_spaces': {'type': 'integer', 'description': 'Number of existing on-site parking spaces (0 if none)'},
        'applicant_name': {'type': 'string', 'description': 'Name of the applicant'},
    },
    required=['property_address', 'zone_code', 'proposed_use', 'development_type', 'floor_area_sqm'],
)
def generate_see_draft(arguments: dict):
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


def _see_form(arguments: dict, name: str):
    """Shared implementation for preview_see_form and fill_see_pdf.

    The two differ only in what they do with the generated form data, and
    `name` selects which. Kept as one function so the scope checks, blocking
    issues and field derivation cannot drift between preview and fill — a
    preview that did not match what got written would be worse than none.
    """
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
            # Present on both paths. This tool used to return success=False when
            # it refused and omit the key entirely when it worked, so a caller
            # checking response["success"] saw None on the happy path and could
            # reasonably read it as failure.
            "success": True,
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


@tool(
    name='preview_see_form',
    description='Preview exactly what will be written into the official Lismore SEE PDF, including every tick. Shows the questions still unanswered and any issue that blocks the form being generated. Review this before calling fill_see_pdf.',
    properties={
        'applicant_name': {'type': 'string', 'description': 'Full name of the applicant'},
        'minor_development_type': {'type': 'string', 'enum': ['dwelling_single_storey', 'residential_addition_single_storey', 'ancillary_residential_structure', 'strata_subdivision'], 'description': 'REQUIRED. Which of the four development types this Council template covers. Anything outside this list (commercial work, change of use, multi-storey) cannot use this form - build a purpose-written SEE with generate_see_draft instead.'},
        'property_address': {'type': 'string', 'description': "Full street address, e.g. '45 Keen Street, Lismore NSW 2480'. Prefer the separate unit/street_number/street/suburb fields where the address has a shop or unit number."},
        'unit': {'type': 'string', 'description': "Tenancy identifier if any, e.g. 'Shop 3', 'Unit 2'"},
        'street_number': {'type': 'string', 'description': "Street number only, e.g. '88' or '5-7'"},
        'street': {'type': 'string', 'description': "Street name only, e.g. 'Keen Street'"},
        'suburb': {'type': 'string', 'description': 'Suburb only, without NSW or postcode'},
        'building_name': {'type': 'string', 'description': 'Building name, if known'},
        'lot_dp': {'type': 'string', 'description': "Land identifier as text, e.g. 'Lot 12 DP 758651' or 'SP 12345'. Prefer lot/plan_type/plan_number. The form is not generated without a plan number."},
        'lot': {'type': 'string', 'description': 'Lot number on its own'},
        'plan_type': {'type': 'string', 'enum': ['DP', 'SP', 'CP'], 'description': 'Deposited, Strata or Community plan'},
        'plan_number': {'type': 'string', 'description': "Plan number on its own, e.g. '758651'"},
        'section': {'type': 'string', 'description': 'Section number, if the land has one'},
        'zone_code': {'type': 'string', 'description': "Zone code under Lismore LEP 2012, e.g. 'R1', 'E2'. Employment zones replaced the B-series codes in 2023."},
        'proposed_use': {'type': 'string', 'description': "Proposed land use, e.g. 'dwelling house', 'shed'"},
        'development_type': {'type': 'string', 'description': "Type: 'new_building', 'alteration', 'change_of_use', 'fitout'"},
        'floor_area_sqm': {'type': 'number', 'description': 'Floor area in square metres'},
        'building_description': {'type': 'string', 'description': "Description of the proposed works, in the applicant's own words. Used verbatim as the description of development."},
        'site_description': {'type': 'string', 'description': 'Physical description of the site: shape, slope, vegetation, waterways'},
        'surrounding_context': {'type': 'string', 'description': 'Land uses and development on surrounding land'},
        'existing_use': {'type': 'string', 'description': 'Present and previous use of the site'},
        'hours_of_operation': {'type': 'string', 'description': 'Proposed operating hours, where the use has any'},
        'num_employees': {'type': 'integer', 'description': 'Number of employees'},
        'num_customers': {'type': 'integer', 'description': 'Maximum customers at any time'},
        'estimated_cost': {'type': 'number', 'description': 'Estimated cost of works in dollars'},
        'is_flood_affected': {'type': 'boolean', 'description': 'Is the site flood prone? Omit if unknown - the tick is then left blank rather than guessed.'},
        'is_bushfire_prone': {'type': 'boolean', 'description': 'Is the site bushfire prone? Omit if unknown.'},
        'is_heritage': {'type': 'boolean', 'description': 'Is the site a heritage item under LEP 2012 Schedule 5? Omit if unknown.'},
        'in_heritage_conservation_area': {'type': 'boolean', 'description': 'Is the site within a heritage conservation area? Omit if unknown.'},
        'internal_works_only': {'type': 'boolean', 'description': 'True if the works are wholly internal. Lets the excavation and vegetation questions be answered from that fact.'},
        'parking_spaces_provided': {'type': 'integer', 'description': 'Off-street parking spaces provided on site. Compared against the DCP Chapter 7 rate so any shortfall is stated.'},
        'stormwater_to_council_system': {'type': 'boolean', 'description': 'True if stormwater goes to the Council drainage system; false if disposed of another way (describe it in comments.stormwater_details).'},
        'answers': {'type': 'object', 'description': "The applicant's answers to the form's Yes/No questions, as {question_key: true|false}. Any question left out stays blank on the form and is returned in unanswered_questions - these are declarations signed as true, so they are never filled in on the applicant's behalf. Keys: zone_objectives, dcp_accordance, visually_prominent, inconsistent_streetscape, out_of_character, inconsistent_land_use, setback_variation, privacy_issues, overshadowing, acoustic_issues, views_impact, legal_access, increase_traffic, additional_access, parking_addressed, utilities_available, air_pollution, water_pollution, noise_impacts, excavation, erosion, contamination, sustainable, heritage_impact, aboriginal, remove_vegetation, threatened_species, effluent, trade_waste, hazardous_waste, rainwater_tanks, overland_risks, economic_social, crime_prevention, permissible."},
        'comments': {'type': 'object', 'description': "Free text for the form's comment boxes, as {field: text}. Keys: hazards_comments, constraints, surrounding_land_use, planning_comments, context_comment, privacy_comments, access_comments, environmental_comments, flora_comments, waste_comments, social_comments, other_matters, stormwater_details, traffic_amount."},
    },
    required=['applicant_name', 'property_address', 'lot_dp', 'zone_code', 'proposed_use', 'development_type', 'floor_area_sqm', 'minor_development_type'],
)
def preview_see_form(arguments: dict):
    return _see_form(arguments, "preview_see_form")


@tool(
    name='fill_see_pdf',
    description="Fill the official Lismore SEE PDF form and save it. Refuses proposals outside the template's 'Minor Development Only' scope, and refuses to write a blank land identifier. Questions the applicant has not answered are left blank and reported rather than guessed. Run preview_see_form first.",
    properties={
        'applicant_name': {'type': 'string', 'description': 'Full name of the applicant'},
        'minor_development_type': {'type': 'string', 'enum': ['dwelling_single_storey', 'residential_addition_single_storey', 'ancillary_residential_structure', 'strata_subdivision'], 'description': 'REQUIRED. Which of the four development types this Council template covers. Anything outside this list (commercial work, change of use, multi-storey) cannot use this form - build a purpose-written SEE with generate_see_draft instead.'},
        'property_address': {'type': 'string', 'description': "Full street address, e.g. '45 Keen Street, Lismore NSW 2480'. Prefer the separate unit/street_number/street/suburb fields where the address has a shop or unit number."},
        'unit': {'type': 'string', 'description': "Tenancy identifier if any, e.g. 'Shop 3', 'Unit 2'"},
        'street_number': {'type': 'string', 'description': "Street number only, e.g. '88' or '5-7'"},
        'street': {'type': 'string', 'description': "Street name only, e.g. 'Keen Street'"},
        'suburb': {'type': 'string', 'description': 'Suburb only, without NSW or postcode'},
        'building_name': {'type': 'string', 'description': 'Building name, if known'},
        'lot_dp': {'type': 'string', 'description': "Land identifier as text, e.g. 'Lot 12 DP 758651' or 'SP 12345'. Prefer lot/plan_type/plan_number. The form is not generated without a plan number."},
        'lot': {'type': 'string', 'description': 'Lot number on its own'},
        'plan_type': {'type': 'string', 'enum': ['DP', 'SP', 'CP'], 'description': 'Deposited, Strata or Community plan'},
        'plan_number': {'type': 'string', 'description': "Plan number on its own, e.g. '758651'"},
        'section': {'type': 'string', 'description': 'Section number, if the land has one'},
        'zone_code': {'type': 'string', 'description': "Zone code under Lismore LEP 2012, e.g. 'R1', 'E2'. Employment zones replaced the B-series codes in 2023."},
        'proposed_use': {'type': 'string', 'description': "Proposed land use, e.g. 'dwelling house', 'shed'"},
        'development_type': {'type': 'string', 'description': "Type: 'new_building', 'alteration', 'change_of_use', 'fitout'"},
        'floor_area_sqm': {'type': 'number', 'description': 'Floor area in square metres'},
        'building_description': {'type': 'string', 'description': "Description of the proposed works, in the applicant's own words. Used verbatim as the description of development."},
        'site_description': {'type': 'string', 'description': 'Physical description of the site: shape, slope, vegetation, waterways'},
        'surrounding_context': {'type': 'string', 'description': 'Land uses and development on surrounding land'},
        'existing_use': {'type': 'string', 'description': 'Present and previous use of the site'},
        'hours_of_operation': {'type': 'string', 'description': 'Proposed operating hours, where the use has any'},
        'num_employees': {'type': 'integer', 'description': 'Number of employees'},
        'num_customers': {'type': 'integer', 'description': 'Maximum customers at any time'},
        'estimated_cost': {'type': 'number', 'description': 'Estimated cost of works in dollars'},
        'is_flood_affected': {'type': 'boolean', 'description': 'Is the site flood prone? Omit if unknown - the tick is then left blank rather than guessed.'},
        'is_bushfire_prone': {'type': 'boolean', 'description': 'Is the site bushfire prone? Omit if unknown.'},
        'is_heritage': {'type': 'boolean', 'description': 'Is the site a heritage item under LEP 2012 Schedule 5? Omit if unknown.'},
        'in_heritage_conservation_area': {'type': 'boolean', 'description': 'Is the site within a heritage conservation area? Omit if unknown.'},
        'internal_works_only': {'type': 'boolean', 'description': 'True if the works are wholly internal. Lets the excavation and vegetation questions be answered from that fact.'},
        'parking_spaces_provided': {'type': 'integer', 'description': 'Off-street parking spaces provided on site. Compared against the DCP Chapter 7 rate so any shortfall is stated.'},
        'stormwater_to_council_system': {'type': 'boolean', 'description': 'True if stormwater goes to the Council drainage system; false if disposed of another way (describe it in comments.stormwater_details).'},
        'answers': {'type': 'object', 'description': "The applicant's answers to the form's Yes/No questions, as {question_key: true|false}. Any question left out stays blank on the form and is returned in unanswered_questions - these are declarations signed as true, so they are never filled in on the applicant's behalf. Keys: zone_objectives, dcp_accordance, visually_prominent, inconsistent_streetscape, out_of_character, inconsistent_land_use, setback_variation, privacy_issues, overshadowing, acoustic_issues, views_impact, legal_access, increase_traffic, additional_access, parking_addressed, utilities_available, air_pollution, water_pollution, noise_impacts, excavation, erosion, contamination, sustainable, heritage_impact, aboriginal, remove_vegetation, threatened_species, effluent, trade_waste, hazardous_waste, rainwater_tanks, overland_risks, economic_social, crime_prevention, permissible."},
        'comments': {'type': 'object', 'description': "Free text for the form's comment boxes, as {field: text}. Keys: hazards_comments, constraints, surrounding_land_use, planning_comments, context_comment, privacy_comments, access_comments, environmental_comments, flora_comments, waste_comments, social_comments, other_matters, stormwater_details, traffic_amount."},
        'output_filename': {'type': 'string', 'description': "Output filename only — any path component is stripped. When running locally over stdio, saved to documents/output/; when served publicly over HTTP, returned inline as base64 and never written to disk. Default: 'SEE_filled.pdf'"},
    },
    required=['applicant_name', 'property_address', 'lot_dp', 'zone_code', 'proposed_use', 'development_type', 'floor_area_sqm', 'minor_development_type'],
)
def fill_see_pdf_tool(arguments: dict):
    return _see_form(arguments, "fill_see_pdf")
