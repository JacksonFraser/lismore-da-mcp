"""Residential development standards, Lismore DCP Chapter 1.

Re-transcribed 2026-08-08 from `documents/dcp/chapter-1-residential-development.pdf`
(56 pages). PLAN.md item 0.6, and the second half of the item 0.5 finding: these
were the two data files Phase 0 never audited, and both turned out to be
invented rather than transcribed.

**Almost none of the previous figures were in the chapter.** Of about nineteen
numbers in the old file, two were recognisably derived from Chapter 1 and even
those had lost the conditions that make them mean anything. The rest collided
with unrelated numbers elsewhere in the document, which is what made them look
plausible:

  * a "0.9m side setback" — Chapter 1's 0.9m is the **small lot housing** side
    setback (A26.3), which applies only on lots under 400m², and separately the
    0.9m x 0.9m *recess in a front fence* (A17.3)
  * a "4.5m front setback to an articulated facade" — the chapter's 4.5m is the
    Health Precinct's non-habitable-room separation for five storey buildings
    (A39). The front setback is **6m** (A1.1), flat
  * "15% deep soil" — the chapter's 15% is **land steeper than 15%**, excluded
    from an open space calculation (A8.1 note)
  * "maximum 50% site coverage" — there is no site coverage control. A7.1
    requires **landscaping and open space over 40% of the site**, which is a
    different measurement taken from the other direction
  * "80m² private open space, minimum dimension 5m" — A8.1 says 80m² with a
    **2.5m** minimum dimension, plus 25m² of functional open space at 4m, and
    only for detached dwellings on lots **under** 400m². Larger lots have no
    specific requirement at all
  * battle-axe setbacks, building envelopes at 45°, garage widths as a
    proportion of frontage, driveway widths — **none of these appear anywhere in
    Chapter 1**

**The chapter's structure is the thing the old file most misrepresented, and it
changes what an answer from it can claim.** Chapter 1 is written as Performance
Criteria with Acceptable Solutions against them. §1.3: meeting the Acceptable
Solution is *one* way to satisfy the criterion, and "alternatively, Council may
be prepared to approve development proposals that demonstrate consistency with
Design Principles and Performance Criteria". So a figure here is a safe harbour,
not a limit — reporting "you must have a 6m setback" is wrong in a way that
matters, because it forecloses an argument the chapter explicitly invites. Every
entry therefore carries its Performance Criterion alongside the number.

Note also what §4.1 does **not** set: there is no side or rear setback for an
ordinary lot. A4.2 handles it by performance — "progressively set back from
boundaries as building height increases" — and the only numeric side setback in
the chapter is small lot housing's. `NOT_SET_BY_THIS_CHAPTER` records that and
the other gaps, because "the DCP does not set one" is a real answer to a
question applicants ask constantly, and inventing 0.9m to fill it is what the
old file did.

`scripts/audit_standards.py` checks every stored string still appears in the
chapter, the same guarantee `audit_flood.py` and `audit_signage.py` give.
"""

CHAPTER = "DCP Chapter 1"
SOURCE_PDF = "documents/dcp/chapter-1-residential-development.pdf"

# §1.3, verbatim. The sentence that makes every figure below a safe harbour
# rather than a limit.
HOW_THIS_CHAPTER_WORKS = {
    "verbatim": (
        "The specific requirements for residential development addressed by this chapter are "
        "divided into primary Elements which comprise specified Design Principles, Performance "
        "Criteria and Acceptable Solutions."
    ),
    "alternative_verbatim": (
        "Development proposals must be consistent with the Design Principles outlined in Part 3 "
        "of this document. This can be achieved by meeting the Acceptable Solution or "
        "alternatively, Council may be prepared to approve development proposals that "
        "demonstrate consistency with Design Principles and Performance Criteria."
    ),
    "what_it_means": (
        "An Acceptable Solution is a deemed-to-comply figure, not a maximum or a minimum you are "
        "held to. A proposal that misses one is not non-compliant — it has to be argued against "
        "the Performance Criterion instead, which the chapter expressly provides for. Say which "
        "you are doing in the Statement of Environmental Effects."
    ),
    "early_contact_verbatim": (
        "Applicants are strongly encouraged to contact Council early in the design process as "
        "early engagement assists in minimising conflicts through the development application "
        "process and reduces assessment timeframes."
    ),
    "section": "1.3",
    "page": 3,
}

# §2. Only the terms Chapter 1 defines itself — "Terms not defined in LEP 2012
# dictionary are defined in this section."
DEFINITIONS = {
    "deep_soil_zone": (
        "deep soil zone means areas of soil not covered by buildings or structures within a "
        "development that allow infiltration of rainwater to the water table and reduce "
        "stormwater run off."
    ),
    "functional_open_space": (
        "functional open space means the main area of private open space which is part of the "
        "primary open space area located directly accessible to the living area of the dwelling "
        "and capable of being landscaped or screened to ensure that the area has privacy from "
        "adjoining development."
    ),
    "primary_open_space": (
        "primary open space means the part of the site or building which is designed, or "
        "developed, or capable of being maintained and used as lawn, courtyard or planted "
        "gardens and is available for use and enjoyment of the occupants of the development"
    ),
    "medium_density": (
        "medium density means a residential development containing three or more dwellings on "
        "one site such as residential flat buildings and multi-dwelling housing."
    ),
    "expanded_dwelling": (
        "expanded dwelling means an dwelling comprising a main building and a maximum of three "
        "habitable outbuildings."
    ),
    "small_lot": "small lot means an allotment of land which has a minimum area of less than 400m2.",
    "small_lot_housing": (
        "small lot housing – means dwellings on allotments that have a minimum area of less than "
        "400m2."
    ),
    "common_open_space": (
        "common open space means the open space area which is available and accessible to all "
        "residents."
    ),
    "adaptable_housing": (
        "adaptable housing is housing designed for people with changing physical needs as they "
        "grow older or lose full mobility."
    ),
    "north": (
        "north refers to true solar north. This direction is taken to be 11o west of magnetic "
        "north in the Lismore City area."
    ),
    "rms_roads": (
        "roads and maritime services (RMS) roads are the Bruxner Highway, Bangalow Road, Nimbin "
        "Road, Blue Knob Road, Dunoon Road, Rous Road, Coraki Road, Eltham Road)"
    ),
}

ELEMENTS = {
    "setbacks": {
        "section": "4.1",
        "title": "Setbacks, Design, Density and Height",
        "page": 8,
        "performance_criteria": {
            "P1": (
                "Development is sited and designed taking into account: a) the topography of the "
                "land; b) the relationship to adjoining premises and the street; c) the locality "
                "that establishes the overall setting of the site; d) the character and scale of "
                "surrounding development; e) maximising solar access to both indoor and outdoor "
                "livings area, allowing sufficient space for landscaping and maintaining privacy "
                "and amenity; f) the compatibility of the garage and carport with the dwelling."
            ),
        },
        "acceptable_solutions": {
            "A1.1": (
                "Buildings, (not including earthworks, retaining walls and fencing elements), are "
                "setback 6m from the boundary fronting the street in zones R1, R2, R3 and RU5."
            ),
            "A1.2": (
                "For a corner allotment in zones R1, R2, R3 and RU5, the setback is 6m from the "
                "primary street and 3m from the secondary road."
            ),
            "A1.3": (
                "Buildings on allotments with rear lane frontage must be sufficiently setback to "
                "ensure vehicular parking can be accommodated completely off road. Where the "
                "garage is perpendicular to the lane, it must be setback 5.5m."
            ),
            "A1.4": (
                "Buildings are setback 15m from the boundary fronting the street in zones RU1, R5 "
                "and E3 unless A1.5 applies."
            ),
            "A1.5": (
                "Buildings in zones RU1, R5 or E3 with frontage to RMS roads (see Definitions) "
                "are to be setback 28m from the boundary fronting the street."
            ),
        },
        # A1.4 reaches E3 Productivity Support, a business zone. It is the only
        # numeric setback in this chapter that applies outside the residential
        # and village zones, and no other tool here carries it.
        "front_setback_by_zone": {
            "R1": "6m", "R2": "6m", "R3": "6m", "RU5": "6m",
            "RU1": "15m, or 28m with frontage to an RMS road",
            "R5": "15m, or 28m with frontage to an RMS road",
            "E3": "15m, or 28m with frontage to an RMS road",
        },
    },
    "density": {
        "section": "4.1",
        "title": "Density (multi dwelling housing)",
        "page": 8,
        "performance_criteria": {
            "P3": (
                "Dwelling density and site coverage are consistent with the character and amenity "
                "of the residential area."
            ),
        },
        "acceptable_solutions": {
            "A3": (
                "Provided the development satisfies other criteria in section 4, the dwelling "
                "density per site area for multi dwelling housing shall not exceed the following:"
            ),
        },
        # Site area required *per dwelling*, so a larger figure is a lower
        # density. Read from the A3 table.
        "site_area_per_dwelling": {
            "1 bedroom": {"lot_under_1200m2": "200m2", "lot_over_1200m2": "180m2",
                          "verbatim_row": "1 bedroom 200m2 180m2"},
            "2 bedroom": {"lot_under_1200m2": "250m2", "lot_over_1200m2": "220m2",
                          "verbatim_row": "2 bedroom 250m2 220m2"},
            "3 bedroom": {"lot_under_1200m2": "300m2", "lot_over_1200m2": "270m2",
                          "verbatim_row": "3 bedroom 300m2 270m2"},
        },
    },
    "building_height": {
        "section": "4.1",
        "title": "Building Height, Bulk and Scale",
        "page": 10,
        "performance_criteria": {
            "P4": (
                "The development is of a height that will ensure: Consistency with the prevailing "
                "height of other buildings in the vicinity; Adequate daylight for habitable rooms "
                "and open space areas; Minimal overshadowing and overlooking of adjoining "
                "premises; Compatibility with the local streetscape and character of the area;"
            ),
        },
        "acceptable_solutions": {
            "A4.1": (
                "Buildings comply with the building height controls specified in the Lismore "
                "Local Environmental Plan 2012."
            ),
            "A4.2": (
                "Development is progressively set back from boundaries as building height "
                "increases so as to minimise adverse impacts on existing or future development "
                "on adjoining properties by way of overshadowing, reducing privacy or "
                "unreasonably obstructing views."
            ),
        },
        # The DCP sets no height number of its own; A4.1 defers to the LEP map,
        # which is site-specific. lookup_site_constraints reads it by address.
        "the_number_is_not_here": (
            "Chapter 1 sets no height limit. A4.1 defers to the Height of Buildings Map in LEP "
            "2012, which varies block by block — lookup_site_constraints reads it for an address. "
            "8.5m is common across the LGA but is not a DCP control and is not universal."
        ),
    },
    "visual_privacy": {
        "section": "4.2",
        "title": "Visual Privacy",
        "page": 14,
        "performance_criteria": {
            "P5": (
                "Overlooking of the internal living areas of adjacent dwellings is to be "
                "minimised by: careful building layout; spatial separation of buildings; location "
                "and design of windows and balconies; and the use of screen walls, fences and "
                "landscaping."
            ),
        },
        "acceptable_solutions": {
            "A5.1": (
                "Maintain visual privacy between dwellings by: offsetting windows alongside "
                "boundaries; installing windows at different heights to the adjoining buildings; "
                "installing garden beds along the boundary line which are mass planted with "
                "appropriate trees and shrubs that also define usable open space."
            ),
            "A5.2": (
                "A courtyard with a depth of at least 10 metres is maintained between dwellings "
                "in multi dwelling housing developments where courtyards face each other."
            ),
            "A5.3": (
                "Where habitable room windows look directly at habitable room windows in an "
                "adjacent dwelling, privacy is protected by: (a) window sill heights being a "
                "minimum of 1.5 metres above floor level; and/or (b) fixing permanent screens "
                "that are durable and have a maximum of 25% openings; and/or (c) installing "
                "obscure glass; and/or (d) if at ground level, screen fencing to a maximum height "
                "of 1.8 metres."
            ),
            "A5.4": (
                "Decks, verandahs, terraces, balconies and other external living areas within 4 "
                "metres from a side or rear boundary are screened with a maximum opening of 25%."
            ),
        },
    },
    "acoustic_privacy": {
        "section": "4.3",
        "title": "Acoustic Privacy",
        "page": 17,
        "performance_criteria": {
            "P6": (
                "The siting of buildings, room layout, window and wall location and the use of "
                "materials minimise impacts from external noise sources."
            ),
        },
        "acceptable_solutions": {
            "A6.1": "Garages and driveways are located away from bedrooms of adjacent dwellings.",
            "A6.2": (
                "No common driveway is located within 2 metres of the window of a habitable room "
                "unless there is screening at least 1.8 metres high between the window and the "
                "driveway or a vertical separation of at least 1.5 metres between the driveway "
                "level and the window sill."
            ),
        },
    },
    "open_space_and_landscaping": {
        "section": "4.4",
        "title": "Open Space and Landscaping",
        "page": 19,
        "performance_criteria": {
            "P7": (
                "Adequate open space and landscaped area is provided on site: to cater for the "
                "requirements of occupants for relaxation, dining, entertainment, recreation and "
                "children's play;"
            ),
            "P8": (
                "Open space for each dwelling shall be well defined, functional, usable and "
                "accessible from living areas with access to natural light."
            ),
        },
        "acceptable_solutions": {
            "A7.1": (
                "Landscaping and open space shall comprise 40% of the site. 70% of the "
                "landscaping and open space area is to be permeable."
            ),
            "A7.2": (
                "Any area of less than 1 m2 or 1 m in width is not counted in the required "
                "landscaped and open space area."
            ),
            "A8.1": (
                "The following minimum areas of total and functional open space are provided."
            ),
            "A8.2": (
                "Multi dwelling housing, shop top housing or residential flat buildings with no "
                "direct ground level access to living areas shall provide a 10m2 screened balcony "
                "or roof garden with a minimum dimension of 2.5m."
            ),
            "A9.1": (
                "Functional open space shall be landscaped, fenced or screened where necessary to "
                "maintain privacy and ensure amenity."
            ),
        },
        # The A8.1 table. "Primary" and "total" mean the same thing — the
        # chapter says so in the Figure 11 caption.
        "private_open_space": {
            "detached dwelling on a lot over 400m2": {
                "primary_area": None,
                "verbatim": (
                    "There is no specific requirement; however all dwellings shall have suitable "
                    "private open space areas which are functional."
                ),
            },
            "detached dwelling on a lot under 400m2": {
                "primary_area": "80m2", "primary_dimension": "2.5m",
                "functional_area": "25m2", "functional_dimension": "4m",
                "verbatim_row": "Detached dwellings (on lots < 400m2) 80m2 2.5m 25m2 4m",
            },
            "secondary dwelling": {
                "primary_area": "35m2", "primary_dimension": "3m",
                "functional_area": "15m2", "functional_dimension": "2.5m",
                "verbatim_row": "Secondary dwelling 35m2 3m 15m2 2.5m",
            },
            "dual occupancy, attached or semi-detached dwelling, multi dwelling housing, "
            "residential flat building": {
                "primary_area": "35m2", "primary_dimension": "3m",
                "functional_area": "16m2", "functional_dimension": "4m",
                "verbatim_row": "35m2 3m 16m2 4m",
            },
            "multi dwelling housing or residential flat building above ground level": {
                "primary_area": "20m2", "primary_dimension": "2.5m",
                "verbatim": (
                    "For units above the ground floor, 20m2 of private open space per unit shall "
                    "be provided at ground floor"
                ),
            },
        },
        "excluded_from_the_calculation": (
            "The calculation of open space shall not include areas used for vehicle parking or "
            "movement, setback areas less than 1 metres in width, land steeper than 15% or any "
            "area occupied by a rainwater tank."
        ),
        "primary_open_space_is": (
            "Primary open space is the balance of area outside of the building envelope, "
            "hardstand and areas less than 2.0m wide or steeper than 15%."
        ),
    },
    "earthworks": {
        "section": "4.5",
        "title": "Earthworks, Retaining Walls and Erosion controls",
        "page": 23,
        "performance_criteria": {
            "P10": (
                "Earthworks and retaining walls:- a) Preserve the stability of the site and "
                "adjoining land; b) Minimise site disturbance from excessive cut and fill."
            ),
        },
        "acceptable_solutions": {
            "A10.1": (
                "The maximum height for cut and fill is 1.8 metres above or below natural ground "
                "level except where it is incorporated into the dwelling structure."
            ),
            "A10.2": (
                "The height of retaining walls is limited to 1.8 metres above natural ground "
                "level and constructed of materials that complement the streetscape and site "
                "landscaping."
            ),
            "A10.3": (
                "All areas containing cut or fill are to be drained, stabilised and landscaped to "
                "prevent surface erosion."
            ),
            "A10.4": (
                "If the cut or fill is located less than 1m from any boundary, a maximum depth of "
                "1m is permitted. Any retaining wall above 600mm must be suitably designed and "
                "approved prior to construction so that structural integrity can be confirmed."
            ),
            "A10.5": (
                "The horizontal distance between a cut and a filled area shall be equal to the "
                "height or depth of the fill or cut, whichever is the greater."
            ),
            "A10.6": (
                "Earthworks and retaining walls are located at least 1.5m from any sewer main or "
                "Council stormwater drainage line, or the equivalent invert depth of the main or "
                "line, whichever is the greater."
            ),
            "A10.7": "Earthworks and retaining walls do not encroach into any registered easement.",
            "A11": (
                "Soil erosion and sediment controls are in accordance with Guidelines for the "
                "Control of Erosion and Sedimentation on Building and Development Sites - Lismore "
                "City Council."
            ),
        },
        "engineer_note": (
            "Retaining walls in excess of 1.2m require a report from a suitably qualified "
            "structural engineer."
        ),
    },
    "car_parking": {
        "section": "4.6",
        "title": "Off Street Car Parking, Carports, Garages, Outbuildings and Driveways",
        "page": 28,
        "performance_criteria": {
            "P12": (
                "The development shall contain adequate visitor and resident car parking, taking "
                "into account:"
            ),
            "P14": (
                "Carports, garages and outbuildings do not dominate the streetscape and are "
                "compatible with the building height, roof form, detailing, materials and colours "
                "of the main building."
            ),
        },
        "acceptable_solutions": {
            "A12.1": (
                "For single dwellings two (2) off street car parking spaces are provided. Car "
                "spaces are to comply with applicable front building line (front setback). "
                "However, where the building line is <6m, parking spaces must be at least 5.5 "
                "metres from the front boundary."
            ),
            "A12.2": (
                "For attached and detached dual occupancies of up to 125m² total combined floor "
                "space, one (1) level off street car parking space is provided for each dwelling "
                "behind the building line. Where the total combined floor area of the dual "
                "occupancy exceeds a total of 125m², two (2) off street car parking spaces per "
                "unit are provided."
            ),
            "A12.3": (
                "Where only one (1) car parking space is to be provided, it must be under cover. "
                "Where more than one (1) parking space is to be provided, at least one (1) is to "
                "be under cover."
            ),
            "A13.1": (
                "Each dwelling unit is to have one covered parking space, located as close as "
                "practicable to the dwelling unit."
            ),
            "A13.2": (
                "Where six or more visitor spaces are required, the spaces shall be located in "
                "groups of three and not scattered individually around the development. All "
                "visitors' spaces shall be clearly marked."
            ),
            "A12.4": (
                "The number of off street parking spaces for multi-dwelling housing shall be:"
            ),
            "A14.1": (
                "Detached carports, garages and outbuildings that are in front of the dwelling in "
                "Residential R1, R2, R3 and RU5 zones, shall not have a floor area greater than "
                "60m² and an external wall height of 3.3 metres above natural ground."
            ),
            "A14.2": (
                "On steeply sloping sites (over 20%), it may be better to provide a detached "
                "garage or carport to reduce the length of steep drive and reduce the amount of "
                "cut and fill required."
            ),
            # The chapter's own words. Worth carrying rather than omitting: it
            # tells an applicant the criterion has to be argued on its merits,
            # which is different from there being no criterion.
            "A15": "No acceptable solution.",
            "A16.1": "Vehicles can safely enter and reverse from a lot in a single movement.",
            "A16.2": (
                "Where a street carries more than 5000 vehicles per day all vehicles can move in "
                "a forward direction when entering or leaving the site."
            ),
            "A16.3": (
                "The maximum gradient for driveways is 25% with a maximum change in grade of "
                "12.5%."
            ),
            "A16.4": (
                "Where lots fall steeply below street level, the garage or carport is constructed "
                "closer to the street to reduce the need for steeply sloping driveways and large "
                "amounts of cut and fill."
            ),
            "A16.5": (
                "Driveways are integrated with the site using landscaping and appropriate "
                "drainage and erosion control measures, particularly on steep slopes."
            ),
            "A16.6": (
                "The location and design of driveways is consistent with the Subdivision and "
                "Infrastructure Chapters of this Development Control Plan, the Northern Rivers "
                "Design Manual and the Lismore City Council Design and Construction Specification "
                "Vehicular Access Policy."
            ),
        },
        # A12.4. These agree with data/parking.py's Chapter 7 Schedule 1 rates,
        # which is worth knowing: two chapters set residential parking and they
        # do not conflict.
        "multi_dwelling_rates": {
            "1 bedroom": "1", "2 bedrooms": "1.5", "3 or more bedrooms": "2",
            "visitor": "1 space for each five dwelling units.",
            "verbatim_row": "3 or more 2",
        },
        "cbd_shop_top_note": (
            "Shop top housing in the CBD is not required to provide car parking spaces."
        ),
    },
    "fences": {
        "section": "4.7",
        "title": "Fences",
        "page": 33,
        "exempt_first_verbatim": (
            "The majority of fences in all zones can be constructed as Exempt Development under "
            "the State Environmental Planning Policy (Exempt and Complying Development Codes) "
            "2008 (Codes SEPP) subject to criteria. These provisions are aimed at providing "
            "guidance for fencing that is not permissible as Exempt Development."
        ),
        "zones_verbatim": (
            "The following fencing controls are generally limited to Zones R1, R2, R3, R5 and "
            "RU5."
        ),
        "performance_criteria": {
            "P17.1": (
                "Fences must not: Impair driver or pedestrian visibility at road intersections; "
                "Prevent residents of a dwelling from casually observing the adjacent street;"
            ),
        },
        "acceptable_solutions": {
            "A17.1 front": "Front fence – 1.2m",
            "A17.1 side": "Side fence – 1.2m within the building line setback and 1.8m for the remainder.",
            "A17.1 rear": (
                "Rear Fence – 1.8m, unless the rear fence is the primary frontage and front fence "
                "provisions may apply."
            ),
            "A17.2": (
                "Front and side fences within the building line setback higher than 1.2m but not "
                "higher than 1.8m may be permitted in the following circumstances:"
            ),
            "A17.3": (
                "Any front fence higher than 1.2m must be: Constructed of a mix of materials with "
                "50% transparency and integrated landscaping; or Located not less than 50cm "
                "inside the front boundary with the area in front of the fence to be landscaped; "
                "or Articulated with recessed sections of a minimum 0.9m x 0.9m at a maximum "
                "interval of 5m to allow planning of vegetation."
            ),
            "A18": (
                "Fencing of the secondary frontage will be allowed up to 1.8m high on the "
                "boundary, up to either of the following alignment setbacks from the primary "
                "street: The required building line setback in that location (6m in zones R1, R2, "
                "R3, and RU5; and 15m in Zone R5); or If the existing dwelling is forward of the "
                "established building line setback, in line with the existing dwelling"
            ),
        },
        "front_fence_is": (
            "A front fence is any fence or like barrier erected forward of the building line "
            "setback, whether it is erected on the boundary or not."
        ),
    },
    "service_areas_and_waste": {
        "section": "4.8",
        "title": "Service Areas and Waste Management",
        "page": 35,
        "performance_criteria": {
            "P20": (
                "Site facilities such as waste bin enclosures, storage areas and clothes drying "
                "areas are to be conveniently accessible and visually unobtrusive."
            ),
        },
        "acceptable_solutions": {
            "A20.1": (
                "At least three (3) m2 is provided for each dwelling to accommodate 3 x 240 litre "
                "bins. The storage area is paved and in a location readily accessible to the "
                "waste collection point."
            ),
            "A20.2": (
                "Medium density collective storage areas for waste bins are to be adequately "
                "screened from the street, located behind the front setback and should not cause "
                "odour or noise impacts for neighbours"
            ),
            "A20.4": (
                "A paved and screened drying area of at least 7m2 is provided for each dwelling "
                "unit in medium density development."
            ),
            "A20.3": (
                "Suitable waste collection areas are to be provided for medium density "
                "development and the use of street frontages for large numbers of bins is to be "
                "avoided."
            ),
            "A20.5": "Common television antenna be provided for medium density development",
            "A21.1": (
                "A site waste minimisation and management plan is to be submitted with the "
                "development applications for dwelling houses, semi-detached dwellings and dual "
                "occupancies in accordance with Section 4.1 DCP Chapter 15 Waste Minimisation."
            ),
            "A21.2": (
                "A site waste minimisation and management plan is to be submitted with the "
                "development applications for medium density development in accordance with "
                "Section 4.2 DCP Chapter 15 Waste Minimisation."
            ),
        },
    },
    "orientation_and_shade": {
        "section": "4.9",
        "title": "Orientation, Glazing and Shade Control",
        "page": 37,
        "performance_criteria": {
            "P22": (
                "Development is designed to incorporate passive solar design to maximise winter "
                "sun and summer shade."
            ),
        },
        "acceptable_solutions": {
            "A22.1": (
                "Orientation of the length of the building is between 30° east of north and 15° "
                "west of north where permitted by the configuration of the lot."
            ),
            "A22.2": (
                "For new and infill development maintain at least 3 hours solar access to 50% of "
                "private open spaces of the proposed development, and to 50% of private open "
                "space of adjoining properties, between 9.00am and 3.00pm on June 21."
            ),
            "A22.3": (
                "Locate a living room on the northern side of the dwelling to receive suitable "
                "solar access. Rooms such as bedrooms, bathrooms, toilets and laundries are "
                "located on the southern side to provide buffers to summer heat and/or winter "
                "wind."
            ),
            "A22.4": (
                "Eaves, awnings, pergolas or deciduous vines and trees are used to provide shade."
            ),
            "A23.1": "Windows are located to maximise opportunities for cross ventilation.",
            "A23.2": (
                "Windows of north facing habitable rooms receive at least three hours of sunlight "
                "between 9 am and 3pm on 21 June."
            ),
        },
        "basix_verbatim": (
            "An application for residential development must be accompanied by a NSW Building "
            "Sustainability Index (BASIX) assessment"
        ),
    },
    "on_site_sewage": {
        "section": "4.10",
        "title": "On-Site Sewage and Waste Water Management",
        "page": 40,
        "applies_verbatim": (
            "This Element applies to development applications for residential development on land "
            "that is not connected to Council's reticulated sewerage system. These provisions are "
            "generally limited to rural, large lot residential and village zones with the "
            "exception of Caniaba, Nimbin and North Woodburn within Zone RU5 Village."
        ),
        "performance_criteria": {
            "P24": (
                "On-site sewage and waste water generated from the dwelling is treated so that:- "
                "a) Public health is maintained"
            ),
        },
        "acceptable_solutions": {
            "A24.1": (
                "In areas not serviced by a reticulated sewerage system, on-site sewage "
                "management systems are installed in accordance with Council's On-Site Sewage and "
                "Wastewater Management Strategy."
            ),
        },
    },
}

# §5 to §10 — housing types with their own provisions on top of the elements
# above. The old file had none of these.
HOUSING_TYPES = {
    "expanded_dwelling": {
        "section": "5",
        "page": 40,
        "what_it_is": (
            "An expanded dwelling is a single dwelling comprising a main building and a maximum "
            "of three (3) habitable outbuildings."
        ),
        "acceptable_solutions": {
            "A25.1": (
                "A maximum of three (3) outbuildings are provided and are connected to the main "
                "building by paths with an all-weather surface."
            ),
            "A25.2": (
                "All buildings are contained within a radius no greater than 20 metres from the "
                "perimeter of the main building."
            ),
            "A25.3": (
                "One outbuilding is limited to a maximum gross floor area of 45m² and the others "
                "are limited to a maximum of 30m²."
            ),
            "A25.4": (
                "Each separate outbuilding may consist of a maximum of two (2) rooms with an "
                "ensuite or bathroom."
            ),
            "A25.5": "No outbuilding is to contain a kitchen.",
            "A25.6": (
                "No more than one laundry is provided, which may be contained in either one of "
                "the outbuildings or the main building."
            ),
        },
    },
    "small_lot_housing": {
        "section": "6",
        "page": 41,
        "what_it_is": (
            "small lot housing – means dwellings on allotments that have a minimum area of less "
            "than 400m2."
        ),
        "acceptable_solutions": {
            "A26.1": (
                "The materials and building form complements the materials and building form of "
                "adjoining dwellings."
            ),
            "A26.2": (
                "Building height is no higher than 8.5 metres as provided in the Lismore Local "
                "Environmental Plan 2012."
            ),
            "A26.3": (
                "The minimum distance between the external building wall and the side boundary is "
                "0.9 metres."
            ),
            "A27.1": (
                "The design of small lot housing demonstrates:- Adequate privacy within and "
                "between dwellings, including adjoining dwellings;"
            ),
            "A27.2": (
                "Development applications for dwellings on lots less than 400m2 to be in "
                "accordance with a Plan of Development approved by Council at subdivision stage."
            ),
            "A27.3": "Vehicle access and car parking to be provided at the rear of the lot.",
        },
        "note": (
            "A26.3 is the only numeric side setback in Chapter 1, and it applies here only — on "
            "lots under 400m². The previous version of this file quoted it as the side setback "
            "for all residential development."
        ),
    },
    "secondary_dwelling": {
        "section": "7",
        "page": 43,
        "zones_verbatim": (
            "Secondary dwellings are permitted with consent under State Environmental Planning "
            "Policy (Housing) 2021 and/ or Lismore LEP 2012 in the R1 General Residential, R2 Low "
            "Density Residential, R3 Medium Density Residential, R5 Large Lot Residential and RU5 "
            "Village zones."
        ),
        "max_floor_area_verbatim": (
            "The maximum gross floor area under the LEP is whichever of the following is greater: "
            "a) 60m2 b) 25% of the total floor area of the principal dwelling"
        ),
        "cannot_be_varied_verbatim": (
            "The floor area is a development standard under LEP clause 5.4(9). This maximum floor "
            "area cannot be increased in accordance with LEP clause 4.6(8)(c)."
        ),
        "site_area_and_parking_verbatim": (
            "The SEPP provides for a minimum site area of 450m2 and additional car parking is not "
            "mandatory."
        ),
        "complying_development_verbatim": (
            "Secondary dwellings may also be Complying Development under the Housing SEPP in "
            "certain circumstances."
        ),
        "note": (
            "The floor area cap is the one development standard in this chapter that clause 4.6 "
            "cannot be used to vary — the chapter says so directly. An applicant who plans to "
            "argue their way past 60m² needs to know that before designing, not after."
        ),
    },
    "shop_top_housing": {
        "section": "8",
        "page": 45,
        "what_it_is": (
            "Shop top housing refers to one or more dwellings located above ground floor retail "
            "or business premises."
        ),
        "acceptable_solutions": {
            "P30.1": (
                "Each dwelling shall have direct unrestricted access that is separate from the "
                "retail or business premises."
            ),
            "A31.1": (
                "Private open space, either at ground level or in the form of a balcony must be "
                "at least 20m² and directly accessible from the living area."
            ),
            "A32.1": (
                "The impact of external noise is minimised by locating bedrooms away from noise "
                "sources."
            ),
            "A32.2": "The dwelling contains sound attenuation measures.",
            "A33.1": (
                "Each dwelling shall have its own amenities, separate from the commercial or "
                "retail use."
            ),
            "A33.2": (
                "Dwellings with access to ground level private open space shall be provided a "
                "screened clothes drying area."
            ),
            "A33.4": (
                "Each dwelling shall have convenient access to a mail box and a lockable storage "
                "facility."
            ),
        },
        "note": (
            "The one housing type in this chapter a business is likely to be building: a shop "
            "owner putting a flat above the premises. Car parking is not required for shop top "
            "housing in the CBD (§4.6, A12.4 note)."
        ),
    },
    "adaptable_housing": {
        "section": "9",
        "page": 45,
        "acceptable_solutions": {
            "A34.1": (
                "One adaptable dwelling per five dwellings is provided for developments with more "
                "than five dwellings."
            ),
            "A34.2": (
                "Adaptable housing is to be consistent with Australian Standard 4299-1995 – "
                "Adaptable Housing."
            ),
        },
    },
    "rural_dual_occupancy": {
        "section": "10",
        "page": 46,
        "lep_clause": "Clause 4.2C of the Lismore LEP allows for dual occupancies within the RU1 Primary Production Zone.",
        "provisions": [
            (
                "Dwellings should be clustered within the same general vicinity and/or around "
                "other existing buildings such as farm sheds in order to minimise the footprint "
                "of the residential use of agricultural land and to reduce the likelihood of land "
                "use conflict with adjoining properties."
            ),
            (
                "A single driveway to both dwellings is preferred in order minimise the footprint "
                "of driveways on the agricultural use and scenic amenity of the land."
            ),
        ],
    },
}

# §11. Its own controls, and the only part of Chapter 1 that speaks to
# non-residential development — which is why it is carried in a file this
# repository's audience might otherwise have no reason to open.
HEALTH_PRECINCT = {
    "section": "11",
    "page": 46,
    "boundary_verbatim": (
        "The Lismore Health Precinct comprises the area surrounding the Lismore Base Hospital, "
        "generally as bounded by: Brewster Street to the west; Orion Street to the north; Hunter "
        "Street, Bent Street and Rotary Park Reserve to the east; and McKenzie Street and Uralba "
        "Street to the south."
    ),
    "why_it_differs_verbatim": (
        "These changes enable four and five storey buildings to be erected in parts of the "
        "Precinct, as compared to the typical 8.5m (2 storey) height control across most of the "
        "Lismore LGA"
    ),
    "one_and_two_storeys_verbatim": (
        "For 1 and 2 storey residential development in the Health Precinct, the general "
        "provisions of Chapter 1 Residential Development apply."
    ),
    "taller_residential": {
        "A35": (
            "The planning provisions contained within the Apartment Design Guide are complied "
            "with, particularly those contained within Part 3 'Siting the Development' and Part 4 "
            "'Designing the Development'."
        ),
        "A36": "The site has an area of at least 1200m2.",
        "A38": "Deep soil zones on site meet the following minimum requirements:",
        "A37.1": "The development setback shall be 6 metres.",
        "A37.2": (
            "For a corner allotment the setback is 6m from the primary street and 4m from the "
            "secondary road."
        ),
        "A40.1": (
            "Buildings are designed to provide a 3 storey presentation to the street, with the "
            "4th and/or 5th storey set back at least 3m from the front building elevation"
        ),
        "A40.2": (
            "The development is provided as a series of buildings, rather than one large building."
        ),
        "A41.1": (
            "Roof structures form part of the building elevation when viewed from the street and "
            "include pitched, hipped and gabled elements, clad with low reflective materials."
        ),
        "A41.2": (
            "A variety of building materials are incorporated into the design, including masonry "
            "brick and lightweight cladding materials such as weatherboard."
        ),
        "A41.3": (
            "Buildings address the public street, with ground floor units provided with direct "
            "pedestrian access from the street."
        ),
        "A41.4": "Vehicle and pedestrian points of entry are separated.",
        "A41.5": (
            "Windows and deep balconies and / or decks are provided facing the public street."
        ),
        "A41.6": (
            "The front building setback is landscaped with soft landscaping and includes trees "
            "for shade and screening."
        ),
        "A43.1": (
            "Carparking areas are provided either at the rear of the site or integrated into the "
            "building form via under croft parking."
        ),
        "A43.2": "Car parking access is provided via integrated access points.",
        "A43.3": "No car parking is provided within the front building setback.",
        "A44": (
            "Road standard along the frontage must meet the requirements set out in Chapters 5A, "
            "5B and 6 of the DCP respectively."
        ),
    },
    # A39 / A55. These are the figures the old file mistook for ordinary front
    # and side setbacks.
    "building_separation": {
        "verbatim_intro": (
            "Minimum separation distances from buildings to the side and rear boundaries are as "
            "follows:"
        ),
        "rows": {
            "Up to 12m (4 storeys)": {"habitable_rooms_and_balconies": "6m",
                                      "non_habitable_rooms": "3m",
                                      "verbatim_row": "Up to 12m (4 storeys) 6m 3m"},
            "Up to 16m (5 storeys)": {"habitable_rooms_and_balconies": "9m",
                                      "non_habitable_rooms": "4.5m",
                                      "verbatim_row": "Up to 16m (5 storeys) 9m 4.5m"},
        },
        "source": "Apartment Design Guideline",
        "applies_to": (
            "Buildings of three or more storeys in the Health Precinct only. The chapter notes "
            "that for buildings less than 2 storeys, the ordinary residential setbacks apply."
        ),
    },
    "non_residential": {
        "A45.1": (
            "Roof structures form part of the building elevation when viewed from the street and "
            "include pitched, hipped and gabled elements, clad with low reflective materials."
        ),
        "A45.2": (
            "A variety of building materials are incorporated into the design, including masonry "
            "brick and lightweight cladding materials such as weatherboard."
        ),
        "A45.3": (
            "Buildings address the public street, with any ground floor commercial units provided "
            "with direct pedestrian access from the street."
        ),
        "A45.4": "Vehicle and pedestrian points of entry are separated.",
        "A45.5": (
            "Windows and deep balconies and / or decks are provided facing the public street."
        ),
        "A45.6": (
            "The front building setback is landscaped with soft landscaping and includes trees "
            "for shade and screening."
        ),
        "A46.1": "Development setback shall be 6 metres.",
        "A46.2": (
            "For a corner allotment the setback is 6m from the primary street and 4m from the "
            "secondary road."
        ),
        "A45.7": (
            "Fencing in the front setback is residential in scale and form and includes at least "
            "50% visually permeable elements."
        ),
        "A49.1": (
            "At least 3m2 is provided for each 'waste service' to a commercial unit. The storage "
            "area is in a location readily accessible to the waste collection point."
        ),
        "A50.1": (
            "Carparking is provided on site in accordance with the rates and design requirements "
            "of Chapter 7 Off Street Carparking."
        ),
        "A49.2": "Collective storage areas for garbage bins are screened by landscaping or fencing.",
        "A49.3": (
            "The development application is to be accompanied by a Site Waste Minimisation and "
            "Waste Management Plan in accordance with DCP Chapter 15."
        ),
        "A50.2": (
            "Carparking areas are provided either at the rear of the site or integrated into the "
            "building form via under croft parking."
        ),
        "A50.3": "No car parking is provided within the front building setback.",
        "A50.4": "Loading docks and the like are located at the rear or side of the premises.",
        "A51": (
            "Advertising and signage should be in accordance with Chapter 9 - Outdoor Advertising "
            "Structures of the Lismore Development Control Plan."
        ),
        "A52": (
            "Road standard along the frontage must meet the requirements set out in Chapters 5A, "
            "5B and 6 of the DCP respectively."
        ),
        "A53": "The site has an area of at least 1200m2.",
        "A54": "Deep soil zones on site meet the following minimum requirements:",
        "A54.2": (
            "Deep soil zones are provided in locations which assist in buffering the development "
            "from adjoining residential uses."
        ),
        "A56.1": (
            "Buildings are designed to provide a 3 storey presentation to the street, with the "
            "4th / 5th storeys set back at least 3m from the front building elevation."
        ),
        "A56.2": (
            "The development is to give the appearance of a series of buildings, rather than one "
            "large building."
        ),
        "A50.5": (
            "For specialist medical practices 'stacked parking' may be provided for staff working "
            "at the premises only when a parking management plan accompanies the application "
            "which demonstrates that staff can conveniently access these spaces."
        ),
    },
    "apartment_design_guide_verbatim": (
        "For residential developments in the Health Precinct comprising three or more storeys and "
        "that have four or more units, the provisions of State Environmental Planning Policy 65 – "
        "Design Quality of Residential Apartment Development (SEPP 65) and associated Apartment "
        "Design Guide will apply"
    ),
    "sepp_65_note": (
        "SEPP 65 was repealed and its provisions moved into State Environmental Planning Policy "
        "(Housing) 2021. The Apartment Design Guide it refers to remains in force. The chapter's "
        "citation is to the superseded instrument — noted, not corrected, because the current "
        "instrument is not carried in this repository. §1.4 of the same chapter already refers to "
        "the Housing SEPP, so the chapter is inconsistent with itself here."
    ),
}

# The questions applicants actually ask that this chapter does not answer. Every
# one of these had a confident invented figure in the previous version of this
# file, which is why they are named rather than left silent — "the DCP sets no
# figure" is the answer, and it is a different answer from "we don't know".
NOT_SET_BY_THIS_CHAPTER = {
    "side_setback": {
        "the_question": "What is my side setback?",
        "answer": (
            "Chapter 1 sets no numeric side setback for an ordinary lot. A4.2 handles it by "
            "performance instead — development is 'progressively set back from boundaries as "
            "building height increases'. The only figure in the chapter is A26.3's 0.9m, which "
            "applies to small lot housing on lots under 400m². The Codes SEPP sets its own side "
            "setbacks for exempt and complying development, and they are not this chapter's."
        ),
        "previously_claimed": "0.9m single storey, 1.5m upper floors, a 45° building envelope",
    },
    "rear_setback": {
        "the_question": "What is my rear setback?",
        "answer": (
            "Chapter 1 sets none. A4.2 applies, as for side setbacks. The Health Precinct "
            "building separation table (A39) sets rear distances for buildings of three or more "
            "storeys there, and nowhere else."
        ),
        "previously_claimed": "3m for single storey, 6m for two storey",
    },
    "site_coverage": {
        "the_question": "What is my maximum site coverage?",
        "answer": (
            "Chapter 1 sets no site coverage maximum. It controls the same thing from the other "
            "direction: A7.1 requires landscaping and open space to comprise 40% of the site, 70% "
            "of that permeable. P3 mentions site coverage but only as a matter to be consistent "
            "with the character of the area."
        ),
        "previously_claimed": "Maximum 50% in R1/R2/R3",
    },
    "deep_soil_percentage": {
        "the_question": "How much deep soil zone do I need?",
        "answer": (
            "The chapter defines a deep soil zone (§2) and requires one for taller buildings in "
            "the Health Precinct (A38, A54), but the minimum figures are in a table reproduced as "
            "an image from the Apartment Design Guideline, with no readable text. The figure is "
            "not recoverable from this document — the Apartment Design Guide is the source, and "
            "it is not carried here."
        ),
        "previously_claimed": "15% of the site",
    },
    "battle_axe_lots": {
        "the_question": "What setback applies to a battle-axe lot?",
        "answer": (
            "Chapter 1 does not mention battle-axe lots or access handles. A1.3 covers rear lane "
            "frontage, which is a different configuration."
        ),
        "previously_claimed": "5m from the access handle boundary",
    },
    "garage_and_driveway_widths": {
        "the_question": "How wide can my garage or driveway be?",
        "answer": (
            "Chapter 1 sets no width for either. A14.1 caps the floor area of a detached garage "
            "in front of the dwelling at 60m² with a 3.3m wall height, and A16.3 caps driveway "
            "gradient at 25%, but nothing controls width. Chapter 7 and the Vehicular Access "
            "Policy, which A16.6 refers to, are where a width would come from."
        ),
        "previously_claimed": "Garage max 50% of frontage; driveway 3m, or 5.5m dual crossover",
    },
}
