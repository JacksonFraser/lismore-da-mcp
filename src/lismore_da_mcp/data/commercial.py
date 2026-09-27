"""Commercial development design controls, Lismore DCP Chapter 2.

Transcribed 2026-09-27 from `documents/dcp/chapter-2-commercial-development.pdf`
(22 pages). ROADMAP.md D1: the one DCP chapter written for the audience this
server is for, which until now was reachable only through keyword search.

**The chapter is two different documents under one title**, and which one
applies is decided by a map that nothing here can read:

  * **Part A — Urban Design in the Lismore CBD** applies to "the CBD (as shown
    on Map 1)". It is design principles in prose under numbered sections A.1-A.13
    and italic subheadings: weather protection, shopfronts, heritage, the 14m
    blank wall rule, signage. Its verbs are mostly "should", occasionally "must"
    and once "will not be permitted", so every control is quoted with its own
    modal verb rather than paraphrased into a rule.
  * **Part B — Lismore Health Precinct Brewster Street B3 Commercial Core Zone**
    applies to land on Map 2. It is a Performance Criteria / Acceptable
    Solutions table (Table B1) laid out like Chapter 1's.

Map 1 and Map 2 are images with no extractable text, so the precinct is never
inferred — not from the address and not from the zone. `PRECINCTS` records how
to settle it instead. Note that Chapter 2's Map 1 is not Chapter 7's Map 1 (the
CBD parking boundary); they are separate maps in separate chapters and nothing
here establishes that they draw the same line.

**The chapter still says B3.** "B3 Commercial Core" is the zone name from before
the 2023 Employment Zones reform, which renamed it E2 Commercial Centre. The
quotes keep the chapter's words; `zone_today` carries the translation.

**How to read a figure here is not Chapter 1's rule.** Chapter 1 §1.3 says an
Acceptable Solution is one way to meet a Performance Criterion and Council "may
be prepared to approve" the other. Chapter 2 contains no such sentence — Table
B1 has the same two columns but never says so. What does apply is the DCP
Introduction's "Variations to the Plan", which is narrower: a departure "will
only be considered where the variation is considered to be minor", compliance is
impossible or impractical, or the alternative is a better design. That is
quoted in `HOW_TO_READ_THIS_CHAPTER` from the Introduction itself.

**What the chapter does not contain matters as much as what it does.** It never
mentions a change of use; it sets no awning height, depth or clearance, no side
or rear setback in the CBD, no floor space ratio, and no CBD height limit of its
own. `NOT_SET_BY_THIS_CHAPTER` records each, and the audit asserts the phrases
are absent, because a presence check cannot see an invention.

`scripts/audit_commercial.py` checks every stored string still appears in the
chapter, that each figure appears inside its own quote, that every numbered
section, subheading and Table B1 label is carried, and that the absences hold.
"""

CHAPTER = "DCP Chapter 2"
SOURCE_PDF = "documents/dcp/chapter-2-commercial-development.pdf"
INTRODUCTION_PDF = "documents/dcp/dcp-introduction-may-2025.pdf"

HOW_TO_READ_THIS_CHAPTER = {
    # DCP Introduction, "Variations to the Plan" — checked against that
    # document, not Chapter 2. Chapter 2 has no reading rule of its own.
    "variations_verbatim": (
        "Council may approve development that does not strictly comply with this Plan. This will "
        "only be considered where the variation is considered to be minor, or where it can be "
        "demonstrated that compliance is physically impossible or impractical, or where the "
        "alternative proposed is substantiated as a better design solution. Variations to this "
        "Plan will not be supported where the purpose of the variation is to erode either the "
        "objectives or minimum standards, or simply to save development costs."
    ),
    "not_a_guarantee_verbatim": (
        "Compliance with the provisions of this Plan does not necessarily imply that Council will "
        "grant consent to a Development Application."
    ),
    # A.3, Chapter 2's own words on how Part A is applied.
    "part_a_study_first_verbatim": (
        "The relevant sections of this Chapter must be studied by an applicant before a building "
        "is designed and a building subject to this part of the DCP must comply with the DCP "
        "principles."
    ),
    "part_a_design_early_verbatim": (
        "Council acknowledges that attempting, either by negotiation or condition of consent, to "
        "add the required design attributes to a building after it has been fully designed, may "
        "result in a poor outcome. If considered early in the design process inclusion of the "
        "required design elements can be easy and cost effective."
    ),
    "part_a_merit_verbatim": (
        "Council will assess each application on its individual merit, taking into account the "
        "adjacent building design, context and form as well as the overall character of the "
        "surrounding streetscape."
    ),
    "what_it_means": (
        "Part A is design principles assessed on merit against the building's neighbours, and "
        "each is quoted with its own verb — most say 'should', a few say 'must' or 'will not be "
        "permitted', and the difference is the point. Part B is laid out as Performance Criteria "
        "and Acceptable Solutions, but unlike DCP Chapter 1 (§1.3) Chapter 2 never says that an "
        "Acceptable Solution is only one way to meet its criterion. A departure from either part "
        "is a variation under the DCP Introduction — considered where it is minor, where "
        "compliance is impossible or impractical, or where the alternative is a better design, "
        "and not where it only saves cost. Argue it against the objective in the Statement of "
        "Environmental Effects; do not present a missed figure as compliant."
    ),
}

# Where each Part applies. Both are maps with no extractable text.
PRECINCTS = {
    "cbd": {
        "part": "A",
        "name": "Lismore CBD (Part A - Urban Design in the Lismore CBD)",
        "map": "Chapter 2 Map 1 — 'Land to which Part A of this chapter applies'",
        "applies_verbatim": (
            "The purpose of Part A is to identify general design principles for new and "
            "renovating buildings within the CBD (as shown on Map 1)."
        ),
        # A.4 — "the Block" is named by several controls, and unlike Map 1 the
        # chapter defines it in words.
        "the_block_verbatim": (
            "Most retail activity in Lismore is centred on “the Block”. This was the block on the "
            "original village plan bounded by Molesworth, Magellan, Keen and Woodlark Streets."
        ),
        "how_to_find_it": (
            "Map 1 is an image on page 3 of the chapter with no extractable text, so neither an "
            "address nor a zone settles it. It is not Chapter 7's Map 1 (the CBD parking "
            "boundary) either — a different map in a different chapter. Look at Map 1 in the "
            "chapter (read_dcp_section, chapter-2, page 3), or ask the Duty Planner."
        ),
    },
    "brewster_street": {
        "part": "B",
        "name": "Lismore Health Precinct, Brewster Street (Part B)",
        "map": "Chapter 2 Map 2 — 'Land to which Part B of this chapter applies'",
        "applies_verbatim": (
            "The purpose of Part B is to identify general design principles for new buildings "
            "within the land zoned B3 Commercial Core in the vicinity of Brewster Street within "
            "the Lismore Health Precinct. This is the area generally bounded by Brewster Street, "
            "Orion Street and Uralba Street and in the B3 zone, see map 2."
        ),
        "zone_today": (
            "B3 Commercial Core is the pre-2023 name; the Employment Zones reform renamed it E2 "
            "Commercial Centre. Part B covers only the part of that zone on Map 2 — being in E2 "
            "does not put a site in Part B."
        ),
        "how_to_find_it": (
            "Map 2 is an image on page 18 of the chapter with no extractable text (read_dcp_section, "
            "chapter-2, page 18). The description above is the chapter's own and says 'generally'."
        ),
    },
}

# A.1-A.3 and B.1-B.4: the framing sections. Carried so the audit can account
# for them; the selector returns them as context, not as controls.
PART_A_FRAME = {
    "purpose": {
        "section": "A.1",
        "heading": "Purpose",
        "page": 3,
        "verbatim": (
            "Design principles include protection of building occupants and pedestrians from the "
            "extremes of Lismore weather, ensuring access for the disabled, incorporation of crime "
            "prevention measures and recognition of Lismore's heritage values."
        ),
    },
    "objectives": {
        "section": "A.2",
        "heading": "Objectives of Part A",
        "page": 4,
        "verbatim": (
            "The primary objective of this Chapter is to create an aesthetically pleasing, "
            "comfortable, safe and functional CBD streetscape environment, which exploits and "
            "improves upon the existing distinctive built form and locational attributes of the "
            "city."
        ),
        "design_should_include_verbatim": (
            "New buildings, or redevelopment of existing buildings, should include in their design"
        ),
        "design_should_include": [
            "Weather protection for pedestrians",
            "Energy efficiency",
            "Crime prevention design principles",
            "Disabled access",
            "Respect for streetscape and adjoining buildings.",
        ],
    },
    "how_to_use": {
        "section": "A.3",
        "heading": "How to Use Part A",
        "page": 4,
        "verbatim": (
            "This Part sets out Lismore City Council's requirements for the incorporation of "
            "measures for weather protection, energy efficiency, disabled access, respect for "
            "streetscape and heritage values and crime prevention to be included in new and "
            "renovating buildings in the central business district."
        ),
    },
}

PART_B_FRAME = {
    "purpose": {
        "section": "B.1",
        "heading": "Purpose",
        "page": 18,
        "note": "The B.1 text is carried as PRECINCTS['brewster_street']['applies_verbatim'].",
    },
    "health_precinct": {
        "section": "B.2",
        "heading": "Lismore Health Precinct",
        "page": 18,
        "boundary_verbatim": (
            "The Lismore Health Precinct comprises the area surrounding the Lismore Base Hospital, "
            "generally as bounded by: Brewster Street to the west; Leycester Street to the north; "
            "Hunter Street, Bent Street and Rotary Park Reserve to the east; and McKenzie Street "
            "and Uralba Street to the south."
        ),
        "note": (
            "DCP Chapter 1 §11 describes the same precinct with Orion Street, not Leycester "
            "Street, as its northern boundary. Both are quoted as written; the maps decide."
        ),
        "objectives": [
            "Encouraging additional residential densities in a location which is readily "
            "accessible to employment, transport, education and recreation facilities;",
            "Supporting additional specialist medical practices and health services facilities to "
            "be established in close proximity to the Lismore Base Hospital; and",
            "Providing design controls to encourage and facilitate change, in a manner which is "
            "compatible with or does not detract from the existing residential character of the "
            "much of the locality.",
        ],
    },
    "pre_lodgement": {
        "section": "B.3",
        "heading": "Pre-lodgement Consultation",
        "page": 19,
        "verbatim": (
            "Applicants are strongly encouraged to contact Council early in the design process, so "
            "that development plans may be prepared which are consistent with Council’s vision for "
            "the Health Precinct."
        ),
    },
    "preferred_design_outcomes": {
        "section": "B.4",
        "heading": "Preferred Design Outcomes",
        "page": 19,
        "active_frontage_verbatim": (
            "Council is particularly keen to promote an ‘active’ building interface with Brewster "
            "and Uralba Streets to facilitate the longer term pedestrian activation of these "
            "streets."
        ),
        "ground_floor_verbatim": (
            "as well as commercial activities on the ground floor to service both residents and "
            "users of the fields (such as cafes)."
        ),
        "interface_verbatim": (
            "Council is keen to ensure that development within the Brewster Street B3 Commercial "
            "Core Zone is designed such that a sympathetic interface is provided between "
            "residential and non-residential development in the Precinct."
        ),
        "table_applies_verbatim": "To achieve these outcomes, the design criteria documented in "
                                  "Table B1 apply.",
    },
}

# Sections that describe rather than control. Carried by name so the audit can
# tell "read and deliberately left out" from "never read".
DESCRIPTIVE_SECTIONS = {
    "A.4": {
        "heading": "Lismore CBD Characteristics",
        "why_not_carried": "Description of the CBD's existing character. Its one operative "
                           "fact, the definition of 'the Block', is carried in PRECINCTS.",
    },
    "A.5": {
        "heading": "Historical Development",
        "why_not_carried": "History of the CBD's awnings and building stock. No control.",
    },
    "A.6": {
        "heading": "Urban Design Initiatives",
        "why_not_carried": "Records the 1991 City Centre Strategy. No control.",
    },
}

# The work each Part A topic is written for. Our reading, not the chapter's
# words — which is why it is a separate map rather than a field the audit would
# check. Over-inclusive on purpose: a principle wrongly listed costs a sentence,
# one wrongly omitted costs a redesign.
NEW = "new_building"
ALTER = "alterations_or_additions"

PART_A = {
    "general_guidelines": {
        "section": "A.7",
        "heading": "General Guidelines",
        "page": 6,
        "applies_to": (NEW, ALTER),
        "intro_verbatim": "The guidelines for the CBD are intended to reinforce the existing "
                          "urban form and character.",
        "building_forms_should": [
            "Relate to Lismore’s climate by incorporating weather protection elements for "
            "pedestrians;",
            "Draw from local issues, including cultural, existing built form, landscape and other "
            "environmental influences;",
            "Not detract from existing vistas and views;",
            "Be energy efficient;",
            "Make a positive contribution to the streetscape; and",
            "Be compatible with local heritage values.",
        ],
    },
    "new_buildings": {
        "section": "A.8",
        "heading": "New Buildings (Infill Development)",
        "page": 6,
        "applies_to": (NEW,),
        "intro_verbatim": (
            "The designer should always take into account the height and proportions of "
            "neighbouring buildings and continue themes common to these buildings while "
            "introducing contributory elements that are unique to the new building."
        ),
        "principles_verbatim": "The following principles should be observed when infill "
                               "development is being established:",
        "principles": [
            "Ensure new buildings maintain an appropriate scale, mass, detail and continuity of "
            "facade to the street; for example, bulky buildings can be broken into smaller "
            "components to better reflect the character of the neighbours;",
            "Infill development should be of contemporary design. It is essential however that "
            "the design is sympathetic to adjoining developments and the existing streetscape;",
            "The principles of energy efficiency should be used in the design of the new building.",
            "Unless the building is set back from the street, the street frontage should contain "
            "elements to protect pedestrians from weather extremes.",
            "Where the proposal is to establish a traditional veranda style structure, it must be "
            "of construction and design that will safely absorb vehicular impacts and not obstruct "
            "pedestrians using the footpath; and",
            "A pedestrian friendly environment should be created as part of any new development "
            "and should be suitable for disabled access.",
        ],
    },
    "corner_buildings": {
        "section": "A.8",
        "heading": "Corner Buildings",
        "subheading": True,
        "page": 6,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "In the event of a corner block becoming available for development the design should "
            "make an effort to address the corner either in the form of a building itself, or in "
            "the awning treatment."
        ),
    },
    "shop_fronts": {
        "section": "A.8",
        "heading": "Shop Fronts",
        "subheading": True,
        "page": 6,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "While there is no need to faithfully recreate the earlier style of shop front, the "
            "design should harmonise with and complement the existing streetscape character."
        ),
    },
    "large_scale_developments": {
        "section": "A.8",
        "heading": "Large Scale Developments",
        "subheading": True,
        "page": 7,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "Large-scale developments such as shopping centres, registered clubs, bulky goods "
            "premises and office premises are particularly difficult to integrate unobtrusively "
            "into the streetscapes of older regional urban centres."
        ),
        "facade_verbatim": (
            "Building facades should relate to the street and be of a human scale. It is important "
            "to minimise visual impact by breaking up the expanse of the facade and there are a "
            "number of methods by which this can be achieved:"
        ),
        "methods": [
            "Horizontal elements such as awnings and cornice detailing may be introduced;",
            "The roofline can be broken with a pediment or rounded elements;",
            "Plantings, landscape elements and lattice screening can be used to integrate the "
            "development into the landscape; and",
            "Large walls or facades should incorporate vertical and horizontal elements or shop "
            "fronts to break up the massing of the buildings.",
            "Minimising the use of bright or intrusive colours.",
        ],
    },
    "additions_to_existing_buildings": {
        "section": "A.9",
        "heading": "Additions to Existing Buildings",
        "page": 7,
        "applies_to": (ALTER,),
        "demolition_verbatim": "Complete or partial demolition of any building requires "
                               "development consent from Council.",
        "intro_verbatim": (
            "When renovating or adding to an existing building within the CBD precinct, the "
            "following requirements apply:"
        ),
        "requirements": [
            "Any redevelopment should retain a form and scale that complements the existing "
            "streetscape;",
            "Where possible, verandas can be reinstated;",
            "Ensure any additional awnings or verandahs are sympathetic to adjoining buildings and "
            "the existing streetscape;",
            "The materials and colours to be used in additions or renovations should be similar to "
            "and complement those used in existing structures;",
            "Awnings should be connected to adjoining buildings to provide continuous weather "
            "protection and should extend to the kerb line.",
            "The redevelopment of alleyways and laneways in compliance with the adopted "
            "streetscape plans.",
        ],
        "laneway_exception_verbatim": (
            "Redevelopment of buildings fronting laneways will not be required to include awnings "
            "if such would conflict with traffic movement or truck deliveries."
        ),
        "note": (
            "The demolition sentence is the DCP's. Some demolition is Exempt or Complying "
            "Development under the Codes SEPP, which the DCP does not override — ask before "
            "assuming either way."
        ),
    },
    "weather_protection": {
        "section": "A.10",
        "heading": "Weather Protection",
        "page": 7,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "Provision of shade which screens ultraviolet radiation must be integral in the design "
            "of buildings in the CBD."
        ),
        "principles_verbatim": (
            "When designing and implementing for weather protection within the CBD, the following "
            "principles are to be followed:"
        ),
        "principles": [
            "Buildings constructed to front property boundary are to include features to protect "
            "pedestrians from rain, wind and summer sun;",
            "Setting of upper levels of building back above an existing/specified parapet line, "
            "will allow mid-winter sun penetration to the street during the midday period;",
            "Shading devices which permit winter and exclude summer sun should be used.",
            "Redevelopment of buildings constructed to street boundary is to make provision for "
            "extending weather protected routes, particularly along main pedestrian routes to "
            "transport centres;",
            "Awnings should be designed to respect and complement the existing streetscape, "
            "character and buildings to which they are attached. Where this involves heritage "
            "items, the design and use of awnings will need to be considered carefully;",
            "Individual entrance canopies are generally inappropriate on frontages to streets as "
            "they tend to distract even further from the visual continuity of the streetscape;",
            "Buildings set back from the street are to use landscaping to enhance climate control "
            "by shading walls and windows in summer;",
            "All plantings should place an emphasis on shade provision wherever possible and "
            "conform with the rainforest theme currently evident in the CBD, and as proposed in "
            "the City Centre Streetscape Study, and should serve to unify the street planting "
            "environment.",
        ],
        "cross_reference": (
            "A.9 adds that awnings 'should be connected to adjoining buildings to provide "
            "continuous weather protection and should extend to the kerb line'. The chapter sets "
            "no awning height, depth or clearance (see what_the_chapter_does_not_set). An awning "
            "over the footpath is work over a public road, which needs a Roads Act s138 "
            "approval separate from the DA (get_other_approvals, road_reserve_works)."
        ),
    },
    "street_furniture": {
        "section": "A.11",
        "heading": "Surface Treatment and Street Furniture",
        "page": 8,
        "applies_to": (NEW, ALTER),
        "principles": [
            "Footpaths that are in poor condition should be replaced for both safety reasons and "
            "aesthetic ones. The treatment of footpaths should be durable and of a non-slip "
            "surface;",
            "Tactile tiles should be included as they assist visually impaired people to negotiate "
            "independently through the CBD;",
            "Preference will be given to designs which complement the existing character of the "
            "CBD and streetscape consideration shall be given to Clause 27 of AS1428.2 in the "
            "selection and location of street furniture suitable for use by the disabled.",
            "Street furniture is to be made from robust materials, not have components that can be "
            "easily removed and should be made of durable materials to ensure its long term use "
            "and low maintenance;",
        ],
        "note": "Mostly addressed to Council's own streetscape works; it reaches a private "
                "development where the proposal includes footpath or public-space works.",
    },
    "disabled_access": {
        "section": "A.12",
        "heading": "Disabled Access",
        "page": 8,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "Access for disabled persons must always be considered in the planning, designs and "
            "use of public facilities and public spaces. Access to buildings for the disabled "
            "shall comply with the Building Code of Australia."
        ),
        "principles": [
            "Platform steps with short risers and wide tread are preferred;",
            "The provision of sheltered drop-off and pick-up points should be considered;",
            "Disabled carparking spaces should be close to amenities;",
            "Ensure access to buildings and other public spaces are available to people of all "
            "abilities;",
            "Changes in level of less than 150mm and single steps are to be avoided as they can "
            "easily be missed by visually impaired people;",
            "The tread surface on stairs should be constructed with a non-slip surface;",
            "At least the first step and the last step in a flight of steps should be painted "
            "white or in a light colour, or be constructed in a light material and tactile ground "
            "indicators at the top and bottom of the stair.",
        ],
        "not_exhaustive_verbatim": (
            "This is not an exhaustive list. Reference should be made to the Building Code of "
            "Australia for requirements for access for disabled persons."
        ),
    },
    "crime_prevention": {
        "section": "A.12",
        "heading": "Crime Prevention",
        "subheading": True,
        "page": 8,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "Chapter 13 sets out design requirements for new buildings in accordance with Crime "
            "Prevention through Environmental Design principles."
        ),
    },
    "heritage_buildings": {
        "section": "A.12",
        "heading": "Heritage Buildings",
        "subheading": True,
        "page": 9,
        "applies_to": (NEW, ALTER),
        "molesworth_verbatim": (
            "Molesworth Street retains a large amount of its heritage. Building designs in "
            "Molesworth Street therefore need to pay particular attention to the streetscape and "
            "the integrity of individual heritage buildings. In Keen, Woodlark and Magellan "
            "Streets a greater degree of flexibility may be exercised, however, several basic "
            "characteristics need to be recognised in order to maintain compatibility with "
            "existing contributory facades."
        ),
        "awnings_verbatim": (
            "Elaborate details should be avoided, as should awning forms that are not traditional "
            "to the Lismore streetscape."
        ),
        "significance_verbatim": (
            "All future development undertaken in the CBD should recognise the heritage "
            "significance of buildings identified in Lismore LEP 2012, and in the Lismore Citywide "
            "Heritage Study, and seek to conserve rather than detract from that significance."
        ),
        "refer_verbatim": "Refer also to Chapter 12 – Heritage Conservation.",
        "near_heritage_verbatim": (
            "The following design features should be considered when a development is in the "
            "proximity of an item of environmental heritage or within a conservation area:"
        ),
        "near_heritage": [
            "The character of an individual heritage item and its setting should be maintained or "
            "enhanced through careful consideration of alterations and additions or construction "
            "of new structures;",
            "The removal or alteration of any distinctive architectural feature should be avoided "
            "and deteriorating architectural or decorative features should be repaired rather than "
            "replaced where possible. Local Heritage Assistance Grants may be available for this "
            "purpose;",
            "Proposals for complete or partial demolition of listed heritage buildings or "
            "buildings within the nominated conservation precincts shall be assessed in the "
            "context of the buildings contribution to streetscape and likely effect on individual "
            "architectural integrity; and",
            "The design, style, materials and colour for new construction shall be considered on "
            "an individual basis on the premise that contemporary styles may be more appropriate "
            "than emulating traditional designs.",
        ],
        "guidelines_by_verbatim": "Existing heritage buildings should form the basis for design "
                                  "guidelines for new development by:",
        "guidelines_by": [
            "aligning horizontal elements",
            "repeating major vertical bay widths",
            "re-interpreting proportion and articulation of facade components",
            "providing examples of materials and colours.",
        ],
        "note": (
            "None of this requires a heritage document. Whether one is wanted is LEP cl 5.10(5), "
            "which says Council *may* require one — ask before commissioning it."
        ),
    },
    "retention_of_trees": {
        "section": "A.12",
        "heading": "Retention of Trees",
        "subheading": True,
        "page": 9,
        "applies_to": (NEW, ALTER),
        "verbatim": "Every effort should be made to retain mature trees and shrubs on both private "
                    "and public land.",
        "replacement_verbatim": (
            "Where Council consents to the removal of a tree, Council will normally require its "
            "replacement with two or more trees for each tree removed."
        ),
        "lopping_verbatim": (
            "Where approval is granted to significantly lop or top a tree Council may require the "
            "planting of one or more further trees."
        ),
        "stale_reference": (
            "The chapter refers to 'Chapter 14 - Preservation of Trees or Vegetation'. That chapter "
            "was repealed and replaced by Chapter 14 Vegetation Protection (DCP amendment 29, "
            "2020); the current one is documents/dcp/chapter-14-vegetation-protection.pdf."
        ),
    },
    "site_analysis": {
        "section": "A.13",
        "heading": "Specific Requirements",
        "page": 10,
        "applies_to": (NEW,),
        "verbatim": (
            "A site analysis is to be prepared and submitted as part of the Development "
            "Application for any new building in the CBD. This analysis is to illustrate the "
            "relationship of the new building to those adjoining so that impact on the "
            "streetscape may be evaluated."
        ),
        "additional_verbatim": (
            "For new developments or redevelopments within the CBD precinct identified by this "
            "plan, there are a number of additional requirements that will have to be met before "
            "council will give approval."
        ),
    },
    "building_heights": {
        "section": "A.13",
        "heading": "Building Heights",
        "subheading": True,
        "page": 11,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "The height of a building within the CBD is not to exceed the maximum height shown for "
            "the land in Lismore LEP 2012 Height of Buildings Map."
        ),
        "parapet_verbatim": (
            "Continuity of the streetscape can be achieved by maintaining consistent parapet "
            "heights"
        ),
        "infill_height_verbatim": (
            "Generally, the height of infill development should be determined by the ridge heights "
            "of adjoining development unless the additional height is set back from the street "
            "frontage."
        ),
        "note": (
            "The chapter sets no height figure of its own. It mentions 'fourteen metres' and 'six "
            "(6) storeys' only as description — the Manchester Unity building, and the City Centre "
            "Strategy's view of viability. The limit is the LEP map, which "
            "lookup_site_constraints reads by address."
        ),
    },
    "roof_form": {
        "section": "A.13",
        "heading": "Roof Form",
        "subheading": True,
        "page": 11,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "It is desirable for all new development within the CBD to have a parapet or similar "
            "structure, in a design that complements the existing built environment"
        ),
        "match_verbatim": (
            "Roof forms should relate to adjoining buildings by matching style and pitch. Roof "
            "materials should be carefully selected to harmonise with neighbouring buildings."
        ),
    },
    "windows_and_doors": {
        "section": "A.13",
        "heading": "Windows and Doors",
        "subheading": True,
        "page": 11,
        "applies_to": (NEW, ALTER),
        "west_windows_verbatim": (
            "By reducing the size of west facing windows or by designing appropriate window covers "
            "or awnings"
        ),
        "display_windows_verbatim": (
            "Display windows should not comprise uninterrupted expanses of glass; there should be "
            "a regular rhythm of glass and framing."
        ),
        "not_permitted_verbatim": (
            "Glass curtain walls or large areas of featureless blank walls will not be permitted. "
            "The visual impact of such elevations needs to be ‘broken up’ or articulated."
        ),
        "wall_length_verbatim": (
            "To counteract the visual impact of large blank walls with new developments in the CBD "
            "no external wall should be greater than 14m in length unless a return, buttress, "
            "balcony, or recess to a depth of at least 600mm, or some other acceptable design "
            "feature is used to break up the straight run of the wall."
        ),
        "note": (
            "The 14m wall rule is Chapter 2's, for new developments in the CBD. An earlier "
            "version of this repository attributed a 14m wall length to Chapter 1, where it does "
            "not appear."
        ),
    },
    "design": {
        "section": "A.13",
        "heading": "Design",
        "subheading": True,
        "page": 13,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "New developments should not directly copy existing designs of historic buildings, but "
            "may incorporate design elements, which complement neighbouring buildings and the "
            "surrounding streetscape"
        ),
        "facade_verbatim": (
            "The façade of the building should incorporate symmetrically placed upper level "
            "windows of vertical proportions and contain no greater than equal portions of glass "
            "to masonry."
        ),
    },
    "scale_mass": {
        "section": "A.13",
        "heading": "Scale/Mass",
        "subheading": True,
        "page": 14,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "Oversize buildings that overwhelm existing structures and dominate the streetscape "
            "will be discouraged"
        ),
        "merit_verbatim": (
            "Each development will be assessed on individual merit, and will consider its position "
            "in the streetscape and adjoining buildings."
        ),
    },
    "setback": {
        "section": "A.13",
        "heading": "Setback",
        "subheading": True,
        "page": 15,
        "applies_to": (NEW,),
        "verbatim": (
            "Buildings which do not create a continuous line with adjacent buildings for the first "
            "two storeys will be discouraged, especially within “the Block”"
        ),
        "car_parking_verbatim": (
            "The placement of carparking areas between a building and the front boundary is "
            "undesirable."
        ),
        "outside_the_block_verbatim": (
            "It is suggested that any new infill development, which is not within “the Block” and "
            "is adjacent to older style buildings or heritage items, should be setback from the "
            "existing building line to allow landscaping to be established."
        ),
        "note": "No setback figure: the CBD rule is continuity with the neighbours.",
    },
    "materials": {
        "section": "A.13",
        "heading": "Materials",
        "subheading": True,
        "page": 16,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "Building elevations that are visible to the street should utilise materials common in "
            "the precinct. Council will ensure that buildings with glazed facades, roofs and "
            "awnings minimise glare by restricting use of highly reflective glass, which should "
            "reduce hazardous or uncomfortable glare from reflective materials."
        ),
    },
    "colour": {
        "section": "A.13",
        "heading": "Colour",
        "subheading": True,
        "page": 16,
        "applies_to": (NEW, ALTER),
        "brickwork_verbatim": "Existing brickwork which has not previously been painted should be "
                              "retained.",
        "verbatim": (
            "The use of bright colours will be discouraged as they have the potential to adversely "
            "affect the visual amenity of the CBD, however, applications will be assessed on "
            "individual merit, taking into consideration adjoining buildings and the existing "
            "streetscape."
        ),
        "heritage_verbatim": (
            "In the case of items environmental heritage identified in Schedule 5 of the Lismore "
            "LEP 2012, Council will also assess applications in light of the published guidelines "
            "for heritage colours which have been recognised by the Australian Heritage Commission "
            "and other official heritage organisations."
        ),
    },
    "signage": {
        "section": "A.13",
        "heading": "Signage",
        "subheading": True,
        "page": 16,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "Signage should not dominate facades and should be sympathetic to the building on "
            "which it is being placed"
        ),
        "chapter_9_verbatim": (
            "Advertising and signage should be in accordance with Chapter 9 - Outdoor Advertising "
            "Structures of the Lismore Development Control Plan. Signs on heritage buildings "
            "should:"
        ),
        "heritage_signs": [
            "Be restricted to discrete panels of the building;",
            "Not dominate the facade;",
            "Be of heritage character, with details of size, style and colour to be provided with "
            "Development Applications.",
        ],
        "the_block_verbatim": (
            "Council will pay particular attention to how all proposed signage that is to be "
            "placed on buildings within the ‘Block’ complies with Council’s regulations."
        ),
        "cross_reference": (
            "Chapter 9 is now titled 'Signage'. Whether the sign needs an application at all is "
            "get_signage_requirements — most shopfront signage is Exempt Development."
        ),
    },
    "quality_infrastructure": {
        "section": "A.13",
        "heading": "Quality Infrastructure",
        "subheading": True,
        "page": 17,
        "applies_to": (NEW, ALTER),
        "verbatim": (
            "Where development will result in increased traffic generation, upgrades of the road "
            "frontages or other external road works will be required to ensure the standard of "
            "the road meets the requirements set out in chapters 5A, 5B and 6 of the DCP."
        ),
    },
}

# Table B1, Part B. Performance Criteria and Acceptable Solutions, verbatim.
TABLE_B1 = {
    "street_setbacks": {
        "heading": "Street Setbacks",
        "performance_criteria": {
            "P1": "Development is sited and designed taking into account the relationship to "
                  "adjoining premises and the street.",
        },
        "acceptable_solutions": {
            "A1.1": "Buildings are setback an equal or greater distance from the street as "
                    "buildings on adjoining lots. Where there is no adjoining development (or the "
                    "setback is greater than 6m) the setback shall be 6 metres.",
            "A1.2": "For a corner allotment, the setback is 6m from the primary street and 4m from "
                    "the secondary road where there is no adjoining development.",
        },
    },
    "street_address": {
        "heading": "Street Address",
        "performance_criteria": {
            "P2": "Buildings are oriented to the public street and provide for passive observation "
                  "of the street network.",
        },
        "acceptable_solutions": {
            "A2.1": "Buildings address the public street, with ground floor commercial premises "
                    "provided with direct pedestrian access from the street.",
            "A2.2": "Windows and deep balconies and / or decks are provided facing the public "
                    "street.",
            "A2.3": "Buildings are designed to provide a 2 storey presentation to the street, with "
                    "the 3rd / 4th storey set back at least 3m from the front building elevation.",
            "A2.4": "The building facade is provided with architectural features to articulate and "
                    "visually ‘break up’ long expanses of wall.",
        },
    },
    "flooding": {
        "heading": "Flooding",
        "performance_criteria": {
            "P3": "Development is designed taking into account the flood characteristics of the "
                  "area.",
        },
        "acceptable_solutions": {
            "A3.1": "Non-residential land uses are provided on the ground floor.",
            "A3.2": "Developments comply with the provisions of DCP Chapter 8.",
        },
    },
    "brewster_and_uralba_streets": {
        "heading": "Brewster Street & Uralba Street",
        "performance_criteria": {
            "P4": "Active street frontages and pedestrian friendly environments are provided to "
                  "Brewster Street and Uralba Street.",
        },
        "acceptable_solutions": {
            "A4.1": "Small scale retail and commercial shop frontages are provided to the street.",
            "A4.2": "The front building setback is landscaped and includes shade trees.",
            "A4.3": "Awnings (for weather protection) and street furniture are provided within the "
                    "front building setback.",
            "A4.4": "Vehicle and pedestrian points of entry are separated.",
        },
    },
    "carparking_and_loading": {
        "heading": "On-Site Carparking & Loading Facilities",
        "performance_criteria": {
            "P5": "Adequate provision is made for on-site car parking and loading facilities.",
            "P6": "On-site car parking and loading areas do not dominate the front setbacks.",
        },
        "acceptable_solutions": {
            "A5": "On site car parking is provided in accordance with Chapter 7 of this DCP.",
            "A6.1": "Carparking areas are provided either at the rear of the site or integrated "
                    "into the building form via under croft parking.",
            "A6.2": "Car parking access is provided via integrated access points.",
            "A6.3": "No car parking is provided within the front building setback.",
            "A6.4": "Loading docks and the like are located at the rear or side of the premises.",
        },
    },
    "signage": {
        "heading": "Signage",
        "performance_criteria": {
            "P7": "Signage does not dominate facades and is included as an integral part of the "
                  "building design.",
        },
        "acceptable_solutions": {
            "A7": "Advertising and signage is provided in accordance with Chapter 9 - Outdoor "
                  "Advertising Structures of the Lismore Development Control Plan.",
        },
    },
    "taller_buildings_site_area": {
        "heading": "Taller Buildings (3 levels or more) — Site Area",
        "taller_only": True,
        "performance_criteria": {
            "P8": "Taller buildings (3 levels or more) are located on sites of a suitable size to "
                  "enable buildings to be offset from property boundaries, achieve good "
                  "orientation and to provide substantial onsite landscaping.",
        },
        "acceptable_solutions": {
            "A8": "The site has an area of at least 1200m2.",
        },
    },
    "taller_buildings_residential_interface": {
        "heading": "Taller Buildings (3 levels or more) — Interface with Residential Areas",
        "taller_only": True,
        "adjoining_r2_only": True,
        "performance_criteria": {
            "P9": "Taller buildings adjoining the R2 Low Density Residential zone are designed and "
                  "sited having regard to the residential character of the locality and to reduce "
                  "the visual and amenity impacts on adjoining properties.",
            "P10": "For taller buildings adjoining the R2 Low Density Residential Zone adequate "
                   "building separation distances are shared equitably between neighbouring sites "
                   "to achieve reasonable levels of external and internal visual privacy.",
        },
        "acceptable_solutions": {
            "A9.1": "The development is provided as a series of buildings rather than one large "
                    "building.",
            "A9.2": "A variety of building materials are incorporated into the design, including "
                    "masonry brick and lightweight cladding materials such as weatherboard.",
            "A10": "Minimum separation distances from side and rear boundaries adjoining the R2 "
                   "Low Density Residential Zone are as follows:",
        },
    },
    "road_quality": {
        "heading": "Road Quality",
        "performance_criteria": {
            "P11": "Any additional traffic generated from a proposal will require the upgrade of "
                   "frontages or other external road works.",
        },
        "acceptable_solutions": {
            "A11": "Road standard along the frontage must meet the requirements set out in "
                   "Chapters 5A, 5B and 6 of the DCP respectively.",
        },
    },
}

# A10's table. One row, and it stops at 11.5 metres.
SEPARATION_TABLE = {
    "columns_verbatim": "Height Habitable Rooms & Balconies Non-habitable rooms",
    "rows": [
        {
            "height": "Up to 11.5 metres",
            "habitable_rooms_and_balconies": "6 metres",
            "non_habitable_rooms": "3 metres",
        },
    ],
}

# Every number the selector compares against, each with the quote it was read
# from. The audit checks the value sits, as written, inside its own quote.
FIGURES = {
    "cbd_external_wall_max_m": {
        "value": 14, "unit": "m", "as_written": "14m",
        "quote": PART_A["windows_and_doors"]["wall_length_verbatim"],
    },
    "cbd_wall_articulation_depth_mm": {
        "value": 600, "unit": "mm", "as_written": "600mm",
        "quote": PART_A["windows_and_doors"]["wall_length_verbatim"],
    },
    "cbd_level_change_to_avoid_mm": {
        "value": 150, "unit": "mm", "as_written": "150mm",
        "quote": PART_A["disabled_access"]["principles"][4],
    },
    "cbd_replacement_trees_per_tree": {
        "value": 2, "unit": "trees", "as_written": "two or more trees",
        "quote": PART_A["retention_of_trees"]["replacement_verbatim"],
    },
    "brewster_street_setback_m": {
        "value": 6, "unit": "m", "as_written": "6 metres",
        "quote": TABLE_B1["street_setbacks"]["acceptable_solutions"]["A1.1"],
    },
    "brewster_corner_secondary_setback_m": {
        "value": 4, "unit": "m", "as_written": "4m from the secondary road",
        "quote": TABLE_B1["street_setbacks"]["acceptable_solutions"]["A1.2"],
    },
    "brewster_upper_storey_setback_m": {
        "value": 3, "unit": "m", "as_written": "at least 3m",
        "quote": TABLE_B1["street_address"]["acceptable_solutions"]["A2.3"],
    },
    "brewster_taller_levels": {
        "value": 3, "unit": "levels", "as_written": "3 levels or more",
        "quote": TABLE_B1["taller_buildings_site_area"]["performance_criteria"]["P8"],
    },
    "brewster_taller_site_area_m2": {
        "value": 1200, "unit": "m2", "as_written": "1200m2",
        "quote": TABLE_B1["taller_buildings_site_area"]["acceptable_solutions"]["A8"],
    },
    "brewster_separation_height_limit_m": {
        "value": 11.5, "unit": "m", "as_written": "Up to 11.5 metres",
        "quote": "Up to 11.5 metres 6 metres 3 metres",
    },
    "brewster_separation_habitable_m": {
        "value": 6, "unit": "m", "as_written": "6 metres",
        "quote": "Up to 11.5 metres 6 metres 3 metres",
    },
    "brewster_separation_non_habitable_m": {
        "value": 3, "unit": "m", "as_written": "3 metres",
        "quote": "Up to 11.5 metres 6 metres 3 metres",
    },
}

# What Chapter 2 does not contain, and what governs instead. `absent_phrases`
# are asserted absent from the chapter by the audit — a presence check cannot
# catch an invention, and each of these is a question applicants ask.
NOT_SET_BY_THIS_CHAPTER = {
    "change_of_use": {
        "the_question": "Does Chapter 2 apply to a change of use with no building work?",
        "answer": (
            "The chapter never mentions a change of use. Part A is written for 'new and "
            "renovating buildings' (A.1) and Part B for 'new buildings' (B.1). A business taking "
            "over existing premises without external work meets nothing in it that is addressed "
            "to that case — but any external work does bring it in: a new shopfront, an awning, "
            "signage, a colour scheme. Whether Council treats a particular fitout as 'renovating' "
            "is a Duty Planner question."
        ),
        "absent_phrases": ["change of use", "change in use", "fitout", "fit-out", "fit out"],
    },
    "awning_dimensions": {
        "the_question": "How high, how deep, and how far from the kerb must an awning be?",
        "answer": (
            "Chapter 2 sets no awning height, depth or clearance. It says awnings 'should extend "
            "to the kerb line' and be connected to their neighbours (A.9), and that they should "
            "respect the streetscape (A.10). Ask Council what dimensions it expects; an awning "
            "over the footpath also needs a Roads Act s138 approval, separate from the DA."
        ),
        "absent_phrases": ["clearance", "awning height", "awning depth", "metres above",
                           "above the footpath"],
    },
    "cbd_side_and_rear_setbacks": {
        "the_question": "What side or rear setback applies in the CBD?",
        "answer": (
            "None. Part A has no setback figure at all: its rule is continuity — buildings that "
            "break the line of their neighbours for the first two storeys 'will be discouraged'. "
            "The only side and rear distances in the chapter are Part B's A10 separations, for "
            "taller Brewster Street buildings adjoining the R2 zone."
        ),
        "absent_phrases": ["side setback", "rear setback", "zero setback", "nil setback"],
    },
    "cbd_height": {
        "the_question": "What is the height limit in the CBD?",
        "answer": (
            "Chapter 2 sets none of its own; it defers to the LEP Height of Buildings Map, which "
            "lookup_site_constraints reads by address. The 'fourteen metres' and 'six (6) storeys' "
            "in A.13 are description, not controls."
        ),
        "absent_phrases": ["maximum of six storeys", "storey limit", "height limit of"],
    },
    "floor_space_and_coverage": {
        "the_question": "Is there a floor space ratio, site coverage or landscaping percentage?",
        "answer": (
            "Not in Chapter 2. Floor space ratio, where it applies, is an LEP map; the chapter "
            "sets no site coverage and no landscaped proportion for either part."
        ),
        "absent_phrases": ["floor space ratio", "fsr", "site coverage", "per cent", "%"],
    },
    "parking_rate": {
        "the_question": "How many parking spaces does Chapter 2 require?",
        "answer": (
            "None — it defers. Part B's A5 sends parking to Chapter 7 and Part A sets no rate. "
            "get_parking_rates has Chapter 7's rates, including the fixed CBD rate."
        ),
        "absent_phrases": ["spaces per", "parking spaces per", "car spaces per"],
    },
    "outdoor_dining": {
        "the_question": "Does Chapter 2 control footpath or outdoor dining?",
        "answer": (
            "No. Footpath dining is an approval under the Roads Act and Council's outdoor dining "
            "policy, not a DCP design control — get_other_approvals covers it."
        ),
        "absent_phrases": ["footpath dining", "outdoor dining", "alfresco"],
    },
    "separation_above_11_5m": {
        "the_question": "What separation applies beside R2 for a Brewster Street building over "
                        "11.5 metres?",
        "answer": (
            "A10's table has one row, 'Up to 11.5 metres', and Chapter 2 sets nothing above it. "
            "Chapter 1 §11's Health Precinct table has rows at 12m and 16m, but Chapter 2 does not "
            "adopt it — ask Council which it will apply."
        ),
        "absent_phrases": ["up to 12m", "up to 16m", "(4 storeys)", "(5 storeys)", "9 metres",
                           "4.5 metres"],
    },
    "performance_route": {
        "the_question": "Is an Acceptable Solution in Table B1 only one way to comply, as in "
                        "Chapter 1?",
        "answer": (
            "Chapter 2 does not say so. It has the two columns but not Chapter 1 §1.3's sentence "
            "that 'Council may be prepared to approve' a proposal meeting the Performance "
            "Criteria instead. The DCP Introduction's 'Variations to the Plan' is what applies."
        ),
        "absent_phrases": ["alternatively, council may be prepared to approve",
                           "deemed to comply", "deemed-to-comply"],
    },
}
