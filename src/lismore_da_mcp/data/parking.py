"""Off-street parking rates, Lismore DCP Chapter 7 Schedule 1.

Transcribed 2026-08-02 from `documents/dcp/chapter-7-off-street-carparking.pdf`,
Schedule 1 "Carparking Requirements for Specific Land Uses", pp. 11-15.

**The previous version of this file did not match the DCP**, and not marginally.
It was found by the audit written for PLAN.md 0.2:

  * `dwelling_house` carried what is actually the *dual occupancy* rule
  * `warehouse` said 1 per 100m2 where the DCP says 1 per 300m2 — overstating 3x
  * `restaurant`/`cafe` used "1 per 10m2 dining area", a basis that appears
    nowhere in Schedule 1
  * the multi-dwelling and flat-building tiers were wrong in both the per-unit
    rates and the visitor ratio
  * `take_away` and `secondary_dwelling` had confident rates despite Schedule 1
    having no entry for either

Parking is the recurring argument between a CBD business and Council, so these
are among the most consequential numbers in the repo. Understating sends a DA
back; overstating can talk someone out of a viable proposal.

Each entry carries:

  `dcp_use`      the land use exactly as Schedule 1 names it, or None if absent
  `rate`         the requirement verbatim, so the real rule can always be shown
  `spaces`       a short form for display
  `source`       page, for anyone checking
  `spec`         a structured form — **only** where the rule can be computed
  `note`         what the caller has to decide, where the rule is conditional

`spec` is deliberately None where the DCP assesses a use "on merits", where the
rule needs an input the caller has not supplied, or where the use is not in the
schedule at all. The estimator then shows the rule and declines to produce a
number rather than inventing one — a confident wrong space count is exactly what
sends a DA back.

`scripts/audit_parking_rates.py` checks every `rate` string still appears in the
PDF, so a reissued chapter is caught rather than silently diverging.

Spec grammar
------------
    sum       components, added
    or_       an alternative area-based rate; requirement is the greater of the two
    or_alt    an alternative set of components; requirement is the greater
    minimum   floor applied last
    tiers     rate varies with floor area

Component forms:
    {"one_per": N, "of": "seats"}   1 space per N of something the caller counts
    {"rate": R, "per": "seats"}     R spaces per one of something
    {"rate": R, "per_area": A}      R spaces per A m2 of the entry's `basis`
"""

SCHEDULE = "DCP Chapter 7 Schedule 1"

# What a spec may ask the caller to count, and the argument it arrives as.
#
# Ten of these twelve had no argument on `get_parking_rates` until 2026-08-20,
# so the caller could not supply them however hard they tried. A medical centre
# charged "4 per practitioner, plus 1 per employee" answered 5 spaces for 5
# employees, with "not counted: practitioners" three levels down in
# `calculation.basis` — against a real requirement of 17 for three
# practitioners. ROADMAP.md S3.
#
# `tools/parking.py` now builds its schema from this dict, so a countable added
# to a rate cannot fail to be askable. That is what this mapping was for; it was
# imported and never read.
COUNTABLE = {
    "seats": "seats",
    "employees": "num_employees",
    "children": "children",
    "beds": "beds",
    "rooms": "rooms",
    "practitioners": "practitioners",
    "dwellings": "dwellings",
    "accommodation_units": "accommodation_units",
    "work_bays": "work_bays",
    "bedrooms_1": "one_bedroom_units",
    "bedrooms_2": "two_bedroom_units",
    "bedrooms_3": "three_bedroom_units",
}

# What each argument means, in the caller's words. Keyed by argument name, so a
# rate that starts counting something new needs a line here before it can be
# asked for — `tests/test_parking.py` checks the two dicts agree exactly.
COUNTABLE_DESCRIPTIONS = {
    "seats": "Seats, for rates based on seating (restaurants, places of worship, function centres).",
    "num_employees": "Number of employees, for rates with a staff component.",
    "children": "Places for children, for a centre-based child care facility.",
    "beds": "Beds, for a hospital, nursing home or similar.",
    "rooms": "Guest rooms, for a motel or hotel.",
    "practitioners": (
        "Practitioners, for a medical centre — the dominant term in its rate "
        "(4 spaces each, against 1 per employee). Without it no number is given."
    ),
    "dwellings": "Number of dwellings.",
    "accommodation_units": "Self-contained accommodation units, for tourist and visitor accommodation.",
    "work_bays": "Work bays, for a vehicle repair station or similar.",
    "one_bedroom_units": "Number of one-bedroom units, where the rate varies by bedroom count.",
    "two_bedroom_units": "Number of two-bedroom units.",
    "three_bedroom_units": "Number of three-bedroom units.",
}

# The café rule is the one genuinely ambiguous entry in Schedule 1, and it is
# also the one a CBD business argues about most. Its wording —
#
#     "1 per 3 seats, plus 1 per 2 employees or 15 per 100m2 GFA
#      (whichever is greater)"
#
# does not say what "(whichever is greater)" governs, and the three available
# readings give materially different answers:
#
#     A   max(seats + employees, GFA)      the reading this file used until
#                                          2026-08-02
#     B   seats + max(employees, GFA)      considered and rejected — see below
#     C   employees + max(seats, GFA)      what is implemented
#
# **C is implemented on the strength of Tweed Shire Council's published review**,
# "Review of car parking requirements for small business" (2018 council business
# paper, attachment 2), which tabulates eight councils' rates and cites this exact
# document — "Lismore City, Ref: DCP 2012 - Chapter 7 - Schedule 1". It splits
# every rate into a Staff column and a Customer column, and reads this one as:
#
#     Staff parking     1/2 employees
#     Customer parking  1/3 seats or 15/100m2 GFA whichever is greater
#
# https://www.tweed.nsw.gov.au/files/assets/public/v/1/documents/council/council-meetings/archived/2018/21-attach-2-ecm-review-of-car-parking-requirements-for-small-business.pdf
#
# That reading is also the only one that makes the comparison meaningful. Seats
# and floor area are two proxies for the *same* quantity — how many customers the
# premises holds — so "whichever is greater" picking between them is a sensible
# instruction. Reading A compares a staff-plus-customer total against a
# customer-only measure, which compares unlike things.
#
# The schedule's own drive-through entry confirms the pattern, and there the
# wording is unambiguous because the two customer measures sit adjacent:
# "1 per employee, plus 12 per 100m2 GFA or 1 per 4 seats (whichever is greater),
# plus queuing area". Staff additive, customer measures alternated. The café entry
# means the same thing; its clauses are merely written in a jumbled order.
#
# What changed in practice: A and C agree whenever the seats basis exceeds the
# floor-area basis, which is why this went unnoticed — the worked example
# throughout this repo (80m2, 40 seats, 6 staff) returns 17 under both. They
# diverge for a sparsely seated café in a large tenancy, where A understated:
# 80m2 with 20 seats and 6 staff is 12 under A and **15** under C.
#
# `rate` below is the DCP's own wording and must not be edited to match the
# interpretation — `scripts/audit_parking_rates.py` checks it against the PDF.
_RESTAURANT = {
    "dcp_use": "Restaurant or cafe",
    "spaces": "1 per 2 employees, plus the greater of 1 per 3 seats or 15 per 100m² GFA",
    "rate": "1 per 3 seats, plus 1 per 2 employees or 15 per 100m2 GFA (whichever is greater)",
    "source": f"{SCHEDULE}, p14",
    "basis": "GFA",
    "note": "Schedule 1's wording leaves it open what '(whichever is greater)' applies to. "
            "This follows the reading that the staff component is added and the greater is "
            "taken between the two measures of customer capacity — seats and floor area — "
            "which is how Tweed Shire's 2018 cross-council review reads this schedule, and "
            "how Schedule 1's own drive-through entry is worded. Confirm with Council if the "
            "number is close to what you can provide. A drive-through has its own, stricter "
            "entry in Schedule 1.",
    "spec": {
        "sum": [
            {"one_per": 2, "of": "employees"},
            {"greater_of": [{"one_per": 3, "of": "seats"}, {"rate": 15, "per_area": 100}]},
        ],
    },
}

_OFFICE = {
    "spaces": "1 per 30m² GFA (ground/1st floor), 1 per 40m² above; minimum 2",
    "rate": "1 per 30m2 GFA for ground or 1st floor level and 1 per 40m2 GFA at subsequent "
            "upper levels. Minimum number of 2 spaces per office.",
    "basis": "GFA",
    "note": "The rate depends which floor the space is on, so a single figure needs the "
            "floor-by-floor areas. Any estimate here assumes ground or first floor — the "
            "stricter rate.",
    "spec": {"sum": [{"rate": 1, "per_area": 30}], "minimum": 2},
}

_HOTEL = {
    "dcp_use": "Hotel or motel accommodation",
    "spaces": "1 per accommodation unit + 1 per 2 employees + area-based components",
    "rate": "1 per accommodation unit, plus 1 per manager's/owner's residence, plus 1 per 2 "
            "employees, plus 1 per 30m2 public area (if a restaurant is included in the "
            "motel), plus 1 per 15m2 function room area",
    "source": f"{SCHEDULE}, p12",
    "note": "Any estimate covers the accommodation and employee components only. The "
            "residence, restaurant and function-room components need those areas. A pub is "
            "a separate entry with its own bar, lounge, gaming and dining rates.",
    "spec": {"sum": [{"rate": 1, "per": "accommodation_units"},
                     {"one_per": 2, "of": "employees"}]},
}

_UNITS = {
    "spaces": "1 per 1-bed, 1.5 per 2-bed, 2 per 3-bed, plus 1 per 5 units visitor",
    "rate": "1 per 1 bedroom unit, plus 1.5 per 2 bedroom unit, plus 2 per 3 bedroom unit, "
            "plus 1 per 5 units visitor parking",
    "spec": {"sum": [{"rate": 1, "per": "bedrooms_1"},
                     {"rate": 1.5, "per": "bedrooms_2"},
                     {"rate": 2, "per": "bedrooms_3"},
                     {"one_per": 5, "of": "dwellings"}]},
}

PARKING_RATES = {
    # --- the business uses this tool exists for -----------------------------
    "restaurant": {**_RESTAURANT},
    "cafe": {**_RESTAURANT},
    "shop": {
        "dcp_use": "Shop (individual)",
        "spaces": "4.4 per 100m² GFA",
        "rate": "4.4 per 100m2 GFA",
        "source": f"{SCHEDULE}, p14",
        "basis": "GFA",
        "note": "A shopping complex, liquor outlet and neighbourhood shop each have their "
                "own rate in Schedule 1.",
        "spec": {"sum": [{"rate": 4.4, "per_area": 100}]},
    },
    "retail": {
        "dcp_use": "Shop (individual)",
        "spaces": "4.4 per 100m² GFA",
        "rate": "4.4 per 100m2 GFA",
        "source": f"{SCHEDULE}, p14",
        "basis": "GFA",
        "note": "Schedule 1 has no land use called 'retail'. Shop (individual) is the closest "
                "— confirm which shop category applies.",
        "spec": {"sum": [{"rate": 4.4, "per_area": 100}]},
    },
    "neighbourhood_shop": {
        "dcp_use": "Neighbourhood shop",
        "spaces": "5 per 100m² GFA",
        "rate": "5 per 100m2 GFA",
        "source": f"{SCHEDULE}, p12",
        "basis": "GFA",
        "spec": {"sum": [{"rate": 5, "per_area": 100}]},
    },
    "office": {**_OFFICE, "dcp_use": "Office premises", "source": f"{SCHEDULE}, p13"},
    "business_premises": {**_OFFICE,
                          "dcp_use": "Business premises (other than funeral homes)",
                          "source": f"{SCHEDULE}, p11"},
    "bulky_goods": {
        "dcp_use": "Bulky goods premises",
        "spaces": "3 per 100m² GFA up to 400m², 2 per 100m² above",
        "rate": "Less than or equal to 400m2 GFA – 3 per 100m2; GFA > 400m2 – 2 per 100m2",
        "source": f"{SCHEDULE}, p11",
        "basis": "GFA",
        "spec": {"tiers": [{"up_to_area": 400, "rate": 3, "per_area": 100},
                           {"rate": 2, "per_area": 100}]},
    },
    "industry": {
        "dcp_use": "Industry (heavy, general and light)",
        "spaces": "1 per 100m² GFA, minimum 2",
        "rate": "1 per 100m2 GFA or part thereof. Minimum of 2 spaces per unit or separate "
                "leased area",
        "source": f"{SCHEDULE}, p12",
        "basis": "GFA",
        "note": "The minimum of 2 applies per unit or separate leased area, so a multi-unit "
                "development needs it counted per tenancy.",
        "spec": {"sum": [{"rate": 1, "per_area": 100}], "minimum": 2},
    },
    "warehouse": {
        "dcp_use": "Warehouse or distribution centre",
        "spaces": "1 per 300m²",
        "rate": "1 per 300m2",
        "source": f"{SCHEDULE}, p15",
        "basis": "GFA",
        "spec": {"sum": [{"rate": 1, "per_area": 300}]},
    },
    "medical_centre": {
        "dcp_use": "Medical centre",
        "spaces": "4 per practitioner + 1 per employee",
        "rate": "4 per practitioner, plus 1 per employee",
        "source": f"{SCHEDULE}, p12",
        "spec": {"sum": [{"rate": 4, "per": "practitioners"},
                         {"rate": 1, "per": "employees"}]},
    },
    "gym": {
        "dcp_use": "Recreation facility (indoor) — Gymnasium/fitness centre",
        "spaces": "1 per 25m² GFA + 1 per 2 employees",
        "rate": "1 per 25m2 GFA, plus 1 per 2 employees",
        "source": f"{SCHEDULE}, p13",
        "basis": "GFA",
        "spec": {"sum": [{"rate": 1, "per_area": 25}, {"one_per": 2, "of": "employees"}]},
    },
    "hotel": {**_HOTEL},
    "motel": {**_HOTEL},
    "childcare_centre": {
        "dcp_use": "Child care centre",
        "spaces": "1 per employee + 1 per 10 children (1 per 15 with 3 set-down areas)",
        "rate": "1 per employee, plus 1 per 15 children (if provision of 3 set down/pick up "
                "areas) or 1 per 10 children, plus 2 per owner/manager dwelling house",
        "source": f"{SCHEDULE}, p11",
        "note": "The children rate depends on whether three set-down/pick-up areas are "
                "provided: 1 per 15 with them, 1 per 10 without. Any estimate assumes the "
                "stricter 1 per 10.",
        "spec": {"sum": [{"rate": 1, "per": "employees"}, {"one_per": 10, "of": "children"}]},
    },
    "place_of_worship": {
        "dcp_use": "Place of public worship",
        "spaces": "1 per 10 seats",
        "rate": "1 per 10 seats",
        "source": f"{SCHEDULE}, p13",
        "spec": {"sum": [{"one_per": 10, "of": "seats"}]},
    },
    "function_centre": {
        "dcp_use": "Function centre",
        "spaces": "1 per 10 seats or 1 per 10m² public floor space (greater)",
        "rate": "1 per 10 seats or 1 per 10m2 of public floor space, whichever is greater",
        "source": f"{SCHEDULE}, p12",
        "basis": "public floor space",
        "spec": {"sum": [{"one_per": 10, "of": "seats"}], "or_": {"rate": 1, "per_area": 10}},
    },
    "vehicle_repair_station": {
        "dcp_use": "Vehicle repair station",
        "spaces": "4 per work bay + 1 per employee",
        "rate": "4 per work bay, plus 1 per employee",
        "source": f"{SCHEDULE}, p15",
        "spec": {"sum": [{"rate": 4, "per": "work_bays"}, {"rate": 1, "per": "employees"}]},
    },
    "service_station": {
        "dcp_use": "Service station",
        "spaces": "1 per employee + 4 per work bay + 1 articulated vehicle space",
        "rate": "1 per employee, plus 4 per work bay, plus a minimum of 1 articulated vehicle "
                "parking space",
        "source": f"{SCHEDULE}, p14",
        "spec": {"sum": [{"rate": 1, "per": "employees"}, {"rate": 4, "per": "work_bays"}]},
    },

    # --- residential --------------------------------------------------------
    "dwelling_house": {
        "dcp_use": "Dwelling house",
        "spaces": "2 per dwelling (1 undercover)",
        "rate": "2 per dwelling (1 undercover)",
        "source": f"{SCHEDULE}, p11",
        "spec": {"sum": [{"rate": 2, "per": "dwellings"}], "defaults": {"dwellings": 1}},
    },
    "dual_occupancy": {
        "dcp_use": "Dual occupancy",
        "spaces": "1 per dwelling under 125m², 2 per dwelling over",
        "rate": "1 per dwelling if GFA is <125m2 or 2 per dwelling if GFA is >125m2",
        "source": f"{SCHEDULE}, p11",
        "basis": "GFA per dwelling",
        "note": "The tier is on each dwelling's own floor area, not the site total, so a "
                "figure needs the area of each dwelling.",
        "spec": None,
    },
    "multi_dwelling_housing": {**_UNITS, "dcp_use": "Multi dwelling housing",
                               "source": f"{SCHEDULE}, p12"},
    "residential_flat_building": {**_UNITS, "dcp_use": "Residential flat building",
                                  "source": f"{SCHEDULE}, p14"},
    "boarding_house": {
        "dcp_use": "Boarding house",
        "spaces": "1 per 3 beds + 1 per 5 beds visitor, or 1 per room + 1 per 5 rooms (greater)",
        "rate": "1 per 3 beds plus 1 per 5 beds visitor space or 1 per room plus 1 per 5 rooms "
                "visitor space (whichever the greater).",
        "source": f"{SCHEDULE}, p11",
        "spec": {
            "sum": [{"one_per": 3, "of": "beds"}, {"one_per": 5, "of": "beds"}],
            "or_alt": [{"rate": 1, "per": "rooms"}, {"one_per": 5, "of": "rooms"}],
        },
    },
    "caravan_park": {
        "dcp_use": "Caravan park",
        "spaces": "1 per site + residence + 1 per 2 employees + 1 per 10 sites visitor",
        "rate": "1 per serviced caravan/camp site, plus 1 per manager/owner residence, plus "
                "1 per 2 employees, plus 1 per 10 sites for visitors",
        "source": f"{SCHEDULE}, p11",
        "spec": None,
    },

    # The one Schedule 1 entry where the CBD answer is *zero*, and it was
    # missing entirely until 2026-08-20. `get_parking_rates` errored and
    # suggested `shop` — 4.4 per 100m² — telling a CBD business to build parking
    # the DCP expressly does not require. SCENARIOS.md D8.
    #
    # `spec` is None for the same reason as dual_occupancy: outside the CBD the
    # tier is on *each dwelling's* GFA, and one floor-area figure cannot resolve
    # it. Inside the CBD there is nothing to compute — Schedule 1 says no
    # requirement, and `cbd_answer` carries that.
    "shop_top_housing": {
        "dcp_use": "Shop top housing",
        "spaces": "CBD: none. Outside the CBD: 1 per dwelling under 125m², 2 per dwelling over",
        "rate": "CBD (defined in Map 1) - No carparking requirements Outside the CBD - 1 per "
                "dwelling if GFA <125m2 or 2 per dwelling if GFA is >125m2",
        "source": "DCP Chapter 7 Schedule 1, p14",
        "basis": "GFA per dwelling, outside the CBD only",
        "note": "Inside the CBD this use has no carparking requirement at all — Schedule 1 says "
                "so expressly, and it is the reason shop top housing is viable above a CBD "
                "shopfront. Outside the CBD the tier is on each dwelling's own floor area, not "
                "the site total, so a figure needs the area of each dwelling. Being residential "
                "accommodation, §7.7.3.1 exception (i) keeps it on Schedule 1 rather than the "
                "fixed 3.3/100m² CBD rate — which here means zero, not 3.3.",
        "spec": None,
    },

    # --- uses Schedule 1 does not name --------------------------------------
    #
    # Kept because callers ask for them, but with no invented number. The
    # previous file gave both a confident rate with no basis in the DCP at all.
    "take_away": {
        "dcp_use": None,
        "spaces": "not specified in Schedule 1",
        "rate": "Schedule 1 has no entry for take away food and drink premises.",
        "source": SCHEDULE,
        "note": "Council may assess it against 'Restaurant or cafe' (1 per 3 seats, plus 1 per "
                "2 employees or 15 per 100m2 GFA, whichever is greater), or against the "
                "separate drive-through entry if there is one. Confirm which applies with the "
                "Duty Planner before relying on a number.",
        "spec": None,
    },
    "secondary_dwelling": {
        "dcp_use": None,
        "spaces": "not specified in Schedule 1",
        "rate": "Schedule 1 has no entry for secondary dwellings.",
        "source": SCHEDULE,
        "note": "Secondary dwellings are generally dealt with under the Housing SEPP rather "
                "than this schedule, and the SEPP may set its own parking requirement. "
                "Confirm with Council.",
        "spec": None,
    },
}


# ---------------------------------------------------------------------------
# The Lismore CBD is assessed under a different rate entirely (§7.7.2, §7.7.3)
# ---------------------------------------------------------------------------
#
# Schedule 1 above is **not** the rate inside the CBD. §7.7.2 sets it as the
# minimum "for developments located outside the Lismore CBD, as defined on
# Map 1"; §7.7.3.1 replaces it inside the CBD with a single fixed rate of 3.3
# spaces per 100m2 GFA for all non-residential use.
#
# Everything in this file predates that distinction, so every answer this
# server has ever given a CBD business used the wrong schedule. It is not a
# rounding difference. An 80m2 café with four staff:
#
#     Schedule 1 (what the tool said)   14 spaces
#     §7.7.3.1 fixed CBD rate            3 spaces
#     less the §7.7.3.4 deemed credit    2 spaces  (80m2 @ 2.5/100m2)
#     ------------------------------------------------
#     net requirement                    1 space
#
# and that one space may itself be satisfied by a payment under §7.7.3.3
# rather than built. "You are 14 spaces short, justify it" and "you owe one
# space, which you can pay for" are different proposals — the first talks a
# viable business out of a tenancy. This is the same failure as PLAN.md 0.3:
# the numbers were nobody's guess, they were simply never read.
#
# **CBD membership is never inferred.** Map 1 defines the boundary and is a
# bitmap on the last page of the chapter with no extractable text, so nothing
# here can decide it. The E2 Commercial Centre zone is close but is not the
# same line. The caller states it or the tool returns both readings.

CHAPTER = "DCP Chapter 7"

CBD_FIXED_RATE = {
    "rate": 3.3,
    "per_area": 100,
    "verbatim": "a fixed rate of no less than 3.3 car spaces/100m2 of gross floor area "
                "(as defined in the Lismore LEP) shall be required for development within "
                "the CBD/City Centre",
    "source": f"{CHAPTER} §7.7.3.1, p8",
    # Exception (i). Residential and tourist accommodation stay on Schedule 1
    # even inside the CBD, so the fixed rate must not be applied to them.
    "excluded_uses": (
        "residential_flat_building", "multi_dwelling_housing", "dwelling_house",
        "dual_occupancy", "secondary_dwelling", "boarding_house", "motel",
        "bed_and_breakfast", "caravan_park",
        # Residential accommodation, so exception (i) sends it to Schedule 1 —
        # which for the CBD says "no carparking requirements". Off this list it
        # would be charged 3.3/100m² for a use the DCP charges nothing for.
        "shop_top_housing",
    ),
    "exclusion_verbatim": "Where the development is (or includes) residential accommodation "
                          "or tourist and visitor accommodation, the minimum number of spaces "
                          "required shall be as described in Schedule 1",
}

# §7.7.3.4. Read the formula carefully: the credit is the requirement the
# *existing* building would generate at 2.5/100m2 **less the spaces already on
# the site**. A site that already parks its own cars gets a smaller credit, not
# a larger one — the credit represents parking the site is deemed to have
# contributed to the CBD pool, and spaces it kept for itself are not in it.
CBD_PARKING_CREDIT = {
    "rate": 2.5,
    "per_area": 100,
    "verbatim": "Deemed Parking Credit = parking requirement for existing development @ 2.5 "
                "spaces/100m2 gross floor area less the number of parking spaces physically "
                "provided on the existing development site.",
    "source": f"{CHAPTER} §7.7.3.4, p10",
    "evidenced_alternative": "Where evidence can be provided that the development site has, "
                             "through cash in lieu payment, provided a greater number of "
                             "parking spaces to the CBD than that given by the above formula, "
                             "the greater number of parking spaces shall be taken to be the "
                             "allowable reduction applied to the proposed development parking "
                             "requirement. The onus is on the developer to prove the existence "
                             "of any such payments.",
}

# §7.7.3.3 and §7.7.3.2. Both reduce the requirement by 25%, and both apply
# only to the component treated that way — not to the whole requirement.
CBD_REDUCTIONS = {
    "consolidated": {
        "name": "Monetary contribution in lieu of providing the space (consolidated parking)",
        "reduction": 0.25,
        "verbatim": "Where an applicant considers it impractical, impossible or undesirable to "
                    "physically provide the required parking spaces on site in the CBD, a cash "
                    "contribution for each parking space not provided may be accepted by "
                    "Council under Section 94 of the Environmental Planning and Assessment Act "
                    "1979 to provide “consolidated” parking elsewhere.",
        "source": f"{CHAPTER} §7.7.3.3, pp9-10",
    },
    "shared": {
        "name": "Shared parking — spaces on site left open to the public",
        "reduction": 0.25,
        "verbatim": "Where part or the whole of the parking required for a new development "
                    "(apart from the residential uses listed above) is shared parking the "
                    "minimum requirement for the component of parking that is shared will be "
                    "reduced by 25%.",
        "source": f"{CHAPTER} §7.7.3.2, p9",
        "conditions": [
            "At least 6 spaces if the parking is visible from a vehicle on a public road, or "
            "15 spaces if it is not.",
            "Provided within the development site.",
            "Available to the general public at least 9am–11pm, Monday to Saturday.",
            "Not reserved for users of the development — spaces cannot be marked for the use "
            "of employees or customers of the business.",
            "Signposted as available to the public, and designed to Crime Prevention by "
            "Design principles.",
        ],
        # §7.7.3.2's closing note. Order matters: 25% of the post-credit
        # requirement is a smaller reduction than 25% of the gross one.
        "ordering": "The reduction in car parking required will be calculated after any "
                    "parking credit is applied (refer to section 7.7.3.4 below).",
    },
}

# The rate for the §7.7.3.3 payment is **not recoverable from this repo**, and
# saying so is the honest answer rather than a gap to be filled with a guess.
# The DCP points at "Council's Contributions Plan prepared pursuant to Section
# 94", and §7.7.3.1(ii)(d) at "the Lismore Contributions Plan (Section 2.5.5)".
# Section 94 was repealed and re-enacted as Section 7.11 in 2017, and the
# current plan in this repo — Section 7.11 Infrastructure Contributions Plan
# 2024-2041 — has **no car parking contribution category at all** (its
# categories are community facilities, public domain, open space, walking and
# cycling, traffic management, stormwater, heavy haulage, administration), and
# no section 2.5.5. So the DCP's cross-reference is stale and whether the
# payment is still levied, and at what rate, is a question only Council can
# answer. Same treatment as the Section 64 charge in data/contributions.py:
# name it, source it, refuse to invent it.
CBD_CASH_IN_LIEU_RATE = {
    "status": "not quantifiable from Council's published documents",
    "why": "DCP §7.7.3.3 sets the contribution at the rate in Council's contributions plan, "
           "but it cites the repealed Section 94 and a section number that does not exist in "
           "the current plan. The Section 7.11 Infrastructure Contributions Plan 2024-2041 "
           "carries no car parking contribution category, so no rate can be read from it.",
    "ask_council": "Ask the Duty Planner whether a contribution in lieu of parking is still "
                   "levied in the CBD and at what rate per space, before assuming a shortfall "
                   "can be paid out.",
    "source": f"{CHAPTER} §7.7.3.3; Section 7.11 Contributions Plan 2024-2041",
}

# §7.7.3.1(iii). Small but directly useful: a fitout expanding within an
# existing CBD tenancy may add floor space once without a parking charge.
CBD_EXPANSION_ALLOWANCE = {
    "verbatim": "Existing commercial premises (commercial premises has the same meaning as in "
                "Lismore LEP 2012) within the Lismore CBD (see map 1 of this DCP) may, with "
                "consent, increase internal floor space by up to 20% of the existing building "
                "GFA up to a maximum of 40m2 without incurring Section 94 charges for car "
                "parking. This allowance will only be available once to each premises (whether "
                "20% or 40m2 is achieved or not), and any further internal extensions will "
                "attract relevant Sec 94 charges.",
    "percent": 0.20,
    "cap_sqm": 40,
    "source": f"{CHAPTER} §7.7.3.1(iii), p9",
    "note": "Once per premises, from 28 April 2011. Ask Council whether a previous occupant "
            "of the tenancy has already used it — the allowance attaches to the premises, not "
            "to the business.",
}

# §7.7.3.1(ii). Outdoor dining is where a café's parking charge is actually
# decided, and the answer turns on two things a business can control: whether
# the area is enclosed, and whether it is in the Magellan Street precinct.
CBD_OUTDOOR_DINING = {
    "source": f"{CHAPTER} §7.7.3.1(ii), pp8-9",
    "rules": [
        "Unenclosed outdoor dining, anywhere in the CBD: no parking charge — an unenclosed "
        "area is not gross floor area, so it does not generate a requirement at all.",
        "Enclosed outdoor dining inside the Magellan Street Entertainment/Activity Precinct: "
        "no parking charge.",
        "Enclosed outdoor dining outside that precinct: charged at the DCP rate for "
        "non-provision of parking.",
        "If a new outdoor dining area removes on-street spaces, a contribution for the lost "
        "spaces is levied — unless the area is within the Magellan Street precinct.",
    ],
    "note": "“Enclosed” has the same meaning as in the definition of gross floor area in "
            "Lismore LEP 2012. The Magellan Street precinct is Map No 2 of Council's Outdoor "
            "Dining Policy adopted 14 September 2010. Whether a proposed screen or awning "
            "makes an area enclosed is worth settling with Council before building it.",
}

# §7.5. These are the grounds an under-provision is actually argued on. A
# shortfall is not waved through by asserting that the street is quiet — it is
# argued against the criteria the consent authority is directed to consider.
MERIT_CRITERIA = {
    "source": f"{CHAPTER} §7.5, p3",
    "intro": "In determining the carparking requirements for any development, Council shall "
             "consider:",
    "criteria": [
        "The minimum number of spaces required by Schedule 1 (outside the CBD) or clause "
        "7.7.3 (inside it).",
        "The size, type and nature of the development and its traffic generating potential.",
        "Traffic volumes on the public road network servicing the development.",
        "The probable mode of transport of users to and from the development.",
        "The characteristics of the streetscape, the site, topography, neighbouring "
        "development pattern and street design — including existing on-street parking, "
        "loading spaces and access arrangements.",
        "The time of peak demand for parking — evening versus normal retail use may allow "
        "shared use of facilities.",
    ],
}

# §7.7.2. A genuine reduction for mixed proposals, and one applicants miss:
# two uses in one tenancy are normally added together, but a use operating
# entirely outside the other's hours is not.
COMBINED_USES = {
    "verbatim": "Where combinations of uses are incorporated in the one development, for "
                "example, restaurant and shop, the parking provision shall be the combined "
                "total of the requirements specified in Schedule 1. However, where one of the "
                "uses will operate exclusively outside the hours of the other, the car parking "
                "rate will be based on the higher land use parking requirement.",
    "source": f"{CHAPTER} §7.7.2, p8",
}

# §7.7.3.5 inside the CBD, §7.7.2 outside it. Worth stating because a business
# widening a driveway for a delivery bay can create a requirement it never
# counted on.
ON_STREET_LOSS = {
    "outside_cbd": "On-street car parking spaces lost as a result of a development, for "
                   "example, through construction of an additional driveway entrance, will be "
                   "required to be provided off-street by the development, unless a variation "
                   "can be justified under this chapter.",
    "in_cbd": "Where on-street car parking spaces in the CBD are lost as a result of a "
              "development taking place, for example, through construction of an additional "
              "driveway entrance, a “debit” may occur.",
    "source": f"{CHAPTER} §7.7.2 and §7.7.3.5, pp8, 10",
}

# §7.7.1. Applies regardless of location, and is a function of what is
# provided rather than what is required.
DISABILITY_PARKING = {
    "verbatim": "Regardless of the location of the development, parking for people with "
                "disability shall be provided at a rate of no less than 1 space for every 100 "
                "spaces provided by a development.",
    "source": f"{CHAPTER} §7.7.1, p8",
}
