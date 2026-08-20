"""Building SEE form data from proposal details.

Derives the form's answers from what the caller supplied, refusing where the
proposal falls outside the template's "Minor Development Only" scope.
"""

from lismore_da_mcp.data.parking import PARKING_RATES
from lismore_da_mcp.data.zones import ZONES
from lismore_da_mcp.landuse import classify_land_use
from lismore_da_mcp.see.fields import (
    RESIDENTIAL_ZONES,
    SEE_COMMENT_FIELDS,
    SEE_QUESTIONS,
    SEE_TEMPLATE_SCOPE,
)
from lismore_da_mcp.vocabulary import (
    MINOR_DEVELOPMENT_SYNONYMS,
    PARKING_SYNONYMS,
    resolve,
)
from lismore_da_mcp.parking import estimate_spaces
from lismore_da_mcp.see.parsers import (
    parse_land_identifier,
    parse_street_address,
)

def generate_see_form_data(
    applicant_name: str,
    property_address: str,
    lot_dp: str,
    zone_code: str,
    proposed_use: str,
    development_type: str,
    floor_area_sqm: float,
    minor_development_type: str = "",
    building_description: str = "",
    hours_of_operation: str = "",
    num_employees: int = 0,
    num_customers: int = 0,
    estimated_cost: float = 0,
    is_flood_affected: bool | None = None,
    is_bushfire_prone: bool | None = None,
    is_heritage: bool | None = None,
    in_heritage_conservation_area: bool | None = None,
    existing_use: str = "",
    site_description: str = "",
    surrounding_context: str = "",
    unit: str = "",
    street_number: str = "",
    street: str = "",
    suburb: str = "",
    building_name: str = "",
    lot: str = "",
    plan_type: str = "",
    plan_number: str = "",
    section: str = "",
    internal_works_only: bool = False,
    parking_spaces_provided: int | None = None,
    stormwater_to_council_system: bool | None = None,
    answers: dict | None = None,
    comments: dict | None = None,
) -> dict:
    """Build the SEE form data, plus a report of what still needs answering.

    Returns {"fields", "unanswered_questions", "derived_answers", "blocking_issues",
    "parking", "required_documents"}. Nothing is ticked unless the answer was given
    in `answers` or is entailed by another supplied fact (listed in derived_answers).
    """
    answers = {k: v for k, v in (answers or {}).items() if v is not None}
    comments = {k: v.strip() for k, v in (comments or {}).items() if isinstance(v, str) and v.strip()}

    blocking: list[str] = []
    derived: dict[str, str] = {}
    required_documents: list[str] = []

    unknown_answers = sorted(set(answers) - set(SEE_QUESTIONS))
    if unknown_answers:
        blocking.append(
            "Unrecognised answer key(s): " + ", ".join(unknown_answers)
            + ". Valid keys: " + ", ".join(sorted(SEE_QUESTIONS))
        )
    unknown_comments = sorted(set(comments) - set(SEE_COMMENT_FIELDS))
    if unknown_comments:
        blocking.append(
            "Unrecognised comment key(s): " + ", ".join(unknown_comments)
            + ". Valid keys: " + ", ".join(sorted(SEE_COMMENT_FIELDS))
        )

    # --- scope: this template covers minor residential development only --------
    # Resolve loosely — "shed" and "single storey dwelling" are how an applicant
    # describes the work, not the enum. But only naming is loose: a proposal
    # outside the template's scope is still refused, because filling this form
    # for, say, a commercial fitout would produce a document Council rejects.
    scope_match = resolve(minor_development_type, SEE_TEMPLATE_SCOPE, MINOR_DEVELOPMENT_SYNONYMS)
    if scope_match:
        minor_development_type = scope_match.key
    else:
        blocking.append(
            "This form is for 'Minor Development Only'. Set minor_development_type to one of: "
            + ", ".join(SEE_TEMPLATE_SCOPE)
            + ". Anything else needs a purpose-written SEE (see the generate_see_draft tool)."
        )

    zone_code = (zone_code or "").upper().strip()
    zone_info = ZONES.get(zone_code, {})
    if not zone_info:
        blocking.append(
            f"Zone '{zone_code}' is not in the LEP 2012 zone list. Valid zones: "
            + ", ".join(sorted(z for z in ZONES if "redirect_to" not in ZONES[z]))
        )
    elif "redirect_to" in zone_info:
        replacement = zone_info["redirect_to"]
        blocking.append(
            f"Zone {zone_code} was replaced by {replacement} under the employment zones reform. Use {replacement}."
        )
        zone_info = ZONES.get(replacement, {})
        zone_code = replacement

    zone_name = zone_info.get("name", "")

    if minor_development_type == "dwelling_single_storey":
        if zone_code and zone_code not in RESIDENTIAL_ZONES:
            blocking.append(
                f"The template restricts single dwellings to residential zones; {zone_code} is not one "
                f"({', '.join(sorted(RESIDENTIAL_ZONES))})."
            )
        if in_heritage_conservation_area:
            blocking.append(
                "The template excludes single dwellings in heritage conservation areas — a purpose-written SEE is required."
            )

    # --- permissibility, from the LEP land use table ---------------------------
    proposed_use = (proposed_use or "").strip()
    permissibility = classify_land_use(proposed_use, zone_info, zone_code) if zone_info else None
    if permissibility and permissibility["permissible"] is not None:
        answers.setdefault("permissible", permissibility["permissible"])
        derived["permissible"] = permissibility["basis"]

    # --- answers entailed by supplied facts -----------------------------------
    if is_heritage is not None or in_heritage_conservation_area is not None:
        heritage_affected = bool(is_heritage or in_heritage_conservation_area)
        answers.setdefault("heritage_impact", heritage_affected)
        derived["heritage_impact"] = (
            "site declared a heritage item or within a heritage conservation area"
            if heritage_affected else "site declared as neither a heritage item nor in a conservation area"
        )
        if heritage_affected:
            required_documents.append(
                "Heritage Impact Statement (DCP Chapter 12) — the impact on heritage significance must be assessed, not assumed"
            )

    if internal_works_only:
        for key, basis in (
            ("excavation", "internal works only — no ground disturbance proposed"),
            ("remove_vegetation", "internal works only — no vegetation removal proposed"),
            ("threatened_species", "internal works only — no habitat disturbance proposed"),
        ):
            if key not in answers:
                answers[key] = False
                derived[key] = basis

    if is_flood_affected:
        required_documents.append(
            "Flood Risk Assessment and floor levels relative to the Flood Planning Level (LEP cl 5.21, DCP Chapter 8)"
        )
    if is_bushfire_prone:
        required_documents.append(
            "Bushfire assessment addressing Planning for Bushfire Protection (BAL rating)"
        )

    # --- parking, from the DCP rate rather than an assertion -------------------
    parking = None
    # Same loose resolution the parking tool uses, so "coffee shop" gets a rate
    # here too rather than silently omitting the parking section of the form.
    rate_match = resolve(proposed_use or "", PARKING_RATES, PARKING_SYNONYMS)
    rate_entry = PARKING_RATES.get(rate_match.key) if rate_match else None
    if rate_entry:
        parking = estimate_spaces(rate_entry, floor_area_sqm, {"employees": num_employees})
        # A rate with an unsupplied term yields no count, and a shortfall cannot
        # be computed from one. Dropping it here keeps the form's parking answer
        # blank rather than derived from a partial sum. ROADMAP.md S3.
        if parking and parking["spaces_required"] is None:
            parking = None
        if parking:
            parking["spaces_provided"] = parking_spaces_provided
            if parking_spaces_provided is None:
                parking["shortfall"] = None
            else:
                parking["shortfall"] = max(0, parking["spaces_required"] - parking_spaces_provided)

    # --- text boxes: supplied text, or facts, never filler --------------------
    def article(word: str) -> str:
        return "an" if word[:1].lower() in "aeiou" else "a"

    dev_type_desc = {
        "new_building": "Construction of a new building",
        "alteration": "Alterations and additions to an existing building",
        "change_of_use": "Change of use of an existing premises",
        "fitout": "Internal fit-out of an existing premises",
    }.get(development_type, development_type)

    proposal_lines = []
    if building_description:
        proposal_lines.append(building_description)
    elif proposed_use:
        proposal_lines.append(f"{dev_type_desc} to {article(proposed_use)} {proposed_use}.")
    else:
        proposal_lines.append(f"{dev_type_desc}.")
    proposal_lines.append("")
    if floor_area_sqm:
        proposal_lines.append(f"Floor area: {floor_area_sqm:g}m²")
    if hours_of_operation:
        proposal_lines.append(f"Hours of operation: {hours_of_operation}")
    if num_employees:
        proposal_lines.append(f"Number of employees: {num_employees}")
    if num_customers:
        proposal_lines.append(f"Maximum customers: {num_customers}")
    if estimated_cost:
        proposal_lines.append(f"Estimated cost of works: ${estimated_cost:,.0f}")
    proposal_desc = "\n".join(proposal_lines).strip()

    site_lines = [site_description] if site_description else []
    if zone_name:
        site_lines.append(f"The site is zoned {zone_code} {zone_name} under Lismore LEP 2012.")
    if existing_use:
        site_lines.append(f"Existing use: {existing_use}")
    site_desc = "\n\n".join(site_lines).strip()

    hazard_lines = []
    if is_flood_affected:
        hazard_lines.append(
            "The site is flood prone. Floor levels, structural soundness and evacuation are to be assessed "
            "against LEP 2012 clause 5.21 and DCP Chapter 8."
        )
    if is_bushfire_prone:
        hazard_lines.append(
            "The site is bushfire prone. Planning for Bushfire Protection applies and a BAL assessment is required."
        )
    if is_flood_affected is False and is_bushfire_prone is False and not hazard_lines:
        hazard_lines.append("The site is not identified as flood prone or bushfire prone.")
    hazards_comments = comments.get("hazards_comments") or "\n".join(hazard_lines)

    constraint_lines = []
    if is_heritage:
        constraint_lines.append(
            "The site is a heritage item under LEP 2012 Schedule 5. A Heritage Impact Statement accompanies "
            "this application; the impact on heritage significance is assessed there."
        )
    if in_heritage_conservation_area:
        constraint_lines.append("The site is within a heritage conservation area.")
    constraints = comments.get("constraints") or "\n".join(constraint_lines)

    planning_lines = [f"Zone: {zone_code} {zone_name}".strip()]
    if permissibility:
        planning_lines.append(permissibility["statement"])
    if comments.get("planning_comments"):
        planning_lines.append(comments["planning_comments"])
    planning_comments = "\n".join(line for line in planning_lines if line)

    access_lines = [comments["access_comments"]] if comments.get("access_comments") else []
    if parking:
        summary = (
            f"Off-street parking: DCP Chapter 7 indicates approximately {parking['spaces_required']} "
            f"space(s) for this use ({'; '.join(parking['basis'])})."
        )
        if parking_spaces_provided is not None:
            summary += f" {parking_spaces_provided} space(s) are provided on site."
            if parking["shortfall"]:
                summary += (
                    f" This is a shortfall of {parking['shortfall']} space(s), which is addressed in the "
                    "parking assessment accompanying this application."
                )
        access_lines.append(summary)
    access_comments = "\n".join(access_lines)

    waste_lines = [comments["waste_comments"]] if comments.get("waste_comments") else []
    if stormwater_to_council_system:
        waste_lines.append("Stormwater is disposed of to the Council drainage system.")
    elif stormwater_to_council_system is False and comments.get("stormwater_details"):
        waste_lines.append(f"Stormwater disposal: {comments['stormwater_details']}")
    waste_comments = "\n".join(waste_lines)

    social_lines = [comments["social_comments"]] if comments.get("social_comments") else []
    if num_employees:
        social_lines.append(f"The proposal will provide employment for {num_employees} people.")
    social_comments = "\n".join(social_lines)

    # --- assemble the fields --------------------------------------------------
    address = parse_street_address(property_address, unit, street_number, street, suburb)
    land = parse_land_identifier(lot_dp, lot, plan_type, plan_number, section)

    if not land["plan_number"]:
        blocking.append(
            "The land could not be identified. Supply plan_type ('DP', 'SP' or 'CP') and plan_number, "
            "or a lot_dp string such as 'Lot 12 DP 758651'. The form is not written with a blank land identifier."
        )
    if not address["street_number"] or not address["street"]:
        blocking.append(
            "The street address could not be split reliably. Supply street_number and street "
            "(plus unit for a shop or unit tenancy)."
        )

    plan_box = land["plan_number"]
    if plan_box and land["plan_type"] and land["plan_type"] != "DP":
        plan_box = f"{land['plan_type']} {plan_box}"

    fields: dict = {
        "applicant_name": applicant_name,
        "address_number": " ".join(p for p in (address["unit"], address["street_number"]) if p).strip(),
        "street_name": address["street"],
        "building_name": building_name,
        "suburb": address["suburb"],
        "lot": land["lot"],
        "dp": plan_box,
        "section": land["section"],

        "description_of_development": proposal_desc,
        "description_of_site": site_desc,
        "present_previous_use": existing_use,

        "bushfire_prone": is_bushfire_prone,
        "flooding": is_flood_affected,
        "hazards_comments": hazards_comments,
        "constraints": constraints,
        "surrounding_land_use": comments.get("surrounding_land_use") or surrounding_context,

        "planning_comments": planning_comments,
        "context_comment": comments.get("context_comment", ""),
        "privacy_comments": comments.get("privacy_comments", ""),
        "access_comments": access_comments,
        "traffic_amount": comments.get("traffic_amount", ""),
        "environmental_comments": comments.get("environmental_comments", ""),
        "flora_comments": comments.get("flora_comments", ""),
        "waste_comments": waste_comments,
        "stormwater_details": comments.get("stormwater_details", ""),
        "social_comments": social_comments,
        "other_matters": comments.get("other_matters", ""),

        "stormwater_council": stormwater_to_council_system,
        "stormwater_other": (not stormwater_to_council_system) if stormwater_to_council_system is not None else None,

        "declaration_name_1": applicant_name,
        "declaration_name_2": "",
        "declaration_date_1": "",  # signed and dated by hand
        "declaration_date_2": "",
    }

    # One tick per answered question; unanswered questions stay blank on the form.
    unanswered = []
    for key, question in SEE_QUESTIONS.items():
        value = answers.get(key)
        if value is None:
            fields[f"{key}_yes"] = None
            fields[f"{key}_no"] = None
            unanswered.append({"key": key, "question": question})
        else:
            fields[f"{key}_yes"] = bool(value)
            fields[f"{key}_no"] = not bool(value)

    if is_flood_affected is None:
        unanswered.append({"key": "flooding", "question": "Is the site subject to flooding or stormwater inundation?"})
    if is_bushfire_prone is None:
        unanswered.append({"key": "bushfire_prone", "question": "Is the site bushfire prone?"})
    if stormwater_to_council_system is None:
        unanswered.append({"key": "stormwater", "question": "How will stormwater from roof and hard standing be disposed of?"})
    if answers.get("increase_traffic") and not fields["traffic_amount"]:
        unanswered.append({"key": "traffic_amount", "question": SEE_COMMENT_FIELDS["traffic_amount"]})
    if parking and parking.get("shortfall") is None:
        unanswered.append({
            "key": "parking_spaces_provided",
            "question": f"How many off-street parking spaces are provided? DCP Chapter 7 indicates approximately {parking['spaces_required']}.",
        })
    if not fields["present_previous_use"]:
        unanswered.append({"key": "existing_use", "question": "What is the present use and previous use of the site?"})

    # Comment boxes that are questions in their own right, not optional extras
    for field, question in (
        ("constraints", "What other constraints exist on the site (vegetation, easements, sloping land, drainage lines, contamination)?"),
        ("surrounding_land_use", "What types of land use and development exist on surrounding land?"),
    ):
        if not fields[field]:
            unanswered.append({"key": field, "question": question})

    return {
        "fields": fields,
        "unanswered_questions": unanswered,
        "derived_answers": derived,
        "blocking_issues": blocking,
        "parking": parking,
        "required_documents": required_documents,
    }
