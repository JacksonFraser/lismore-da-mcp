"""Lodgement readiness, and the brief for the free Duty Planner session."""

import json
import textwrap

from mcp.types import TextContent

from lismore_da_mcp.data.contacts import CONTACT_INFO
from lismore_da_mcp.data.parking import PARKING_RATES
from lismore_da_mcp.data.readiness import HOW_TO_USE_THE_SESSION
from lismore_da_mcp.data.readiness import REJECTION_WINDOW
from lismore_da_mcp.data.readiness import STATUTORY_CONTENT
from lismore_da_mcp.parking import cbd_location
from lismore_da_mcp.parking import cbd_spaces
from lismore_da_mcp.parking import estimate_spaces
from lismore_da_mcp.parking import uses_schedule_1_in_cbd
from lismore_da_mcp.readiness import Proposal
from lismore_da_mcp.readiness import assess
from lismore_da_mcp.readiness import open_questions
from lismore_da_mcp.readiness import site_constraints
from lismore_da_mcp.registry import tool
from lismore_da_mcp.vocabulary import PARKING_SYNONYMS
from lismore_da_mcp.vocabulary import resolve

# Both tools describe the same proposal, so they take the same arguments. Two
# drifting copies of a twelve-argument schema is a maintenance problem, and a
# caller who has described their proposal to one tool should not have to
# describe it differently to the other.
PROPOSAL_ARGUMENTS = {
    'proposed_use': {'type': 'string', 'description': "The use that will operate on the land — 'cafe', 'restaurant or cafe', 'office premises', 'hairdresser', 'warehouse'. NOT the work: 'fitout' and 'change of use' describe what you are doing and cannot be checked for permissibility. Put those in development_type."},
    'property_address': {'type': 'string', 'description': "Optional but worth supplying. The site address, used to derive the zone and to read the heritage and bushfire mapping. Without it, permissibility and the site constraints are not checked at all."},
    'zone_code': {'type': 'string', 'description': "Optional. The LEP zone, if already known — 'E2', 'MU1', 'RU5'. Derived from the address if not supplied. Never guess it."},
    'development_type': {'type': 'string', 'description': "Optional. What you are doing, in plain words: 'change of use', 'fitout', 'new tenancy', 'commercial', 'industrial', 'signage', 'demolition', 'subdivision', 'dwelling'. Selects the document checklist."},
    'existing_use': {'type': 'string', 'description': "Optional. The existing or most recent approved use of the premises. It drives the Section 7.11 allowance and the contamination question, and it belongs in the description of development."},
    'floor_area_sqm': {'type': 'number', 'description': 'Optional. Gross floor area in square metres.', 'minimum': 0},
    # Several Schedule 1 rates add a staff or seating component to the area
    # component, and without these the parking requirement cannot be worked out
    # at all — the café rate is the common case. They used to be absent, and the
    # area-only figure was reported as the requirement anyway. ROADMAP.md S3.
    'num_employees': {'type': 'integer', 'description': 'Optional. Number of employees. Several parking rates add a staff component, and without it no parking figure can be given for those uses.', 'minimum': 0},
    'seats': {'type': 'integer', 'description': 'Optional. Seats, for a restaurant, café, place of worship or function centre.', 'minimum': 0},
    'spaces_provided': {'type': 'integer', 'description': 'Optional. Car parking spaces available on the site.', 'minimum': 0},
    'location': {'type': 'string', 'description': "Optional. 'cbd' if the site is inside the Lismore CBD as drawn on Map 1 of DCP Chapter 7, or 'outside_cbd'. Do not infer it from the zone — it changes the parking requirement several-fold."},
    'catchment': {'type': 'string', 'description': "Optional. The Section 7.11 contributions catchment, if Council has confirmed it: 'urban', 'rural' or 'rural_village'."},
    'contravenes_development_standard': {'type': 'boolean', 'description': 'Optional. Whether the proposal exceeds a development standard — height, floor space ratio or minimum lot size. If true, a clause 4.6 written request must accompany the application.'},
    'documents_prepared': {'type': 'array', 'items': {'type': 'string'}, 'description': "Optional. Documents you already have ready, in your own words — 'site plan', 'SEE', 'BASIX', 'owner's consent'. Matched conservatively against the checklist: anything not clearly matched is reported as still missing."},
    'development_characteristics': {'type': 'array', 'items': {'type': 'string'}, 'description': "Optional. Site or proposal characteristics that may trigger a referral to another agency: 'bushfire_prone', 'near_waterway', 'vegetation_clearing', 'classified_road', 'state_heritage', 'significant_traffic'."},
}


def _proposal(arguments: dict) -> tuple[Proposal, dict]:
    """Build the proposal, resolving what can be resolved from the address.

    Returns the proposal and a record of how each derived fact was learned. The
    record is returned to the caller rather than kept internal, because a zone
    read off the wrong property flows straight into a permissibility answer —
    the applicant has to be able to see which address was matched.
    """
    how: dict = {}
    address = (arguments.get("property_address") or "").strip()
    zone = (arguments.get("zone_code") or "").strip().upper()

    if not zone and address:
        try:
            from lismore_da_mcp.addresses import lookup_zone

            found = lookup_zone(address)
        except Exception as exc:                                   # noqa: BLE001
            found = {"error": str(exc)}
        if found.get("zone_code"):
            zone = found["zone_code"]
            how["zone"] = (f"Read from the NSW Land Zoning Map for "
                           f"{found.get('matched_address', address)}. Check that is the right "
                           "property — a zone for the wrong address is worse than no zone.")
        else:
            how["zone"] = (f"Could not be derived from the address ({found.get('error', 'no '
                           'result')}). Read it off the NSW Planning Portal and pass zone_code.")
    elif zone:
        how["zone"] = "Supplied by the caller."

    flood, heritage, bushfire, note = site_constraints(address)
    how["constraints"] = note

    proposal = Proposal(
        proposed_use=(arguments.get("proposed_use") or "").strip(),
        development_type=(arguments.get("development_type") or "").strip(),
        property_address=address,
        zone_code=zone,
        existing_use=(arguments.get("existing_use") or "").strip(),
        floor_area_sqm=arguments.get("floor_area_sqm") or None,
        # No `or None`: a supplied 0 has to survive, or the caller cannot say
        # "no staff" — which is a different fact from not saying anything.
        num_employees=arguments.get("num_employees"),
        seats=arguments.get("seats"),
        contravenes_development_standard=arguments.get("contravenes_development_standard"),
        documents_prepared=list(arguments.get("documents_prepared") or []),
        development_characteristics=list(arguments.get("development_characteristics") or []),
        in_cbd=cbd_location(arguments.get("location")),
        catchment=(arguments.get("catchment") or "").strip(),
        flood=flood,
        heritage=heritage,
        bushfire=bushfire,
        constraints_note=note,
    )
    return proposal, how


def _parking(p: Proposal, spaces_provided) -> dict | None:
    """Where parking stands, and whether a shortfall is certain.

    A shortfall is only reported as settled when both readings of the chapter
    agree. Inside the CBD the requirement is a fixed 3.3 spaces/100m²; outside
    it, the Schedule 1 rate — and until the site is placed on Map 1 the honest
    position is a range, not a number. Reporting the lower reading would tell a
    business it complies when it may owe eleven more spaces; reporting the
    higher would talk it out of a viable tenancy.
    """
    match = resolve(p.proposed_use, PARKING_RATES, PARKING_SYNONYMS)
    if not match:
        return None
    entry = PARKING_RATES[match.key]
    schedule_1 = estimate_spaces(entry, p.floor_area_sqm, {
        "employees": p.num_employees,
        "seats": p.seats,
    })
    cbd = None if uses_schedule_1_in_cbd(match.key) else cbd_spaces(p.floor_area_sqm)

    # A rate whose terms were not all supplied returns no number. Carrying that
    # through rather than falling back on the area-only figure is the point of
    # ROADMAP.md S3: the café rate adds a staff component, and reporting the
    # area component alone as "the requirement" is how an 80m² café was told its
    # parking was adequate against a real requirement of 14 spaces.
    if schedule_1 and schedule_1["spaces_required"] is None:
        return {
            "rate_matched": match.key,
            "spaces_required": None,
            "cannot_calculate": schedule_1["cannot_calculate"],
            "supply": schedule_1["supply"],
            "counted_so_far": schedule_1["counted_so_far"],
            "spaces_provided": spaces_provided,
            "shortfall": None,
            "note": (
                "No parking figure is given because the rate has a term that was not "
                "supplied. This is not a shortfall of zero — it is an unanswered question, "
                "and Council will ask it."
            ),
        }

    if p.in_cbd is True and cbd:
        readings = [cbd["spaces_required"]]
    elif p.in_cbd is False and schedule_1:
        readings = [schedule_1["spaces_required"]]
    else:
        readings = [r["spaces_required"] for r in (schedule_1, cbd) if r]
    if not readings:
        return None

    result = {
        "rate_matched": match.key,
        "basis": (schedule_1 or {}).get("basis"),
        "for_the_full_calculation": "get_parking_rates, which takes every countable the rates use.",
        "spaces_required": readings[0] if len(readings) == 1 else
                           f"between {min(readings)} and {max(readings)} — the CBD and Schedule 1 "
                           "readings differ and the site has not been placed on Map 1",
        "spaces_provided": spaces_provided,
        "shortfall": None,
    }
    if spaces_provided is not None:
        if min(readings) > spaces_provided:
            result["shortfall"] = True
            result["note"] = (f"Short by at least {min(readings) - spaces_provided} space(s) on "
                              "every reading of the chapter. get_parking_rates sets out what the "
                              "DCP offers — it does not have to be built.")
        elif max(readings) <= spaces_provided:
            result["shortfall"] = False
        else:
            result["note"] = ("Whether there is a shortfall depends on which rate applies. "
                              "Settle the CBD boundary before assuming either.")
    else:
        result["note"] = ("Spaces provided were not stated, so no shortfall has been "
                          "calculated — and none has been assumed either way.")
    return result


@tool(
    name='check_da_readiness',
    description="Check a proposal against everything that has to be in place before lodging: the document checklist, the site constraints, the referrals, and the Regulation's own content requirements. Returns what would stop the application, what could get it rejected in the first 14 days, what is missing, and what only Council can settle. Run this before lodging — a rejected DA is taken never to have been made and starts again from zero.",
    properties=PROPOSAL_ARGUMENTS,
    required=['proposed_use'],
)
def check_da_readiness(arguments: dict):
    p, how = _proposal(arguments)
    parking = _parking(p, arguments.get("spaces_provided"))
    result = assess(p, has_parking_shortfall=parking.get("shortfall") if parking else None)

    severities = [f["severity"] for f in result["findings"]]
    if "stop" in severities:
        verdict = ("Do not lodge yet — something below would stop the application rather than "
                   "delay it.")
    elif "rejection_risk" in severities or "incomplete" in severities:
        verdict = ("Not ready. The items below are what Council checks in the first 14 days, "
                   "before anyone assesses the merits.")
    else:
        verdict = ("Nothing this tool can check is outstanding. That is a smaller claim than "
                   "'ready': Council runs the completeness check, and some rejection grounds — "
                   "whether the description of development is clear, whether the plans are "
                   "legible at the scale printed — cannot be tested from here.")

    response = {
        "verdict": verdict,
        "what_this_prevents": REJECTION_WINDOW["plain"],
        "understood_as": {
            "proposed_use": p.proposed_use,
            "development_type": result["development_type_used"],
            "zone_code": p.zone_code or None,
            "address": p.property_address or None,
            "existing_use": p.existing_use or None,
            "flood": _tri(p.flood),
            "heritage": _tri(p.heritage),
            "bushfire": _tri(p.bushfire),
        },
        "how_that_was_established": how,
        "outstanding": result["findings"],
        "documents": result["documents"],
        "approvals_to_list_on_the_application": {
            "why": STATUTORY_CONTENT["list_of_approvals"]["plain"],
            "clause": STATUTORY_CONTENT["list_of_approvals"]["clause"],
            "list_these": result["approvals_to_list_on_the_application"],
        },
        "questions_for_council": [
            {"question": q["question"], "cost_if_unresolved": q["cost_if_unresolved"]}
            for q in result["questions_for_council"]
        ],
        "next": "prepare_prelodgement_brief with the same arguments turns those questions into "
                "a brief to take to the free Duty Planner session.",
    }
    if parking:
        response["parking"] = parking
    if result["referrals"]["triggered"]:
        response["referrals"] = result["referrals"]["triggered"]
        response["referrals_change_the_timeline"] = (
            "If any of these is an approval under EP&A Act s4.46, the application is integrated "
            "development: the assessment period becomes 60 days rather than 40, and every "
            "approval must be identified on the application or it can be rejected under "
            "s39(1)(d)."
        )
    if result["referrals"]["not_recognised"]:
        response["characteristics_not_recognised"] = {
            "not_assessed": result["referrals"]["not_recognised"],
            "note": "These were not recognised and have NOT been checked for referrals. Re-send "
                    "them using the triggers listed by check_referrals, or treat them as "
                    "unchecked.",
        }
    if result["approval_questions"]:
        response["questions_that_change_the_approvals_list"] = result["approval_questions"]

    response["not_checked_here"] = [
        "Whether the plans are drawn to scale, legible, and consistent with the SEE. Council "
        "rejects on this and nothing here can open a file.",
        "The cost of the application — calculate_da_fees composes the lodgement fee and the "
        "Section 7.11 contribution, which is usually the far larger number.",
        "Whether consent is needed at all. Some changes of use are exempt or complying "
        "development under the Codes SEPP, and existing use rights may apply.",
        "Anything a State Environmental Planning Policy requires. This server carries the LEP "
        "and the DCP, not the SEPPs.",
    ]
    response["guidance_only"] = ("This is guidance, not a determination. Council runs the "
                                 "completeness check and decides the application.")
    return [TextContent(type="text", text=json.dumps(response, indent=2))]


def _tri(value: bool | None) -> str:
    return "yes" if value else ("no" if value is False else "not established")


def _wrap(text: str, indent: str = "       ") -> str:
    return textwrap.fill(text, width=78, initial_indent=indent, subsequent_indent=indent)


def _bullet(text: str, indent: str = "   ") -> str:
    """A bullet whose continuation lines hang under the text, not the marker.

    This is printed and carried into a room. A wrapped bullet that returns to
    the margin reads as a new point, and the sections it is used for are lists
    of things to check off one at a time.
    """
    return textwrap.fill(text, width=78,
                         initial_indent=f"{indent}• ", subsequent_indent=f"{indent}  ")


# Fifteen minutes is the constraint, and it is a real one. Five questions asked
# properly beats ten asked in a hurry, so the rest go under "if there is time"
# rather than being dropped — the applicant chooses, having been told the cost
# of each.
QUESTIONS_IN_THE_SESSION = 5


@tool(
    name='prepare_prelodgement_brief',
    description="Produce a written brief to take to Lismore Council's free Duty Planner drop-in (Tuesdays and Thursdays, 8:30-10:30am, no appointment). It assembles the questions this server has declined to answer — the CBD parking boundary, the flood planning level, the contributions catchment, the Section 64 charge, whether the change of use needs a DA at all — ranked by what each costs to leave unresolved, and says which questions NOT to spend the session on because they are already answered. Returns plain text to print and take in.",
    properties=PROPOSAL_ARGUMENTS,
    required=['proposed_use'],
)
def prepare_prelodgement_brief(arguments: dict):
    p, how = _proposal(arguments)
    parking = _parking(p, arguments.get("spaces_provided"))
    result = assess(p, has_parking_shortfall=parking.get("shortfall") if parking else None)
    questions = open_questions(p, parking.get("shortfall") if parking else None)
    duty = CONTACT_INFO["duty_planner"]

    lines = [
        "PRE-LODGEMENT BRIEF",
        "=" * 78,
        f"For: {CONTACT_INFO['council']} — {duty['service']}",
        f"     {duty['days']}, {duty['time']} — {duty['location']}",
        f"     {duty['appointment']}. Council: {CONTACT_INFO['phone']}",
        "",
        _wrap("Prepared by the Lismore DA assistant. Guidance only — nothing in it is a "
              "determination, and nothing said at a duty planner session binds Council.", ""),
        "",
        "-" * 78,
        "1. THE PROPOSAL",
        "-" * 78,
        f"   Address:        {p.property_address or '[not supplied]'}",
        f"   Zone:           {p.zone_code or '[not established]'}",
        f"   Proposed use:   {p.proposed_use or '[not supplied]'}",
        f"   Existing use:   {p.existing_use or '[not supplied]'}",
        f"   Floor area:     {f'{p.floor_area_sqm:g}m²' if p.floor_area_sqm else '[not supplied]'}",
        f"   Inside the CBD: {_tri(p.in_cbd)}",
        "",
        "   Site constraints as established so far:",
        f"     Flood     {_tri(p.flood)}",
        f"     Heritage  {_tri(p.heritage)}",
        f"     Bushfire  {_tri(p.bushfire)}",
        _wrap(how.get("constraints", ""), "     "),
        "",
        "-" * 78,
        "2. ALREADY ANSWERED — please do not spend the session on these",
        "-" * 78,
    ]

    settled = _settled(p, result, parking)
    for item in settled:
        lines.append(_bullet(item))
    if not settled:
        lines.append(_wrap("Nothing yet. Supply the address, the proposed use and the "
                           "development type and this section fills itself in.", "   "))

    lines += [
        "",
        "-" * 78,
        "3. QUESTIONS — ask in this order. The session is fifteen minutes.",
        "-" * 78,
    ]
    for n, q in enumerate(questions[:QUESTIONS_IN_THE_SESSION], start=1):
        lines += [
            textwrap.fill(q["question"], width=78,
                          initial_indent=f"   Q{n}. ", subsequent_indent="       "),
            "",
            _wrap(f"Why it matters: {q['why_it_matters']}"),
            _wrap(f"If unresolved: {q['cost_if_unresolved']}"),
            _wrap(f"Ask it as: \"{q['ask_it_as']}\""),
            "",
            "       Answer: " + "_" * 55,
            "               " + "_" * 55,
            "",
        ]
    if not questions:
        lines.append(_wrap("No open questions were raised by what you supplied. That usually "
                           "means the proposal has not been described in enough detail rather "
                           "than that nothing is unsettled.", "   "))

    if len(questions) > QUESTIONS_IN_THE_SESSION:
        lines += [
            "-" * 78,
            "4. IF THERE IS TIME",
            "-" * 78,
        ]
        for q in questions[QUESTIONS_IN_THE_SESSION:]:
            lines.append(_bullet(q["question"]))
            lines.append(_wrap(q["cost_if_unresolved"], "     "))
        lines.append("")

    lines += [
        "-" * 78,
        "5. BEFORE LODGING, REGARDLESS",
        "-" * 78,
        _wrap(REJECTION_WINDOW["plain"], "   "),
        "",
    ]
    for finding in result["findings"]:
        if finding["severity"] in ("stop", "rejection_risk", "confirm_before_lodging"):
            lines.append(_bullet(finding["finding"]))
            lines.append(_wrap(finding["do_this"], "     "))
    for missing in result["documents"]["missing"][:12]:
        lines.append(_bullet(f"Not yet ready: {missing}"))
    lines.append("")

    lines += ["-" * 78, "HOW TO USE THE FIFTEEN MINUTES", "-" * 78]
    for note in HOW_TO_USE_THE_SESSION:
        lines.append(_bullet(note))
    lines += [
        "",
        "   Pre-lodgement meeting, for anything larger than a fitout:",
        f"     {CONTACT_INFO['pre_lodgement_form']}",
        "   Lodgement:",
        f"     {CONTACT_INFO['planning_portal']}",
    ]

    return [TextContent(type="text", text="\n".join(lines))]


def _settled(p: Proposal, result: dict, parking: dict | None) -> list[str]:
    """What has already been answered, so the session is not spent on it.

    Built from what was actually resolved rather than from a fixed list. A
    section claiming the zone is settled when no address was supplied would
    waste the session more surely than saying nothing.
    """
    settled = []
    if p.zone_code:
        settled.append(f"The zone is {p.zone_code}, read from the NSW Land Zoning Map. "
                       "Worth confirming the address matched, not the zoning itself.")
        blocked = any(f["severity"] == "stop" for f in result["findings"])
        if p.proposed_use and not blocked:
            settled.append(f"'{p.proposed_use}' is not prohibited in {p.zone_code} under the LEP "
                           "2012 land use table. (The table is not the whole story — a SEPP can "
                           "permit what it omits — but the table has been checked.)")
    if result["development_type_used"]:
        settled.append("The document checklist for this kind of development, from "
                       "get_da_checklist. Section 5 below lists what is still outstanding.")
    if parking and isinstance(parking["spaces_required"], int):
        settled.append(f"The parking requirement is {parking['spaces_required']} space(s) under "
                       "DCP Chapter 7, and the chapter's remedies for a shortfall are known.")
    if result["approvals_to_list_on_the_application"]:
        settled.append("Which non-DA approvals this business needs — trade waste, food premises "
                       "registration, the Construction and Occupation Certificates and the rest "
                       "— from get_other_approvals.")
    settled.append("How long assessment takes and what stops the clock, from the EP&A "
                   "Regulation. The 40 days is calendar days and is a deemed-refusal threshold, "
                   "not a date Council must decide by — no need to ask.")
    return settled
