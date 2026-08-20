"""What a lodgeable DA must contain, what gets one rejected, and what only Council can answer.

PLAN.md Phase 3. Two halves, and they come from opposite places.

The first half is **statutory**: sections 24, 25, 27 and 35B of the
Environmental Planning and Assessment Regulation 2021 say what a development
application must contain, and section 39 says what a consent authority may
reject it for. Both are quoted verbatim from
`documents/legislation/epa-regulation-2021-assessment-periods.txt` — the same
fetched text `data/timing.py` draws on — and `scripts/audit_readiness.py`
checks they still appear in it. `data/timing.py` already carries s39's
*consequence* (an application rejected under it is "taken never to have been
made"); this module carries its *grounds*, paragraph by paragraph, because a
tool that is trying to prevent a rejection needs to check against each one
rather than against a summary.

The rejection grounds are worth reading before writing anything that acts on
them. Every one of them is **administrative** — an illegible application, a
missing document, an unidentified approval. None is about the merits of the
proposal. That is the whole reason Phase 3 is possible at all: the failure this
prevents is one a checklist can actually catch, unlike a refusal.

The second half is the opposite: **`DUTY_PLANNER_QUESTIONS` is the list of
things no document in this repository can settle.** Each one was found by an
earlier item hitting a wall and declining to guess — the CBD boundary that is a
bitmap (PLAN.md 2.2), the Section 7.11 catchment that changes retail rates by
20% (2.1), the Section 64 charge whose plan carries no non-residential
conversion table (2.1), the contribution-in-lieu rate that cites a repealed
Act (2.2). Those refusals are correct and they stay. What was missing is that
they were scattered across five tools' outputs, so nobody assembled them into
the one thing they are collectively good for: the agenda for the free
fifteen-minute Duty Planner session, which is the cheapest advice in this
process and the only place these can be answered.

Each carries what it costs to leave unresolved, because fifteen minutes does
not fit ten questions and the applicant has to choose.
"""

REGULATION = "Environmental Planning and Assessment Regulation 2021"
SOURCE_DOC = "documents/legislation/epa-regulation-2021-assessment-periods.txt"

# What the Regulation requires a DA to contain. This is separate from Council's
# document checklist (`data/checklists.py`): the checklist is what a good
# application carries, this is what the law requires, and only the second one
# gets an application rejected outright.
STATUTORY_CONTENT = {
    "approved_form": {
        "clause": "s24(1)",
        # Quoted as two fragments because the regulation prints a worked example
        # between paragraphs (b) and (c), so the section does not read
        # continuously in the source and a single quote spanning them would be
        # one this repository's own audit could not verify.
        "verbatim": "A development application must—(a) be in the approved form, and (b) contain "
                    "all the information and documents required by—(i) the approved form, and "
                    "(ii) the Act or this Regulation",
        "and": {
            "clause": "s24(1)(c)",
            "verbatim": "be submitted on the NSW planning portal",
        },
        "plain": "Everything below is required by this section. The Portal's own form is the "
                 "approved form, so its mandatory fields are statutory requirements rather than "
                 "administrative preference.",
        "applies_to": "Every development application.",
    },
    "when_it_is_lodged": {
        "clause": "s24(3)",
        "verbatim": "A development application is lodged—(a) on the day on which the fees payable "
                    "for the development application under this Regulation are paid",
        "plain": "Submitting is not lodging. Nothing starts — not the assessment period, not the "
                 "14-day rejection window — until the fee is paid, and the fee cannot be paid "
                 "until the application passes the completeness check.",
        "applies_to": "Every development application.",
    },
    "list_of_approvals": {
        "clause": "s25",
        "verbatim": "A development application must contain the following information—(a) a list "
                    "of the provisions of an Act or environmental planning instrument requiring "
                    "concurrence to be obtained before granting development consent, (a1) a list "
                    "of the provisions of an Act or environmental planning instrument requiring "
                    "the consent authority to consult with a consultation body before granting "
                    "development consent, (b) a list of the approvals of the kind referred to in "
                    "the Act, section 4.46(1) that must be obtained before the development may "
                    "lawfully be carried out.",
        "plain": "The application has to *list* the other approvals the development needs. This "
                 "is a content requirement, not a suggestion, and it is the one most often met "
                 "with a blank field — the applicant reads it as asking whether the approvals "
                 "have been obtained, which is not what it asks. Where the development is "
                 "integrated, section 39(1)(d) additionally makes failing to identify them a "
                 "ground to reject the application outright.",
        # s25(b) applies to every application; s39(1)(d) opens "for an
        # application for integrated development" and does not. Citing the
        # rejection ground against every proposal overstates the consequence for
        # the ordinary business DA, which is not integrated. SCENARIOS.md D12.
        "applies_to": "Every development application — this content requirement is not limited "
                      "to integrated development. The *rejection ground* in s39(1)(d) is: it "
                      "reads 'for an application for integrated development', so for a "
                      "non-integrated DA a missing list is a deficiency to fix rather than a "
                      "ground to reject.",
    },
    "basix_certificate": {
        "clause": "s27(1)",
        "verbatim": "A development application for BASIX development must be accompanied by—(a) a "
                    "relevant BASIX certificate for the development issued no earlier than 3 "
                    "months before the day on which the development application is submitted on "
                    "the NSW planning portal, and (b) the other matters required by the BASIX "
                    "certificate.",
        "plain": "The certificate expires for lodgement purposes at three months. One obtained "
                 "early in a project and held while plans were finalised is a common way to have "
                 "a residential DA sent back for a document the applicant believes it has.",
        "applies_to": "BASIX development — residential. A commercial fitout is not BASIX "
                      "development; shop-top housing above it can be.",
    },
    "clause_4_6_request": {
        "clause": "s35B(2)",
        "verbatim": "The development application must be accompanied by a document that sets out "
                    "the grounds on which the applicant seeks to demonstrate that—(a) compliance "
                    "with the development standard is unreasonable or unnecessary in the "
                    "circumstances, and (b) there are sufficient environmental planning grounds "
                    "to justify the contravention of the development standard.",
        "plain": "A written request under LEP clause 4.6 has to be *in* the application, not "
                 "offered later when the breach is noticed. The two limbs above are the whole "
                 "test, and a request that argues only that the proposal is reasonable — without "
                 "addressing why compliance is unnecessary — has answered half of it.",
        "applies_to": "Any proposal contravening a development standard: height, floor space "
                      "ratio, minimum lot size. Not a DCP control — a DCP variation is argued "
                      "differently and clause 4.6 does not apply to it.",
    },
}

# s39(1). Carried in full, including the paragraphs that cannot apply to a
# Lismore business, because a list of five out of six grounds invites the reader
# to wonder what was left out. `not_applicable_here` says which and why.
REJECTION_GROUNDS = {
    "unclear": {
        "clause": "s39(1)(a)",
        "verbatim": "the application is illegible or unclear about the development consent sought",
        "means": "The application has to say plainly what consent is being sought. For a business "
                 "this is usually the description of development: 'fitout' or 'renovation' does "
                 "not name a consent, where 'change of use from shop to food and drink premises "
                 "(cafe), with associated fitout and signage' does.",
    },
    "missing_documents": {
        "clause": "s39(1)(b)",
        "verbatim": "the application does not contain the information and documents that are "
                    "required by—(i) the approved form, or (ii) the Act or this Regulation",
        "means": "The broadest ground and the one that catches most rejections. It covers "
                 "everything in STATUTORY_CONTENT and every mandatory field of the Portal form.",
    },
    "state_significant_incomplete": {
        "clause": "s39(1)(c)",
        "verbatim": "for an application for State significant development—the Planning Secretary "
                    "considers the application incomplete for reasons given by written notice to "
                    "the applicant",
        "means": "State significant development only.",
        "not_applicable_here": "No local business DA is State significant development — the "
                               "thresholds are in the Planning Systems SEPP and are far above a "
                               "shop, cafe or workshop.",
    },
    "approvals_not_identified": {
        "clause": "s39(1)(d)",
        "verbatim": "for an application for integrated development—the application does not "
                    "identify all of the approvals required to be obtained, as referred to in the "
                    "Act, section 4.46, before the development may be carried out",
        "means": "This is section 25(b) with teeth. If the development is integrated — it needs "
                 "an approval from another agency as well as consent — and the application does "
                 "not name every one of them, it can be rejected. Naming them costs nothing; "
                 "missing one costs the application.",
    },
    "no_biodiversity_report": {
        "clause": "s39(1)(e)",
        "verbatim": "for an application required to be accompanied by a biodiversity development "
                    "assessment report under the Biodiversity Conservation Act 2016—the "
                    "application is not accompanied by a report",
        "means": "Triggered by clearing above the Biodiversity Offsets Scheme threshold or an "
                 "impact on threatened species. Rare on an urban fitout; real on a rural or "
                 "greenfield site.",
    },
    "no_species_impact_statement": {
        "clause": "s39(1)(f)",
        "verbatim": "for an application required to be accompanied by a species impact statement "
                    "under the Fisheries Management Act 1994, section 221ZW—the application is "
                    "not accompanied by a statement",
        "means": "Aquatic habitat — dredging, reclamation, works in a waterway.",
    },
}

# The 14-day window, quoted here because it is the sentence that makes this
# whole check worth running before lodgement rather than after.
REJECTION_WINDOW = {
    "clause": "s39(1)",
    "verbatim": "A consent authority may reject a development application within 14 days after "
                "receiving the application if—",
    "plain": "Rejection happens in the first fortnight, before assessment starts. By the time "
             "anyone has looked at the merits the risk has passed — which is why the fortnight "
             "before lodgement is where this is cheap to fix. What a rejection costs is in "
             "get_assessment_timeline: the application is taken never to have been made.",
}

# Everything below here is not from the Regulation. These are the questions the
# tools in this repository have refused to answer, each with the reason it was
# refused. Ordered by what it costs to leave unresolved, because the Duty
# Planner session is fifteen minutes and this list is longer than that.
#
# `applies` is prose for the reader; `readiness.py` decides applicability. No
# logic lives in this module.
DUTY_PLANNER_QUESTIONS = [
    {
        "key": "codes_sepp_or_existing_use_rights",
        "question": "Is this change of use exempt or complying development under the Codes SEPP, "
                    "or do existing use rights apply — and if so, do I need a DA at all?",
        "why_it_matters": "This is the only question on the list that can remove the entire "
                          "application. Some changes of use between similar commercial uses need "
                          "no consent; where the current use is no longer permissible, existing "
                          "use rights may carry it.",
        "cost_if_unresolved": "A DA that did not have to be lodged: the fee, the contribution, "
                              "the drafting, and six weeks of rent on premises that could have "
                              "opened.",
        "why_we_cannot_answer_it": "It turns on the SEPP and on the site's approval history, "
                                   "neither of which is in this repository. The LEP land use "
                                   "table cannot answer it.",
        "applies": "Any change of use or fitout of existing premises.",
        "ask_it_as": "Here is the existing approved use and here is what I want to do. Is this "
                     "exempt or complying development, or does it need a DA?",
    },
    {
        "key": "cbd_boundary",
        "question": "Is this site inside the Lismore CBD as Map 1 of DCP Chapter 7 draws it?",
        "why_it_matters": "It decides which parking rate applies, and the two are not close. "
                          "Inside the CBD it is a fixed 3.3 spaces per 100m² of gross floor area "
                          "(§7.7.3.1); outside it, the Schedule 1 rate. On an 80m² cafe that is "
                          "the difference between owing three spaces and owing fourteen.",
        "cost_if_unresolved": "A parking case argued against the wrong rate — and a proposal "
                              "abandoned over a shortfall that was never real.",
        "why_we_cannot_answer_it": "Map 1 is a bitmap on the last page of the chapter with no "
                                   "extractable text. The E2 zone runs close to that line but is "
                                   "not the same line, so it cannot be inferred from the zone.",
        "applies": "Any non-residential proposal where the parking requirement matters.",
        "ask_it_as": "Is this address inside the CBD boundary on Map 1 of DCP Chapter 7?",
    },
    {
        "key": "flood_planning_level",
        "question": "Is this site in the flood planning area, and what is the Flood Planning "
                    "Level for it?",
        # "the exemption precinct's evacuation and refuge requirements" was here
        # until 2026-08-20. There is no such precinct in DCP Chapter 8, in LEP
        # 2012 or anywhere in documents/ — CLAUDE.md recorded it as invented and
        # removed on 2026-08-06 and this copy survived into the Duty Planner
        # brief. SCENARIOS.md D11.
        "why_it_matters": "It sets the minimum floor level, and for a commercial fitout it "
                          "decides how much of the floor area has to sit above that level. "
                          "Which controls apply turns on the flood hazard area from Map 1 of "
                          "DCP Chapter 8 — the High Flood Risk Area requires a mezzanine refuge "
                          "above the 1-in-500 year level and the Flood Fringe does not, so the "
                          "area matters as much as the level.",
        "cost_if_unresolved": "The single most likely subject of a request for information on a "
                              "Lismore commercial DA, and the one most likely to change the "
                              "design after the lease is signed.",
        "why_we_cannot_answer_it": "The NSW state Flood Planning Map holds no features at all "
                                   "for the Lismore LGA, so mapping can confirm flooding here "
                                   "but can never rule it out. Council holds the flood levels "
                                   "and provides them on request.",
        "applies": "Every proposal in this LGA. Much of it is flood affected and the CBD was "
                   "inundated in 2022.",
        "ask_it_as": "What is the Flood Planning Level at this address, and what floor level "
                     "will Council require for this use?",
    },
    {
        "key": "section_64_charge",
        "question": "What will the Section 64 water and wastewater headworks charge be for this "
                    "use?",
        "why_it_matters": "For a food premises it is large, it is payable before the Construction "
                          "Certificate, and it is the charge most likely to arrive as a surprise "
                          "after the budget is set.",
        "cost_if_unresolved": "An unbudgeted four- or five-figure charge at the point where the "
                              "fitout is meant to start.",
        "why_we_cannot_answer_it": "The Development Servicing Plan's rates are in 2016 dollars, "
                                   "indexed annually, and it carries no table converting a "
                                   "non-residential use into equivalent tenements. Only Council "
                                   "can do that conversion.",
        "applies": "Any use that increases water or wastewater demand — every food premises, and "
                   "most changes of use into one.",
        "ask_it_as": "How many equivalent tenements will Council assess this use at, and what is "
                     "the current charge per ET?",
    },
    {
        "key": "contribution_catchment",
        "question": "Which Section 7.11 contributions catchment is this site in?",
        "why_it_matters": "The rates differ by catchment, and for retail the rural rate is 20% "
                          "higher than the urban one — $24,210 against $20,102 per 100m². It is "
                          "usually the largest single number in the whole application.",
        "cost_if_unresolved": "A contribution estimate that is out by a fifth, in a budget where "
                              "the contribution is typically many times the lodgement fee.",
        "why_we_cannot_answer_it": "The catchment is not derivable from the address by anything "
                                   "here, and defaulting to urban would quietly understate every "
                                   "village proposal.",
        "applies": "Any proposal where a Section 7.11 contribution is payable.",
        "ask_it_as": "Which contributions catchment does this address fall in under the Section "
                     "7.11 Plan 2024-2041?",
    },
    {
        "key": "existing_use_allowance",
        "question": "Will Council accept the previous use as the lawful existing use for the "
                    "Section 7.11 allowance, and what evidence does it want?",
        "why_it_matters": "Section 2.7 of the plan charges the contribution on the *increase* in "
                          "demand over the existing lawful use. Shop to cafe comes to nil; office "
                          "to cafe comes to about $12,310 on 80m². The allowance is not automatic "
                          "and has to be evidenced with the application.",
        "cost_if_unresolved": "A contribution levied in full because the previous use was "
                              "asserted rather than evidenced — argued after the consent is "
                              "conditioned, which is far harder than lodging the evidence.",
        "why_we_cannot_answer_it": "It depends on the site's approval history and on what Council "
                                   "accepts as proof of it. Ask under the word 'allowance': "
                                   "'credit' is section 2.8 and means negotiated works-in-kind, "
                                   "which is a different provision.",
        "applies": "Any change of use where the previous use generated demand of its own.",
        "ask_it_as": "The premises was last used as X. What evidence do you need for the section "
                     "2.7 allowance for the existing development?",
    },
    {
        "key": "integrated_development",
        "question": "Is this integrated development, and which approvals should the application "
                    "list under section 25(b)?",
        "why_it_matters": "Two things follow. The assessment period becomes 60 days instead of "
                          "40, and failing to identify every approval is a ground to reject the "
                          "application outright under s39(1)(d).",
        "cost_if_unresolved": "A rejection — which is not a delay. The application is taken never "
                              "to have been made and starts again from zero.",
        "why_we_cannot_answer_it": "check_referrals lists the likely triggers, but whether a "
                                   "given approval is actually required is the referral agency's "
                                   "call and Council makes the referral.",
        "applies": "Any proposal triggering a referral — bushfire, waterway, vegetation, "
                   "state heritage, a scheduled activity, or access to a classified road.",
        "ask_it_as": "Do you consider this integrated development, and which approvals should I "
                     "list on the application?",
    },
    {
        "key": "parking_contribution_in_lieu",
        "question": "Is a contribution in lieu of parking available for this site, and at what "
                    "rate?",
        "why_it_matters": "DCP §7.7.3.3 provides for consolidated parking in the CBD — paying "
                          "rather than building the spaces, with the amount paid reduced by a "
                          "further 25%. For a tenancy that physically cannot fit a car space it "
                          "is often the only way through.",
        "cost_if_unresolved": "A shortfall argued as a hardship when it could have been paid, or "
                              "a budget with no line for it.",
        "why_we_cannot_answer_it": "The DCP sets the mechanism but points at the repealed Section "
                                   "94 and at a plan section that does not exist in the current "
                                   "plan, and the Section 7.11 Plan 2024-2041 has no car parking "
                                   "contribution category. The rate is not recoverable from any "
                                   "document held here.",
        "applies": "Any CBD proposal that cannot meet its parking requirement on site.",
        "ask_it_as": "Chapter 7 §7.7.3.3 allows a contribution in lieu of parking. Is that "
                     "available here, and what is the current rate?",
    },
    {
        "key": "heritage_status",
        "question": "Is this site a heritage item, or in a heritage conservation area?",
        "why_it_matters": "It brings in LEP cl 5.10, under which Council *may* require a "
                          "heritage management document — ask which form, rather than "
                          "commissioning a Heritage Impact Statement on spec. It also brings in "
                          "DCP Chapter 12, and for signage the §9.2 prohibition, under which "
                          "only building and business identification signs remain available. "
                          "Ask about cl 5.10(10) too if the land use table prohibits your use: "
                          "a heritage building can be approved for a purpose the Plan would "
                          "otherwise disallow, where the use funds its conservation.",
        "cost_if_unresolved": "A document missing from the lodgement, and a signage proposal "
                              "designed against the wrong rules.",
        "why_we_cannot_answer_it": "lookup_site_constraints reads the state heritage layer, which "
                                   "answers for mapped items but is not a substitute for Schedule "
                                   "5 of the LEP and Council's own conservation area mapping.",
        "applies": "Any proposal where the heritage status has not been positively established.",
        "ask_it_as": "Is this property a heritage item or within a conservation area under LEP "
                     "2012?",
    },
    {
        "key": "gfa_increase_within_tenancy",
        "question": "If the fitout adds floor area inside the existing tenancy — a mezzanine, an "
                    "enclosed dining area — is that charged a Section 7.11 contribution?",
        "why_it_matters": "It changes both the contribution and, if the enclosure is permanent, "
                          "the parking requirement: unenclosed outdoor dining is not gross floor "
                          "area and generates no parking requirement at all under §7.7.3.1(ii), "
                          "while an enclosed area does.",
        "cost_if_unresolved": "A design decision made without knowing what it costs.",
        "why_we_cannot_answer_it": "The contributions plan does not address this case, so any "
                                   "answer here would be an invention.",
        "applies": "Any fitout that adds enclosed floor area within existing premises.",
        "ask_it_as": "The fitout adds Xm² of enclosed floor area inside the tenancy. Is that "
                     "charged under the Section 7.11 plan?",
    },
]

# Said at the top of the brief. The duty planner session is free, drop-in and
# fifteen minutes, which is a real constraint on how many of the above fit.
HOW_TO_USE_THE_SESSION = [
    "It is fifteen minutes. Take the questions, not the whole proposal — a planner asked to "
    "review a scheme will spend the time reading, and answer nothing.",
    "Ask the top questions first. They are ordered by what they cost to leave unresolved, not by "
    "how interesting they are.",
    "Write the answers down against the questions, with the date and the planner's name. An "
    "answer you can point back to is worth far more than one you remember.",
    "Nothing said at a duty planner session binds Council, and the planner will say so. It is "
    "still the best information available before lodgement, and it is free.",
    "For anything larger than a fitout, book a pre-lodgement meeting instead — it is a longer, "
    "paid, formal session and the drop-in is not a substitute for it.",
]
