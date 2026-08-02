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
