"""How long a DA takes, and what stops the clock.

PLAN.md item 2.5. Transcribed 2026-08-06 from
`documents/legislation/epa-regulation-2021-assessment-periods.txt`, the
Environmental Planning and Assessment Regulation 2021, Part 4 Division 4 and
Part 3 Divisions 1-2.

This is the one Phase 2 item whose source was **not** already in the repo —
nothing under `documents/` said anything about assessment time. Rather than
write the periods from memory, which is precisely the failure PLAN.md 0.3
records, the regulation was fetched (`scripts/fetch_epa_regulation.py`) and
these are quoted from it.

Doing that immediately contradicted this repo's own knowledge base. CLAUDE.md
said *"Standard: 40 business days for most local development"*. Section 91(4)
says **"The assessment period is 40 days"** — calendar days. The regulation says
"business days" in the two places it means them, so the distinction is the
drafter's, not an inference. Forty business days is about eight weeks; forty
calendar days is under six.

Three things matter more than the headline number, and none of them are
guessable:

  * **The 40 days is a deemed-refusal threshold, not a service promise.**
    Section 91(1) says the consent authority "is taken to have refused" consent
    if it has not determined the application in time. That gives the applicant
    a right to appeal as though refused — it does not mean the DA has been
    refused, and councils routinely take longer without the application dying.
  * **A request for more information stops the clock — but only if it is made
    within 25 days of lodgement** (s94(3)). A later request does not stop it.
    That limit is invisible to applicants and changes what a delay costs.
  * **Silence is treated as refusing to supply** (s36(5)). Miss the deadline in
    the request and you are *taken to have notified* that the information will
    not be provided; the clock restarts and the application is assessed on what
    is already there.

And the one that catches an unprepared lodgement: a DA that is rejected under
s39 is **"taken never to have been made"**. Not delayed — undone.

`scripts/audit_timing.py` checks every quote below still appears in the fetched
regulation text.
"""

REGULATION = "Environmental Planning and Assessment Regulation 2021"
SOURCE_DOC = "documents/legislation/epa-regulation-2021-assessment-periods.txt"

# s91. The assessment period by kind of development. Ordered most-specific
# first: a proposal can be several of these at once and the longer period wins,
# so the 40 days is the fallback rather than the rule.
ASSESSMENT_PERIODS = {
    "state_significant": {
        "days": 90,
        "applies_to": "State significant development",
        "verbatim": "The assessment period is 90 days for a development application for State "
                    "significant development.",
        "clause": "s91(3)",
    },
    "crown": {
        "days": 70,
        "applies_to": "Crown development applications",
        "verbatim": "For the purposes of the Act, section 4.33(2), the prescribed period is 70 "
                    "days after the day on which the Crown development application is lodged.",
        "clause": "s95(1)",
    },
    "designated_or_integrated": {
        "days": 60,
        "applies_to": "Designated development, integrated development (other than Class 1 "
                      "aquaculture), development requiring concurrence, or an application "
                      "accompanied by a biodiversity development assessment report proposing to "
                      "reduce the biodiversity credits to be retired",
        "verbatim": "The assessment period is 60 days for a development application—(a) for "
                    "designated development, or (b) for integrated development, other than "
                    "integrated development that is Class 1 aquaculture development, or (c) for "
                    "development requiring concurrence, or (d) that is accompanied by a "
                    "biodiversity development assessment report under the Biodiversity "
                    "Conservation Act 2016 that proposes to reduce the number of biodiversity "
                    "credits required to be retired.",
        "clause": "s91(2)",
    },
    "standard": {
        "days": 40,
        "applies_to": "Every other development application — the ordinary local DA, including a "
                      "commercial change of use or fitout",
        "verbatim": "The assessment period is 40 days for all other development applications, "
                    "other than a Crown development application referred to in section 95.",
        "clause": "s91(4)",
    },
}

# The distinction the whole tool turns on. "40 days" is widely quoted as though
# it were a delivery commitment; it is the point at which an appeal right
# arises.
WHAT_THE_PERIOD_ACTUALLY_IS = {
    "verbatim": "A consent authority is taken to have refused development consent if it has not "
                "determined the development application within the assessment period calculated "
                "in accordance with this Division.",
    "clause": "s91(1)",
    "plain": "This is a deemed refusal, and a deemed refusal is an appeal right rather than an "
             "outcome. Passing the period does not mean the DA has been refused, does not "
             "invalidate it, and does not oblige Council to stop assessing it. It means the "
             "applicant may appeal to the Land and Environment Court as if it had been refused. "
             "Most applicants do not, because appealing is slower and dearer than waiting.",
    "why_it_matters": "Plan the fitout around what Council's assessment actually takes, not "
                      "around 40 days. Ask the Duty Planner what current turnaround looks like "
                      "for the kind of DA you are lodging — it is a fair question and the "
                      "answer is not in any document.",
}

# s92. The start is not when you press submit.
CLOCK_START = {
    "verbatim": "The assessment period for a development application commences on the day on "
                "which the development application is lodged.",
    "clause": "s92(1)",
    "plain": "Lodged, not submitted. An application reaches lodgement when it passes the "
             "Planning Portal's completeness check and the fees are paid. Days spent going back "
             "and forth before that are not in the assessment period at all — they are simply "
             "lost, and they are the part most within the applicant's control.",
}

# s94(2)-(3). The stop-the-clock provision, and its limit.
CLOCK_STOPS = {
    "verbatim": "The assessment period for a development application ceases to run during the "
                "period between the day on which a consent authority requests additional "
                "information from an applicant under section 36 and the earlier of—(a) the day "
                "on which the information is given to the consent authority, or (b) the day on "
                "which the applicant gives, or is taken to have given, written notice to the "
                "consent authority that the information will not be given.",
    "clause": "s94(2)",
    "the_25_day_limit": {
        "verbatim": "Subsection (2) applies only if the consent authority’s request is made "
                    "within 25 days after the day on which the development application is "
                    "lodged.",
        "clause": "s94(3)",
        "plain": "The clock only stops if Council asks within 25 days of lodgement. A request "
                 "made on day 30 does not stop it — the assessment period keeps running while "
                 "the applicant prepares the response. This cuts both ways and almost nobody "
                 "knows it: it limits how long an early request can suspend the application, "
                 "and it means a late request leaves Council's own time running.",
    },
    "referral_authority_requests": {
        "verbatim": "The assessment period for development to which Part 3, Division 3 applies "
                    "ceases to run during the period between the day on which the referral "
                    "authority requests additional information from a consent authority under "
                    "section 46 and the earlier of—(a) the day on which the consent authority "
                    "gives the information to the referral authority, or (b) the day on which "
                    "the consent authority gives, or is taken to have given, written notice to "
                    "the referral authority that the information will not be given.",
        "clause": "s94(6)",
        "plain": "Integrated development referred to another agency has a second way for the "
                 "clock to stop, on the same 25-day style limit (s94(7)). Two agencies means "
                 "two chances for the clock to pause.",
    },
}

# s36. What a request for additional information must contain, and the trap in
# subsection (5).
INFORMATION_REQUESTS = {
    "power": {
        "verbatim": "A consent authority that receives a development application may request "
                    "additional information about the development from the applicant.",
        "clause": "s36(1)",
    },
    "what_the_request_must_say": {
        "verbatim": "A consent authority’s request must—(a) be made through the NSW planning "
                    "portal, and (b) specify a reasonable period within which the additional "
                    "information must be given to the consent authority, and (c) specify the "
                    "number of days in the assessment period that have elapsed, and (d) inform "
                    "the applicant that the assessment period ceases to run",
        "clause": "s36(3)",
        "plain": "The request has to tell you how many days have already elapsed. That is the "
                 "number to read first — it is the only reliable way to know where the "
                 "application actually stands, and it is on every request by law.",
    },
    "silence_counts_as_refusing": {
        "verbatim": "The applicant is taken to have notified the consent authority that the "
                    "applicant will not provide the additional information if the applicant has "
                    "not provided the information by the end of—(a) the period specified under "
                    "subsection (3)(b), or (b) a further period allowed by the consent "
                    "authority.",
        "clause": "s36(5)",
        "plain": "Missing the deadline is not a neutral delay. You are treated as having said "
                 "you will not provide the information: the clock restarts and the application "
                 "is determined on what is already in front of Council, which is usually the "
                 "version that prompted the question. If more time is needed, ask for it before "
                 "the deadline — subsection (5)(b) expressly contemplates an extension.",
    },
    "what_they_cannot_ask_for": {
        "verbatim": "A consent authority may not request additional information in relation to "
                    "building work or subdivision work if the information is required to "
                    "accompany an application for a construction certificate or subdivision "
                    "works certificate.",
        "clause": "s36(2)",
        "plain": "A genuine limit on what can be demanded at DA stage. Construction-level "
                 "detail belongs with the Construction Certificate, and being asked for it with "
                 "the DA is worth a polite question rather than three weeks of engineering.",
    },
}

# s39. The one that undoes an application rather than delaying it.
REJECTION = {
    "grounds_verbatim": "A consent authority may reject a development application within 14 days "
                        "after receiving the application if—(a) the application is illegible or "
                        "unclear about the development consent sought, or (b) the application "
                        "does not contain the information and documents that are required by—(i) "
                        "the approved form, or (ii) the Act or this Regulation",
    "clause": "s39(1)",
    "consequence_verbatim": "For the purposes of the Act, a development application is taken "
                            "never to have been made if—(a) the application is rejected by a "
                            "consent authority under this section, and (b) the determination to "
                            "reject the application is not changed following a review.",
    "consequence_clause": "s39(2)",
    "plain": "A rejected DA is not a delayed DA. It is taken never to have been made, so there "
             "is nothing to resume — the application is lodged again from the beginning, and "
             "the assessment period starts over from zero. The window is the first 14 days "
             "after receipt.",
    "fee_is_refunded": {
        "verbatim": "If a consent authority rejects an application, the consent authority must "
                    "refund to the applicant the whole of the fee paid for the application.",
        "clause": "s254(1)",
        "plain": "The fee comes back in full, which is small comfort — the weeks do not.",
    },
    "review_right": {
        "verbatim": "A council is taken to have refused an application for review of a decision "
                    "to reject and not determine a development application or modification "
                    "application if it does not determine the application for review within 14 "
                    "days after the application for review is made.",
        "clause": "s247",
        "plain": "A rejection can be reviewed, and the review itself has a 14-day deemed "
                 "refusal period.",
    },
}

# The things an applicant controls, which is the point of the item: a business
# planning a fitout needs to know which of its own omissions cost it weeks.
WHAT_THE_APPLICANT_CONTROLS = [
    {
        "lever": "Lodge something complete enough not to be rejected",
        "costs_if_missed": "The whole application. A rejection under s39 means it is taken "
                           "never to have been made and starts again from zero.",
        "how": "Run get_da_checklist for the development type and check every item before "
               "lodging. Rejection grounds are administrative — missing documents, an unclear "
               "description — not judgements about the merits.",
    },
    {
        "lever": "Pre-empt the obvious information request",
        "costs_if_missed": "The clock stops for as long as the response takes, and the elapsed "
                           "time is time the business is paying rent without trading.",
        "how": "The predictable requests for a business DA are parking, flood, waste, and "
               "evidence of the previous use where a Section 7.11 allowance is claimed. Address "
               "them in the SEE rather than waiting to be asked.",
    },
    {
        "lever": "Answer a request inside the period it specifies",
        "costs_if_missed": "You are taken to have said you will not provide it (s36(5)), and "
                           "the DA is determined on what is already there.",
        "how": "If the work will take longer, ask for an extension before the deadline rather "
               "than after it.",
    },
    {
        "lever": "Use the free Duty Planner before lodging",
        "costs_if_missed": "Nothing directly — but it is the cheapest way to find the objection "
                           "that would otherwise arrive as a request for information on day 20.",
        "how": "Tuesdays and Thursdays, 8:30–10:30am, no appointment. Take the specific "
               "questions, not the whole proposal.",
    },
    {
        "lever": "Include the signage and any ancillary approvals in the one application",
        "costs_if_missed": "A second application, a second fee and a second wait.",
        "how": "DCP Chapter 9 §9.5 expressly allows signage to ride on the development "
               "application for the site. See get_other_approvals for what else runs in "
               "parallel.",
    },
]
