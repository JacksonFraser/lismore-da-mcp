"""The readings this repository has taken where a source admits more than one.

ROADMAP.md B1. Built on the same insight as `DUTY_PLANNER_QUESTIONS` in
`data/readiness.py`, from the other side. That list collects this repository's
**refusals** — the walls it hit and declined to guess past. This one collects
its **judgements**: the places where it did not refuse, but read an ambiguous
provision one way and computed from that reading.

Those are where a business gets hurt now, because the data underneath them is
right. Every figure in the CBD parking answer is transcribed correctly and
audited; if Council reads §7.7.3.1 differently, the answer is out by fourteen
spaces anyway, and no presence check in `scripts/` can see it. Until this file
existed each judgement was defended in prose where it was made — a comment
above `_RESTAURANT`, a docstring in `cbd_spaces()`, an `assumption` key three
levels down in a contribution — and nothing assembled them.

Each entry carries:

  `key`                        stable id; tools cite it in the answer that
                               depends on it
  `topic`                      which part of the process it bites on
  `in_one_line`                the reading, short enough to sit in an answer
  `provision`                  where it comes from — source document, section
                               or clause, PDF page where the source is a PDF,
                               and the words verbatim
  `reading`                    the reading taken, and what the code does with it
  `alternative`                the other reading the words admit
  `why_this_one`               why this one was taken
  `cost_if_council_disagrees`  what it costs the applicant if Council reads it
                               the other way — the field that makes the
                               register usable rather than merely honest
  `if_wrong_this_tool`         'understates the burden', 'overstates the
                               burden' or 'either way' — which way the error
                               falls on the applicant if Council disagrees.
                               'overstates' is not harmless: an overstated
                               requirement can talk a business out of a viable
                               tenancy
  `relied_on_by`               the tools whose answers depend on it
  `duty_planner_question`      the key of the `DUTY_PLANNER_QUESTIONS` entry
                               under which to raise it, where one exists
  `planner_review`             ROADMAP.md B2: 'unreviewed' until a planner has
                               been through it, then 'confirmed', 'disputed' or
                               'unresolved'. A disputed entry becomes a
                               correction or a Duty Planner question.

**Every `verbatim` string is checked** by `scripts/audit_interpretations.py`
against its source document, on the stated page where there is one. The
register quotes provisions; it never paraphrases one into a `verbatim` field.
Reasoning goes in `reading`, `why_this_one` and `alternative`, which are this
repository's words and say so.

**The rule** (CLAUDE.md Part 1): if you take a reading where the source admits
another, register it here. Otherwise the judgement is invisible, and the next
person to read the code assumes it was the only possibility.

Tools cite an entry with `interpretations.cite()` inside the answer that turns
on it, and only there — never as a standing caveat. Entries whose reading is
the stricter one and cost nothing if Council disagrees are registered for the
planner review but not cited in answers, because a note that can only ever say
"this might be better than it looks" is the standing caveat item 0.1 diagnosed.

No logic lives in this module.
"""

CH7 = "documents/dcp/chapter-7-off-street-carparking.pdf"
CH8 = "documents/dcp/chapter-8-flood-prone-lands.pdf"
CH1 = "documents/dcp/chapter-1-residential-development.pdf"
CH9 = "documents/dcp/chapter-9-signage.pdf"
PLAN = "documents/fees/section-7.11-contributions-plan-2024-2041.pdf"
FEES = "documents/fees/fees-and-charges-2026-27.pdf"
LEP = "documents/lep/lep-2012-nsw-full.txt"
REG = "documents/legislation/epa-regulation-2021-assessment-periods.txt"

REVIEW_STATES = ("unreviewed", "confirmed", "disputed", "unresolved")
DIRECTIONS = ("understates the burden", "overstates the burden", "either way")

INTERPRETATIONS = [
    # ------------------------------------------------------------------ parking
    {
        "key": "cbd_fixed_rate_replaces_schedule_1",
        "topic": "parking",
        "in_one_line": "Inside the Lismore CBD the fixed 3.3 spaces/100m² GFA rate replaces "
                       "Schedule 1 for non-residential uses — it is not a floor under it.",
        "provision": [
            {"source": CH7, "where": "§7.7.2", "page": 8,
             "verbatim": "The minimum number of spaces for developments located outside the "
                         "Lismore CBD, as defined on Map 1, shall be the number contained in "
                         "Schedule 1, rounded up to the next whole number."},
            {"source": CH7, "where": "§7.7.3.1", "page": 8,
             "verbatim": "a fixed rate of no less than 3.3 car spaces/100m2 of gross floor area "
                         "(as defined in the Lismore LEP) shall be required for development "
                         "within the CBD/City Centre"},
            {"source": CH7, "where": "§7.7.3.1 exception (i)", "page": 8,
             "verbatim": "Where the development is (or includes) residential accommodation or "
                         "tourist and visitor accommodation, the minimum number of spaces "
                         "required shall be as described in Schedule 1"},
        ],
        "reading": "Schedule 1 is the rate outside the CBD only. Inside it, a non-residential "
                   "use is charged 3.3 spaces per 100m² GFA and nothing else, so an 80m² café "
                   "owes 3 spaces before any credit.",
        "alternative": "'No less than 3.3' is a floor, and Schedule 1 — which §7.7.2 also calls "
                       "a minimum — still applies inside the CBD, so the greater of the two "
                       "governs.",
        "why_this_one": "§7.7.2 confines Schedule 1 to 'developments located outside the "
                        "Lismore CBD'. Exception (i) expressly sends residential and tourist "
                        "accommodation back to Schedule 1 inside the CBD, which would be "
                        "pointless if Schedule 1 applied there anyway. And §7.7.3 describes the "
                        "scheme as a single fixed rate adopted as an incentive to CBD "
                        "development.",
        "cost_if_council_disagrees": "An 80m² café with 40 seats and 6 staff owes 17 spaces "
                                     "rather than 3 — fourteen more to provide, pay for in lieu "
                                     "at a rate this repository cannot quote, or justify.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["get_parking_rates", "check_da_readiness", "generate_see_draft"],
        "duty_planner_question": "cbd_boundary",
        "planner_review": "unreviewed",
    },
    {
        "key": "cafe_whichever_is_greater",
        "topic": "parking",
        "in_one_line": "The café rate is read as staff spaces plus the greater of the seats "
                       "basis and the floor-area basis.",
        "provision": [
            {"source": CH7, "where": "Schedule 1, Restaurant or cafe", "page": 14,
             "verbatim": "1 per 3 seats, plus 1 per 2 employees or 15 per 100m2 GFA "
                         "(whichever is greater)"},
            {"source": CH7, "where": "Schedule 1, Restaurant or cafe incorporating "
                                     "drive-through", "page": 14,
             "verbatim": "1 per employee, plus 12 per 100m2 GFA or 1 per 4 seats (whichever "
                         "is greater), plus queuing area"},
        ],
        "reading": "1 per 2 employees, plus the greater of 1 per 3 seats or 15 per 100m² GFA. "
                   "80m² with 40 seats and 6 staff is 17 spaces; with 20 seats, 15.",
        "alternative": "Two others. (A) the greater of [seats plus staff] and the floor-area "
                       "basis — 80m², 20 seats, 6 staff gives 12. (B) seats plus the greater of "
                       "[staff] and the floor-area basis, which is the order the words are "
                       "written in — 80m², 40 seats, 6 staff gives 26.",
        "why_this_one": "Seats and floor area are two measures of the same thing — how many "
                        "customers the premises holds — so 'whichever is greater' choosing "
                        "between them is a sensible instruction; the drive-through entry "
                        "directly below is worded that way unambiguously. Tweed Shire's 2018 "
                        "cross-council review ('Review of car parking requirements for small "
                        "business', attachment 2) cites this schedule and reads it this way. "
                        "That review is not in documents/, so it is supporting reasoning, not "
                        "an audited quote.",
        "cost_if_council_disagrees": "Under reading B, the worked example (80m², 40 seats, "
                                     "6 staff) needs 26 spaces, not 17. Under reading A a "
                                     "sparsely seated café owes fewer than this tool says "
                                     "(12 against 15).",
        "if_wrong_this_tool": "either way",
        "relied_on_by": ["get_parking_rates", "check_da_readiness", "generate_see_draft"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
    {
        "key": "cbd_credit_on_change_of_use",
        "topic": "parking",
        "in_one_line": "The §7.7.3.4 deemed parking credit is applied to a change of use of an "
                       "existing CBD building, not only to demolition and rebuilding.",
        "provision": [
            {"source": CH7, "where": "§7.7.3.4", "page": 10,
             "verbatim": "Where an existing site within the Lismore CBD is to be redeveloped, "
                         "the existing site will be deemed to have provided parking to the CBD "
                         "and a parking credit will be applied to the overall requirement for "
                         "car parking for the proposed redevelopment."},
        ],
        "reading": "'Redeveloped' covers any new development of an existing CBD site, "
                   "including a change of use inside the existing building. Supplying "
                   "existing_gfa_sqm applies the credit.",
        "alternative": "'Redeveloped' means the site is cleared and built on again, so a change "
                       "of use in the same building earns no credit.",
        "why_this_one": "The credit is calculated from the existing building's floor area and "
                        "represents parking the site is deemed to have already contributed to "
                        "the CBD — which is as true of a building changing use as of one being "
                        "replaced. The section does not define 'redeveloped'.",
        "cost_if_council_disagrees": "An 80m² café taking over an 80m² CBD shop owes 3 spaces "
                                     "rather than 1 — two more to provide or pay for in lieu.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["get_parking_rates"],
        "duty_planner_question": "cbd_boundary",
        "planner_review": "unreviewed",
    },
    {
        "key": "cbd_rounding",
        "topic": "parking",
        "in_one_line": "The CBD requirement is rounded up once, after the parking credit is "
                       "subtracted.",
        "provision": [
            {"source": CH7, "where": "§7.7.2", "page": 8,
             "verbatim": "shall be the number contained in Schedule 1, rounded up to the next "
                         "whole number"},
            {"source": CH7, "where": "§7.7.3.4", "page": 10,
             "verbatim": "Deemed Parking Credit = parking requirement for existing development "
                         "@ 2.5 spaces/100m2 gross floor area less the number of parking spaces "
                         "physically provided on the existing development site."},
        ],
        "reading": "The fixed-rate requirement and the credit are both kept as fractions, the "
                   "credit is subtracted, and the net is rounded up to a whole space — 80m² at "
                   "3.3 is 2.64, less a 2.0 credit is 0.64, so 1 space.",
        "alternative": "§7.7.3.1 says nothing about rounding and §7.7.3.4 nothing about "
                       "rounding the credit, so either could be rounded first: the requirement "
                       "rounded up before the credit comes off, the credit rounded down before "
                       "it does, or no rounding at all with a fractional space paid for in "
                       "lieu.",
        "why_this_one": "The only rounding rule in the chapter (§7.7.2, repeated in exception "
                        "(i)) rounds a requirement up to the next whole number. Applying it "
                        "once, to the requirement actually owed, neither invents a space nor "
                        "gives one away.",
        "cost_if_council_disagrees": "At most one space, in either direction.",
        "if_wrong_this_tool": "either way",
        "relied_on_by": ["get_parking_rates"],
        "duty_planner_question": "cbd_boundary",
        "planner_review": "unreviewed",
    },
    {
        "key": "cbd_credit_not_for_schedule_1_uses",
        "topic": "parking",
        "in_one_line": "The §7.7.3.4 credit is applied only to the fixed CBD rate, not to a "
                       "residential or tourist use kept on Schedule 1 inside the CBD.",
        "provision": [
            {"source": CH7, "where": "§7.7.3.1 exception (i)", "page": 8,
             "verbatim": "Where the development is (or includes) residential accommodation or "
                         "tourist and visitor accommodation, the minimum number of spaces "
                         "required shall be as described in Schedule 1"},
            {"source": CH7, "where": "§7.7.3.4", "page": 10,
             "verbatim": "a parking credit will be applied to the overall requirement for car "
                         "parking for the proposed redevelopment."},
        ],
        "reading": "For a use exception (i) sends to Schedule 1 — a motel, a boarding house, "
                   "residential flats — existing_gfa_sqm is not applied, and the answer says "
                   "the question is not settled here.",
        "alternative": "The credit applies to 'the overall requirement' of any redevelopment "
                       "of an existing CBD site, whichever rate that requirement was "
                       "calculated under.",
        "why_this_one": "It is the stricter reading, taken because §7.7.3.4 sits among the "
                        "fixed-rate provisions and its 2.5/100m² formula is calibrated against "
                        "the fixed rate. The words 'overall requirement' do support the "
                        "alternative, which is why the tool declines rather than asserting.",
        "cost_if_council_disagrees": "The tool overstates: a CBD motel or boarding house in an "
                                     "existing building owes fewer spaces than shown — 2.5 per "
                                     "100m² of the existing building, less spaces already on "
                                     "site.",
        "if_wrong_this_tool": "overstates the burden",
        "relied_on_by": ["get_parking_rates"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
    {
        "key": "unenclosed_dining_generates_no_parking",
        "topic": "parking",
        "in_one_line": "Unenclosed outdoor dining in the CBD is not gross floor area, so it "
                       "generates no parking requirement at all.",
        "provision": [
            {"source": CH7, "where": "§7.7.3.1 exception (ii)(c)", "page": 8,
             "verbatim": "For 'unenclosed' outdoor dining areas in all CBD/City Centre "
                         "locations, Section 94 charges for non-provision of car parking in "
                         "accordance with the specified rate under this DCP do not apply in "
                         "accordance with the definition of GFA."},
        ],
        "reading": "Because the fixed rate is charged on GFA and an unenclosed area is not "
                   "GFA, keeping outdoor dining unenclosed is offered as a way to avoid any "
                   "parking requirement for it.",
        "alternative": "The paragraph waives only the Section 94 cash-in-lieu charge for "
                       "spaces not provided; it does not say the area generates no "
                       "requirement, so Council could still count the seating towards the "
                       "requirement.",
        "why_this_one": "The paragraph grounds itself 'in accordance with the definition of "
                        "GFA', and the rate it waives is a rate per 100m² of GFA — an area "
                        "outside GFA contributes nothing to that product.",
        "cost_if_council_disagrees": "About one space per 30m² of outdoor dining at the fixed "
                                     "rate, to provide or pay for in lieu.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["get_parking_rates"],
        "duty_planner_question": "gfa_increase_within_tenancy",
        "planner_review": "unreviewed",
    },
    # ------------------------------------------------------------ contributions
    {
        "key": "allowance_same_floor_area",
        "topic": "contributions",
        "in_one_line": "Where the previous use's floor area is not given, it is taken to equal "
                       "the proposal's.",
        "provision": [
            {"source": PLAN, "where": "Section 2.7", "page": 20,
             "verbatim": "Contributions required under this Plan are based on the estimated net "
                         "increase in demand. When calculating contributions, the contribution "
                         "that would be applicable to any existing lawful development on the "
                         "site of a proposed new development will be discounted."},
        ],
        "reading": "A change of use in an existing tenancy is netted against the previous use "
                   "at the same floor area unless existing_gross_floor_area_m2 is supplied — "
                   "the ordinary case, and the answer says it was assumed.",
        "alternative": "The discount is measured on the lawful existing development as "
                       "evidenced, which may be smaller than the proposal — part of the "
                       "building vacant, the proposal adding floor space, or only part of the "
                       "previous use approved.",
        "why_this_one": "For a like-for-like tenancy it is the right figure, and the plan gives "
                        "no other default. It is a factual assumption rather than a reading of "
                        "the words, registered because it changes the number and the "
                        "applicant may not notice it was made.",
        "cost_if_council_disagrees": "A restaurant expanding from 100m² to 140m² nets to $0 on "
                                     "this assumption against a real $8,040 (urban).",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["calculate_da_fees"],
        "duty_planner_question": "existing_use_allowance",
        "planner_review": "unreviewed",
    },
    {
        "key": "allowance_netted_as_totals",
        "topic": "contributions",
        "in_one_line": "The section 2.7 allowance is subtracted as one total, not "
                       "infrastructure category by category.",
        "provision": [
            {"source": PLAN, "where": "Section 2.7", "page": 20,
             "verbatim": "Council will only consider an allowance for the existing development "
                         "to the extent of the demand for specific public infrastructure "
                         "arising from that development."},
        ],
        "reading": "The allowance is the Table E2 rate for the previous use times its units, "
                   "subtracted from the proposal's Table E2 total.",
        "alternative": "The allowance is limited category by category: an existing use's "
                       "demand for open space cannot offset a new use's demand for traffic "
                       "management. Where the previous and proposed uses draw on different "
                       "categories, the net is larger.",
        "why_this_one": "Table E2 publishes only totals, and for a change between two "
                        "non-residential uses the categories are identical — each Table E2 "
                        "category is at least as large for the busier use — so the two readings "
                        "give the same figure for the commonest business change of use. They "
                        "diverge only when a residential use becomes a non-residential one. "
                        "The words 'specific public infrastructure' favour the alternative, so "
                        "the tool cites this entry whenever the two uses are of different "
                        "kinds.",
        "cost_if_council_disagrees": "A house becoming an 80m² café (urban) nets to $9,029 on "
                                     "this reading and $11,498 category by category — about "
                                     "$2,470 more.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["calculate_da_fees"],
        "duty_planner_question": "existing_use_allowance",
        "planner_review": "unreviewed",
    },
    {
        "key": "contribution_pro_rata",
        "topic": "contributions",
        "in_one_line": "A rate per 100m² GFA is applied pro rata — 80m² is charged as 0.8 of a "
                       "unit, not a whole one.",
        "provision": [
            {"source": PLAN, "where": "Table E2", "page": 7,
             "verbatim": "Retail premises 100m2 GFA 2.17 7 $20,101.55 $24,210.38 $24,210.38"},
        ],
        "reading": "The contribution is the Table E2 rate times floor area divided by 100.",
        "alternative": "Charged per 100m² or part of 100m², so any part unit is charged as a "
                       "whole one.",
        "why_this_one": "Table E2 states a rate per unit and the plan nowhere says 'or part' "
                        "(the fees schedule does, where it means it). The per-worker and "
                        "per-trip rates Table E2 is built from are proportional by nature.",
        "cost_if_council_disagrees": "Up to one whole unit: an 80m² café (urban) is $16,081 on "
                                     "this reading and $20,102 if charged per whole 100m².",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["calculate_da_fees"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
    {
        "key": "food_and_drink_charged_as_retail",
        "topic": "contributions",
        "in_one_line": "A café, restaurant, takeaway or pub is charged at Table E2's 'Retail "
                       "premises' rate.",
        "provision": [
            {"source": PLAN, "where": "Appendix A — Glossary", "page": 36,
             "verbatim": "Terms used in this Plan have the following meanings except where the "
                         "meaning of a term is inconsistent with the Act or the Standard "
                         "Instrument—Principal Local Environmental Plan (SILEP), in which case "
                         "the definition in the Act or SILEP will prevail"},
            {"source": LEP, "where": "Dictionary, food and drink premises",
             "verbatim": "Food and drink premises are a type of retail premises—see the "
                         "definition of that term in this Dictionary."},
        ],
        "reading": "Table E2's 'Retail premises' carries its LEP meaning, which includes food "
                   "and drink premises, so food and drink uses take the retail rate — the "
                   "highest non-residential rate in the plan.",
        "alternative": "Table E2 names only 'Retail premises', and Note E sends development "
                       "'not specified in this table' to a section 1.5 calculation from worker "
                       "numbers and peak vehicle trips — which a restaurant's traffic report "
                       "might put above or below 7 trips per 100m².",
        "why_this_one": "The glossary defers to the Standard Instrument's meanings and does "
                        "not define retail premises itself; under the Standard Instrument food "
                        "and drink premises are retail premises.",
        "cost_if_council_disagrees": "A different figure in either direction, which only a "
                                     "section 1.5 calculation by Council can give.",
        "if_wrong_this_tool": "either way",
        "relied_on_by": ["calculate_da_fees"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
    {
        "key": "warehouse_charged_as_industry",
        "topic": "contributions",
        "in_one_line": "A warehouse or distribution centre is charged at Table E2's "
                       "'Industry' rate.",
        "provision": [
            {"source": LEP, "where": "Dictionary, industry",
             "verbatim": "industry means any of the following— (a) general industry, "
                         "(b) heavy industry, (c) light industry,"},
            {"source": PLAN, "where": "Table E2, note E", "page": 7,
             "verbatim": "Other development not specified in this table will be assessed in "
                         "accordance with Section 1.5 and Section 1.6 of this Plan and the per "
                         "person/PVT rates specified in Table E1."},
        ],
        "reading": "'warehouse or distribution centre' resolves to the Industry row, on the "
                   "basis that its worker density and traffic are closer to industry than to "
                   "any other row.",
        "alternative": "The LEP's definition of industry does not include a warehouse or "
                       "distribution centre, and the glossary defers to that meaning — so a "
                       "warehouse is development 'not specified in this table' and note E "
                       "sends it to a section 1.5 calculation.",
        "why_this_one": "It is the weakest reading in this register. The textual case favours "
                        "the alternative; the Industry row was taken because it gives a figure "
                        "where the alternative gives none. Registered so a planner can say "
                        "which Council applies.",
        "cost_if_council_disagrees": "A different figure in either direction — a section 1.5 "
                                     "calculation from worker numbers and peak vehicle trips, "
                                     "usually needing a traffic report.",
        "if_wrong_this_tool": "either way",
        "relied_on_by": ["calculate_da_fees"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
    {
        "key": "tourist_rural_published_figure",
        "topic": "contributions",
        "in_one_line": "The published rural rate for tourist accommodation is used, although "
                       "it does not rebuild from Table E1.",
        "provision": [
            {"source": PLAN, "where": "Table E2", "page": 7,
             "verbatim": "Tourist and visitor accommodation, camping grounds, caravan parks, "
                         "eco-tourist facilities Bed / Site 0.6 0.4 $1,352.49 $1,374.61 "
                         "$1,374.61"},
        ],
        "reading": "$1,374.61 per bed or site in both rural catchments, as printed.",
        "alternative": "The printed figure omits the Open Space and Recreation component that "
                       "every other rural row and the urban tourist row include; rebuilt from "
                       "Table E1 it is $1,587.29, and Council may levy that.",
        "why_this_one": "The published figure is what the plan says is levied. Whether the "
                        "omission is deliberate is not recoverable from the document "
                        "(KNOWN_TABLE_DISCREPANCIES in data/contributions.py).",
        "cost_if_council_disagrees": "$212.68 more per bed or site — $4,254 on a 20-site "
                                     "rural caravan park.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["calculate_da_fees"],
        "duty_planner_question": "contribution_catchment",
        "planner_review": "unreviewed",
    },
    # ------------------------------------------------------------------- flood
    {
        "key": "flood_change_of_use_with_fitout",
        "topic": "flood",
        "in_one_line": "A change of use with an internal fitout that adds no floor space is "
                       "within the §8.3 exemption from the commercial and industrial controls.",
        "provision": [
            {"source": CH8, "where": "§8.3", "page": 3,
             "verbatim": "The controls applying to new commercial and industrial development in "
                         "the High Flood Risk Area and the Flood Fringe Area are not applicable "
                         "where a change of use is proposed."},
            {"source": CH8, "where": "§8.3", "page": 3,
             "verbatim": "Where minor extensions to the existing floor space are proposed, the "
                         "proposal will be considered on its merits."},
        ],
        "reading": "With is_change_of_use, the 25%-of-GFA-above-the-FPL requirement, the "
                   "engineer's risk analysis and (High Flood Risk) the mezzanine refuge are "
                   "reported as lifted. A fitout that extends floor space is sent to merit "
                   "assessment, as §8.3 says.",
        "alternative": "A change of use accompanied by substantial building work is 'new "
                       "commercial development', so the controls apply to it; the exemption is "
                       "only for a change of use with little or no work.",
        "why_this_one": "§8.3 draws its line at extensions to floor space, not at building "
                        "work, and a change of use almost always involves a fitout — reading "
                        "the exemption as excluding any fitout would leave it applying to "
                        "almost nothing.",
        "cost_if_council_disagrees": "The controls come back: 25% of the floor area at or "
                                     "above the Flood Planning Level and a structural "
                                     "engineer's risk analysis, plus a mezzanine refuge above "
                                     "the 1-in-500 year level in the High Flood Risk Area — "
                                     "enough to change the design.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["get_flood_requirements"],
        "duty_planner_question": "flood_planning_level",
        "planner_review": "unreviewed",
    },
    {
        "key": "flood_exemption_reaches_cbd_flood_liable",
        "topic": "flood",
        "in_one_line": "The §8.3 change-of-use exemption reaches the CBD Flood Liable area, "
                       "because that area has the Flood Fringe's controls.",
        "provision": [
            {"source": CH8, "where": "§8.3", "page": 3,
             "verbatim": "A fifth category - CBD Flood Liable, also shown on Map 1, has the "
                         "same planning controls as the Flood Fringe Area."},
            {"source": CH8, "where": "§8.3", "page": 3,
             "verbatim": "The controls applying to new commercial and industrial development in "
                         "the High Flood Risk Area and the Flood Fringe Area are not applicable "
                         "where a change of use is proposed."},
        ],
        "reading": "Everything the chapter says about the Flood Fringe applies to CBD Flood "
                   "Liable land — the change-of-use exemption, and the §8.6.4(2) exemption "
                   "from the structural adequacy certificate for work under $50,000.",
        "alternative": "The exemption names only the High Flood Risk and Flood Fringe areas; "
                       "CBD Flood Liable land takes the Flood Fringe's 'planning controls' but "
                       "not the exemption from them.",
        "why_this_one": "An exemption from a control is part of what the control is. Giving "
                        "the CBD the Flood Fringe's controls without their exemption would make "
                        "the CBD — where most change-of-use DAs are — stricter than the fringe, "
                        "which nothing in the chapter suggests.",
        "cost_if_council_disagrees": "For a CBD change of use, the same as "
                                     "flood_change_of_use_with_fitout: 25% of the floor area at "
                                     "or above the Flood Planning Level and an engineer's risk "
                                     "analysis.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["get_flood_requirements"],
        "duty_planner_question": "flood_planning_level",
        "planner_review": "unreviewed",
    },
    {
        "key": "flood_exemption_leaves_building_controls",
        "topic": "flood",
        "in_one_line": "The §8.3 exemption lifts the commercial and industrial controls only; "
                       "the controls on all development still bite on any works.",
        "provision": [
            {"source": CH8, "where": "§8.5.4 / §8.6.4", "page": 6,
             "verbatim": "All applications involving new building work are to be accompanied by "
                         "a certificate of structural adequacy"},
        ],
        "reading": "Floor-level certificates, structural adequacy and flood-compatible "
                   "materials are still listed as applying to what is built.",
        "alternative": "They are part of 'the controls applying to new commercial and "
                       "industrial development' in those areas, and are lifted with the rest.",
        "why_this_one": "They are headed as controls on all development, not on commercial or "
                        "industrial development, and bite on building work rather than on the "
                        "use. It is the stricter reading.",
        "cost_if_council_disagrees": "None beyond having prepared for controls Council does "
                                     "not require — a structural engineer's certificate that "
                                     "was not needed.",
        "if_wrong_this_tool": "overstates the burden",
        "relied_on_by": ["get_flood_requirements"],
        "duty_planner_question": "flood_planning_level",
        "planner_review": "unreviewed",
    },
    {
        "key": "flood_controls_despite_lep_2000_reference",
        "topic": "flood",
        "in_one_line": "Chapter 8's controls are applied to LEP 2012 land, despite §8.3 tying "
                       "them to LEP 2000.",
        "provision": [
            {"source": CH8, "where": "§8.3", "page": 3,
             "verbatim": "Controls in this Plan are listed for new residential, commercial and "
                         "industrial development on flood prone land and apply only where such "
                         "development is permissible in the zone under the Lismore Local "
                         "Environmental Plan 2000."},
        ],
        "reading": "The cross-reference is stale — LEP 2012 superseded LEP 2000 for most of the "
                   "LGA — and the controls are applied as though it read LEP 2012.",
        "alternative": "Read literally, the controls apply only where LEP 2000 still applies, "
                       "which is almost nowhere.",
        "why_this_one": "The chapter is published as part of the DCP applying to LEP 2012 "
                        "land, and Council plainly applies it there. It is the stricter "
                        "reading.",
        "cost_if_council_disagrees": "None — the alternative would relieve the applicant of "
                                     "controls, not add any.",
        "if_wrong_this_tool": "overstates the burden",
        "relied_on_by": ["get_flood_requirements"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
    # -------------------------------------------------------------------- fees
    {
        "key": "fee_schedule_column",
        "topic": "fees",
        "in_one_line": "The single figures on fees schedule p30 are read as 2026-27 values, "
                       "though the page prints two year columns.",
        "provision": [
            {"source": FEES, "where": "p30, Development Application (Lodgement Fee)", "page": 30,
             "verbatim": "Estimated cost of development - fixed by Schedule 4 Part 2 Item 2.1 of "
                         "the EP & A Regulations Up to $5,000 L N $147.00 $153.00 "
                         "$5,001-$50,000 L N $235.00+"},
        ],
        "reading": "Only the first row carries both a 'Year 25/26' and a 'Year 26/27' figure; "
                   "every other row's single figure is taken to be 2026-27.",
        "alternative": "The single figures belong to the 25/26 column, and the 2026-27 fees "
                       "are one indexation higher.",
        "why_this_one": "By position, every single figure sits under the 26/27 column; by "
                        "arithmetic, every bracket is two years of indexation above its 2024-25 "
                        "value (data/fees.py docstring). Two independent checks agree.",
        "cost_if_council_disagrees": "About 4% on the lodgement fee — roughly $20 on a $500 "
                                     "fee.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["calculate_da_fees"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
    # ---------------------------------------------------------------- heritage
    {
        "key": "heritage_document_is_discretionary",
        "topic": "heritage",
        "in_one_line": "Council may ask for a heritage management document; supplying one "
                       "unasked is not a lodgement requirement.",
        "provision": [
            {"source": LEP, "where": "cl 5.10(5)",
             "verbatim": "The consent authority may, before granting consent to any "
                         "development—"},
            {"source": LEP, "where": "cl 5.10(5)",
             "verbatim": "require a heritage management document to be prepared that assesses "
                         "the extent to which the carrying out of the proposed development "
                         "would affect the heritage significance of the heritage item or "
                         "heritage conservation area concerned."},
        ],
        "reading": "The tools say Council may require a heritage document and advise asking "
                   "which form before commissioning one, rather than listing a Heritage Impact "
                   "Statement as required.",
        "alternative": "The clause is a discretion, but Council's practice is to exercise it "
                       "for every proposal affecting an item or conservation area, so a "
                       "heritage document is required in fact.",
        "why_this_one": "The clause says 'may', and DCP Chapter 12 requires no document "
                        "(audit_heritage.py pins both). A report bought on spec may be the "
                        "wrong one of the three forms.",
        "cost_if_council_disagrees": "A request for information after lodgement — the report "
                                     "then, and a paused assessment — rather than a rejection.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["check_da_readiness", "prepare_prelodgement_brief", "generate_see_draft",
                         "lookup_site_constraints"],
        "duty_planner_question": "heritage_status",
        "planner_review": "unreviewed",
    },
    # ---------------------------------------------------------------- land use
    {
        "key": "nearest_listed_type_decides",
        "topic": "permissibility",
        "in_one_line": "Where a land use table lists two ancestors of a use in different "
                       "sections, the nearer one decides.",
        "provision": [
            {"source": LEP, "where": "cl 2.3(3)(b)",
             "verbatim": "a reference to a type of building or other thing does not include "
                         "(despite any definition in this Plan) a reference to a type of "
                         "building or other thing referred to separately in the Land Use Table "
                         "in relation to the same zone."},
            {"source": LEP, "where": "Dictionary, light industry",
             "verbatim": "Light industries are a type of industry—see the definition of that "
                         "term in this Dictionary."},
        ],
        "reading": "An artisan food and drink industry is a type of light industry, which is a "
                   "type of industry. In MU1 and E3, 'Light industries' is permitted with "
                   "consent and 'Industries' prohibited; 'Industries' does not include light "
                   "industry, so it does not include a type of light industry either, and the "
                   "use is permitted with consent.",
        "alternative": "cl 2.3(3)(b) removes only the separately listed term itself from its "
                       "parent. An artisan food and drink industry is still, by definition, an "
                       "industry, so the prohibited 'Industries' entry catches it too — and the "
                       "use is prohibited, or at best contested.",
        "why_this_one": "A thing that is a type of light industry is referred to by 'light "
                        "industries'; excluding light industry from 'industries' while keeping "
                        "its subtypes in would make the exclusion meaningless for every subtype. "
                        "The nearer entry is the more specific statement of what the zone "
                        "wants.",
        "cost_if_council_disagrees": "The permissibility answer flips from 'permitted with "
                                     "consent' to 'prohibited' for artisan food and drink, "
                                     "creative and high technology industries and data centres "
                                     "in E3 and MU1, and home industry in MU1.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["check_permissibility"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
    # ---------------------------------------------------------------- signage
    {
        "key": "signage_residential_means_r_zones",
        "topic": "signage",
        "in_one_line": "The §9.2 prohibition in 'residential' areas is applied to R1, R2, R3 "
                       "and R5 only — not RU5 Village.",
        "provision": [
            {"source": CH9, "where": "§9.2", "page": 2,
             "verbatim": "The SEPP prohibits the display of an advertisement within the "
                         "following zones or descriptions:"},
            {"source": CH9, "where": "§9.2", "page": 2,
             "verbatim": "residential (but not including mixed residential/business zones)"},
        ],
        "reading": "§9.2's descriptions are mapped to zones: residential to R1, R2, R3 and R5; "
                   "open space to RE1 and RE2; waterway to W1 and W2; conservation to C1–C3. "
                   "MU1 is excluded by §9.2's own carve-out.",
        "alternative": "RU5 Village, where housing is the dominant use, is 'residential' for "
                       "the SEPP — or is a mixed residential/business zone, which the "
                       "carve-out would exclude again.",
        "why_this_one": "RU5 is a rural zone in the Standard Instrument, not a residential "
                        "one, and a Lismore village centre is where its shops are. The mapping "
                        "is this repository's; a False from it means 'not prohibited on zoning "
                        "grounds', never 'permitted'.",
        "cost_if_council_disagrees": "In a village such as Nimbin, advertising signs other than "
                                     "business and building identification signs would be "
                                     "prohibited.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["get_signage_requirements"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
    # ----------------------------------------------------------------- timing
    {
        "key": "assessment_days_are_calendar_days",
        "topic": "timing",
        "in_one_line": "The 40-day assessment period is 40 calendar days, not business days.",
        "provision": [
            {"source": REG, "where": "s91(4)",
             "verbatim": "The assessment period is 40 days for all other development "
                         "applications, other than a Crown development application referred to "
                         "in section 95."},
            {"source": REG, "where": "elsewhere in the Regulation",
             "verbatim": "within 20 business days after the operator was notified of the "
                         "proposal"},
        ],
        "reading": "Forty calendar days from lodgement, after which the application may be "
                   "treated as refused for the purpose of an appeal.",
        "alternative": "Forty business days — about eight weeks rather than six.",
        "why_this_one": "The Regulation says 'business days' where it means them, as the "
                        "second quote shows; s91 does not.",
        "cost_if_council_disagrees": "Timing only: an applicant treating the application as "
                                     "deemed refused at day 41 would be about two weeks early.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["get_assessment_timeline"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
    # -------------------------------------------------------------- standards
    {
        "key": "acceptable_solutions_are_safe_harbours",
        "topic": "standards",
        "in_one_line": "DCP Chapter 1's figures are deemed-to-comply safe harbours, not limits.",
        "provision": [
            {"source": CH1, "where": "§1.3", "page": 5,
             "verbatim": "Development proposals must be consistent with the Design Principles "
                         "outlined in Part 3 of this document. This can be achieved by meeting "
                         "the Acceptable Solution or alternatively, Council may be prepared to "
                         "approve development proposals that demonstrate consistency with "
                         "Design Principles and Performance Criteria."},
        ],
        "reading": "Every figure is reported as one way to satisfy its Performance Criterion, "
                   "with the argument against the criterion named as open to the applicant.",
        "alternative": "'May be prepared to approve' is discretion, and Council treats the "
                       "Acceptable Solutions as the standard in practice.",
        "why_this_one": "It is what §1.3 says, and telling an applicant 'you must have 6m' "
                        "forecloses an argument the chapter expressly invites.",
        "cost_if_council_disagrees": "A performance-based design refused or sent back for "
                                     "amendment — redesign, and the amended plan fee.",
        "if_wrong_this_tool": "understates the burden",
        "relied_on_by": ["get_residential_standards", "get_setback_requirements"],
        "duty_planner_question": None,
        "planner_review": "unreviewed",
    },
]

BY_KEY = {entry["key"]: entry for entry in INTERPRETATIONS}
