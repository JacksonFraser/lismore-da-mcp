"""Statement of Environmental Effects: guidance, drafting and the official form."""

from pathlib import Path
import base64
import json
import shutil
import tempfile
import textwrap

from mcp.types import TextContent

from lismore_da_mcp.config import DOCS_DIR
from lismore_da_mcp.config import PUBLIC_MODE
from lismore_da_mcp.config import SEE_TEMPLATE_PATH
from lismore_da_mcp.data.parking import PARKING_RATES
from lismore_da_mcp.data.see_templates import SEE_TEMPLATES
from lismore_da_mcp.data.zones import ZONES
from lismore_da_mcp.fees import calculate_da_fee
from lismore_da_mcp.landuse import classify_land_use
from lismore_da_mcp.parking import cbd_spaces
from lismore_da_mcp.parking import estimate_spaces
from lismore_da_mcp.readiness import site_constraints as _site_constraints
from lismore_da_mcp.registry import tool
from lismore_da_mcp.see.fields import PURPOSE_WRITTEN_SEE_HEADINGS, SEE_QUESTIONS
from lismore_da_mcp.see.fields import SEE_TEMPLATE_SCOPE
from lismore_da_mcp.see.fill import fill_see_pdf
from lismore_da_mcp.see.generate import generate_see_form_data
from lismore_da_mcp.vocabulary import PARKING_SYNONYMS
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


def _flood_section(is_flood, development_type):
    """Flood always gets a section. Silence is the failure mode here.

    Much of the Lismore LGA is flood affected, the CBD was inundated in 2022,
    and the state flood layer holds no Lismore data — so a draft that simply
    omits flood is one Council comes back on.
    """
    if is_flood:
        internal = development_type in ("change_of_use", "fitout")
        return (
            "The site is within the flood planning area. LEP 2012 clause 5.21 and DCP\n"
            "    Chapter 8 apply.\n"
            "    • [APPLICANT] State the Flood Planning Level for the site and the floor level\n"
            "      of the premises relative to it. Council provides the flood level on request.\n"
            "    • [APPLICANT] Address structural soundness, and evacuation — a site-specific\n"
            "      evacuation plan is required in the CBD exemption precinct.\n"
            "    • [APPLICANT] Address flood storage and conveyance, and the handling of\n"
            "      stock, plant and hazardous materials in a flood."
            + ("\n    • The proposal involves no external works and does not alter flood flows."
               if internal else "")
        )
    if is_flood is False:
        return (
            "The applicant has advised the site is not within the flood planning area.\n"
            "    [APPLICANT] Confirm this against Council's flood mapping and retain the\n"
            "    confirmation — much of the LGA is affected and the flood provisions are\n"
            "    under review."
        )
    return (
        "[APPLICANT TO COMPLETE — DO NOT LEAVE BLANK] Flood has not been established for\n"
        "    this site. Much of the Lismore LGA is flood affected, the CBD was inundated in\n"
        "    2022, and the NSW state flood layer holds no Lismore data, so it cannot rule\n"
        "    flooding out. Obtain the Flood Planning Level from Council, state the floor\n"
        "    level relative to it, and address clause 5.21 and DCP Chapter 8. A SEE that is\n"
        "    silent on flood is a common reason for a request for information."
    )


def _heritage_section(is_heritage):
    if is_heritage:
        return (
            "The site is a heritage item or within a heritage conservation area.\n"
            "    A Heritage Impact Statement is required (DCP Chapter 12). The impact on\n"
            "    heritage significance must be assessed, not assumed.\n"
            "    • [APPLICANT] Address any external change — shopfront, awning, signage,\n"
            "      colours, materials — which is where heritage objections usually arise."
        )
    if is_heritage is False:
        return "The site is not a heritage item and is not within a heritage conservation area."
    return (
        "[APPLICANT TO COMPLETE] Heritage status has not been established. Check the LEP\n"
        "    2012 Schedule 5 listing and the heritage map, or use lookup_site_constraints."
    )


def _parking_section(proposed_use, floor_area, existing_parking, num_employees,
                     zone_code=None):
    """Parking from the DCP rate, or an honest refusal — never an assumed pass.

    This section used to resolve the rate by hand (`proposed_use.replace(" ", "_")`,
    with a special case for café) and then read the space count out of the rate's
    prose with a substring test for "10m". Any rate that was not a plain area
    rate — the café rule among them — fell through to a "[CALCULATE BASED ON DCP]"
    placeholder, and the compliance line below it compared the spaces provided
    against `0`, because a string is not an int. So an 80m² café with no on-site
    parking was told "the existing parking provision is adequate for the proposed
    use" against a real requirement of 14 spaces — in a document that goes to
    Council over the applicant's name.

    `estimate_spaces` is the same estimator get_parking_rates and the Council
    form use, so all three now agree. Where it declines to produce a figure, so
    does this: an unstated requirement is left to the applicant rather than
    quietly treated as met.

    Schedule 1 is only the rate *outside* the CBD (§7.7.2). Inside it §7.7.3.1
    substitutes a flat 3.3/100m², which for the same 80m² café is 3 spaces
    against Schedule 1's 14 — before the §7.7.3.4 credit. Nothing here can
    place the site: Map 1 is a bitmap, and the E2 zone is close to the boundary
    but is not the boundary. So on an E2 site this states both figures and
    refuses to assert a shortfall, rather than writing a number into a document
    that goes to Council over the applicant's name and may be four times too
    high.
    """
    match = resolve(proposed_use or "", PARKING_RATES, PARKING_SYNONYMS)
    entry = PARKING_RATES.get(match.key) if match else None
    existing_line = (
        f"Existing Spaces:     {existing_parking}" if existing_parking is not None
        else "Existing Spaces:     [NOT STATED]"
    )

    if not entry:
        return (
            "Parking Requirement: no DCP Chapter 7 rate could be matched to this use.\n"
            f"    {existing_line}\n"
            "    [APPLICANT TO COMPLETE] Identify the applicable rate in DCP Chapter 7\n"
            "    Schedule 1, state the requirement and the spaces provided, and address any\n"
            "    shortfall. Parking is one of the things a Council assessment argues about."
        )

    lines = [f"Parking Requirement: {entry['rate']}"]
    estimate = estimate_spaces(entry, floor_area or None, {"employees": num_employees or 0})

    if not estimate:
        lines.append("Required Spaces:     [APPLICANT TO CALCULATE — see the rate above]")
        lines.append(existing_line)
        lines.append(
            "[APPLICANT TO COMPLETE] The rate above cannot be turned into a space count from\n"
            "    the details supplied, so no compliance is claimed here. Work it out against\n"
            "    DCP Chapter 7 Schedule 1 and address any shortfall."
        )
        return "\n    ".join(lines)

    required = estimate["spaces_required"]

    # An E2 site may or may not be inside the CBD as Map 1 draws it, and the two
    # rates can differ by more than a factor of four. Asserting either one would
    # be inventing the answer to a question this repo cannot settle — but
    # declining to assess at all would give up the guarantee that matters most
    # here, that a shortfall is never written up as adequate. So both rates are
    # assessed, and the draft only defers where they actually disagree about the
    # outcome.
    cbd = cbd_spaces(floor_area or None) if zone_code == "E2" else None
    alternatives = sorted({required, cbd["spaces_required"]}) if cbd else [required]
    ambiguous = len(alternatives) > 1

    if ambiguous:
        lines.append(f"Required Spaces:     {required} (DCP Chapter 7 Schedule 1) or "
                     f"{cbd['spaces_required']} (the fixed CBD rate, clause 7.7.3.1)")
    else:
        lines.append(f"Required Spaces:     {required}")
    lines.append(f"Basis:               {'; '.join(estimate['basis'])}")
    lines.append(existing_line)

    worst, best = max(alternatives), min(alternatives)

    if existing_parking is None:
        lines.append(
            "[APPLICANT TO COMPLETE] The number of existing on-site spaces was not stated,\n"
            "    so compliance is not assessed here. State it and address any shortfall."
        )
    elif existing_parking >= worst:
        # Compliant on either reading, so which rate applies does not change the
        # conclusion and the draft can state it plainly.
        lines.append(
            f"Parking Compliance: the {existing_parking} space(s) provided meet the DCP "
            f"requirement of {required}."
            + (f" They also meet the fixed CBD rate of {cbd['spaces_required']}, so the "
               "conclusion holds whichever rate applies." if ambiguous else "")
        )
    else:
        gap = (f"between {best - existing_parking} and {worst - existing_parking} space(s), "
               f"depending on which rate applies"
               if ambiguous and existing_parking < best
               else f"{worst - existing_parking} space(s) under Schedule 1, but none under "
                    f"the fixed CBD rate" if ambiguous
               else f"{required - existing_parking} space(s)")
        lines.append(
            f"Parking Shortfall: {gap}.\n"
            "    [APPLICANT TO ADDRESS] A shortfall has to be justified in the SEE. Nearby\n"
            "    on-street or public parking is an argument for a variation, not evidence of\n"
            "    compliance; Council may also accept a contribution in lieu. Raise it with the\n"
            "    Duty Planner before lodging."
        )

    if ambiguous:
        lines.append(
            "[APPLICANT TO RESOLVE] This site is zoned E2, so it may fall within the\n"
            "    Lismore CBD as defined on Map 1 of DCP Chapter 7. Which rate applies is not\n"
            "    a detail: Schedule 1 applies outside the CBD (clause 7.7.2) and gives\n"
            f"    {required} space(s), while inside it the fixed rate of 3.3 spaces/100m² GFA\n"
            f"    (clause 7.7.3.1) gives {cbd['spaces_required']}. If the site is in the CBD, a\n"
            "    deemed parking credit for the existing building (clause 7.7.3.4) reduces the\n"
            "    requirement further, and a shortfall may be met by a contribution in lieu\n"
            "    rather than by construction (clause 7.7.3.3). Confirm the site's position on\n"
            "    Map 1 with the Duty Planner, then state the applicable requirement here."
        )

    if estimate.get("caveat"):
        # Wrapped to the document's rule width. The café caveat is a paragraph
        # explaining which reading of Schedule 1's "(whichever is greater)" the
        # figure above follows, and as one unbroken line it is the thing an
        # applicant scrolls past rather than reads.
        lines.append("\n    ".join(
            textwrap.wrap(f"Note: {estimate['caveat']}", width=76,
                          subsequent_indent="  ")
        ))

    return "\n    ".join(lines)


def _bushfire_section(is_bushfire):
    if is_bushfire:
        return (
            "The site is on bushfire prone land. Planning for Bushfire Protection applies,\n"
            "    a bushfire assessment is required, and the development may be integrated\n"
            "    development requiring referral to the RFS."
        )
    if is_bushfire is False:
        return "The site is not mapped as bushfire prone land."
    return "[APPLICANT TO COMPLETE] Bushfire prone status has not been established."


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
    # property_address, zone_code, proposed_use, development_type and
    # floor_area_sqm are declared required, and validate_arguments rejects a call
    # that omits one or sends it empty — so they are read directly. Defaulting
    # them here would only mask that gate if it ever regressed.
    property_address = arguments["property_address"]
    zone_code = arguments["zone_code"].upper()
    proposed_use = arguments["proposed_use"]
    development_type = arguments["development_type"]
    floor_area = arguments["floor_area_sqm"]

    lot_dp = arguments.get("lot_dp", "[LOT/DP NOT PROVIDED]")
    site_area = arguments.get("site_area_sqm", "[NOT PROVIDED]")
    existing_use = arguments.get("existing_use", "Vacant/Unknown")
    building_description = arguments.get("building_description", "[NOT PROVIDED]")
    hours = arguments.get("hours_of_operation", "[NOT PROVIDED]")
    num_employees = arguments.get("num_employees")
    num_customers = arguments.get("num_customers")
    employees_line = num_employees if num_employees is not None else "[NOT PROVIDED]"
    customers_line = num_customers if num_customers is not None else "[NOT PROVIDED]"
    estimated_cost = arguments.get("estimated_cost", 0)
    # Constraints. The caller may assert them; where they have not,
    # look them up from the address rather than writing a draft that is
    # silent about the site it is for. PLAN.md 1.2: a café SEE for a CBD
    # address previously mentioned flood zero times, and a SEE that does
    # not address flood in Lismore is one Council comes back on.
    is_flood, is_heritage, is_bushfire, constraint_note = _site_constraints(
        property_address,
        arguments.get("is_flood_affected"),
        arguments.get("is_heritage"),
    )
    # Left as None when not supplied. Defaulting to 0 would state a fact about
    # the site the applicant never gave, and the parking section declines to
    # assess compliance against an unstated figure rather than assuming one.
    existing_parking = arguments.get("existing_parking_spaces")
    applicant_name = arguments.get("applicant_name", "[APPLICANT NAME]")

    # Get zone information
    zone_info = ZONES.get(zone_code, {})
    zone_name = zone_info.get("name", "Unknown Zone")
    zone_objectives = zone_info.get("objectives", [])

    # The prose below varies on these rather than re-testing the same substrings
    # at each use, which is how "cafe" came to be checked four separate ways and
    # how an accented "café" slipped past all of them.
    proposed_use_lower = proposed_use.lower().strip().replace("é", "e")
    in_cbd = zone_code == "E2"
    internal_only = development_type in ("change_of_use", "fitout")
    is_food_premises = any(w in proposed_use_lower for w in ("cafe", "restaurant"))
    generates_food_waste = is_food_premises or "food" in proposed_use_lower

    # Permissibility from the shared classifier, so this draft and
    # check_permissibility can't disagree about the same land use
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

    parking_block = _parking_section(
        proposed_use, floor_area, existing_parking, num_employees, zone_code
    )

    traffic_scale = (
        "minimal" if isinstance(num_customers, (int, float)) and num_customers <= 20
        else "moderate" if isinstance(num_customers, (int, float))
        else "[TO BE ASSESSED]"
    )

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

    2.3 Site Constraints
    --------------------
    Flood:      {"Within the flood planning area" if is_flood else ("Applicant advises not flood affected - verify with Council" if is_flood is False else "NOT ESTABLISHED - see 4.1.4. Cannot be ruled out from mapping alone in this LGA")}
    Heritage:   {"Heritage item or conservation area" if is_heritage else ("Not a heritage item or conservation area" if is_heritage is False else "Not established")}
    Bushfire:   {"Bushfire prone land" if is_bushfire else ("Not mapped as bushfire prone" if is_bushfire is False else "Not established")}

    {constraint_note}

    2.4 Surrounding Context
    -----------------------
    The site is located within the {zone_name} zone. The surrounding area is
    characterised by {"commercial and retail uses typical of the Lismore CBD" if in_cbd else "uses consistent with the " + zone_name + " zone"}.

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
    Height:             {"Not applicable - no external works" if internal_only else "[CHECK HEIGHT MAP]"}
    Floor Space Ratio:  {"Not applicable - no increase in GFA" if internal_only else "[CHECK FSR MAP]"}

    4.1.4 Clause 5.21 - Flood Planning
    {_flood_section(is_flood, development_type)}

    4.1.5 Heritage
    {_heritage_section(is_heritage)}

    4.1.6 Bushfire
    {_bushfire_section(is_bushfire)}

    4.2 Lismore Development Control Plan
    -------------------------------------

    4.2.1 Chapter 2 - Commercial Development
    The proposal is consistent with the objectives of commercial development in the
    Lismore CBD, providing active street frontage and contributing to the vitality
    of the commercial centre.

    4.2.2 Chapter 7 - Off-Street Car Parking
    {parking_block}

    4.3 State Environmental Planning Policies
    -----------------------------------------
    [APPLICANT TO COMPLETE] The SEPPs relevant to this proposal must be identified and
    addressed. Which apply depends on the use and the site - commonly the Housing SEPP,
    the Exempt and Complying Development Codes, Transport and Infrastructure, Resilience
    and Hazards (contamination, clause 4.6 of Chapter 4 applies to a change to a more
    sensitive use), and Industry and Employment for advertising. Do not state that no
    SEPP precludes consent unless that has actually been checked.

    ================================================================================
    5. ENVIRONMENTAL IMPACT ASSESSMENT
    ================================================================================

    5.1 Visual Impact
    -----------------
    {"The proposal involves internal works only with no change to the external appearance of the building. There is no adverse visual impact." if internal_only else "[ASSESS VISUAL IMPACT OF PROPOSED WORKS]"}

    5.2 Traffic and Parking
    -----------------------
    The proposed {proposed_use.lower()} will generate {traffic_scale} traffic movements
    consistent with the commercial nature of the area.

    The site is located within the Lismore CBD with access to {"on-street parking, " if in_cbd else ""}public
    transport, and pedestrian connections.

    5.3 Noise and Amenity
    ---------------------
    The proposed hours of operation ({hours}) are consistent with
    the commercial character of the area. {"No amplified music or entertainment is proposed." if is_food_premises else ""}

    Noise impacts will be limited to {"normal cafe/restaurant operations including customer conversation and kitchen equipment" if is_food_premises else "normal business operations"}.

    5.4 Waste Management
    --------------------
    {"Food waste and general waste will be stored in appropriate bins within the premises and collected by a licensed waste contractor." if generates_food_waste else "Waste will be managed in accordance with Council requirements."}

    5.5 Stormwater and Drainage
    ---------------------------
    {"No changes to existing stormwater or drainage arrangements." if internal_only else "[APPLICANT TO ADDRESS STORMWATER MANAGEMENT]"}

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
    service provision. Environmental impacts are minimal given the {"internal nature of the works" if internal_only else "scale and nature of the proposal"}.

    (c) Suitability of the Site
    The site is suitable for the proposed development, being located within a
    {"commercial centre with supporting infrastructure" if in_cbd else "zone that permits the proposed use"}.

    (d) Submissions
    To be addressed following public exhibition (if required).

    (e) Public Interest
    The proposal is in the public interest as it:
    • Provides employment opportunities
    • Contributes to the {"vitality of the CBD" if in_cbd else "local economy"}
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


# --- the official form's arguments ------------------------------------------
#
# preview_see_form and fill_see_pdf take exactly the same input: one shows what
# will be written, the other writes it. `_see_form()` already keeps their
# *behaviour* in step, for the reason given in its docstring — a preview that
# did not match what got written would be worse than no preview. This keeps
# their *schemas* in step too. They were 37 identical lines duplicated across
# both decorators, differing only in fill's extra output_filename, with nothing
# to stop an edit landing in one and not the other.

_SEE_FORM_NOTE = (
    ' A complete call needs only the eight required arguments — the address and'
    ' lot/DP components are parsed out of property_address and lot_dp, and the'
    ' optional arguments refine the answers rather than being needed to get one.'
)

_SEE_FORM_REQUIRED = ['applicant_name', 'property_address', 'lot_dp', 'zone_code', 'proposed_use', 'development_type', 'floor_area_sqm', 'minor_development_type']

_SEE_FORM_PROPERTIES = {
'applicant_name': {'type': 'string', 'description': 'Full name of the applicant'},
'minor_development_type': {'type': 'string', 'description': 'REQUIRED. Which of the four development types this Council template covers: dwelling_single_storey, residential_addition_single_storey, ancillary_residential_structure, strata_subdivision. Plain wording is accepted and resolved - "shed", "carport", "pool", "extension", "single storey dwelling". Anything outside that scope (commercial work, change of use, multi-storey) cannot use this form - build a purpose-written SEE with generate_see_draft instead.'},
'property_address': {'type': 'string', 'description': "Full street address, e.g. '45 Keen Street, Lismore NSW 2480' or 'Shop 3, 88 Keen Street, Lismore NSW 2480'. This is normally all that is needed: unit, street_number, street and suburb are parsed out of it. Supply those separately only to correct a parse."},
'unit': {'type': 'string', 'description': "Optional override. Derived from property_address when omitted. Tenancy identifier if any, e.g. 'Shop 3', 'Unit 2'"},
'street_number': {'type': 'string', 'description': "Optional override. Derived from property_address when omitted. Street number only, e.g. '88' or '5-7'"},
'street': {'type': 'string', 'description': "Optional override. Derived from property_address when omitted. Street name only, e.g. 'Keen Street'"},
'suburb': {'type': 'string', 'description': 'Optional override. Derived from property_address when omitted — but a single-segment address like "Keen Street" has nothing identifying a suburb, so supply it there. Suburb only, without NSW or postcode'},
'building_name': {'type': 'string', 'description': 'Building name, if known'},
'lot_dp': {'type': 'string', 'description': "Land identifier as text, e.g. 'Lot 12 DP 758651', 'Lot 5 Section 3 DP 1234' or 'SP 12345'. This is normally all that is needed: lot, plan_type, plan_number and section are parsed out of it. Supply those separately only to correct a parse. The form is not generated without a plan number."},
'lot': {'type': 'string', 'description': 'Optional override. Derived from lot_dp when omitted. Lot number on its own'},
'plan_type': {'type': 'string', 'description': 'Optional override. Derived from lot_dp when omitted. DP (Deposited), SP (Strata) or CP (Community) plan; case is normalised'},
'plan_number': {'type': 'string', 'description': "Optional override. Derived from lot_dp when omitted. Plan number on its own, e.g. '758651'"},
'section': {'type': 'string', 'description': 'Optional override. Derived from lot_dp when omitted. Section number, if the land has one'},
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
}

# Only fill writes a file, so only fill takes a filename.
_FILL_ONLY_PROPERTIES = {
    'output_filename': {'type': 'string', 'description': "Output filename only — any path component is stripped. When running locally over stdio, saved to documents/output/; when served publicly over HTTP, returned inline as base64 and never written to disk. Default: 'SEE_filled.pdf'"},
}


@tool(
    name='preview_see_form',
    description='Preview exactly what will be written into the official Lismore SEE PDF, including every tick. Shows the questions still unanswered and any issue that blocks the form being generated. Review this before calling fill_see_pdf.' + _SEE_FORM_NOTE,
    properties=dict(_SEE_FORM_PROPERTIES),
    required=_SEE_FORM_REQUIRED,
)
def preview_see_form(arguments: dict):
    return _see_form(arguments, "preview_see_form")


@tool(
    name='fill_see_pdf',
    description="Fill the official Lismore SEE PDF form and save it. Refuses proposals outside the template's 'Minor Development Only' scope, and refuses to write a blank land identifier. Questions the applicant has not answered are left blank and reported rather than guessed. Run preview_see_form first." + _SEE_FORM_NOTE,
    properties={**_SEE_FORM_PROPERTIES, **_FILL_ONLY_PROPERTIES},
    required=_SEE_FORM_REQUIRED,
)
def fill_see_pdf_tool(arguments: dict):
    return _see_form(arguments, "fill_see_pdf")
