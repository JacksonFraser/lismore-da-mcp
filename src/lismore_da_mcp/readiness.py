"""Is this proposal ready to lodge, and what should be asked of Council first.

PLAN.md Phase 3. Almost nothing here is new knowledge — the checklist, the
constraints, the referrals, the parking rate and the statutory content
requirements all already exist in this repository. What did not exist was
anything that ran them against *one proposal at once* and said what was
missing. An applicant had to know to call seven tools and to notice that the
answer to the third one changed what the fifth one required.

Three rules shape it, and they are not the same rules the rest of the server
follows.

**Over-list, like `approvals.py` and unlike everything else.** A requirement
wrongly listed costs a business a sentence of reading; one wrongly omitted
costs it the application. So an unresolved trigger produces the requirement
*plus* the question, never silence.

**A document the applicant says they have is never reported as verified.**
Nothing here can open a file. `document_gap` echoes the applicant's own words
back and matches them conservatively: an unmatched requirement is reported
missing, and words that matched nothing are reported too rather than being
quietly dropped — the failure to prevent is a tool that tells someone their
lodgement is complete when it is not.

**A "ready" verdict is never given.** The most this returns is that nothing it
can check is outstanding, which is a much smaller claim. Council runs the
completeness check, and the grounds it can reject on include ones no tool can
test — whether the description of development is clear, whether the plans are
legible at the scale printed.
"""

import re
from dataclasses import dataclass, field

from lismore_da_mcp.approvals import FOOD_WORDS
from lismore_da_mcp.approvals import relevant as relevant_approvals
from lismore_da_mcp.data.approvals import APPROVALS
from lismore_da_mcp.data.checklists import DA_CHECKLISTS
from lismore_da_mcp.data.checklists import UNIVERSAL_DOCUMENTS
from lismore_da_mcp.data.readiness import DUTY_PLANNER_QUESTIONS
from lismore_da_mcp.data.readiness import REJECTION_GROUNDS
from lismore_da_mcp.data.readiness import STATUTORY_CONTENT
from lismore_da_mcp.data.referrals import CHARACTERISTIC_TRIGGERS
from lismore_da_mcp.data.referrals import REFERRAL_REQUIREMENTS
from lismore_da_mcp.data.zones import ZONES
from lismore_da_mcp.landuse import NOT_A_LAND_USE
from lismore_da_mcp.landuse import canonical_use
from lismore_da_mcp.landuse import classify_land_use
from lismore_da_mcp.vocabulary import CHECKLIST_SYNONYMS
from lismore_da_mcp.vocabulary import DOCUMENT_SYNONYMS
from lismore_da_mcp.vocabulary import resolve


@dataclass
class Proposal:
    """One proposal, as the applicant described it plus what was looked up.

    Constraints are tri-state throughout — True, False, or None for "not
    established" — for the same reason the SEE generator makes them so: "we did
    not find it" and "it is not there" lead to different advice, and in this
    LGA the difference is load-bearing for flood.
    """

    proposed_use: str = ""
    development_type: str = ""
    property_address: str = ""
    zone_code: str = ""
    existing_use: str = ""
    floor_area_sqm: float | None = None
    contravenes_development_standard: bool | None = None
    documents_prepared: list[str] = field(default_factory=list)
    development_characteristics: list[str] = field(default_factory=list)
    in_cbd: bool | None = None
    catchment: str = ""

    flood: bool | None = None
    heritage: bool | None = None
    bushfire: bool | None = None
    constraints_note: str = ""

    @property
    def is_change_of_use(self) -> bool:
        return bool(
            self.existing_use
            or checklist_key(self.development_type) == "change_of_use"
            or canonical_use(self.development_type) in _PROCESS_WORDS
        )

    @property
    def is_food(self) -> bool:
        use = f"{self.proposed_use} {self.development_type}".lower()
        return any(word in use for word in FOOD_WORDS)


_PROCESS_WORDS = {canonical_use(term) for term in NOT_A_LAND_USE}

# Tokens carrying no distinguishing force in a document name. "plan" is
# deliberately absent: it is what separates a site plan from a site survey.
_NOISE = {"a", "an", "the", "of", "for", "and", "or", "to", "with", "in", "on",
          "any", "this", "from", "if", "your", "my", "we", "have", "got"}


def site_constraints(address, asserted_flood=None, asserted_heritage=None):
    """What is known about the site's constraints, and how it was learned.

    A caller's explicit True/False wins. Otherwise the address is looked up, so
    an answer is not silent about the site it is about. Returns tri-state
    values — True, False, or None for "not established" — because "we did not
    find it" and "it is not there" are different things to put in front of an
    applicant, and different things to write in a document going to Council.

    Written for the SEE generator (PLAN.md 1.2) and moved here when the
    readiness check needed the same tri-state rule. One implementation, because
    the rule it encodes — that the flood layer can confirm but never clear —
    is the kind that a second copy quietly loses.
    """
    flood, heritage, bushfire = asserted_flood, asserted_heritage, None
    note = "Constraints as supplied by the applicant."

    if flood is not None and heritage is not None:
        return flood, heritage, bushfire, note

    if not address or address.startswith("["):
        return flood, heritage, bushfire, "No address supplied, so constraints were not checked."

    try:
        from lismore_da_mcp.addresses import lookup_constraints

        result = lookup_constraints(address)
    except Exception:                                          # noqa: BLE001
        return flood, heritage, bushfire, "The constraint lookup was unavailable."

    if "error" in result:
        return flood, heritage, bushfire, (
            "Constraints could not be looked up for this address "
            f"({result['error']}). They must be confirmed with Council."
        )

    found = result.get("constraints", {})
    if heritage is None:
        answer = found.get("heritage", {}).get("answer")
        heritage = True if answer == "affected" else (False if answer == "not_within_a_mapped_area" else None)
    answer = found.get("bushfire", {}).get("answer")
    bushfire = True if answer == "affected" else (False if answer == "not_within_a_mapped_area" else None)
    if flood is None:
        # Deliberately not set from the layer. The state flood dataset holds no
        # Lismore data at all, so it can confirm flooding but never rule it out;
        # treating "not found" as "not flood affected" would be the single most
        # harmful thing this could assert.
        flood = None

    return flood, heritage, bushfire, (
        f"Heritage and bushfire read from the NSW planning layers for "
        f"{result.get('matched_address')}. Flood was not, and cannot be, ruled out this way."
    )


def checklist_key(term: str) -> str | None:
    """The DA_CHECKLISTS key a development type resolves to, or None."""
    match = resolve(term or "", DA_CHECKLISTS, CHECKLIST_SYNONYMS)
    return match.key if match else None


def short_name(document: str) -> str:
    """The document's name, without the explanation that follows it.

    Checklist entries are written to be read — "Access report — compliance with
    the Disability (Access to Premises) Standards (commonly required)" — so the
    name is the part before the em dash or the parenthesis. Matching against the
    whole string instead would let any two entries mentioning "Council" look
    alike.
    """
    name = document.split(" — ")[0].split(" (")[0]
    return name.strip().rstrip(",.")


def _words(text: str) -> list[str]:
    """Comparable words, in order.

    Punctuation is stripped before `canonical_use` singularises, or the comma in
    "Operating hours, staff numbers" leaves the token "hour," which matches
    nothing an applicant would type.
    """
    cleaned = re.sub(r"[^a-z0-9 ]", " ", canonical_use(text))
    return [w for w in cleaned.split() if len(w) > 1 and w not in _NOISE]


def _tokens(text: str) -> set[str]:
    return set(_words(text))


def _expand(claim: str) -> str:
    """Turn a counter-shorthand into the phrasing the checklists use.

    'SEE' shares no word at all with 'Statement of Environmental Effects', so
    without this the single most universally prepared document in a DA is
    reported missing to anyone who calls it by its acronym.
    """
    return DOCUMENT_SYNONYMS.get(str(claim).strip().lower(), claim)


def _claims(claim: str, requirement: str) -> bool:
    """Does this claim plausibly refer to this requirement?

    Deliberately strict in one direction. Requiring the head noun to agree stops
    "fire safety schedule" from being accepted as "fire safety upgrade report" —
    two documents that share most of their words and none of their content. The
    cost of being strict is a requirement listed as missing that the applicant
    already has, which they will notice; the cost of being loose is a lodgement
    reported complete that Council rejects.
    """
    claim_words, name_words = _words(_expand(claim)), _words(short_name(requirement))
    claim_tokens, name_tokens = set(claim_words), set(name_words)
    if not claim_tokens or not name_tokens:
        return False
    if claim_tokens <= name_tokens or name_tokens <= claim_tokens:
        return True
    # Both ends have to agree: the head noun says what the document *is*, and
    # the first word says what it is *about*. Overlap alone is not enough —
    # "waste management plan" and "stormwater management plan" share two words
    # out of three, agree on the head, and are different documents.
    return (claim_words[-1] == name_words[-1]
            and claim_words[0] == name_words[0]
            and len(claim_tokens & name_tokens) >= 2)


def document_gap(required: list[str], claimed: list[str]) -> dict:
    """Which required documents the applicant has said they have.

    Never asserts a document is adequate, only that it was named. Words that
    matched no requirement come back under `not_recognised` rather than being
    dropped — an applicant who typed a document nobody asked for should be told
    so, not left believing it counted.
    """
    claimed = [c for c in (claimed or []) if str(c).strip()]
    matched: dict[str, list[str]] = {}
    for requirement in required:
        hits = [c for c in claimed if _claims(c, requirement)]
        if hits:
            matched[requirement] = hits

    used = {c for hits in matched.values() for c in hits}
    return {
        "said_to_be_ready": [
            {"requirement": r, "you_listed": hits} for r, hits in matched.items()
        ],
        "missing": [r for r in required if r not in matched],
        "not_recognised": [c for c in claimed if c not in used],
    }


def _permissibility(p: Proposal) -> list[dict]:
    """Can this use operate on this land at all. The one true blocker."""
    if canonical_use(p.proposed_use) in _PROCESS_WORDS:
        return [{
            "severity": "stop",
            "finding": f"'{p.proposed_use}' describes the work, not the use that will operate "
                       "on the land, so permissibility has not been checked at all.",
            "why": "The LEP land use table answers one question — may this use operate here. "
                   "Asked with a process word it falls through to the table's catch-all and "
                   "returns a confident answer to a question nobody asked.",
            "do_this": "Re-run with the use itself: 'restaurant or cafe' for a cafe, "
                       "'office premises' for an office. Put the change of use in "
                       "development_type instead.",
        }]

    if not p.zone_code:
        return [{
            "severity": "stop",
            "finding": "The zone is not known, so nothing here has checked whether the use is "
                       "permitted.",
            "why": "Permissibility is the first thing that can stop an application, and it is "
                   "the cheapest to check.",
            "do_this": "Supply property_address, or zone_code if you already know it. "
                       "lookup_zone_by_address derives it from the address — never guess it.",
        }]

    zone = ZONES.get(p.zone_code.upper())
    if not zone:
        return [{
            "severity": "stop",
            "finding": f"Zone '{p.zone_code}' is not a Lismore LEP 2012 zone.",
            "why": "The B and IN series were retired in 2023 — B3 is now E2, IN1 is now E4.",
            "do_this": "Call list_zones for the current codes.",
        }]

    classified = classify_land_use(p.proposed_use, zone, p.zone_code.upper())
    if not classified:
        return []
    if classified["permissible"] is False:
        return [{
            "severity": "stop",
            "finding": classified["statement"],
            "why": "A prohibited use cannot be approved in the zone, so the application would "
                   "be refused rather than rejected — and that costs the fee, the drafting and "
                   "the wait.",
            "do_this": "Check the result against check_permissibility, which explains the "
                       "match. Note this reads the LEP land use table only: a State "
                       "Environmental Planning Policy can permit a use the table omits and "
                       "prevails over the LEP, so this is not a settled refusal. Take it to the "
                       "Duty Planner before abandoning the site.",
        }]
    if classified["permissible"] is None:
        return [{
            "severity": "address_in_the_see",
            "finding": classified["statement"],
            "why": "An unsettled permissibility question becomes Council's first question, and "
                   "it is asked before anything else is assessed.",
            "do_this": "Settle the land use term with the Duty Planner and use Council's term "
                       "in the description of development. get_definition gives the Standard "
                       "Instrument definitions.",
        }]
    return []


def _statutory(p: Proposal, approval_names: list[str]) -> list[dict]:
    """The Regulation's own content requirements, and the s39 grounds they map to."""
    findings = []

    # s25(b) with s39(1)(d). The rejection ground businesses have never heard
    # of: the application must *list* the other approvals, and a blank field is
    # a ground to reject rather than an omission to be tidied up later.
    findings.append({
        "severity": "confirm_before_lodging",
        "finding": "The application must list the other approvals this development needs, "
                   "whether or not you have them yet.",
        "why": STATUTORY_CONTENT["list_of_approvals"]["plain"],
        "source": f"{STATUTORY_CONTENT['list_of_approvals']['clause']}; "
                  f"{REJECTION_GROUNDS['approvals_not_identified']['clause']}",
        "do_this": "List these, at least: " + ", ".join(approval_names)
                   + ". get_other_approvals returns them with the issuing authority for each.",
    })

    if p.contravenes_development_standard:
        findings.append({
            "severity": "rejection_risk",
            "finding": "A written request under LEP clause 4.6 must accompany the application.",
            "why": STATUTORY_CONTENT["clause_4_6_request"]["plain"],
            "source": STATUTORY_CONTENT["clause_4_6_request"]["clause"],
            "do_this": "Address both limbs: why compliance is unreasonable or unnecessary here, "
                       "and what environmental planning grounds justify the contravention. "
                       "Arguing only that the proposal is reasonable answers half the test.",
        })
    elif p.contravenes_development_standard is None:
        findings.append({
            "severity": "confirm_before_lodging",
            "finding": "It has not been stated whether the proposal contravenes a development "
                       "standard — height, floor space ratio or minimum lot size.",
            "why": "If it does, a clause 4.6 request has to be in the application. Offering one "
                   "after Council notices the breach is a request for information at best.",
            "do_this": "lookup_site_constraints reads the height limit and minimum lot size for "
                       "the address. A DCP control is not a development standard and clause 4.6 "
                       "does not apply to it — that is argued as a variation instead.",
        })

    if checklist_key(p.development_type) == "dwelling" or "dwelling" in p.proposed_use.lower():
        findings.append({
            "severity": "confirm_before_lodging",
            "finding": "A BASIX certificate must accompany the application and must have been "
                       "issued no earlier than three months before you submit.",
            "why": STATUTORY_CONTENT["basix_certificate"]["plain"],
            "source": STATUTORY_CONTENT["basix_certificate"]["clause"],
            "do_this": "Check the issue date on the certificate you hold before submitting, not "
                       "after.",
        })

    findings.append({
        "severity": "confirm_before_lodging",
        "finding": "The description of development has to say plainly what consent is sought.",
        "why": REJECTION_GROUNDS["unclear"]["means"],
        "source": REJECTION_GROUNDS["unclear"]["clause"],
        "do_this": _suggested_description(p),
    })
    return findings


def _suggested_description(p: Proposal) -> str:
    """A description of development built from what the applicant actually said."""
    use = p.proposed_use or "[the use]"
    if p.is_change_of_use:
        from_use = p.existing_use or "[the existing approved use]"
        core = f"Change of use from {from_use} to {use}"
    else:
        core = f"Development for the purposes of {use}"
    extras = []
    if p.floor_area_sqm:
        extras.append(f"{p.floor_area_sqm:g}m² gross floor area")
    extras.append("associated fitout")
    return (f"Something in the shape of: \"{core}, with " + " and ".join(extras) + "\". "
            "Name the use, the change, and every component you want consented — signage "
            "included, since a component left out of the description is not consented.")


def _site(p: Proposal) -> list[dict]:
    """What the site itself requires be in the application."""
    findings = []

    # Flood is unconditional in this LGA, for the same reason the SEE generator
    # makes it unconditional: the state flood layer holds no Lismore features
    # at all, so nothing here can rule flooding out, and an application silent
    # on flood is one Council comes back on.
    if p.flood:
        findings.append({
            "severity": "incomplete",
            "finding": "The site is flood affected. A Flood Risk Assessment and floor levels "
                       "relative to the Flood Planning Level are required.",
            "why": "LEP 2012 clause 5.21 and DCP Chapter 8. For commercial development a "
                   "proportion of the gross floor area must sit above the Flood Planning Level.",
            "source": "LEP 2012 cl 5.21; DCP Chapter 8",
            "do_this": "get_flood_requirements for the requirement; ask Council for the Flood "
                       "Planning Level at the address.",
        })
    else:
        findings.append({
            "severity": "address_in_the_see",
            "finding": "Flood has not been established for this site — and cannot be ruled out "
                       "from mapping here.",
            "why": "The NSW state Flood Planning Map holds no features for the Lismore LGA, so "
                   "an empty result means the dataset does not cover this council, not that the "
                   "site is unaffected. Much of the LGA is flood affected and the CBD was "
                   "inundated in 2022.",
            "source": "LEP 2012 cl 5.21; DCP Chapter 8",
            "do_this": "Ask Council for the flood status and the Flood Planning Level at the "
                       "address before lodging. An application that says nothing about flood in "
                       "this LGA invites the first request for information.",
        })

    if p.heritage:
        findings.append({
            "severity": "incomplete",
            "finding": "The site is heritage affected. A Heritage Impact Statement is required.",
            "why": "DCP Chapter 12 and LEP Schedule 5. It also changes what signage is "
                   "available: DCP §9.2 prohibits advertising in a heritage area, excepting "
                   "building and business identification signs.",
            "source": "DCP Chapter 12; DCP §9.2",
            "do_this": "get_signage_requirements with is_heritage set, before designing a sign.",
        })
    elif p.heritage is None:
        findings.append({
            "severity": "address_in_the_see",
            "finding": "Heritage status has not been established.",
            "why": "Unestablished is not the same as clear, and a Heritage Impact Statement is "
                   "not something to discover you need at lodgement.",
            "source": "LEP 2012 Schedule 5",
            "do_this": "lookup_site_constraints reads the mapped heritage layer; conservation "
                       "areas are Council's own mapping and are a Duty Planner question.",
        })

    if p.bushfire:
        findings.append({
            "severity": "incomplete",
            "finding": "The site is bushfire prone. A bushfire assessment is required, and the "
                       "application is likely integrated development.",
            "why": "A Bushfire Safety Authority under s100B of the Rural Fires Act is an "
                   "approval under EP&A Act s4.46 — which makes the application integrated, "
                   "extends the assessment period to 60 days, and must be listed on the "
                   "application.",
            "source": "Rural Fires Act s100B; EP&A Regulation s25(b), s39(1)(d)",
            "do_this": "check_referrals with 'bushfire_prone' for the documents the RFS needs.",
        })

    if p.is_change_of_use:
        findings.append({
            "severity": "address_in_the_see",
            "finding": "Contamination has to be addressed where the use becomes more sensitive.",
            "why": "A workshop, service station or dry cleaner becoming a food premises or a "
                   "child care centre can require a Preliminary Site Investigation with no "
                   "building work at all. It is listed here whether or not it applies, because "
                   "discovering it at lodgement costs weeks and a consultant's lead time.",
            "source": "Conditional document in get_da_checklist",
            "do_this": "If the previous use was industrial or automotive, commission the "
                       "Preliminary Site Investigation now rather than when asked.",
        })
    return findings


def referral_triggers(p: Proposal) -> dict:
    """Referrals the proposal appears to trigger, from characteristics and site.

    Derived triggers are kept apart from stated ones. A site flagged on the
    heritage layer is not necessarily on the State Heritage Register, and only
    the State Register brings Heritage Council concurrence — so a derived
    trigger produces a question about integrated development, never an
    assertion that the application is integrated.
    """
    triggered: dict[str, str] = {}
    unrecognised = []
    for characteristic in p.development_characteristics or []:
        text = str(characteristic).lower().replace(" ", "_")
        hit = next((r for key, r in CHARACTERISTIC_TRIGGERS.items() if key in text), None)
        if hit:
            triggered[hit] = f"stated: '{characteristic}'"
        else:
            unrecognised.append(characteristic)

    if p.bushfire:
        triggered.setdefault("rural_fire_service", "site is on bushfire prone land")
    if p.heritage:
        triggered.setdefault(
            "heritage_council",
            "site is heritage affected — Heritage Council concurrence applies only to State "
            "Heritage Register items, which the mapping here does not distinguish")
    if p.flood:
        triggered.setdefault("council_flood_assessment", "site is flood affected")

    return {
        "triggered": {
            key: {"because": why, **{k: v for k, v in REFERRAL_REQUIREMENTS.get(key, {}).items()
                                     if k in ("trigger", "approval", "documents")}}
            for key, why in triggered.items()
        },
        "not_recognised": unrecognised,
    }


def open_questions(p: Proposal, has_parking_shortfall: bool | None = None) -> list[dict]:
    """The Duty Planner questions this proposal actually raises, in cost order.

    Every one of these is a question some tool in this server declined to
    answer. Assembling them is the whole point: individually each looked like a
    caveat on one answer, and together they are the agenda for the fifteen free
    minutes that can settle them.
    """
    triggered = bool(referral_triggers(p)["triggered"])
    applies = {
        "codes_sepp_or_existing_use_rights": p.is_change_of_use,
        "cbd_boundary": p.in_cbd is None,
        "flood_planning_level": True,
        "section_64_charge": p.is_food or bool(p.floor_area_sqm),
        "contribution_catchment": not p.catchment,
        "existing_use_allowance": p.is_change_of_use,
        "integrated_development": triggered,
        "parking_contribution_in_lieu": has_parking_shortfall is not False and p.in_cbd is not False,
        "heritage_status": p.heritage is None,
        "gfa_increase_within_tenancy": p.is_change_of_use,
    }
    return [q for q in DUTY_PLANNER_QUESTIONS if applies.get(q["key"])]


def assess(p: Proposal, has_parking_shortfall: bool | None = None) -> dict:
    """Everything outstanding on this proposal, worst first."""
    checklist = checklist_key(p.development_type) or checklist_key(p.proposed_use)
    required = list(UNIVERSAL_DOCUMENTS)
    if checklist:
        required += DA_CHECKLISTS[checklist]["documents"]

    approval_keys, approval_questions = relevant_approvals(
        p.proposed_use, connected_to_sewer=None)
    approval_names = [APPROVALS[k]["name"] for k in approval_keys]

    documents = document_gap(required, p.documents_prepared)
    findings = _permissibility(p) + _statutory(p, approval_names) + _site(p)

    # One finding carrying the list, rather than one finding per document. The
    # reasoning is identical for every entry, and repeating it fifteen times
    # buries the rejection risks above it under a wall the reader skips.
    if documents["missing"]:
        findings.append({
            "severity": "incomplete",
            "finding": f"{len(documents['missing'])} required document(s) not listed as ready.",
            "not_ready": documents["missing"],
            "why": "Required by Council's checklist for this kind of development. An incomplete "
                   "lodgement does not pass the completeness check, so the fee is not paid, so "
                   "the application is not lodged and no clock starts — the weeks spent going "
                   "back and forth before lodgement are not in the assessment period at all.",
            "source": f"get_da_checklist ({checklist})" if checklist
                      else "documents required for every DA",
            "do_this": "Prepare each, or where one does not apply, say so in the SEE rather than "
                       "leaving the gap unexplained. If you have a document listed here, name it "
                       "in documents_prepared — matching is conservative, so anything not "
                       "clearly recognised is reported as missing.",
        })

    # "confirm_before_lodging" is separated from "rejection_risk" deliberately.
    # Sections 25 and 39(1)(a) apply to every application, so emitting them as
    # deficiencies made the verdict read "not ready" for every proposal ever
    # checked — a warning present on every answer carries no information, which
    # is how the fee scale sat two years stale behind a standing caveat
    # (PLAN.md 0.1). They are still statutory and still rejection grounds; they
    # are simply not evidence that this proposal has something wrong with it.
    order = {"stop": 0, "rejection_risk": 1, "incomplete": 2,
             "confirm_before_lodging": 3, "address_in_the_see": 4}
    findings.sort(key=lambda f: order.get(f["severity"], 9))

    blocking = [f for f in findings if f["severity"] == "stop"]
    return {
        "development_type_used": checklist,
        "findings": findings,
        "documents": documents,
        "referrals": referral_triggers(p),
        "approvals_to_list_on_the_application": approval_names,
        "approval_questions": approval_questions,
        "questions_for_council": open_questions(p, has_parking_shortfall),
        "blocking": bool(blocking),
    }
