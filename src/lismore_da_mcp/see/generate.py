"""Building SEE form data from proposal details.

Derives the form's answers from what the caller supplied, refusing where the
proposal falls outside the template's "Minor Development Only" scope.
"""

from lismore_da_mcp.data.parking import PARKING_RATES
from lismore_da_mcp.data.zones import ZONES
from lismore_da_mcp.landuse import classify_land_use
from lismore_da_mcp.parking import estimate_spaces, resolve_parking_use
from lismore_da_mcp.see.fields import (
    RESIDENTIAL_ZONES,
    SEE_COMMENT_FIELDS,
    SEE_QUESTIONS,
    SEE_TEMPLATE_SCOPE,
)
from lismore_da_mcp.see.parsers import (
    parse_land_identifier,
    parse_street_address,
)
from lismore_da_mcp.vocabulary import (
    MINOR_DEVELOPMENT_SYNONYMS,
    resolve,
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

    blocking = _unknown_key_issues(answers, comments)
    derived: dict[str, str] = {}

    minor_development_type = _resolve_scope(minor_development_type, blocking)
    zone_code, zone_info = _resolve_zone(zone_code, blocking)
    zone_name = zone_info.get("name", "")
    if minor_development_type == "dwelling_single_storey":
        blocking.extend(_single_dwelling_issues(zone_code, in_heritage_conservation_area))

    # --- permissibility, from the LEP land use table ---------------------------
    proposed_use = (proposed_use or "").strip()
    permissibility = classify_land_use(proposed_use, zone_info, zone_code) if zone_info else None
    if permissibility and permissibility["permissible"] is not None:
        answers.setdefault("permissible", permissibility["permissible"])
        derived["permissible"] = permissibility["basis"]

    required_documents = _derive_from_site_facts(
        answers, derived, is_heritage, in_heritage_conservation_area,
        internal_works_only, is_flood_affected, is_bushfire_prone,
    )
    parking = _parking(proposed_use, floor_area_sqm, num_employees, parking_spaces_provided)

    address = parse_street_address(property_address, unit, street_number, street, suburb)
    land = parse_land_identifier(lot_dp, lot, plan_type, plan_number, section)
    blocking.extend(_identification_issues(address, land))

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

        "description_of_development": _proposal_description(
            development_type, proposed_use, building_description, floor_area_sqm,
            hours_of_operation, num_employees, num_customers, estimated_cost,
        ),
        "description_of_site": _site_description(site_description, zone_code, zone_name, existing_use),
        "present_previous_use": existing_use,

        "bushfire_prone": is_bushfire_prone,
        "flooding": is_flood_affected,
        "hazards_comments": comments.get("hazards_comments") or _hazards_text(is_flood_affected, is_bushfire_prone),
        "constraints": comments.get("constraints") or _constraints_text(is_heritage, in_heritage_conservation_area),
        "surrounding_land_use": comments.get("surrounding_land_use") or surrounding_context,

        "planning_comments": _planning_text(zone_code, zone_name, permissibility, comments),
        "context_comment": comments.get("context_comment", ""),
        "privacy_comments": comments.get("privacy_comments", ""),
        "access_comments": _access_text(comments, parking, parking_spaces_provided),
        "traffic_amount": comments.get("traffic_amount", ""),
        "environmental_comments": comments.get("environmental_comments", ""),
        "flora_comments": comments.get("flora_comments", ""),
        "waste_comments": _waste_text(comments, stormwater_to_council_system),
        "stormwater_details": comments.get("stormwater_details", ""),
        "social_comments": _social_text(comments, num_employees),
        "other_matters": comments.get("other_matters", ""),

        "stormwater_council": stormwater_to_council_system,
        "stormwater_other": (not stormwater_to_council_system) if stormwater_to_council_system is not None else None,

        "declaration_name_1": applicant_name,
        "declaration_name_2": "",
        "declaration_date_1": "",  # signed and dated by hand
        "declaration_date_2": "",
    }

    unanswered = _tick_answers(fields, answers)
    unanswered.extend(_unanswered_facts(
        fields, answers, parking, is_flood_affected, is_bushfire_prone, stormwater_to_council_system,
    ))

    return {
        "fields": fields,
        "unanswered_questions": unanswered,
        "derived_answers": derived,
        "blocking_issues": blocking,
        "parking": parking,
        "required_documents": required_documents,
    }


# --- validation and scope ------------------------------------------------------


def _unknown_key_issues(answers: dict, comments: dict) -> list[str]:
    issues = []
    unknown_answers = sorted(set(answers) - set(SEE_QUESTIONS))
    if unknown_answers:
        issues.append(
            "Unrecognised answer key(s): " + ", ".join(unknown_answers)
            + ". Valid keys: " + ", ".join(sorted(SEE_QUESTIONS))
        )
    unknown_comments = sorted(set(comments) - set(SEE_COMMENT_FIELDS))
    if unknown_comments:
        issues.append(
            "Unrecognised comment key(s): " + ", ".join(unknown_comments)
            + ". Valid keys: " + ", ".join(sorted(SEE_COMMENT_FIELDS))
        )
    return issues


def _resolve_scope(minor_development_type: str, blocking: list[str]) -> str:
    """The template covers minor residential development only.

    Naming is resolved loosely ("shed", "single storey dwelling"), but a proposal
    outside the template's scope is still refused: the form would be rejected.
    """
    scope_match = resolve(minor_development_type, SEE_TEMPLATE_SCOPE, MINOR_DEVELOPMENT_SYNONYMS)
    if scope_match.key:
        return scope_match.key
    blocking.append(
        "This form is for 'Minor Development Only'. Set minor_development_type to one of: "
        + ", ".join(SEE_TEMPLATE_SCOPE)
        + ". Anything else needs a purpose-written SEE (see the generate_see_draft tool)."
    )
    return minor_development_type


def _resolve_zone(zone_code: str, blocking: list[str]) -> tuple[str, dict]:
    """The zone code and its LEP entry, following a legacy code to its replacement."""
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
        return replacement, ZONES.get(replacement, {})
    return zone_code, zone_info


def _single_dwelling_issues(zone_code: str, in_heritage_conservation_area: bool | None) -> list[str]:
    issues = []
    if zone_code and zone_code not in RESIDENTIAL_ZONES:
        issues.append(
            f"The template restricts single dwellings to residential zones; {zone_code} is not one "
            f"({', '.join(sorted(RESIDENTIAL_ZONES))})."
        )
    if in_heritage_conservation_area:
        issues.append(
            "The template excludes single dwellings in heritage conservation areas — a purpose-written SEE is required."
        )
    return issues


def _identification_issues(address: dict, land: dict) -> list[str]:
    issues = []
    if not land["plan_number"]:
        issues.append(
            "The land could not be identified. Supply plan_type ('DP', 'SP' or 'CP') and plan_number, "
            "or a lot_dp string such as 'Lot 12 DP 758651'. The form is not written with a blank land identifier."
        )
    if not address["street_number"] or not address["street"]:
        issues.append(
            "The street address could not be split reliably. Supply street_number and street "
            "(plus unit for a shop or unit tenancy)."
        )
    return issues


# --- answers entailed by supplied facts -------------------------------------------


def _derive_from_site_facts(
    answers: dict,
    derived: dict[str, str],
    is_heritage: bool | None,
    in_heritage_conservation_area: bool | None,
    internal_works_only: bool,
    is_flood_affected: bool | None,
    is_bushfire_prone: bool | None,
) -> list[str]:
    """Fill answers the site facts entail, recording why. Returns the documents they require."""
    required_documents: list[str] = []

    if is_heritage is not None or in_heritage_conservation_area is not None:
        heritage_affected = bool(is_heritage or in_heritage_conservation_area)
        answers.setdefault("heritage_impact", heritage_affected)
        derived["heritage_impact"] = (
            "site declared a heritage item or within a heritage conservation area"
            if heritage_affected else "site declared as neither a heritage item nor in a conservation area"
        )
        if heritage_affected:
            required_documents.append(
                "Heritage management document, if Council requires one (LEP cl 5.10(5)) — usually a "
                "Heritage Impact Statement, but a conservation management plan or other guidance "
                "document also satisfies the clause. Ask which is wanted before commissioning one. "
                "Council must consider the heritage impact either way (cl 5.10(4)), so address it "
                "in this SEE regardless"
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
    return required_documents


def _parking(
    proposed_use: str,
    floor_area_sqm: float,
    num_employees: int,
    spaces_provided: int | None,
) -> dict | None:
    """The DCP parking estimate, or None when it cannot be reduced to a space count.

    Resolved as loosely as the parking tool does, so "coffee shop" gets a rate. A
    rate with an unsupplied term yields no count, and is dropped rather than
    reported as a partial sum.
    """
    rate_match = resolve_parking_use(proposed_use or "")[0]
    rate_entry = PARKING_RATES.get(rate_match.key) if rate_match and rate_match.key else None
    if not rate_entry:
        return None
    parking = estimate_spaces(rate_entry, floor_area_sqm, {"employees": num_employees})
    if not parking or parking["spaces_required"] is None:
        return None
    parking["spaces_provided"] = spaces_provided
    parking["shortfall"] = (
        None if spaces_provided is None else max(0, parking["spaces_required"] - spaces_provided)
    )
    return parking


# --- text boxes: supplied text, or facts, never filler -----------------------------

_DEVELOPMENT_TYPE_DESCRIPTIONS = {
    "new_building": "Construction of a new building",
    "alteration": "Alterations and additions to an existing building",
    "change_of_use": "Change of use of an existing premises",
    "fitout": "Internal fit-out of an existing premises",
}


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _proposal_description(
    development_type: str,
    proposed_use: str,
    building_description: str,
    floor_area_sqm: float,
    hours_of_operation: str,
    num_employees: int,
    num_customers: int,
    estimated_cost: float,
) -> str:
    dev_type_desc = _DEVELOPMENT_TYPE_DESCRIPTIONS.get(development_type, development_type)
    if building_description:
        lines = [building_description]
    elif proposed_use:
        lines = [f"{dev_type_desc} to {_article(proposed_use)} {proposed_use}."]
    else:
        lines = [f"{dev_type_desc}."]
    lines.append("")
    if floor_area_sqm:
        lines.append(f"Floor area: {floor_area_sqm:g}m²")
    if hours_of_operation:
        lines.append(f"Hours of operation: {hours_of_operation}")
    if num_employees:
        lines.append(f"Number of employees: {num_employees}")
    if num_customers:
        lines.append(f"Maximum customers: {num_customers}")
    if estimated_cost:
        lines.append(f"Estimated cost of works: ${estimated_cost:,.0f}")
    return "\n".join(lines).strip()


def _site_description(site_description: str, zone_code: str, zone_name: str, existing_use: str) -> str:
    lines = [site_description] if site_description else []
    if zone_name:
        lines.append(f"The site is zoned {zone_code} {zone_name} under Lismore LEP 2012.")
    if existing_use:
        lines.append(f"Existing use: {existing_use}")
    return "\n\n".join(lines).strip()


def _hazards_text(is_flood_affected: bool | None, is_bushfire_prone: bool | None) -> str:
    lines = []
    if is_flood_affected:
        lines.append(
            "The site is flood prone. Floor levels, structural soundness and evacuation are to be assessed "
            "against LEP 2012 clause 5.21 and DCP Chapter 8."
        )
    if is_bushfire_prone:
        lines.append(
            "The site is bushfire prone. Planning for Bushfire Protection applies and a BAL assessment is required."
        )
    if is_flood_affected is False and is_bushfire_prone is False:
        lines.append("The site is not identified as flood prone or bushfire prone.")
    return "\n".join(lines)


def _constraints_text(is_heritage: bool | None, in_heritage_conservation_area: bool | None) -> str:
    lines = []
    if is_heritage:
        # Never assert that a heritage document is attached: cl 5.10(5) only
        # says Council *may* require one, and this goes out over the applicant's name.
        lines.append(
            "The site is a heritage item under LEP 2012 Schedule 5. [APPLICANT TO COMPLETE] "
            "Council may require a heritage management document under LEP cl 5.10(5) — confirm "
            "with Council whether one is required for this proposal and, if so, in what form. "
            "State here how the impact on heritage significance has been assessed; cl 5.10(4) "
            "requires the consent authority to consider it whether or not a document is required."
        )
    if in_heritage_conservation_area:
        lines.append("The site is within a heritage conservation area.")
    return "\n".join(lines)


def _planning_text(zone_code: str, zone_name: str, permissibility: dict | None, comments: dict) -> str:
    lines = [f"Zone: {zone_code} {zone_name}".strip()]
    if permissibility:
        lines.append(permissibility["statement"])
    if comments.get("planning_comments"):
        lines.append(comments["planning_comments"])
    return "\n".join(line for line in lines if line)


def _access_text(comments: dict, parking: dict | None, spaces_provided: int | None) -> str:
    lines = [comments["access_comments"]] if comments.get("access_comments") else []
    if parking:
        summary = (
            f"Off-street parking: DCP Chapter 7 indicates approximately {parking['spaces_required']} "
            f"space(s) for this use ({'; '.join(parking['basis'])})."
        )
        if spaces_provided is not None:
            summary += f" {spaces_provided} space(s) are provided on site."
            if parking["shortfall"]:
                summary += (
                    f" This is a shortfall of {parking['shortfall']} space(s), which is addressed in the "
                    "parking assessment accompanying this application."
                )
        lines.append(summary)
    return "\n".join(lines)


def _waste_text(comments: dict, stormwater_to_council_system: bool | None) -> str:
    lines = [comments["waste_comments"]] if comments.get("waste_comments") else []
    if stormwater_to_council_system:
        lines.append("Stormwater is disposed of to the Council drainage system.")
    elif stormwater_to_council_system is False and comments.get("stormwater_details"):
        lines.append(f"Stormwater disposal: {comments['stormwater_details']}")
    return "\n".join(lines)


def _social_text(comments: dict, num_employees: int) -> str:
    lines = [comments["social_comments"]] if comments.get("social_comments") else []
    if num_employees:
        lines.append(f"The proposal will provide employment for {num_employees} people.")
    return "\n".join(lines)


# --- what is still unanswered ------------------------------------------------------


def _tick_answers(fields: dict, answers: dict) -> list[dict]:
    """One tick per answered question; unanswered ones stay blank and are returned."""
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
    return unanswered


def _unanswered_facts(
    fields: dict,
    answers: dict,
    parking: dict | None,
    is_flood_affected: bool | None,
    is_bushfire_prone: bool | None,
    stormwater_to_council_system: bool | None,
) -> list[dict]:
    unanswered = []
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
    return unanswered
