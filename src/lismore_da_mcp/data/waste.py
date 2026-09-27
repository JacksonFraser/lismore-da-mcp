"""Waste minimisation and management, Lismore DCP Chapter 15.

Transcribed 2026-09-27 from `documents/dcp/chapter-15-waste-minimisation.pdf`
(34 pages). ROADMAP.md D2: until now the checklists named "DCP Chapter 15" seven
times as prose, and nothing here could say what the chapter asks for.

**What a business most needs to know is in §1.3, and it is the opposite of what
the old checklist said.** The chapter applies to demolition, to building work,
and to **"Change of use"** — so a café taking over a shop is inside it, and
§2.1 says the Statement of Environmental Effects "is to include a Site Waste
Minimisation and Management Plan (SWMMP) or other documentation that addresses
the requirements of this DCP chapter". The change-of-use checklist asked only
for "waste storage and collection arrangements".

**What it does not cover matters as much.** §1.3 excludes liquid waste —
"oils, chemicals, grease, interceptor waste and other liquid trade wastes" —
which needs a separate Liquid Trade Waste approval under s68 of the Local
Government Act. A café's grease arrestor is not a Chapter 15 matter.

**How to read it.** Sections 3.2-4.5 each have Objectives, Performance Criteria
and Acceptable Solutions, but in all but two of them the Performance Criteria
read "There are no Performance Criteria" and the Acceptable Solutions say
"must". §1.4.4 allows a written variation request — which has to show the
proposal "complies with relevant Performance Criteria", a test that has nothing
to bite on where there are none. That tension is the chapter's, recorded not
resolved.

**Appendix C is the only place in this repository that gives a volume.** Its
generation rates are a default — §2.3: "In the absence of project specific
calculations" — and the restaurant or café rate is per 1.5m² of floor area, not
per 100m², which makes it large. It is quoted as printed. `scripts/audit_waste.py`
rebuilds the table from the page geometry and compares it cell by cell.

**The chapter's own cross-references are sometimes wrong, and are quoted as
written:** Appendix G cites "the rate described in Appendix B" (the rates are in
Appendix C), and Appendix A's construction page refers to "Section 3.2" (which
is demolition; construction is 3.3). It also cites bodies and instruments since
renamed or replaced — section 79C (now 4.15 of the EP&A Act), WorkCover NSW, the
POEO (Waste) Regulation 2005, SEPP (Major Development) 2005.
"""

__all__ = [
    "CHAPTER", "SOURCE_PDF", "SECTION_TITLES", "HOW_TO_READ_THIS_CHAPTER", "SCOPE",
    "SUBMISSION", "SECTIONS", "GENERATION_RATES", "CONSTRUCTION_RULE_OF_THUMB",
    "BIN_SIZES", "TRUCK_DIMENSIONS", "DEMOLITION_MATERIALS", "APPENDICES",
    "DESCRIPTIVE_SECTIONS", "COUNTED_SECTIONS", "FIGURES", "NOT_SET_BY_THIS_CHAPTER",
]

CHAPTER = "DCP Chapter 15"
SOURCE_PDF = "documents/dcp/chapter-15-waste-minimisation.pdf"

# Every numbered heading, as the body of the chapter prints it. The audit uses
# these to slice the chapter into sections for counting.
SECTION_TITLES = {
    "1.": "INTRODUCTION",
    "1.1": "Purpose of this Section",
    "1.2": "Objectives of this Section",
    "1.3": "Development Covered by this Section of the DCP",
    "1.4": "Development Approval Process",
    "1.4.1": "Development that Requires Consent",
    "1.4.2": "Exempt and Complying Development",
    "1.4.3": "State Significant Development/Major Projects",
    "1.4.4": "Departures from the Controls of this DCP",
    "1.4.5": "Other NSW Government Statutes",
    "1.4.6": "Abbreviations",
    "1.4.7": "Summary Guide to using this DCP",
    "2.": "SUBMISSION REQUIREMENTS FOR DEVELOPMENT APPLICATIONS",
    "2.1": "Documentation required for all Development Applications",
    "2.2": "Site Waste Minimisation and Management Plans (SWMMP)",
    "2.3": "Waste/ Recycling Generation Rates",
    "3.": "GENERAL DEVELOPMENT CRITERIA",
    "3.1": "Exempt and Complying Development",
    "3.2": "Demolition of Buildings or Structures",
    "3.3": "Construction of Buildings and Structures",
    "3.4": "Bin Sizes and Collection Measures",
    "4.": "SPECIFIC DEVELOPMENT CRITERIA",
    "4.1": "Dwelling Houses, Semi-Detached Dwellings and Dual Occupancies",
    "4.2": "Multi Dwelling Housing and Residential Flat Buildings",
    "4.3": "Commercial and Retail Development",
    "4.4": "Mixed Use Development",
    "4.5": "Industrial Development",
}

HOW_TO_READ_THIS_CHAPTER = {
    "merits": {
        "section": "1.4.1",
        "page": 5,
        "verbatim": (
            "Compliance with the minimum provisions herein does not, however, necessarily mean "
            "that an application will be approved, as each application will be considered on its "
            "merits."
        ),
    },
    "departures": {
        "section": "1.4.4",
        "page": 5,
        "verbatim": (
            "It is accepted that optimum waste minimisation and management will necessitate site "
            "specific and sometimes unique solutions. Council may approve variations to the "
            "Acceptable Solutions herein in accordance with the principles of merit-based "
            "assessment. Any request for variation to the provisions must be in writing and must "
            "comprise part of the application. The request must clearly demonstrate that:"
        ),
        "numbered": {
            "must_demonstrate": [
                "The objectives of this DCP are met,",
                "The proposal complies with relevant Performance Criteria,",
                "Compliance with the relevant provisions is unreasonable or unnecessary in the "
                "circumstances of the case, and",
                "The proposed variation results in an equivalent or better outcome in terms of "
                "ESD.",
            ],
        },
    },
    "what_it_means": (
        "Most sections say 'There are no Performance Criteria' and state their Acceptable "
        "Solutions with 'must', so in practice the Acceptable Solutions are the requirement. A "
        "departure is possible, but only by a written variation request lodged with the "
        "application that shows the four things §1.4.4 lists — one of which, compliance with "
        "'relevant Performance Criteria', has nothing to measure against where the section has "
        "none. Section 4.1 (dwellings) is the exception: completing Council's Appendix B "
        "checklist is 'deemed to satisfy' its Performance Criteria."
    ),
}

SCOPE = {
    "section": "1.3",
    "page": 4,
    "applies_verbatim": (
        "This Section of the DCP applies to the following types of development, where that "
        "development may be carried out only with development consent:"
    ),
    "numbered": {
        "covered": [
            "Demolition.",
            "Development involving construction, erection of a building or carrying out works.",
            "Change of use.",
        ],
    },
    "liquid_waste_excluded_verbatim": (
        "Storage and disposal of liquid waste such as oils, chemicals, grease, interceptor waste "
        "and other liquid trade wastes are not covered by this DCP. Developments that generate "
        "these types of waste will require a separate Liquid Trade Waste approval pursuant to "
        "Section 68 of the Local Government Act, 1993."
    ),
    "exempt_and_complying": {
        "section": "1.4.2",
        "page": 5,
        "verbatim": (
            "Preparation of a Site Waste Minimisation and Management Plan (SWMMP) is not required "
            "for exempt and complying development unless specified in an Environmental Planning "
            "Instrument."
        ),
    },
    "exempt_and_complying_demolition": {
        "section": "3.1",
        "page": 8,
        "verbatim": (
            "A SWMMP is not required in association with Exempt and Complying Development carried "
            "out in accordance with the Codes SEPP or Council’s Exempt and Complying Development "
            "provisions."
        ),
        "demolition_verbatim": (
            "Most dwellings and ancillary structures can be demolished as complying development "
            "under the Codes SEPP with the exception of dwellings that are listed as heritage "
            "items or are located within a heritage conservation area under LEP 2012."
        ),
    },
    "cross_reference": "Trade waste: get_other_approvals ('liquid_trade_waste').",
}

SUBMISSION = {
    "documentation": {
        "section": "2.1",
        "page": 7,
        "verbatim": (
            "The Statement of Environmental Effects submitted with development applications is to "
            "include a Site Waste Minimisation and Management Plan (SWMMP) or other documentation "
            "that addresses the requirements of this DCP chapter."
        ),
        "plans_verbatim": (
            "In addition to submission of a SWMMP, the waste management facilities proposed as "
            "part of the development must be clearly illustrated on the plans and drawings "
            "accompanying the development application."
        ),
    },
    "the_plan": {
        "section": "2.2",
        "page": 7,
        "level_of_detail_verbatim": (
            "The level of detail required for the Site Waste Minimisation and Management Plan "
            "(SWMMP) will vary with the size and complexity of the proposed development."
        ),
        "numbered": {
            "stages": [
                "Demolition;",
                "Construction; and",
                "Ongoing operation and use of the development.",
            ],
            "must_nominate": [
                "The volume and type of waste and recyclables to be generated.",
                "Proposed measures for storage and treatment of waste and recyclables onsite.",
                "Proposed measures for disposal of residual waste and recyclables.",
                "Proposed operational procedures for ongoing waste management once the "
                "development is complete.",
                "Proposed means of access and manoeuvring for recycling/ waste management bins "
                "and vehicles.",
            ],
        },
        "stages_verbatim": "The SWMMP must outline measures to minimise and manage waste "
                           "generated during:",
        "provider_verbatim": (
            "The SWMMP must specify the proposed method of recycling or disposal and the waste "
            "management service provider."
        ),
        "template_verbatim": "Appendix A provides a template for the compilation of a SWMMP.",
    },
    "generation_rates": {
        "section": "2.3",
        "page": 7,
        "verbatim": (
            "In the absence of project specific calculations, the rates specified in Appendix C - "
            "Waste/ Recycling Generation Rates and Council’s current rate of provision of services "
            "to residential properties can be used to inform the compilation of a SWMMP."
        ),
    },
}

SECTIONS = {
    "demolition": {
        "section": "3.2",
        "heading": "Demolition of Buildings or Structures",
        "page": 8,
        "applies_to": "Any development involving demolition.",
        "performance_criteria": "There are no Performance Criteria.",
        "acceptable_solution_verbatim": (
            "A Site Waste Minimisation and Management Plan (SWMMP) must be submitted with "
            "development applications seeking consent for demolition. The SWMMP must demonstrate "
            "that the proposed development will:"
        ),
        "numbered": {
            "the_plan_must_demonstrate": [
                "Pursue adaptive reuse opportunities of buildings/ structures.",
                "Identify all waste likely to result from the demolition, and opportunities for "
                "reuse of materials. Refer to Table 1.",
                "Facilitate reuse/ recycling by using the process of 'deconstruction', where "
                "various materials are carefully dismantled and sorted.",
                "Reuse or recycle salvaged materials onsite where possible.",
                "Allocate an area for the storage of materials for use, recycling and disposal "
                "(giving consideration to slope, drainage, location of waterways, stormwater "
                "outlets, vegetation, and access and handling requirements).",
                "Provide separate collection bins or areas for the storage of residual waste.",
                "Clearly ’signpost’ the purpose and content of the bins and storage areas.",
                "Implement measures to prevent damage by the elements, odour and health risks, "
                "and windborne litter.",
                "Minimise site disturbance, limiting unnecessary excavation.",
            ],
            "when_implementing": [
                "Footpaths, public reserves, street gutters are not used as places to store "
                "demolition waste or materials of any kind without Council approval.",
                "Any material moved offsite is transported in accordance with the requirements of "
                "the Protection of the Environment Operations Act, 1997.",
                "Waste is only transported to an approved waste or resource management facility.",
                "Generation, storage, treatment and disposal of hazardous waste and special waste "
                "(including asbestos), is conducted in accordance with relevant waste legislation "
                "administered by the EPA and relevant Workplace Health and Safety legislation "
                "administered by WorkCover NSW.",
            ],
        },
        "records_verbatim": (
            "Evidence such as weighbridge dockets and invoices for waste disposal or recycling "
            "services are retained."
        ),
    },
    "construction": {
        "section": "3.3",
        "heading": "Construction of Buildings and Structures",
        "page": 10,
        "applies_to": "Any development involving building work — which includes a fitout.",
        "performance_criteria": "There are no Performance Criteria",
        "acceptable_solution_verbatim": (
            "A Site Waste Minimisation and Management Plan (SWMMP) must be submitted with "
            "development applications seeking consent for construction of buildings or "
            "structures."
        ),
        "numbered": {
            "the_plan_must": [
                "Estimate volumes of materials to be used and incorporate these volumes into a "
                "Purchasing Policy so that the correct quantities are purchased. For small-scale "
                "building projects see the rates in Appendix C - Waste/ Recycling Generation "
                "Rates for a guide.",
                "Identify potential reuse/ recycling opportunities of excess construction "
                "materials.",
                "Incorporate the use of prefabricated components and recycled materials.",
                "Specify arrangements for the delivery of materials so that materials are "
                "delivered ’as needed’ to prevent the degradation of materials through weathering "
                "and moisture damage.",
                "Consider organising to return excess materials to the supplier or manufacturer.",
                "Allocate an area for the storage of materials for use, recycling and disposal "
                "(considering slope, drainage, location of waterways, stormwater outlets and "
                "vegetation).",
                "Nominate proposed arrangements to ensure appropriate transport, processing and "
                "disposal of waste and recycling; and to ensure that all contractors are aware of "
                "the legal requirements for disposing of waste.",
                "Promote separate collection bins or areas for the storage of residual waste.",
                "Clearly ’signpost’ the purpose and content of the bins and storage areas.",
                "Specify intended implementation measures to prevent damage by the elements, "
                "odour and health risks, and windborne litter.",
                "Minimise site disturbance and limit unnecessary excavation.",
                "Ensure that all waste is transported to a place that can lawfully be used as a "
                "waste facility.",
                "Require retention of all records demonstrating lawful disposal of waste and keep "
                "them readily accessible for inspection by regulatory authorities such as "
                "Council, EPA or WorkCover NSW.",
            ],
        },
    },
    "bins_and_collection": {
        "section": "3.4",
        "heading": "Bin Sizes and Collection Measures",
        "page": 10,
        "applies_to": "All development.",
        "two_levels_verbatim": (
            "For smaller scale developments such as individual dwelling houses, small scale multi "
            "dwelling housing and low key business premises or industries, Council provides a "
            "kerbside pickup service utilising 140L, 240L or 360L ‘wheelie bins’."
        ),
        "bulk_verbatim": (
            "For larger developments a bulk bin service is required, for which the landowner "
            "and/or occupier must enter into a contractual arrangement with Council or a service "
            "provider."
        ),
        "specify_verbatim": (
            "The SWMMP provided with the development application must specify the proposed bin "
            "sizes and collection arrangements for the development."
        ),
        "kerbside_verbatim": (
            "Where collection is proposed by Council’s kerbside pickup service, the SWMMP and "
            "development application must specify and illustrate in a site plan drawn to a "
            "readily legible scale:"
        ),
        "kerbside_75_percent_verbatim": (
            "If the kerbside/ road frontage space intended to be occupied by ‘wheelie bins’ "
            "exceeds 75% of the site’s available kerbside/ road frontage space (after deducting "
            "existing or proposed access driveways), the SWMMP must include justification of "
            "reasons why a bulk bin service should not be provided."
        ),
        "kerbside_unlikely_verbatim": (
            "In those circumstances Council is unlikely to approve a kerbside pickup service for "
            "the development unless it considers that those impacts are likely to be not "
            "significant."
        ),
        "other_collection_verbatim": (
            "Where collection is proposed other than by Council’s kerbside pickup service, the "
            "SWMMP and development application must specify and illustrate in a site plan drawn "
            "to a readily legible scale:"
        ),
        "numbered": {
            "kerbside_site_plan": [
                "The site’s boundary dimensions and available kerbside/ road frontage space, after "
                "deducting existing or proposed access driveways.",
                "The kerbside/ road frontage space intended to be occupied by ‘wheelie bins’ on "
                "pickup days, based on the dimensions of the bins proposed. Bin dimensions are "
                "available on request from Council.",
            ],
            "other_collection_site_plan": [
                "The proposed bin storage location, dimensions, pickup vehicle access and "
                "manoeuvring arrangements.",
                "The proposed means of ensuring that the pickup vehicle can enter and exit the "
                "site in a forward direction and can manoeuvre safely onsite, in accordance with "
                "Council’s DCP requirements for Access and Manoeuvrability for various vehicle "
                "types.",
            ],
        },
        "acceptable_solutions": "Not applicable.",
    },
    "dwellings": {
        "section": "4.1",
        "heading": "Dwelling Houses, Semi-Detached Dwellings and Dual Occupancies",
        "page": 12,
        "applies_to": "Dwelling houses, semi-detached dwellings and dual occupancies.",
        "performance_criteria": (
            "Appropriate waste minimisation measures are to be incorporated into the construction "
            "and post construction phases of the development. Documentation is to be provided "
            "regarding waste and recycling during the construction of, and occupation of the "
            "dwelling."
        ),
        "deemed_to_satisfy_verbatim": (
            "The completion of Council’s Waste Minimisation template checklist for new Dwelling "
            "Houses, Semi-Detached Dwellings and Dual Occupancies is deemed to satisfy these "
            "performance criteria."
        ),
        "acceptable_solution_verbatim": (
            "A Site Waste Minimisation and Management Plan (SWMMP) submitted with a development "
            "application is to include:"
        ),
        "numbered": {
            "the_plan_is_to_include": [
                "The location of an appropriate indoor waste/ recycling storage space,",
                "The location of an onsite waste/ recycling storage area for each dwelling, that "
                "is of sufficient size to accommodate Council’s waste and recycling bins.",
                "Waste container storage in a suitable location so as to avoid vandalism, "
                "nuisance and adverse visual impacts.",
                "Designated area for composting is not to adversely impact on adjoining "
                "properties.",
                "The waste/ recycling storage area should be located in the rear yard or "
                "appropriately screened area and minimise the distance of travel to the "
                "collection point.",
                "Sufficient space within the kitchen (or an alternate location) for the interim "
                "storage of waste and recyclables.",
            ],
        },
    },
    "multi_dwelling": {
        "section": "4.2",
        "heading": "Multi Dwelling Housing and Residential Flat Buildings",
        "page": 13,
        "applies_to": "Multi dwelling housing and residential flat buildings.",
        "performance_criteria": "There are no Performance Criteria.",
        "numbered": {
            "plans_must_show": [
                "The location of an indoor waste/ recycling appropriate storage space for each "
                "dwelling.",
                "The location of individual waste/ recycling storage areas (such as for "
                "townhouses and villas) or a communal waste/ recycling storage room(s) able to "
                "accommodate Council’s waste and recycling bins.",
                "The location of any interim storage facilities for recyclable materials.",
                "The location of any waste compaction equipment.",
                "An identified location for individual compost containers or communal compost "
                "container.",
                "An identified collection point for the collection and emptying of Council’s "
                "waste and recycling bins.",
                "The path of travel for moving bins from the storage area to the identified "
                "collection point (if collection is to occur away from the storage area).",
                "The onsite path of travel for collection vehicles (if collection is to occur "
                "onsite), taking into account accessibility, width, height and grade.",
            ],
            "outcomes": [
                "Systems must be designed to maximise source separation and recovery of "
                "recyclables.",
                "Waste management systems must be designed and operated to prevent the potential "
                "risk of injury or illness associated with the collection, storage and disposal "
                "of wastes.",
            ],
            "minimum_facilities": [
                "Each dwelling unit must be provided with an indoor waste/ recycling cupboard (or "
                "other appropriate storage space) for the interim storage of a minimum one day’s "
                "garbage and recycling generation.",
                "Residential flat buildings must include communal waste/ recycling storage "
                "facilities in the form of a waste/ recycling storage room (or rooms) designed in "
                "accordance with Appendix E - Waste Recycling/ Storage Rooms in Multi Dwelling "
                "Housing and the Better Practice Guide for Waste Management in Multi-Unit "
                "Dwellings.",
                "Multi Dwelling housing in the form of townhouses and villas must include either "
                "individual waste/ recycling storage areas for each dwelling or a communal "
                "facility in the form of a waste/ recycling storage room (or rooms) designed in "
                "accordance with Appendix E - Waste Recycling/ Storage Rooms in Multi Dwelling "
                "Housing and the Better Practice Guide for Waste Management in Multi-Unit "
                "Dwellings.",
                "The waste/ recycling storage area(s) or room(s) must be of a size that can "
                "comfortably accommodate separate garbage, recycling and garden waste containers "
                "at the rate of Council provision.",
                "For residential flat buildings that include 10 or more dwellings, a dedicated "
                "room or caged area must be provided for the temporary storage of discarded bulky "
                "items which are awaiting removal. The storage area must be readily accessible to "
                "all residents and must be located close to the main waste storage room or area.",
            ],
            "location_and_design": [
                "In townhouse and villa developments with individual waste/ recycling storage "
                "areas, such areas must be located and designed in a manner which reduces adverse "
                "impacts upon neighbouring properties and upon the appearance of the premises.",
                "There must be an unobstructed and Continuous Accessible Path of Travel (as per "
                "Australian Standard 1428 Design for Access and Mobility - 2001) from the waste/ "
                "recycling storage area(s) or room(s) to: a. the entry to any Adaptable Housing "
                "(as per Australian Standard 4299 - Adaptable Housing, 1995) b. the principal "
                "entrance to each residential flat building c. the point at which bins are "
                "collected/ emptied.",
                "In instances where a proposal does not comply with these requirements, Council "
                "will consider alternative proposals that seek to achieve a reasonable level of "
                "access to waste/ recycling storage area(s) or room(s).",
                "Communal waste storage areas must have adequate space to accommodate and "
                "manoeuvre Council’s required number of waste and recycling containers.",
                "Each service room and storage area must be located for convenient access by "
                "users and must be well ventilated and well lit.",
                "Where site characteristics, number of bins and length of street frontage allow, "
                "bins may be collected from a kerbside location.",
                "Where bins cannot be collected from a kerbside location or from a temporary "
                "holding area located immediately inside the property boundary, the development "
                "must be designed to allow for onsite access by garbage collection vehicles",
            ],
            "onsite_collection": [
                "If Council waste collectors and/or waste collection vehicles are required to "
                "enter a site for the purpose of emptying bins, then site specific arrangements "
                "must be in place.",
                "If bins need to be moved from normal storage areas to a different location for "
                "collection purposes, it is the responsibility of agents of the owners’ "
                "corporation to move the bins to the collection point no earlier than the evening "
                "before collection day and to then return the bins to their storage areas no "
                "later than the evening of collection day.",
                "Residents must have access to a cold water supply for the cleaning of bins and "
                "the waste storage areas.",
                "The design and location of waste storage areas/ facilities must be such that "
                "they complement the design of both the development and the surrounding "
                "streetscape.",
                "The SWMMP must include measures to ensure that agents of the owners’ corporation "
                "will take responsibility for the management of waste and recyclable materials "
                "generated upon the site.",
            ],
        },
        "indemnity_verbatim": (
            "As a minimum requirement for collection vehicle access, Council will require "
            "indemnity against claims for loss or damage to the pavement or other driving "
            "surface."
        ),
    },
    "commercial_and_retail": {
        "section": "4.3",
        "heading": "Commercial and Retail Development",
        "page": 15,
        "applies_to": "Commercial and retail development — shops, offices, cafés, restaurants, "
                      "takeaways, salons, pubs.",
        "objective_verbatim": (
            "To ensure that new developments and changes to existing developments are designed to "
            "maximise resource recovery (through waste avoidance, source separation and "
            "recycling); and to ensure that appropriate well-designed storage and collection "
            "facilities are accessible to occupants and service providers."
        ),
        "performance_criteria": "There are no Performance Criteria.",
        "acceptable_solution_verbatim": (
            "A Site Waste Minimisation and Management Plan (SWMMP) must be submitted with "
            "development applications. Plans submitted with the development application and "
            "SWMMP must show:"
        ),
        "numbered": {
            "plans_must_show": [
                "The location of the designated waste and recycling storage room(s) or areas, "
                "sized to meet the waste and recycling needs of all tenants.",
                "The location of temporary waste and recycling storage areas within each tenancy.",
                "These are to be of sufficient size to store a minimum of one day’s worth of "
                "waste.",
                "An identified collection point for the collection and emptying of waste, "
                "recycling and garden waste bins.",
                "The path of travel for moving bins from the storage area to the identified "
                "collection point (if collection is to occur away from the storage area).",
                "The onsite path of travel for collection vehicles (if collection is to occur "
                "onsite).",
            ],
            "outcomes": [
                "There must be convenient access from each tenancy to the waste/ recycling "
                "storage room(s) or area(s). There must be step-free access between the point at "
                "which bins are collected/ emptied and the waste/ recycling storage room(s) or "
                "area(s).",
                "Every development must include a designated waste/ recycling storage area or "
                "room(s) (designed in accordance with Appendix G - Commercial/ Industrial Waste "
                "and Recycling Storage Areas).",
                "Depending upon the size and type of the development, it may be necessary to "
                "include a separate waste/ recycling storage room/ area for each tenancy.",
                "All commercial tenants must keep written evidence onsite of a valid contract "
                "with a licensed waste contractor for the regular collection and disposal of the "
                "waste and recyclables that are generated onsite.",
                "Between collection periods, all waste/ recyclable materials generated onsite "
                "must be kept in enclosed bins with securely fitting lids so the contents are not "
                "able to leak or overflow. Bins must be stored in the designated waste/ recycling "
                "storage room(s) or area(s).",
                "Arrangements must be in all parts of the development for the separation of "
                "recyclable materials from general waste. Arrangements must be in all parts of "
                "the development for the movement of recyclable materials and general waste to "
                "the main waste/ recycling storage room/ area. For multiple storey buildings, "
                "this might involve the use of a goods lift.",
                "The waste/ recycling storage room/ area must be able to accommodate bins that "
                "are of sufficient volume to contain the quantity of waste generated (at the rate "
                "described in Appendix C - Waste/ Recycling Generation Rates) between "
                "collections.",
                "The waste/ recycling storage room/ area must provide separate containers for the "
                "separation of recyclable materials from general waste. Standard and consistent "
                "signage on how to use the waste management facilities should be clearly "
                "displayed.",
                "The type and volume of containers used to hold waste and recyclable materials "
                "must be compatible with the collection practices of the nominated waste "
                "contractor.",
                "Waste management facilities must be suitably enclosed, covered and maintained so "
                "as to prevent polluted wastewater runoff from entering the stormwater system.",
                "Where possible, waste/ recycling containers should be collected from a rear lane "
                "access point. The servicing location and methodology shall minimise adverse "
                "impacts upon residential amenity, pedestrian movements and vehicle movements.",
                "The size and layout of the waste/ recycling storage room/ area must be capable "
                "of accommodating reasonable future changes in use of the development.",
                "A waste/ recycling cupboard must be provided for each and every kitchen area in "
                "a development, including kitchen areas in hotel rooms, motel rooms and staff "
                "food preparation areas. Each waste/ recycling cupboard must be of sufficient "
                "size to hold a minimum of a single day’s waste and to hold separate containers "
                "for general waste and recyclable materials.",
                "Premises which generate at least 240 litres per week of meat, seafood, poultry "
                "or food waste must have that waste collected in mobile garbage bins (wheelie "
                "bins) at least twice weekly or must store that waste in a dedicated and "
                "refrigerated waste storage area until collection.",
                "Arrangements must be in place regarding the regular maintenance and cleaning of "
                "waste management facilities. Tenants and cleaners must be aware of their "
                "obligations in regards to these matters.",
            ],
        },
    },
    "mixed_use": {
        "section": "4.4",
        "heading": "Mixed Use Development",
        "page": 16,
        "applies_to": "Mixed use development, including shop top housing.",
        "performance_criteria": "There are no Performance Criteria.",
        "numbered": {
            "outcomes": [
                "The provisions of Clause 4.2 – Multi Dwelling Housing and Residential Flat "
                "Buildings apply to the residential component of mixed use development.",
                "The provisions of Clause 4.3 – Commercial and Retail Development apply to the "
                "non-residential component of mixed use development.",
                "Mixed Use development must incorporate separate and self-contained waste "
                "management systems for the residential component and the non-residential "
                "component. In particular, the development must incorporate separate waste/ "
                "recycling storage rooms/ areas for the residential and non-residential "
                "components. Commercial tenants must be prevented (via signage and other means), "
                "from using the residential waste/ recycling bins and vice versa.",
                "The residential waste management system and the non-residential waste "
                "management system must be designed so that they can efficiently operate without "
                "conflict.",
            ],
        },
    },
    "industrial": {
        "section": "4.5",
        "heading": "Industrial Development",
        "page": 17,
        "applies_to": "Industrial and other similar development types.",
        "performance_criteria": "There are no Performance Criteria.",
        "numbered": {
            "plans_must_show": [
                "The location of designated waste and recycling storage room(s) or areas sized to "
                "meet the waste and recycling needs of all tenants. Waste should be separated "
                "into at least three (3) streams, paper/ cardboard and recyclables, general "
                "waste, and industrial process type wastes.",
                "The onsite path of travel for collection vehicles.",
            ],
            "outcomes": [
                "The SWMMP must provide evidence of compliance with any specific industrial waste "
                "laws/ protocols.",
                "There must be convenient access from each tenancy and/or larger waste producing "
                "area of the development to the waste/ recycling storage room(s) or area(s).",
                "Every development must include a designated general waste/ recycling storage "
                "area or room(s) (designed in accordance with Appendix G - Commercial/ Industrial "
                "Waste and Recycling Storage Areas), as well as designated storage areas for "
                "industrial waste streams (designed in accordance with specific waste laws/ "
                "protocols).",
                "Depending upon the size and type of the development, it might need to include "
                "separate waste/ recycling storage room/ area for each tenancy and/or larger "
                "waste producing areas.",
                "All tenants must keep written evidence onsite of a valid contract with a "
                "licensed waste contractor for the regular collection and disposal of all the "
                "waste streams and recyclables which are generated onsite.",
                "Between collection periods, all waste/ recyclable materials generated onsite "
                "must be kept in enclosed bins with securely fitted lids so the contents are not "
                "able to leak or overflow.",
                "Arrangements must be in place in all parts of the development for the "
                "separation of recyclable materials from general waste.",
                "The waste/ recycling storage room/ areas must be able to accommodate bins that "
                "are of sufficient volume to contain the quantity of waste generated between "
                "collections.",
                "The type and volume of containers used to hold waste and recyclable materials "
                "must be compatible with the collection practices of the nominated waste "
                "contractor.",
                "Waste management storage rooms/ areas must be suitably enclosed, covered and "
                "maintained so as to prevent polluted wastewater runoff from entering the "
                "stormwater system.",
                "A waste/ recycling cupboard must be provided for each and every kitchen area in "
                "the development.",
                "Arrangements must be in place regarding the regular maintenance and cleaning of "
                "waste management facilities.",
                "Production, storage and disposal of hazardous wastes (such as contaminated or "
                "toxic material or products) require particular attention. The appropriate laws "
                "and protocols must be observed.",
            ],
        },
    },
}

# Appendix C, "Ongoing Operation". Cells verbatim, including the chapter's own
# spacing ("floor area/ day"). A row with several cells has several bases — the
# pub row is charged by bed space, bar area and dining area.
FOOD_SHOPS = "Food and drink premises/ food shops:"
GENERATION_RATES = {
    "backpackers_accommodation": {
        "premises": "Backpackers’ accommodation",
        "waste": ["40L/occupant space/week"], "recyclables": ["20L/occupant space/week"],
    },
    "boarding_house_tourist_visitor_accommodation": {
        "premises": "Boarding house, tourist and visitor accommodation",
        "waste": ["60L/occupant space/week"], "recyclables": ["20L/occupant space/week"],
    },
    "butcher": {
        "premises": "Butcher", "group": FOOD_SHOPS,
        "waste": ["80L/100m² floor area/day"], "recyclables": ["Variable"],
    },
    "delicatessen": {
        "premises": "Delicatessen", "group": FOOD_SHOPS,
        "waste": ["80L/100m² floor area/day"], "recyclables": ["Variable"],
    },
    "fish_shop": {
        "premises": "Fish shop", "group": FOOD_SHOPS,
        "waste": ["80L/100m² floor area/day"], "recyclables": ["Variable"],
    },
    "green_grocer": {
        "premises": "Green grocer", "group": FOOD_SHOPS,
        "waste": ["240L/100m² floor area/day"], "recyclables": ["120L/100m² floor area/day"],
    },
    "restaurant_or_cafe": {
        "premises": "Restaurant or cafe", "group": FOOD_SHOPS,
        "waste": ["10L/1.5m² floor area/day"], "recyclables": ["2L/1.5m² floor area/ day"],
    },
    "supermarket": {
        "premises": "Supermarket", "group": FOOD_SHOPS,
        "waste": ["240L/100m² floor area/day"], "recyclables": ["240L/100m² floor area/day"],
    },
    "takeaway_food_and_drink_premises": {
        "premises": "Takeaway food and drink premises", "group": FOOD_SHOPS,
        "waste": ["80L/100m² floor area/day"], "recyclables": ["Variable"],
    },
    "hairdresser_beauty_salon": {
        "premises": "Hairdresser/ beauty salon",
        "waste": ["60L/100m² floor area/day"], "recyclables": ["Variable"],
    },
    "pub_club_hotel_motel": {
        "premises": "Pub, registered club, hotel or motel accommodation",
        "waste": ["5L/bed space/day", "50L/100m² bar area/day", "10L/1.5m² dining area/day"],
        "recyclables": ["1L/bed space/day", "50L/100m² bar area/day",
                        "50L/1.5m² dining area/day"],
    },
    "office_premises": {
        "premises": "Office premises",
        "waste": ["10L/100m² floor area/day"], "recyclables": ["10L/100m² floor area/day"],
    },
    "shop_under_100m2": {
        "premises": "Shop less than 100m² floor area",
        "waste": ["50L/100m² floor area/day"], "recyclables": ["25L/100m² floor area/day"],
    },
    "shop_over_100m2": {
        "premises": "Shop greater than 100m² floor area",
        "waste": ["50L/100m² floor area/day"], "recyclables": ["50L/100m² floor area/day"],
    },
    "showroom": {
        "premises": "Showroom",
        "waste": ["40L/100m² floor area/day"], "recyclables": ["10L/100m² floor area/day"],
    },
    "multi_dwelling_residential_flat": {
        "premises": "Multi dwelling housing, residential flat buildings",
        "waste": ["80L/unit/week"], "recyclables": ["40L/unit/week"],
    },
}

CONSTRUCTION_RULE_OF_THUMB = {
    "section": "Appendix C",
    "page": 27,
    "intro_verbatim": "‘Rule of Thumb’ for renovations and small home building:",
    "rows": [
        "Timber 5-7% of material ordered",
        "Plasterboard 5-20% of materials ordered",
        "Concrete 3-5% of material ordered",
        "Bricks 5-10% of material ordered",
        "Tiles 2-5% of material ordered",
    ],
}

# Appendix D. Each row as it reads across the page.
BIN_SIZES = {
    "section": "Appendix D",
    "page": 28,
    "columns_verbatim": "Bin size Height Depth Width Waste type",
    "rows": [
        "140L Bin 1,065mm 615mm 535mm W, O, R",
        "240L Bin 1,060mm 730mm 535mm W, O, R",
        "360L Bin 1,100mm 848mm 680mm R",
        "660L Bin 1,200mm 780mm 1,260mm W, R",
        "1,100L Bin 1,330mm 1,070mm 1,240mm W, R",
    ],
    "key_verbatim": "W = Waste O = Organics R = Recycling",
}

TRUCK_DIMENSIONS = {
    "section": "Appendix F",
    "page": 30,
    "verbatim": (
        "Length 9.4 metres Width 2.84 metres (including mirrors) 2.25 metres (excluding mirrors) "
        "Height 3.63 metres (operational and travel) Weight 13 tonne (vehicle only) 24 tonne "
        "(vehicle and load) Turning circle 20 metres"
    ),
    "note": "Council's residential garbage truck. A commercial site served by a private "
            "contractor designs to that contractor's vehicle (Appendix G).",
}

# Table 1, §3.2 — material and its reuse potential, as each row reads across.
DEMOLITION_MATERIALS = {
    "section": "3.2",
    "page": 9,
    "rows": [
        "Concrete Reused for filling, levelling or road base",
        "Bricks and Pavers Can be cleaned for reuse or rendered over or crushed for use in "
        "landscaping and driveways",
        "Roof Tiles Can be cleaned and reused or crushed for use in landscaping and driveways",
        "Untreated Timber Reused as floorboards, fencing, furniture, mulched or sent to second "
        "hand timber suppliers",
        "Treated Timber Reused as formwork, bridging, blocking and propping, or sent to second "
        "hand timber suppliers",
        "Doors, Windows, Fittings Sent to second hand suppliers",
        "Glass Reused as glazing or aggregate for concrete production",
        "Metals (fittings, appliances and wiring) Removal for recycling",
        "Synthetic Rubber (carpet underlay) Reprocessed for use in safety devices and speed humps",
        "Significant Trees Relocated either onsite or off site",
        "Overburden Power screened and used as topsoil",
        "Garden Waste Mulched, composted",
        "Carpet Can be sent to recyclers or reused in landscaping",
        "Plasterboard Removal for recycling, return to supplier",
    ],
}

APPENDICES = {
    "A": {
        "heading": "Site Waste Minimisation and Management Plan Template",
        "page": 19,
        "scope_verbatim": (
            "Applicant and Project Details (all developments other than dwelling houses, "
            "semi-detached dwellings, dual occupancies and ancillary structures)"
        ),
        "declaration_verbatim": (
            "This development achieves the waste objectives set out in the DCP. The details on "
            "this form are the provisions for minimising waste on this project. All records "
            "demonstrating lawful disposal of waste will be retained and kept readily accessible "
            "for inspection by regulatory authorities such as Council, EPA or WorkCover NSW."
        ),
        "ongoing_verbatim": (
            "Show the total volume of waste expected to be generated by the development and the "
            "associated waste storage requirements."
        ),
        "ongoing_scope_verbatim": (
            "Ongoing Operation (residential flat buildings, multi dwelling housing, commercial, "
            "mixed use and industrial)"
        ),
        "transfer_verbatim": (
            "Identify each stage of waste transfer between residents’ units/ commercial tenancies "
            "and loading into the collection vehicle, detailing the responsibility for and "
            "location and frequency of, transfer and collection."
        ),
        "note": "The template's forms are on pages 19-25 of the chapter (read_dcp_section, "
                "chapter-15). Its construction page refers to 'Section 3.2', which is demolition; "
                "construction is §3.3.",
    },
    "B": {
        "heading": "Waste Minimisation Template Checklist for Dwellings",
        "page": 26,
        "verbatim": (
            "This waste minimisation template checklist for new dwelling houses, semi-detached "
            "dwellings and dual occupancies can be used to satisfy the performance criteria of "
            "Section 4.1 of this chapter."
        ),
    },
    "C": {
        "heading": "Waste/ Recycling Generation Rates",
        "page": 27,
        "note": "Carried as GENERATION_RATES and CONSTRUCTION_RULE_OF_THUMB.",
    },
    "D": {
        "heading": "Bin sizes and available services",
        "page": 28,
        "note": "Carried as BIN_SIZES.",
    },
    "E": {
        "heading": "Waste Recycling/ Storage Rooms in Multi Dwelling Housing and Residential Flat "
                   "Buildings",
        "page": 29,
        "bca_verbatim": (
            "Waste/ recycling bin storage rooms must be constructed in accordance with the "
            "requirements of the Building Code of Australia (BCA)."
        ),
        "size_verbatim": (
            "Waste/ recycling storage rooms must be of adequate size to comfortably accommodate "
            "all waste, recycling and organics bins associated with the development."
        ),
    },
    "F": {
        "heading": "Garbage Truck Dimensions for Residential Waste Collection",
        "page": 30,
        "verbatim": (
            "It is recommended that an applicant speak with Council’s Waste Services Coordinator "
            "in regards to the design of development proposals that involve garbage trucks "
            "entering the site."
        ),
        "note": "Dimensions carried as TRUCK_DIMENSIONS.",
    },
    "G": {
        "heading": "Commercial/ Industrial Waste and Recycling Storage Areas",
        "page": 31,
        "bca_verbatim": (
            "Waste/ recycling bin storage areas must be constructed in accordance with the "
            "requirements of the Building Code of Australia (BCA)."
        ),
        "location_verbatim": (
            "Waste/ recycling bin storage areas must be integrated into the design of the overall "
            "development. Materials and finishes that are visible from outside should be similar "
            "in style and quality to the external materials used in the rest of the development."
        ),
        "size_verbatim": (
            "Waste/ recycling bin storage areas must be able to accommodate separate general "
            "waste, recycling and organics bins which are of sufficient volume to contain the "
            "quantity of waste generated (at the rate described in Appendix B) between "
            "collections."
        ),
        "access": [
            "There must be step free access between the point at which the bins are collected/ "
            "emptied and the bin storage areas.",
            "Arrangements must be in place so that the bin storage area is not accessible to the "
            "public.",
            "Vermin must be prevented from entering the bin storage area.",
        ],
        "surfaces_verbatim": (
            "Waste/ recycling/ organics bin storage areas must have a smooth, durable floor and "
            "must be enclosed with durable walls/ fences that extend to the height of any bins "
            "which are kept within."
        ),
        "doors_verbatim": (
            "There must be a sign adjacent to the door/ gate that indicates the door/ gate must "
            "remain closed when not in use."
        ),
        "services_verbatim": (
            "Waste/ recycling/ organics storage areas must be serviced by hot and cold water "
            "provided through a centralised mixing valve."
        ),
        "drainage_verbatim": (
            "The floor must be graded so that any water is directed to a sewer authority approved "
            "drainage connection located upon the site."
        ),
        "washing_verbatim": (
            "Bins must only be washed in an area which drains to a sewer authority approved "
            "drainage connection."
        ),
        "note": "The size sentence cites 'Appendix B' for the generation rates; they are in "
                "Appendix C, which §4.3 cites correctly. A bin storage area draining to sewer may "
                "itself need trade waste approval — ask when applying for it.",
    },
    "H": {
        "heading": "Examples of Completed Waste Management Plan Components",
        "page": 33,
        "verbatim": (
            "Details of waste storage and sorting areas and vehicular access (including disposal "
            "trucks) are to be provided on plan drawings."
        ),
        "note": "A worked shopping centre example; its site plan on page 34 is a scanned "
                "drawing with no extractable text.",
    },
}

# Sections that frame rather than control. Named, so the audit can tell
# "read and left out" from "never read".
DESCRIPTIVE_SECTIONS = {
    "1.": {"why_not_carried": "Background: the WA & RR strategy, the waste hierarchy and the "
                              "elements of the DCP. Its numbered lists restate §2.2.",
           "lists_are_descriptive": True},
    "1.1": {"why_not_carried": "Purpose statement; no control."},
    "1.2": {"why_not_carried": "Objectives; restated by each section's own objectives."},
    "1.4": {"why_not_carried": "Heading only."},
    "1.4.3": {"why_not_carried": "Transitional Part 3A State significant projects — not a "
                                 "business DA."},
    "1.4.5": {"why_not_carried": "Advice to check other statutes; no control."},
    "1.4.6": {"why_not_carried": "Abbreviations."},
    "1.4.7": {"why_not_carried": "A reading guide to the chapter."},
    "2.": {"why_not_carried": "Part heading."},
    "3.": {"why_not_carried": "Part heading."},
    "4.": {"why_not_carried": "Part heading."},
}

# Sections whose numbered items the audit counts off the document and matches
# against what is carried.
COUNTED_SECTIONS = ("1.3", "1.4.4", "2.2", "3.2", "3.3", "3.4", "4.1", "4.2", "4.3", "4.4",
                    "4.5")

_C43 = SECTIONS["commercial_and_retail"]["numbered"]["outcomes"]
FIGURES = {
    "food_waste_threshold_litres_per_week": {
        "value": 240, "unit": "L/week", "as_written": "240 litres per week",
        "quote": _C43[13],
    },
    "food_waste_collections_per_week": {
        "value": 2, "unit": "collections/week", "as_written": "twice weekly",
        "quote": _C43[13],
    },
    "tenancy_storage_days": {
        "value": 1, "unit": "day", "as_written": "one day’s worth of waste",
        "quote": SECTIONS["commercial_and_retail"]["numbered"]["plans_must_show"][2],
    },
    "kerbside_frontage_share_percent": {
        "value": 75, "unit": "%", "as_written": "75%",
        "quote": SECTIONS["bins_and_collection"]["kerbside_75_percent_verbatim"],
    },
    "bulky_item_room_dwellings": {
        "value": 10, "unit": "dwellings", "as_written": "10 or more dwellings",
        "quote": SECTIONS["multi_dwelling"]["numbered"]["minimum_facilities"][4],
    },
    "industrial_waste_streams": {
        "value": 3, "unit": "streams", "as_written": "three (3) streams",
        "quote": SECTIONS["industrial"]["numbered"]["plans_must_show"][0],
    },
}

NOT_SET_BY_THIS_CHAPTER = {
    "who_prepares_the_plan": {
        "the_question": "Does the waste management plan have to be prepared by a consultant?",
        "answer": (
            "No. Chapter 15 names no qualification and no professional. §2.2 scales the detail to "
            "the proposal — a single dwelling 'would normally require a very simple SWMMP' — and "
            "Appendix A is a fill-in template. A business can prepare its own."
        ),
        "absent_phrases": ["qualified", "consultant", "accredited", "suitably experienced"],
    },
    "storage_room_size": {
        "the_question": "How big must the bin storage area be?",
        "answer": (
            "The chapter sets no minimum floor area or dimension. The test is capacity: big enough "
            "for the bins holding the waste generated between collections (§4.3, Appendix G), "
            "which Appendix C's rates and Appendix D's bin sizes let you work out."
        ),
        "absent_phrases": ["minimum floor area", "minimum dimension", "storage room of at least",
                           "minimum area of"],
    },
    "collection_frequency": {
        "the_question": "How often must commercial waste be collected?",
        "answer": (
            "Only one frequency is set: premises generating at least 240 litres a week of meat, "
            "seafood, poultry or food waste must have it collected at least twice weekly, or "
            "store it refrigerated (§4.3). Otherwise frequency is whatever the contractor offers, "
            "provided the storage holds what accumulates between collections."
        ),
        "absent_phrases": ["collected weekly", "once a week", "weekly collection",
                           "daily collection"],
    },
    "grease_and_trade_waste": {
        "the_question": "Does Chapter 15 cover the grease trap?",
        "answer": (
            "No — §1.3 excludes grease, interceptor waste and other liquid trade waste, which "
            "need a separate Liquid Trade Waste approval under s68 of the Local Government Act. "
            "get_other_approvals covers it."
        ),
        "absent_phrases": ["grease trap", "grease arrestor", "grease arrester"],
    },
    "food_premises_term": {
        "the_question": "Is there a 'food premises' waste standard?",
        "answer": (
            "The chapter never uses the term. Food businesses fall under §4.3 Commercial and "
            "Retail, whose criterion 14 (food waste of 240 litres a week or more) and Appendix "
            "C's food shop rates are what apply."
        ),
        "absent_phrases": ["food premises"],
    },
    "fees_and_bonds": {
        "the_question": "Is there a fee or bond for the waste plan?",
        "answer": "Chapter 15 sets none. Collection charges are between the business and its "
                  "contractor, or Council's waste service.",
        "absent_phrases": ["bond", "fee "],
    },
}
