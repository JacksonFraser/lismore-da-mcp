"""What a DA has to include, by development type.

PLAN.md item 1.1. This was previously a chain of `if "commercial" in dev_type`
substring tests inside the handler, which is why `change of use` — with spaces,
the way anyone actually writes it — was refused while `change_of_use` worked.
Every other tool got loose term resolution in the 3.1/3.2 work; this one was
missed, and it was missed on the single most common business DA type.

The lists below are the documents Council asks for. An incomplete lodgement is
not assessed at all — the clock never starts — so for a business paying rent on
a tenancy this is one of the cheapest places to save weeks.

Items marked "commonly required" are the ones a business is most often caught
by. They are not universal, and the entries say so rather than presenting them
as certainties — particularly the fit-out specifics, which vary with the
premises and are Council's call.

Where an entry cannot be settled from the documents in `documents/`, it says so
in the answer and points the applicant at Council's free Duty Planner. It does
not carry a marker asking a future maintainer to check with a planner: this
project has no line to Council, so such a marker is a permanent to-do that
reads to the applicant as an unfinished sentence. State the limit plainly
instead, and let the person who actually has standing to ask — the applicant —
go and ask.
"""

# Required for every DA regardless of type.
UNIVERSAL_DOCUMENTS = [
    "Development Application form (via NSW Planning Portal)",
    "Owner's consent (if you are not the owner — a landlord's written consent for a leased tenancy)",
    "Statement of Environmental Effects (SEE)",
    "Site plan (1:100 or 1:200 scale)",
    "Architectural plans (1:100 or 1:200 scale)",
    "Cost of Development Works estimate",
]

# Attached to every response — these depend on the site, not the development
# type, and lookup_site_constraints can answer most of them from an address.
CONDITIONAL_DOCUMENTS = [
    {"condition": "If flood-affected land", "document": "Flood Risk Assessment",
     "how_to_check": "Much of the Lismore LGA is flood affected — ask the Duty Planner. "
                     "lookup_site_constraints cannot rule flooding out."},
    # cl 5.10(5) says the consent authority *may* require a heritage management
    # document, of which a HIS is one of three forms — and (c) reaches land in
    # the *vicinity* of an item, not only the item itself. ROADMAP.md S4.
    {"condition": "If a heritage item, in a conservation area, or in the vicinity of one",
     "document": "Heritage management document, if Council requires one (LEP cl 5.10(5)) — "
                 "usually a Heritage Impact Statement",
     "how_to_check": "lookup_site_constraints reads the heritage layer by address. Ask Council "
                     "whether a document is required and in what form before commissioning "
                     "one; it is discretionary, not automatic."},
    {"condition": "If bushfire prone land", "document": "Bushfire assessment",
     "how_to_check": "lookup_site_constraints reads the bushfire layer by address."},
    {"condition": "If vegetation removal is required", "document": "Vegetation Management Plan"},
    {"condition": "If contamination is suspected, or the use is becoming more sensitive",
     "document": "Preliminary Site Investigation (contamination)",
     "how_to_check": "Moving to a more sensitive use — a workshop becoming a café or a child "
                     "care centre — can trigger this even with no construction."},
    {"condition": "If not connected to reticulated sewer",
     "document": "On-site Sewage Management Report"},
    {"condition": "If a development standard is exceeded (height, floor space, lot size)",
     "document": "Clause 4.6 Variation Request"},
]

DA_CHECKLISTS = {
    "dwelling": {
        "label": "Dwelling / residential development",
        "documents": [
            "BASIX Certificate",
            "Shadow diagrams (if 2+ storeys)",
            "Privacy assessment",
            "Landscape plan",
        ],
    },
    "commercial": {
        "label": "Commercial development",
        "documents": [
            "BCA compliance report",
            "Fire safety schedule",
            "Access report — compliance with the Disability (Access to Premises) Standards "
            "(commonly required)",
            "Waste management plan (construction and ongoing operational waste) — see DCP "
            "Chapter 15",
            "Car parking assessment against DCP Chapter 7 — get_parking_rates gives the rate "
            "and any shortfall",
            "Traffic impact assessment (if significant traffic generation)",
            "Acoustic report (if a noise-generating use, or near residential)",
            "Details of operating hours, staff numbers and deliveries",
            "Signage details, or a statement that signage is a separate application — see DCP "
            "Chapter 9",
        ],
        "also_see": "change_of_use",
        "note": "If you are taking over an existing building rather than building new, use "
                "change_of_use — it carries the items specific to occupying premises somebody "
                "else fitted out.",
    },
    "change_of_use": {
        "label": "Change of use / fit-out of existing premises",
        "documents": [
            "Description of the existing (or most recent) approved use, and the proposed use",
            "BCA compliance assessment for the new use — a building classified for one use "
            "often needs upgrading for another",
            "Fire safety upgrade report (commonly required when the classification changes)",
            "Access upgrade assessment — Disability (Access to Premises) Standards "
            "(commonly required)",
            "Car parking assessment — including any credit for parking attributable to the "
            "previous use (get_parking_rates)",
            "Operating hours, staff numbers, patron or customer numbers, deliveries",
            "Waste storage and collection arrangements — DCP Chapter 15",
            "Acoustic report (if the new use generates noise, especially near residential)",
        ],
        "commonly_missed": [
            "Food premises: mechanical ventilation and exhaust details, grease arrestor and "
            "trade waste — trade waste is a separate Council approval, not part of the DA",
            "Food premises must also be registered with Council under the Food Act — separate "
            "from development consent. See documents/business/",
            "Footpath or outdoor dining is a separate approval again — see the NSW Outdoor "
            "Dining Policy in documents/business/",
            "Contamination: changing to a more sensitive use can require a Preliminary Site "
            "Investigation even with no building work",
        ],
        "also_see": "commercial",
        "note": "Some changes of use between similar commercial uses are exempt or complying "
                "development under the Codes SEPP and may need no DA at all. Existing use "
                "rights may also apply where the current use is no longer permissible. "
                "Neither can be answered from the LEP land use table, so this tool does not "
                "try — both are free Duty Planner questions, and either could save you the "
                "whole application.",
    },
    "industrial": {
        "label": "Industrial development",
        "documents": [
            "BCA compliance report",
            "Fire safety schedule, and a hazardous materials assessment if applicable",
            "Waste management plan — DCP Chapter 15",
            "Car parking and heavy vehicle manoeuvring — DCP Chapter 7 requires loading bays "
            "and manoeuvring areas sized to the vehicle type",
            "Stormwater management plan — DCP Chapter 22",
            "Acoustic report (if near residential or a sensitive receiver)",
            "Details of processes, hours, and any emissions to air or water",
        ],
        "note": "The Airport, Wyrallah Road and North Lismore industrial estates each have "
                "their own DCP Part B chapter with additional controls.",
    },
    "subdivision": {
        "label": "Subdivision",
        "documents": [
            "Survey plan",
            "Subdivision layout plan",
            "Services layout plan",
            "Stormwater management plan",
            "Road layout and pavement design",
        ],
    },
    "signage": {
        "label": "Signage / advertising structures",
        "documents": [
            "Elevation drawings showing sign dimensions, materials and illumination",
            "A photomontage or streetscape photo showing the sign in context",
            "Assessment against DCP Chapter 9",
            "Heritage management document if Council requires one (LEP cl 5.10(5)) — on or "
            "near a heritage item or conservation area",
        ],
        "note": "Signage is frequently a separate application from the fit-out or change of "
                "use, and is a common refusal point in the CBD and conservation areas.",
    },
    "demolition": {
        "label": "Demolition",
        "documents": [
            "Demolition plan and staging",
            "Hazardous materials survey (asbestos)",
            "Waste management plan — DCP Chapter 15",
            "Heritage management document if Council requires one (LEP cl 5.10(5)) — on or "
            "near a heritage item or conservation area",
        ],
    },
}
