"""Developer contributions and charges — the money that is not the DA fee.

Transcribed 2026-08-02 from two documents:

  * `documents/fees/section-7.11-contributions-plan-2024-2041.pdf` — Lismore City
    Council Section 7.11 Infrastructure Contributions Plan 2024-2041, Table E1
    (p6) and Table E2 (p7).
  * `documents/fees/development-servicing-plans-water-wastewater.pdf` — the
    Section 64 Development Servicing Plans, Table 1 (p3).

PLAN.md item 2.1. The reason this file exists: `calculate_da_fees` answered
"what is the DA lodgement fee", and a business reasonably heard that as "what
will this cost me". For an 80m2 retail fitout the lodgement fee is a few hundred
dollars and the Section 7.11 contribution is around **$16,000**. A business that
budgets the first and then receives a consent conditioned on the second is
precisely the business "having issues with Council" that this repo is for.

Table E2 is the operative table — it is what Council levies, expressed per
dwelling, per bed/site or per 100m2 GFA — so its figures are stored verbatim and
are what the tool quotes. Table E1 is the per-person/per-worker/per-PVT basis
underneath it, stored because it is the only way to say anything useful about a
development type Table E2 does not list.

Why both are stored, rather than deriving one from the other
------------------------------------------------------------
E2 is reproducible from E1 — `(occupancy x per-head rates) + (PVTs x traffic
rate)`, then the 4.5% administration loading — and `scripts/audit_contributions.py`
checks that it still is, cell by cell. That is a far better check than a text
search: it catches a mistyped digit in any of the 20 published rates, which a
presence check cannot.

Nineteen of the twenty cells reproduce to within 50c, the published occupancy
figures being rounded to two decimals (Table E2 note B). **One does not:**
tourist and visitor accommodation in the Rural North / Rural South catchments is
$212.68 below its derivation, exactly the Open Space and Recreation component
($339.20 x 0.6 x 1.045). Every other rural row includes that component. It is
listed in `KNOWN_TABLE_DISCREPANCIES` rather than smoothed over by widening the
tolerance, because an audit that tolerates one unexplained gap will tolerate the
next one — the same failure that let the fee scale sit two years stale behind a
standing caveat. The verbatim figure is what Council levies, so the verbatim
figure is what is stored; the derivation is the check, not the answer.

What this file deliberately does not do
---------------------------------------
**It does not guess the catchment.** Contributions differ by catchment, and for
retail the rural rate is *higher* than the urban one ($24,210.38 against
$20,101.55), so quietly defaulting to urban would understate by 20% on a rural
site. The catchment comes from Figures 2 and 3 of the plan, which are maps this
repo cannot read. All three figures are returned unless the caller states one.

**It does not compute a Section 64 charge.** The DSP sets a rate per ET
(equivalent tenement), but it carries no ET conversion table for non-residential
uses — Council assesses that — and its rates are in 2016 dollars indexed to
Sydney CPI each 1 July, so a current figure cannot be produced from this repo.
The rates are stored so the tool can name the charge, say which service area
schedule applies, and tell a food premises to ask Council early, which is worth
considerably more than silence.
"""

# ---------------------------------------------------------------------------
# Section 7.11 infrastructure contributions
# ---------------------------------------------------------------------------

PLAN_NAME = "Lismore City Council Section 7.11 Infrastructure Contributions Plan 2024-2041"
PLAN_SOURCE = "documents/fees/section-7.11-contributions-plan-2024-2041.pdf"
PLAN_BASE_QUARTER = "December 2023"

# Section 4.8 / Table E1: "4.5% of total contribution calculated as per above rates".
ADMIN_LOADING = 0.045

CATCHMENTS = ("urban", "rural_north", "rural_south")

CATCHMENT_NOTE = (
    "Which catchment a site falls in is set by Figures 2 and 3 of the plan, which are "
    "maps. This tool cannot read them, so it does not guess — confirm the catchment with "
    "Council. It matters: for retail premises the rural rate is about 20% higher than the "
    "urban one."
)

# Table E1, p6 — the basis underneath Table E2. Rates are per unit of demand.
# Where the plan prints a single figure spanning all three catchment columns, the
# same figure applies to each; only traffic management is catchment-specific.
INFRASTRUCTURE_RATES = [
    {
        "category": "Community Facilities",
        "basis": "per person (residential)",
        "rates": {"urban": 38.62, "rural_north": 38.62, "rural_south": 38.62},
    },
    {
        "category": "Public Domain",
        "basis": "per person (residential)",
        "rates": {"urban": 65.28, "rural_north": 65.28, "rural_south": 65.28},
    },
    {
        "category": "Public Domain",
        "basis": "per worker (non-residential)",
        "rates": {"urban": 7.96, "rural_north": 7.96, "rural_south": 7.96},
    },
    {
        "category": "Open Space and Recreation",
        "basis": "per person (residential)",
        "rates": {"urban": 339.20, "rural_north": 339.20, "rural_south": 339.20},
        "note": (
            "The plan applies the same rate per bed/site for tourist and visitor "
            "accommodation, camping grounds, caravan parks and eco-tourist facilities."
        ),
    },
    {
        "category": "Walking and Cycling",
        "basis": "per person (residential)",
        "rates": {"urban": 227.40, "rural_north": 227.40, "rural_south": 227.40},
    },
    {
        "category": "Walking and Cycling",
        "basis": "per worker (non-residential)",
        "rates": {"urban": 27.71, "rural_north": 27.71, "rural_south": 27.71},
    },
    {
        "category": "Traffic Management",
        "basis": "per Peak Vehicle Trip (PVT) (residential)",
        "rates": {"urban": 5470.65, "rural_north": 4588.43, "rural_south": 4588.43},
    },
    {
        "category": "Traffic Management",
        "basis": "per PVT (non-residential)",
        "rates": {"urban": 2726.84, "rural_north": 3288.54, "rural_south": 3288.54},
    },
    {
        "category": "Stormwater Management",
        "basis": "per person (residential)",
        "rates": {"urban": 266.22, "rural_north": 266.22, "rural_south": 266.22},
    },
    {
        "category": "Stormwater Management",
        "basis": "per worker (non-residential)",
        "rates": {"urban": 32.44, "rural_north": 32.44, "rural_south": 32.44},
    },
    {
        "category": "Heavy Haulage",
        "basis": "Tonnes per kilometre",
        "rates": {"urban": 0.090, "rural_north": 0.090, "rural_south": 0.090},
        "note": (
            "Section 4.7. Applies to agriculture, extractive industry, forestry, freight "
            "transport facilities, industry, mining, rural industry, transport depots, "
            "truck depots and waste or resource management facilities."
        ),
    },
]

# Which per-head components of Table E1 make up each kind of development. Used by
# the audit to re-derive Table E2, and by the tool to name what a contribution is
# actually buying. `traffic` names which of the two PVT rates applies.
DEMAND_COMPONENTS = {
    "residential": {
        "per_head": ["Community Facilities", "Public Domain", "Open Space and Recreation",
                     "Walking and Cycling", "Stormwater Management"],
        "basis": "per person (residential)",
        "traffic": "per Peak Vehicle Trip (PVT) (residential)",
    },
    "non_residential": {
        "per_head": ["Public Domain", "Walking and Cycling", "Stormwater Management"],
        "basis": "per worker (non-residential)",
        "traffic": "per PVT (non-residential)",
    },
    # Tourist accommodation takes Open Space per bed/site and the non-residential
    # traffic rate — established by deriving it, since the plan does not say so.
    "tourist": {
        "per_head": ["Open Space and Recreation"],
        "basis": "per person (residential)",
        "traffic": "per PVT (non-residential)",
    },
}

# Table E2, p7 — the operative rates, verbatim.
#
#   plan_name   the development type exactly as Table E2 names it
#   base        the unit the rate is charged per, as Table E2 states it
#   occupancy   persons per dwelling (residential) or workers per 100m2 (other)
#   pvts        peak vehicle trips generated per unit
#   demand      which DEMAND_COMPONENTS group derives it
#   rates       total contribution per unit, by catchment
DEVELOPMENT_TYPE_RATES = {
    "dwelling_house": {
        "plan_name": "Dwelling house / residential lot / exhibition home",
        "base": "Dwelling",
        "occupancy": 2.65,
        "pvts": 0.78,
        "demand": "residential",
        "rates": {"urban": 7052.67, "rural_north": 6333.57, "rural_south": 6333.57},
    },
    "secondary_dwelling": {
        "plan_name": "Secondary Dwelling / Rural worker's dwelling",
        "base": "Dwelling",
        "occupancy": 1.50,
        "pvts": 0.45,
        "demand": "residential",
        "rates": {"urban": 4040.87, "rural_north": 3626.01, "rural_south": 3626.01},
    },
    "residential_1_bedroom": {
        "plan_name": "Residential Accommodation with 1 bedroom / bedsit",
        "base": "Dwelling",
        "occupancy": 1.50,
        "pvts": 0.45,
        "demand": "residential",
        "rates": {"urban": 4040.87, "rural_north": 3626.01, "rural_south": 3626.01},
        "note": "Excludes dwelling houses, secondary dwellings and seniors housing.",
    },
    "residential_2_bedroom": {
        "plan_name": "Residential Accommodation with 2 bedrooms",
        "base": "Dwelling",
        "occupancy": 1.85,
        "pvts": 0.45,
        "demand": "residential",
        "rates": {"urban": 4383.48, "rural_north": 3968.61, "rural_south": 3968.61},
    },
    "residential_3_bedroom": {
        "plan_name": "Residential Accommodation with 3 or more bedrooms",
        "base": "Dwelling",
        "occupancy": 2.20,
        "pvts": 0.575,
        "demand": "residential",
        "rates": {"urban": 5440.68, "rural_north": 4910.58, "rural_south": 4910.58},
    },
    "seniors_housing": {
        "plan_name": "Seniors housing",
        "base": "Dwelling",
        "occupancy": 1.75,
        "pvts": 0.4,
        "demand": "residential",
        "rates": {"urban": 3999.75, "rural_north": 3630.98, "rural_south": 3630.98},
        "note": (
            "Excludes residential care facilities. Seniors housing by a social housing "
            "provider is exempt under the prevailing Ministerial Direction (section 1.6)."
        ),
    },
    "tourist_accommodation": {
        "plan_name": (
            "Tourist and visitor accommodation, camping grounds, caravan parks, "
            "eco-tourist facilities"
        ),
        "base": "Bed / Site",
        "occupancy": 0.6,
        "pvts": 0.4,
        "demand": "tourist",
        "rates": {"urban": 1352.49, "rural_north": 1374.61, "rural_south": 1374.61},
    },
    "retail_premises": {
        "plan_name": "Retail premises",
        "base": "100m2 GFA",
        "occupancy": 2.17,
        "pvts": 7,
        "demand": "non_residential",
        "rates": {"urban": 20101.55, "rural_north": 24210.38, "rural_south": 24210.38},
        "note": (
            "Retail premises covers shops and food and drink premises — a cafe, "
            "restaurant, takeaway or pub is charged at this rate, and it is by a wide "
            "margin the highest non-residential rate in the plan because retail is "
            "assessed at 7 peak vehicle trips per 100m2."
        ),
    },
    "business_or_office_premises": {
        "plan_name": "Business Premises and Office Premises",
        "base": "100m2 GFA",
        "occupancy": 2.17,
        "pvts": 1.6,
        "demand": "non_residential",
        "rates": {"urban": 4714.01, "rural_north": 5653.17, "rural_south": 5653.17},
    },
    "industry": {
        "plan_name": "Industry",
        "base": "100m2 GFA",
        "occupancy": 1.14,
        "pvts": 0.7,
        "demand": "non_residential",
        "rates": {"urban": 2075.57, "rural_north": 2486.45, "rural_south": 2486.45},
    },
}

# Cells of Table E2 that do not reproduce from Table E1. Named rather than
# tolerated: an audit that reports the same unexplained difference every run
# teaches its reader to stop reading it.
KNOWN_TABLE_DISCREPANCIES = [
    {
        "development_type": "tourist_accommodation",
        "catchments": ["rural_north", "rural_south"],
        "published": 1374.61,
        "derived": 1587.29,
        "difference": 212.68,
        "explanation": (
            "The published rural figure omits the Open Space and Recreation component "
            "($339.20 x 0.6 occupancy x 1.045 administration = $212.68) that every other "
            "rural row in Table E2 includes, and that the equivalent urban figure "
            "includes. Whether that is intentional is not recoverable from the document. "
            "The published figure is stored, since it is what Council levies."
        ),
    },
]

# How a proposed use reaches a Table E2 row. Keys are terms as they appear in
# LAND_USE_HIERARCHY (data/definitions.py), so a caller saying "cafe" resolves
# through food and drink premises to retail premises without this table having to
# enumerate every business.
HIERARCHY_TO_TYPE = {
    "retail premises": "retail_premises",
    "shop": "retail_premises",
    "food and drink premises": "retail_premises",
    "business premises": "business_or_office_premises",
    "office premises": "business_or_office_premises",
    "industry": "industry",
    "light industry": "industry",
    "general industry": "industry",
    "warehouse or distribution centre": "industry",
    "dwelling house": "dwelling_house",
    "secondary dwelling": "secondary_dwelling",
    "seniors housing": "seniors_housing",
    "tourist and visitor accommodation": "tourist_accommodation",
}

# Section 1.5 / Table E2 note E.
OTHER_DEVELOPMENT = (
    "Development not listed in Table E2 is assessed under sections 1.5 and 1.6 of the "
    "plan against the per person / per worker / per PVT rates in Table E1. That needs a "
    "worker count and a peak vehicle trip figure for the proposal — usually from a "
    "traffic report — so no rate can be quoted here. Ask Council for the calculation "
    "before you commit to a lease."
)

# Section 1.6, verbatim. Ministerial Directions first, then the plan's own list.
EXEMPTIONS = [
    "No contributions for development undertaken by a 'social housing provider' for the "
    "purposes of 'seniors housing' as defined in State Environmental Planning Policy "
    "(Housing for Seniors or People with a Disability) 2004",
    "A maximum of $20,000 per dwelling or per lot for development comprising one or more "
    "dwellings or in the case of subdivision, the creation of one or more residential lots",
    "Development for the purposes of public infrastructure provided by or on behalf of "
    "State Government or the Council",
    "Infrastructure provided by Rous Water or equivalent water, sewer or energy provider",
    "Development for any purpose which seeks only to re-build the same type of residential "
    "accommodation, or the same quantum of non-residential floorspace, as a consequence of "
    "an existing development being no longer able to operate due to flood impact",
    "Where an EPI or Council endorsed DCP requires storage areas in non-residential "
    "development to be located above the Flood Planning Level, the Gross Floor Area of "
    "that storage area is excluded from the calculation of GFA",
    "Temporary uses where the development will cease within 12 months of the date of "
    "granting of development consent",
    "Development that, in the opinion of Council, does not increase the demand for public "
    "infrastructure for which contributions are sought under this Plan",
]

# Section 2.7. This is the provision that matters most to a change of use, which
# is the commonest business DA — the contribution is charged on the *increase* in
# demand, so a shop becoming a cafe (both retail premises) may attract nothing at
# all, while an office becoming a cafe steps from 1.6 PVT to 7 PVT per 100m2.
#
# Note the plan uses "credit" (section 2.8) for something else entirely — a
# negotiated offset for works-in-kind or dedicated land. Use the plan's own word,
# "allowance", or the argument gets made under the wrong heading.
EXISTING_DEVELOPMENT_ALLOWANCE = {
    "section": "Section 2.7 — Allowances for existing development",
    "rule": (
        "Contributions are based on the estimated net increase in demand. The contribution "
        "that would be applicable to any existing lawful development on the site is "
        "discounted."
    ),
    "existing_lawful_development": (
        "Development that existed on the site as at 1 January 2024 and which has the "
        "benefit of a valid development consent or existing use rights."
    ),
    "what_you_must_do": (
        "The allowance is not automatic. Information demonstrating the lawful existence of "
        "the previous use as at 1 January 2024 must be provided with the development "
        "application — so lodge the evidence of the previous use with the DA rather than "
        "arguing it after the consent is conditioned."
    ),
    "limit": (
        "Council will only consider an allowance to the extent of the demand for the "
        "specific public infrastructure arising from the existing development."
    ),
}

INDEXATION = (
    f"Rates are stated at the plan's commencement ({PLAN_BASE_QUARTER} quarter) and are "
    "indexed to the date of payment — land acquisition by Sydney CPI, capital works by ABS "
    "Producer Price Index No. 30 Building Construction NSW (section 2.6). Council also "
    "amends the rates periodically without a new plan. The figures here are the plan's "
    "published rates, so treat them as a floor and ask Council for the current indexed "
    "rate."
)

# ---------------------------------------------------------------------------
# Section 64 water and wastewater developer charges
# ---------------------------------------------------------------------------

DSP_SOURCE = "documents/fees/development-servicing-plans-water-wastewater.pdf"
DSP_DOLLARS = "2016"

# Table 1, p3 — "Developer Charges (2016$)", per ET (equivalent tenement).
# None means the service is not applicable in that area, as the table states.
SECTION_64_CHARGES = {
    "Nimbin": {"water": 3000, "wastewater": 11100},
    "Dunoon": {"water": 3000, "wastewater": None},
    "North Lismore Plateau": {"water": 7400, "wastewater": 11100},
    "Tullera": {"water": 7400, "wastewater": None},
    "South Lismore": {"water": 1400, "wastewater": 6500},
    "East Lismore": {"water": 1400, "wastewater": 11100},
    "Clunes": {"water": 0, "wastewater": None},
    "North Woodburn": {"water": 0, "wastewater": 3000},
}

SECTION_64_NOTES = {
    "what_it_is": (
        "Section 64 of the Local Government Act 1993 lets Council levy developer charges "
        "for water supply and sewerage, set by its Development Servicing Plans. They are "
        "charged per ET (equivalent tenement) — a measure of demand, where one ET is "
        "roughly one house."
    ),
    "why_no_figure": (
        "Two things stop a number being produced here. The rates above are in 2016 dollars "
        "and are adjusted each 1 July by Sydney CPI, and the DSP carries no table "
        "converting a non-residential use into ETs — Council assesses that per proposal. "
        "So the charge is real and can be large, but only Council can quote it."
    ),
    "who_it_catches": (
        "A food premises is the classic case: a cafe or restaurant in a tenancy previously "
        "used as a shop or office can be assessed at several ETs of additional water and "
        "wastewater demand, because of the kitchen. Ask Council for the ET assessment "
        "before signing a lease, not after lodgement."
    ),
    "also": (
        "Rous County Council levies its own bulk water developer charge in its supply area, "
        "separately from Lismore City Council's."
    ),
    "timing": (
        "A Compliance Certificate (or Linen Plan for a subdivision) is not issued until the "
        "charge is paid. If payment is not made within three months of the notice, the "
        "charge is recalculated under whichever DSP is current at that time."
    ),
}
