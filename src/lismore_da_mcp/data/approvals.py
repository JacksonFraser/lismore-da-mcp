"""The approvals that are not the DA.

PLAN.md item 2.4. A business that gets its development consent has not finished
— it has finished the part everyone talks about. The consent says the *use* is
allowed on the land. It does not let anyone build, connect a sink to the sewer,
serve food, put a table on the footpath, pour a beer, or open the doors. Each of
those is a separate approval, most are issued by someone other than the planners
who assessed the DA, and several are on longer lead times than the DA itself.

This is where businesses get caught, and it is cheap to prevent: the whole
value of this file is naming the thing, who issues it, what triggers it, and
when it has to be done relative to the DA.

**Fees are quoted only where this repository carries the document that sets
them** — Council's own `documents/fees/fees-and-charges-2026-27.pdf`, cited by
page. Everything issued by a state agency (Liquor & Gaming, the Long Service
Corporation, the Food Authority) has its fee left out rather than guessed at,
the same rule `data/contributions.py` follows for Section 64.

Two things reading the documents turned up that are not obvious:

  * **Temporary footpath dining is fee-free and is not a Council application.**
    Under the NSW Outdoor Dining Policy 2019 you apply through Service NSW and
    "Council and state government agency fees will be waived". Council's own
    schedule agrees — its Tier 1 and Tier 2 rates read "Subject to NSW Outdoor
    Dining Policy" where Tiers 3 and 4, which are permanent structures, carry
    real per-square-metre annual fees.
  * **Food premises registration stopped being free.** Every annual
    registration fee in Council's schedule was $0.00 in 2025-26 and carries a
    real figure in 2026-27 — $607.50 for a small food business, plus a $355
    administrative assessment fee on a new application. A café budgeting off
    last year's schedule budgets zero for this.
"""

from lismore_da_mcp.data.fees import DA_FEE_SCHEDULE_YEAR

COUNCIL_SCHEDULE = f"Lismore City Council Fees and Charges {DA_FEE_SCHEDULE_YEAR}"

# When an approval has to happen relative to the DA. This is the axis that
# actually costs businesses money, because two of these cannot be started until
# the consent exists and two others should have been started long before it.
TIMING = {
    "before_da": "Best done before the DA is lodged — it can change the design, or the DA "
                 "itself.",
    "with_da": "Can be lodged with the DA, or rolled into it.",
    "after_consent": "Cannot be issued until development consent exists.",
    "before_work": "Must be in place before any building work starts.",
    "before_opening": "Must be in place before the business opens or the premises is occupied.",
    "ongoing": "Continues for as long as the business operates.",
}

APPROVALS = {
    # --- building the fitout ------------------------------------------------
    "construction_certificate": {
        "name": "Construction Certificate (CC)",
        "issued_by": "Lismore City Council or a private accredited certifier — your choice",
        "legislation": "Environmental Planning and Assessment Act 1979",
        "triggered_by": "Any building work, including an internal fitout.",
        "timing": "after_consent",
        "what_it_is": "Certifies that the construction drawings comply with the Building Code "
                      "of Australia and with the conditions of your development consent. The "
                      "DA approves the use and the concept; the CC approves the actual "
                      "drawings you will build from.",
        "fee": "Council quotes on application (the schedule lists Construction Certificates as "
               "POA), because private certifiers compete for this work. Get more than one "
               "quote — you are not obliged to use Council.",
        "fee_source": f"{COUNCIL_SCHEDULE}, p37",
        "gotcha": "Work cannot lawfully start without it, and it is a common source of delay "
                  "because the consent conditions usually require things to be designed and "
                  "submitted first. Read the conditions the day you get the consent, not the "
                  "week you want to start.",
    },
    "principal_certifier": {
        "name": "Principal Certifier appointment",
        "issued_by": "Council or an accredited certifier, appointed by the owner",
        "legislation": "Environmental Planning and Assessment Act 1979",
        "triggered_by": "Any building work.",
        "timing": "before_work",
        "what_it_is": "The certifier who inspects the work at mandatory stages and ultimately "
                      "issues the Occupation Certificate.",
        "gotcha": "Must be appointed at least two days before work commences, and Council must "
                  "be notified. Missing this is an administrative slip that can stop a site.",
    },
    "occupation_certificate": {
        "name": "Occupation Certificate (OC)",
        "issued_by": "The Principal Certifier",
        "legislation": "Environmental Planning and Assessment Act 1979",
        "triggered_by": "Occupying or using a new or altered building.",
        "timing": "before_opening",
        "what_it_is": "Confirms the building is suitable to occupy and that the consent "
                      "conditions have been satisfied.",
        "fee": "Quoted with the certifier's other fees (listed as POA in Council's schedule).",
        "fee_source": f"{COUNCIL_SCHEDULE}, p37",
        "gotcha": "This is the one that most often delays an opening date. Every outstanding "
                  "consent condition has to be discharged first — landscaping, parking line "
                  "marking, a fire safety certificate, a waste enclosure. Businesses book a "
                  "launch, then discover a condition nobody actioned.",
    },
    "long_service_levy": {
        "name": "Building and Construction Industry Long Service Levy",
        "issued_by": "Long Service Corporation (NSW), not Council",
        "legislation": "Building and Construction Industry Long Service Payments Act 1986",
        "triggered_by": "Building work above the Act's cost threshold.",
        "timing": "before_work",
        "what_it_is": "A levy on the cost of building work, payable before a Construction "
                      "Certificate is issued.",
        "fee": "Not quoted here. The rate and the cost threshold are set by the Long Service "
               "Corporation and no document in this repository carries them — confirm both on "
               "the Corporation's site or with your certifier.",
        "gotcha": "It is not in Council's fee schedule because it is not Council's charge, so "
                  "it is easy to leave out of a budget built from Council's fees alone.",
    },

    # --- connecting the premises -------------------------------------------
    "liquid_trade_waste": {
        "name": "Liquid Trade Waste Approval",
        "issued_by": "Lismore City Council (as the water and sewer utility)",
        "legislation": "Local Government Act 1993 section 68",
        "triggered_by": "Discharging anything other than domestic sewage into the sewer — any "
                        "commercial kitchen, café, restaurant, bakery, butcher, hairdresser, "
                        "mechanic or car wash.",
        "timing": "before_opening",
        "what_it_is": "Permission to discharge trade wastewater to the sewer, usually "
                      "conditioned on installing pre-treatment — for a food business, a grease "
                      "arrestor sized by Council.",
        "fee": "Application: $322.50 Classification A, $481.00 Classification B and 2S, "
               "$570.50 Classification C (urban). Then an annual fee of $134.35 and a renewal "
               "fee of $108.65. A non-compliance re-inspection is $152.90 per hour.",
        "fee_source": f"{COUNCIL_SCHEDULE}, pp49, 58",
        "gotcha": "The one that most often surprises a café. A grease arrestor needs physical "
                  "space, drainage falls and access for pump-outs, so it is a design constraint "
                  "and not a form to fill in afterwards. Ask Council what classification and "
                  "what size applies before the kitchen layout is finalised — retrofitting one "
                  "into a finished fitout is expensive.",
    },
    "section_68_approval": {
        "name": "Section 68 approval (water, sewer, stormwater)",
        "issued_by": "Lismore City Council",
        "legislation": "Local Government Act 1993 section 68",
        "triggered_by": "Connecting to or altering water, sewer or stormwater, installing an "
                        "on-site sewage system, or installing a manufactured or moveable "
                        "dwelling.",
        "timing": "after_consent",
        "what_it_is": "A separate Council approval for the physical connection work, distinct "
                      "from the development consent for the use.",
        "fee": "$570.50 urban, $597.50 rural. On-site sewage management over 10EP is "
               "$1,033.00. A stormwater-only application for minor Class 1 and 10 buildings is "
               "$355.00 plus inspection. Inspection fees apply to every Section 68 application: "
               "$375.00 urban, $434.00 rural.",
        "fee_source": f"{COUNCIL_SCHEDULE}, pp29, 31",
        "gotcha": "Inspection fees are charged on top of the application fee and are easy to "
                  "miss when budgeting from the headline figure.",
    },
    "onsite_sewage_management": {
        "name": "On-site sewage management approval",
        "issued_by": "Lismore City Council",
        "legislation": "Local Government Act 1993 section 68",
        "triggered_by": "A premises not connected to reticulated sewer — common outside the "
                        "urban area and in the villages.",
        "timing": "with_da",
        "what_it_is": "Approval to install or alter a septic or aerated system, and then to "
                      "operate it. A commercial food business generates far more load than a "
                      "dwelling, so an existing system is often inadequate.",
        "fee": "$570.50 urban / $597.50 rural, or $1,033.00 where the system exceeds 10EP. A "
               "minor alteration or re-assessment of an existing system is $355.00 plus costs.",
        "fee_source": f"{COUNCIL_SCHEDULE}, p31",
        "gotcha": "Needs a site assessment by a qualified consultant, which takes time and can "
                  "determine whether the site supports the business at all. Start it early — "
                  "on an unsewered site this is the constraint most likely to stop a proposal, "
                  "not a formality after it.",
    },

    # --- opening the doors --------------------------------------------------
    "food_business_notification": {
        "name": "Food business notification and registration",
        "issued_by": "NSW Food Authority (notification) and Lismore City Council "
                     "(registration and inspection)",
        "legislation": "Food Act 2003 (NSW)",
        "triggered_by": "Selling or handling food — any café, restaurant, takeaway, bakery, "
                        "caterer, market stall or mobile food van.",
        "timing": "before_opening",
        "what_it_is": "Every food business must notify its details before it starts trading, "
                      "and Council registers and inspects it on a risk basis.",
        "fee": "Annual registration: $177.50 low risk (packaged goods or coffee only), $607.50 "
               "small (1–5 food handlers), $1,032.50 medium (6–50), $1,500.00 large (50+). A "
               "new application also incurs a $355.00 administrative assessment fee. No "
               "application fee applies if it is associated with a lodged DA.",
        "fee_source": f"{COUNCIL_SCHEDULE}, p39",
        "gotcha": "These fees were $0.00 in the 2025-26 schedule and are real in 2026-27, so a "
                  "budget built from last year's figures has nothing in it for this. Note also "
                  "that the fee is waived on a new application lodged alongside a DA — worth "
                  "timing deliberately.",
    },
    "food_safety_supervisor": {
        "name": "Food Safety Supervisor",
        "issued_by": "A Registered Training Organisation; certificate held by the business",
        "legislation": "Food Act 2003 (NSW), Food Standards Code 3.2.2A",
        "triggered_by": "Most retail food businesses that handle unpackaged, potentially "
                        "hazardous food.",
        "timing": "before_opening",
        "what_it_is": "A nominated, trained supervisor whose certificate must be held by the "
                      "business. Standard 3.2.2A also requires food handler training and a "
                      "documented way of showing compliance.",
        "gotcha": "Not a Council approval and not part of the DA, so it falls off the list "
                  "entirely — then turns up at the first inspection. "
                  "`documents/business/food-standard-3-2-2a-guideline.pdf` covers what the "
                  "standard requires.",
    },
    "fitout_food_premises_standards": {
        "name": "Food premises construction standards",
        "issued_by": "Assessed by Lismore City Council's Environmental Health Officers",
        "legislation": "Food Standards Code 3.2.3 (food premises and equipment)",
        "triggered_by": "Fitting out or altering any premises where food is handled.",
        "timing": "before_da",
        "what_it_is": "Requirements for surfaces, floor and wall junctions, hand basins, sinks, "
                      "storage, ventilation and cleaning — which drive the fitout drawings.",
        "gotcha": "These are design inputs, not a later approval. Council's Environmental "
                  "Health Officers will look at fitout plans before lodgement if asked, and "
                  "DCP Chapter 7 §7.3 encourages exactly that. "
                  "`documents/business/requirements-for-set-up-of-food-premises.pdf` is the "
                  "Council guidance. Fixing a non-compliant fitout after it is built is the "
                  "expensive way to learn this.",
    },
    "liquor_licence": {
        "name": "Liquor licence",
        "issued_by": "Liquor & Gaming NSW / the Independent Liquor & Gaming Authority — not "
                     "Council",
        "legislation": "Liquor Act 2007",
        "triggered_by": "Selling or supplying alcohol.",
        "timing": "after_consent",
        "what_it_is": "A separate state licence. Council is a stakeholder and is notified, but "
                      "it does not issue the licence.",
        "fee": "Not quoted here — set by Liquor & Gaming NSW and not carried in any document "
               "in this repository. It does not appear in Council's fee schedule because it is "
               "not Council's fee.",
        "gotcha": "Two traps. The licence application generally needs development consent "
                  "permitting the use first, so it runs *after* the DA and adds to the "
                  "timeline rather than overlapping it — and it has its own advertising and "
                  "community consultation requirements. Plan for it in the opening date from "
                  "the start.",
    },

    # --- using the footpath -------------------------------------------------
    "outdoor_dining_permit": {
        "name": "Outdoor dining permit (footpath dining)",
        "issued_by": "Applied for through Service NSW; Council and the roads authority are the "
                     "approving agencies",
        "legislation": "NSW Outdoor Dining Policy 2019; Roads Act 1993; Local Government Act "
                       "1993",
        "triggered_by": "Putting tables and chairs on the footpath or road reserve.",
        "timing": "before_opening",
        "what_it_is": "A permit for temporary use of the footpath. Applications go through the "
                      "Service NSW Easy to do Business concierge at "
                      "mybusiness.service.nsw.gov.au, not through a Council DA.",
        "fee": "Fee-free for a permit under the NSW policy: 'Council and state government "
               "agency fees will be waived for businesses that obtain a permit under this "
               "policy.' Council's schedule matches — its Tier 1 (villages) and Tier 2 (CBD "
               "temporary footpath use) rates read 'Subject to NSW Outdoor Dining Policy'. "
               "Permanent structures are different: Tier 3 is $85.25 and Tier 4 $113.65 per "
               "square metre per year.",
        "fee_source": f"{COUNCIL_SCHEDULE}, p47; NSW Outdoor Dining Policy 2019, pp9-10",
        "gotcha": "The line that costs money is temporary versus permanent. Anything permanent "
                  "— a fixed screen, a deck, an awning that is not temporary — falls outside "
                  "the policy, needs separate Council approval and attracts the annual "
                  "per-square-metre licence fee. It can also make the area 'enclosed', which "
                  "under DCP Chapter 7 §7.7.3.1(ii) turns it into gross floor area and "
                  "generates a parking requirement that unenclosed dining does not. Public "
                  "liability insurance, usually $20 million, is required either way.",
    },
    "road_reserve_works": {
        "name": "Section 138 approval (works in the road reserve)",
        "issued_by": "Lismore City Council, or Transport for NSW on a classified road",
        "legislation": "Roads Act 1993 section 138",
        "triggered_by": "Any work in the road reserve — a new or widened vehicle crossing, "
                        "footpath works, a hoarding during construction, a skip bin.",
        "timing": "after_consent",
        "what_it_is": "Consent to carry out work on or over a public road, separate from the "
                      "development consent.",
        "fee": "An event or activity application under section 68/138 is $570.50, with an "
               "urgency fee of $487.00 where it is lodged less than ten working days before.",
        "fee_source": f"{COUNCIL_SCHEDULE}, p31",
        "gotcha": "A fitout that changes the shopfront line or needs a hoarding over the "
                  "footpath needs this, and it is usually discovered by the builder rather "
                  "than planned for.",
    },

    # --- keeping operating --------------------------------------------------
    "fire_safety_statement": {
        "name": "Annual Fire Safety Statement",
        "issued_by": "The owner, certified by an accredited practitioner, lodged with Council "
                     "and Fire and Rescue NSW",
        "legislation": "Environmental Planning and Assessment (Development Certification and "
                       "Fire Safety) Regulation 2021",
        "triggered_by": "Any building with essential fire safety measures — which is most "
                        "commercial premises.",
        "timing": "ongoing",
        "what_it_is": "An annual statement that each fire safety measure has been assessed and "
                      "is working.",
        "gotcha": "An ongoing obligation, not a one-off approval, and it usually transfers to "
                  "a new tenant or owner without anyone mentioning it. Ask who has been "
                  "lodging it before taking on a lease.",
    },
    "waste_and_recycling": {
        "name": "Commercial waste collection",
        "issued_by": "A private contractor, or Council where a service is available",
        "legislation": "Conditions of consent; DCP Chapter 15 Waste Minimisation",
        "triggered_by": "Any commercial premises generating waste.",
        "timing": "before_opening",
        "what_it_is": "Businesses are not on the domestic kerbside service by default. The DA "
                      "will normally condition where bins are stored and how they are "
                      "presented.",
        "gotcha": "Bin storage is a design constraint in a small CBD tenancy with no rear "
                  "access, and a waste management plan is commonly required with the DA. "
                  "Deciding it after the fitout is drawn is how a tenancy loses floor area.",
    },
}

# The order these are usually needed in. Alphabetical order would scatter the
# ones that share a deadline, and the sequence is the actual advice.
SEQUENCE = [
    "fitout_food_premises_standards",
    "onsite_sewage_management",
    "liquid_trade_waste",
    "construction_certificate",
    "long_service_levy",
    "principal_certifier",
    "section_68_approval",
    "road_reserve_works",
    "food_business_notification",
    "food_safety_supervisor",
    "liquor_licence",
    "outdoor_dining_permit",
    "waste_and_recycling",
    "occupation_certificate",
    "fire_safety_statement",
]

# Which approvals a kind of business normally needs. Deliberately generous —
# listing something that turns out not to apply costs a sentence, while omitting
# one costs weeks.
BY_ACTIVITY = {
    "food": [
        "fitout_food_premises_standards", "food_business_notification",
        "food_safety_supervisor", "liquid_trade_waste", "waste_and_recycling",
    ],
    "alcohol": ["liquor_licence"],
    "outdoor_dining": ["outdoor_dining_permit"],
    "building_work": [
        "construction_certificate", "principal_certifier", "occupation_certificate",
        "long_service_levy", "fire_safety_statement",
    ],
    "unsewered": ["onsite_sewage_management"],
    "sewer_connection": ["section_68_approval"],
    "road_reserve": ["road_reserve_works"],
    "any_commercial": ["waste_and_recycling", "fire_safety_statement"],
}

# What the DA is and is not, stated once. The misunderstanding this whole file
# exists to correct.
WHAT_THE_DA_DOES_NOT_COVER = (
    "Development consent decides that the use is allowed on the land and on what terms. It is "
    "not permission to build, to connect to the sewer, to serve food or alcohol, to occupy the "
    "building, or to put anything on the footpath. Each of those is a separate approval, and "
    "several are issued by someone other than Council's planners. Two of them — the "
    "Construction Certificate and the Occupation Certificate — cannot even be applied for until "
    "the consent exists, so they sit after the DA in the timeline rather than beside it."
)
