"""Lismore DCP Part B Chapter 6 — Nimbin Village (October 2021).

ROADMAP D3. Transcribed 2026-09-27 from
`documents/dcp/part-b-chapter-6-nimbin-village.pdf`, read end to end first. Every
string under a `verbatim` key, and every element of the lists named in
`QUOTED_LISTS`, is the chapter's own words; anything else (`plain`,
`why_it_matters`) is this repository's guidance and is labelled so by the tool.
`scripts/audit_nimbin.py` checks the quotes, reads the section headings, the
preferred land use lists, the Live / Work labels and every figure off the
document to report anything not carried, and checks the absences recorded in
`NOT_SET_BY_THIS_CHAPTER` are still absent.

Four things decide how this is used, and each is a rule the tool keeps:

  * **The chapter covers Nimbin only, and the zone is not a proxy for it.** RU5
    Village covers other villages too, and the DCP Introduction records that the
    Part B chapters for Dunoon and Clunes were repealed in 2020 — so no other
    village has a Part B chapter at all. Even within Nimbin, the land it applies
    to is drawn on Figure 1, which is an image. The tool therefore asks which
    village; it never infers Nimbin from "RU5".
  * **The precincts are drawn on Figure 2, the heritage conservation area on
    Figure 3 and the flood hazard on Figure 5 — all images.** None can be read
    from an address, so each is an argument, and without it the tool returns
    every option rather than picking one — the discipline `flood.py` applies to
    Chapter 8's Map 1.
  * **"Preferred" is not "permissible".** §2 says the LEP permits a broad range
    of uses in RU5 with consent, and the precincts only say where each is
    *preferred*. Permissibility still comes from `check_permissibility`; a
    non-preferred use is considered only on the §2 test.
  * **This chapter prevails over the rest of the DCP (§1.3(b)).** Its
    recommendation of a 1m freeboard therefore sits over Chapter 8's figure,
    and its rainwater storage minimum applies where there is no reticulated
    supply.
"""

CHAPTER = "Lismore DCP Part B Chapter 6 — Nimbin Village"
EDITION = "October 2021"
SOURCE_DOC = "documents/dcp/part-b-chapter-6-nimbin-village.pdf"
INTRODUCTION_DOC = "documents/dcp/dcp-introduction-may-2025.pdf"

# Lists whose every element is a verbatim quote. The audit walks these by name.
QUOTED_LISTS = frozenset({
    "objectives", "preferred_land_uses", "performance_criteria", "encouraged",
    "discouraged", "controls", "about",
})

# --------------------------------------------------------------------------
# Where the chapter applies, and what else applies instead of it
# --------------------------------------------------------------------------

APPLICATION = [
    {
        "verbatim": "This Chapter applies to lands in Nimbin village as shown on Figure 1.",
        "section": "1.1",
    },
    {
        "verbatim": "This DCP applies to all land in Nimbin zoned RU5 Village as shown in Figure 1.",
        "section": "2",
    },
]

# The figures the tool cannot read, and why each matters.
UNREADABLE_FIGURES = {
    "Figure 1": "Nimbin Village – land to which this chapter applies",
    "Figure 2": "Nimbin Village Precincts",
    "Figure 3": "Nimbin Heritage Conservation Area",
    "Figure 5": "Nimbin Flood Map (Source: BMT WBM 2013)",
}

# From the DCP Introduction: why no other RU5 village has a chapter of its own.
# Checked against INTRODUCTION_DOC by the audit.
OTHER_VILLAGES = {
    "repealed_chapters": {
        "verbatim": "Repeal of Part B DCPs; Chapter 1 Lismore Urban Area Chapter 2 Land at West "
                    "Goonellabah Chapter 7 Dunoon Village Chapter 8 Clunes Village",
        "where": "DCP Introduction, amendment 28 (adopted 14/7/20, in effect 29/7/20)",
    },
    "bexhill_structure_plan": {
        "verbatim": "Amendment to Part A, Chapter 6 Village, Large Lot Residential and Rural "
                    "Subdivision to include a Structure Plan for land at Bexhill Village",
        "where": "DCP Introduction, amendment 25",
    },
    "part_a_applies_everywhere": {
        "verbatim": "Part A of this Plan applies to development on land throughout Lismore City. "
                    "Part B applies to development within specific areas as identified in the "
                    "individual chapters of that Part.",
        "where": "DCP Introduction, Land to which the Plan Applies",
    },
    "plain": "Only Nimbin has a Part B chapter. Dunoon and Clunes each had one until July 2020, "
             "when both were repealed, so a proposal in any other village is assessed against "
             "the Part A chapters alone — the same ones that apply everywhere. Bexhill has a "
             "structure plan, but it lives in Part A Chapter 6 and is about subdivision.",
}

RELATIONSHIP_TO_OTHER_PLANS = {
    "verbatim": "If any inconsistency arises between these documents and this Chapter, the "
                "following applies: a) development standards in the Lismore LEP prevail over any "
                "development controls in this DCP Chapter; and b) the development controls in "
                "this DCP Chapter prevail over any development controls within the rest of the "
                "Lismore DCP.",
    "section": "1.3",
    "plain": "The LEP beats this chapter; this chapter beats every other DCP chapter. Where it "
             "says something different from Chapter 8 (flood) or Chapter 1 (residential), this "
             "chapter's version is the one Council applies in Nimbin.",
}

DEFINITIONS = {
    "verbatim": "A term or word used in this DCP Chapter has the same meaning as Lismore Local "
                "Environmental Plan 2012 unless otherwise defined.",
    "section": "1.4",
}

CHAPTER_OBJECTIVES = {
    "section": "1.2",
    "objectives": [
        "To define precincts and provide guidelines for new developments within the precincts.",
        "To maintain and enhance the unique character and amenity of Nimbin.",
        "To provide guidelines for the conservation of environmental and built heritage values.",
        "To promote development that will enhance climate change resilience.",
        "To ensure development avoids environmentally sensitive areas and areas that are "
        "potential environmental hazards and / or risks.",
        "To ensure new development provides adequate village infrastructure to meet the needs "
        "of the future inhabitants.",
        "To ensure sufficient water supply is available to service new development within the "
        "village.",
        "To ensure the commercial hub, public spaces and residential areas are well planned and "
        "integrated with pedestrian and cycleway facilities.",
        "To identify and protect significant vegetation within the village and to identify "
        "upgrades of Council facilities to improve shade and amenity on public land.",
        "To promote development that seeks to achieve the principles of ecologically "
        "sustainable development.",
    ],
}

# §1.1 — the constraint that shapes everything else in the chapter.
WATER_SUPPLY = {
    "verbatim": "The major constraint on future development within Nimbin village will be the "
                "secure supply of potable water from Mulgum Creek and the DE Williams Dam. Without "
                "an additional source of water being identified, Council cannot guarantee a secure "
                "yield through its reticulated system and new developments may be required to "
                "supply their own potable water through rainwater collection.",
    "section": "1.1",
    "plain": "Ask early whether the site has a reticulated water supply that Council will "
             "commit to the proposal. A food business uses a lot of water, and the chapter "
             "expressly contemplates new development supplying its own.",
}

# §2 — the rules every precinct is read through.
PRECINCT_RULES = {
    "permissibility": {
        "verbatim": "The Lismore LEP permits (with consent) a broad range of land uses within "
                    "the RU5 zone. This DCP nominates several different precincts that identify "
                    "where certain types of land uses are 'preferred' and provides planning "
                    "controls and guidelines for each of those precincts.",
        "section": "2",
        "plain": "Whether a use is allowed at all is the LEP's question — ask "
                 "check_permissibility with zone RU5. The precincts only say where each use is "
                 "preferred.",
    },
    "purpose": {
        "verbatim": "Precincts are intended to maintain village amenity and character, ensure "
                    "the commercial hub is contained along Cullen Street, provide employment "
                    "(light industrial) lands on the edge of the village, provide for live / work "
                    "opportunities, and minimise the potential for land use conflict.",
        "section": "2",
    },
    "non_preferred": {
        "verbatim": "A development application for a 'non-preferred' land use will only be "
                    "considered where it can be demonstrated that there is no suitable land "
                    "available within the preferred precinct, provided that the 'non-preferred' "
                    "use is consistent with the objectives for the precinct.",
        "section": "2",
        "plain": "This is the test that matters for a business outside its preferred precinct. "
                 "A shop or cafe away from Cullen Street has to show there is no suitable land "
                 "in the Commercial Precinct, and that it fits the objectives of the precinct "
                 "it is in. Gather that evidence — vacancies, sizes, rents — before lodging.",
    },
    "investigation_area": {
        "verbatim": "Council will consider development applications in this area on the merits "
                    "of the proposal, the availability of the reticulated water supply and ability "
                    "for proposals to provide on-site water supply as well as any other "
                    "constraints of the land.",
        "section": "2",
    },
}

# --------------------------------------------------------------------------
# The precincts (§2.1–§2.6), as Figure 2 draws them
# --------------------------------------------------------------------------

_SUSTAINABILITY = [
    "Sustainability principles are incorporated into the design and life cycle of new "
    "buildings. These principles include:",
    "passive solar design that eliminates or reduces the need for auxiliary heating or cooling,",
    "use of building materials that have a low impact on non-renewable resources, minimise "
    "waste and consider the life cycle of the building.",
    "buildings that provide a high degree of water and energy efficiency.",
]

_RESIDENTIAL_HERITAGE = {
    "applies": {
        "verbatim": "To preserve the unique quality of this area, the following standards and "
                    "guidelines apply to development applications in the Nimbin Conservation "
                    "Area within the Residential Precinct. These standards should be addressed "
                    "in conjunction with the requirements of Part A DCP Chapter 12 – Heritage "
                    "Conservation as relevant to Nimbin.",
        "section": "2.1.2",
    },
    "objectives": [
        "To retain the residential qualities which contribute to the heritage significance of "
        "the Nimbin Conservation Area.",
        "To enable changes to the streetscape and buildings within the conservation area but "
        "only where the proposed changes have been subject to public exhibition and do not "
        "remove or detract from the character, scale, form, and heritage significance of the "
        "conservation area.",
        "To ensure that new buildings are carefully designed to fit in with the streetscape "
        "character and heritage significance of the conservation area.",
        "To encourage the removal and reversal of those components which detract from the "
        "heritage significance of the conservation area.",
    ],
    "controls": [
        "Single storey timber and 'gal iron' residential buildings built between 1910 and 1930 "
        "on a minimum ¼ acre block create the residential character of Nimbin village.",
        "Buildings should not appear so large as to dominate its neighbours,",
        "Large parts of buildings should be stepped back from the street,",
        "The size, shape and pitch of roofs should relate to the main roof or those existing in "
        "the street.",
        "Roof extensions are to relate sympathetically to the original roof in shape, pitch, "
        "proportion and materials.",
        "New buildings are to have roofs that reflect the size, mass, shape and pitch of "
        "neighbouring original roofs.",
        "Replacement roof materials are to match original materials or approved alternative "
        "materials.",
        "Existing original verandahs are to be kept and repaired or reinstated where necessary.",
        "Removal, or infill of verandahs visible from a public place is discouraged.",
        "Verandah additions are to be simple in design and are not to compete with the "
        "importance of the original verandah.",
        "Authentic reconstruction of verandahs is encouraged.",
        "The retention, repair and reconstruction of early garages is encouraged.",
        "New garages and carports are to be located preferably at the rear of the house or at "
        "least 1 metre back from the front wall of the house.",
        "Carports may be permitted forward of the building line where access is not available "
        "to the rear or side of the house.",
        "Garages and carports are to be a simple utilitarian design.",
        "The established pattern of front and side setback should be retained.",
        "New buildings or extensions to existing buildings should not be built forward of the "
        "existing front setback and building line.",
        "Where land slope or the existing building height will be maintained split level "
        "development is permitted, provided the building does not appear as a two-storey "
        "building.",
        "Post supported verandahs, porches and pergolas are appropriate.",
        "Construction should be simply detailed.",
        "Building external materials correct for, or compatible to the period of original "
        "construction should be used. Preferred materials include:",
        "Walls – timber 'feathered' chamferboard,",
        "Roofs – corrugated iron,",
        "Windows – timber framed, for new buildings compatible design metal framed may be "
        "appropriate.",
        "Fence height ranges should be between 750-1400mm.",
        "Fences should not completely obscure buildings.",
        "Fences may be constructed of timber picket, chain or woven wire between timber posts, "
        "hedges alone or in combination with timber posts.",
    ],
}

_COMMERCIAL_HERITAGE = {
    "applies": {
        "verbatim": "The following standards and guidelines apply to development applications in "
                    "the Nimbin Heritage Conservation Area within the Commercial Precinct.",
        "section": "2.4",
    },
    "objectives": [
        "To retain the commercial buildings and streetscape qualities which contribute to the "
        "heritage significance of the commercial area within the Nimbin Heritage Conservation "
        "Area.",
        "To enable changes to the streetscape and buildings within the heritage conservation "
        "area but only where the proposed changes have been subject to public exhibition and do "
        "not remove or detract from the character, scale, form and heritage significance of the "
        "conservation area.",
        "To ensure that where new buildings are constructed, they are carefully designed to fit "
        "in with the streetscape character and heritage significance of the conservation area.",
        "To encourage the removal and reversal of those components which detract from the "
        "heritage significance of the conservation area.",
    ],
    "controls": [
        "Single storey timber and 'gal iron' commercial buildings with post supported verandahs "
        "and simple above awning facades built between 1910 and 1920 create the commercial "
        "character of Nimbin village.",
        "Buildings should not appear so large as to dominate its neighbours,",
        "Large parts of buildings should be stepped back from the street,",
        "The size, shape and pitch of roofs should relate to the main roof or those existing in "
        "the main commercial area.",
        "Roof extensions are to relate sympathetically to the original roof in shape, pitch, "
        "proportion and materials.",
        "New buildings are to have roofs that reflect the size, mass, shape and pitch of "
        "neighbouring original roofs.",
        "Replacement roof materials are to match original materials or approved alternative "
        "materials.",
        "The existing pattern of building setback within the commercial area is to be "
        "maintained. Forecourts and entrance areas are not appropriate located directly onto "
        "Cullen Street as they interrupt the continuity and strength of the streetscape.",
        "Infill development to the rear of the existing shops is encouraged, either as additions "
        "to buildings or with separation for natural light and ventilation.",
        "Development should provide accessways from car parks and consider people with "
        "disabilities.",
        "Building external materials correct for, or compatible to the period of original "
        "construction should be used. Preferred materials include:",
        "Walls – timber 'feathered' chamferboard, small areas of face brickwork, tiles and "
        "rendered masonry,",
        "Roofs – corrugated iron,",
        "Windows – timber framed, for new buildings compatible design metal framed may be "
        "appropriate,",
        "Materials should comply with the Building Code of Australia as appropriate.",
        "Removal of or alteration to original facades and murals is not permitted without "
        "consent of Council.",
        "Retention, repair and restoration of original above awning facades are encouraged.",
        "Retention, repair and restoration of original above awning parapet murals are "
        "encouraged.",
        "The design of new commercial buildings is to include verandahs or awnings, to provide "
        "footpath shelter and consolidate the streetscape.",
        "A parapet should be included on new commercial buildings.",
        "Existing original verandahs are to be kept and repaired or reinstated where necessary.",
        # Sic: "infill or verandahs" — the residential version of this sentence
        # says "infill of verandahs". Quoted as printed.
        "Removal, or infill or verandahs visible from a public place is discouraged.",
        "Verandah additions are to be simple in design and are not to compete with the "
        "importance of the original verandah.",
        "Authentic reconstruction of verandahs is encouraged.",
        "Below awning level, new building work and shop front detail work is to be in sympathy "
        "with, and not detract from the style and character of the building and streetscape.",
        "Reinstatement of original street level facades and post supported verandahs is "
        "encouraged.",
        "Recessed shop entrances are appropriate.",
        "Height of stallboards should be consistent (250-500 mm) with those in the commercial "
        "area.",
    ],
    "why_it_matters": "For a business in a Cullen Street shop this is the part that bites. The "
                      "murals and original facades cannot be removed or altered without "
                      "consent, so a fitout that touches the shopfront, the awning or the "
                      "facade above it needs to be designed against these controls — and LEP "
                      "cl 5.10 still applies over them, which check_da_readiness raises when "
                      "the site is heritage affected.",
}

PRECINCTS = {
    "residential_south_of_sibley": {
        "name": "Residential Precinct — South of Sibley Street",
        "section": "2.1.1",
        "about": [
            "The Residential Precinct comprises two physically distinct areas in age and "
            "character. These are the long-established Nimbin housing areas and the more recent "
            "residential subdivision south of Sibley Street and Rainbow Power extending to Cecil "
            "Street along Alternative Way.",
            "Reticulated water supply to new development in this area will be limited by the "
            "availability of reticulated water supply and, apart from single dwelling houses, "
            "development consent will be contingent on a proposal's ability to provide "
            "sufficient rainwater tank water storage.",
        ],
        "objectives": [
            "Ensure new development has access to sufficient water supply to meet the needs of "
            "occupants.",
            "Maintain and enhance village character and scale in the precinct.",
            "Encourage the construction of a diverse range of housing styles that cater to "
            "residents needs at different stages of their life.",
            "Encourage environmentally sustainable design principles.",
            "Create residential neighbourhoods with suitable village amenities including access "
            "to transport and recreation opportunities close to commercial and industrial areas.",
            "Encourage small-scale home-based business opportunities that do not duplicate or "
            "detract from the commercial precinct and do not impact the amenity of surrounding "
            "residents.",
        ],
        "preferred_land_uses": [
            "dwelling houses",
            "expanded dwellings",
            "dual occupancies",
            "home occupations and home business",
            "bed and breakfast accommodation",
        ],
        "performance_criteria": [
            "The urban design of new buildings should be consistent with the bulk, scale and "
            "character of surrounding development and the Nimbin village.",
            *_SUSTAINABILITY,
            "Where no reticulated water supply is available, the provision of sufficient "
            "rainwater tank supply for potable water is incorporated into the design. Rainwater "
            "tank storage with a minimum of 45,000 litres capacity per standard dwelling, "
            "exclusive of any requirements for bushfire protection, is to be supplied to provide "
            "an adequate potable water supply.",
            "Appropriate landscaping is integrated into new development to enhance the visual "
            "amenity of the streetscape. Landscaping and garden design is to incorporate water "
            "conservation principles and measures.",
        ],
    },
    "residential_character": {
        "name": "Residential Precinct — Residential Character (the historic housing)",
        "section": "2.1.2",
        "about": [
            "In the part of the Residential Precinct characterised by more historic housing the "
            "character and amenity are established by single storey dwellings, predominantly "
            "timber, on allotments generally greater than 1000 m2.",
            "Most of the character part of the Residential Precinct is also located within "
            "Nimbin's heritage conservation area shown in Figure 3.",
        ],
        "objectives": [
            "Maintain and enhance the village character and scale of the precinct.",
            "Conserve the built heritage and streetscape significance of the precinct where it "
            "is located within the Nimbin Conservation Area.",
            "Encourage infill subdivision and development which reflects the character and "
            "scale of adjoining land use and precinct generally.",
            "Encourage the incorporation of energy and resource efficient building design "
            "principles in all residential alterations and additions and new infill "
            "developments.",
        ],
        "preferred_land_uses": [
            "dwelling houses",
            "expanded dwellings",
            "dual occupancies",
            "home occupations and home business",
            "bed and breakfast accommodation",
            "centre based child-care",
            "seniors housing",
            "group homes",
        ],
        "performance_criteria": [
            "Proposed development must respect and complement the existing historical and "
            "architectural characteristics of the precinct. Development applications must "
            "demonstrate:",
            "Character, bulk, scale, and density is compatible with the low-rise nature of "
            "surrounding developments,",
            "Building materials, textures and finishes are compatible with surrounding "
            "developments",
        ],
        "design_guidelines": {
            "encouraged": [
                "Use of 'timber and tin' and Federation Style architecture",
                "Buildings that incorporate frontages such as verandahs, porches and bay windows "
                "that break up the façade and reduce the bulk and scale impact from the street.",
                "Simple roof forms",
                "Pitched, hipped or gabled roofs",
                "Buildings that are designed for the sub-tropical climate that provide good air "
                "flow, are well orientated to utilise passive solar energy for heating and "
                "cooling and incorporate extensive covered outdoor areas.",
                "Windows that utilise moveable screens, shutters or awnings that provide climate "
                "control and an aesthetic element.",
            ],
            "discouraged": [
                "Use of brick and tile concrete slab on ground construction",
                "Modernist architecture with a highly urbanised appearance",
            ],
        },
        "heritage_conservation_area": _RESIDENTIAL_HERITAGE,
    },
    "investigation_area": {
        "name": "Investigation Area — South of Cecil Street",
        "section": "2.2.1",
        "about": [
            "The Investigation Area consists of undeveloped land located south of Cecil Street "
            "and an area south of Mulgum Creek.",
            "however, this land is also nominated as an 'investigation area' as it is highly "
            "constrained by flooding (refer to section 3.1) and is unlikely to support new "
            "development.",
            "Development proposals in this precinct will need to demonstrate how adequate water "
            "will be supplied and appropriately address site constraints such as slope, "
            "flooding, contaminated land, and amenity impacts on adjoining land uses. The "
            "quantity of rainwater tank storage will be determined by the size of dwellings with "
            "a minimum supply of 45,000 litres required for a standard dwelling, exclusive of "
            "any requirements for bushfire protection.",
        ],
        "objectives": [
            "To ensure new development has access to sufficient water supply to meet the needs "
            "of occupants.",
            "To encourage the construction of a diverse range of housing styles that cater to "
            "residents needs at different stages of their life.",
            "To encourage environmentally sustainable design principles.",
            "To create residential neighbourhoods with suitable village amenities including "
            "access to transport and recreation opportunities.",
            "To encourage small-scale home-based business opportunities that do not duplicate or "
            "detract from the commercial precinct and do not impact the amenity of surrounding "
            "residents.",
        ],
        "preferred_land_uses": [
            "dwelling houses",
            "expanded dwellings",
            "dual occupancies",
            "centre based child-care",
            "seniors housing",
            "group homes",
            "home occupations, home business",
            "home industries where that industry will not impact on residential amenity",
            "bed and breakfast accommodation",
        ],
        "performance_criteria": [
            "The design of new buildings should be consistent with the bulk, scale and character "
            "of surrounding developments within the precinct.",
            *_SUSTAINABILITY,
            "Where no reticulated water supply is available, the provision of suitable rainwater "
            "tank supply for potable water is incorporated into the design. Rainwater tank "
            "storage with a minimum of 45,000 litres capacity per standard dwelling, exclusive "
            "of any requirements for bushfire protection, is to be supplied to provide an "
            "adequate potable water supply.",
            "Appropriate landscaping is integrated into new development to enhance the visual "
            "amenity of the streetscape.",
        ],
    },
    "live_work": {
        "name": "Live / Work Precinct",
        "section": "2.3",
        "about": [
            "The Live / Work Precinct has been identified as a location for a specific "
            "purpose-built development where residents can live and undertake their businesses. "
            "Providing workspace within a residence reduces car dependency, promotes "
            "opportunities for start-up businesses and improves housing affordability.",
        ],
        "objectives": [
            "To facilitate the development of a purpose-built mixed-use precinct that "
            "incorporates residential and commercial land uses.",
            "To provide a high quality of urban design that incorporates energy and resource "
            "efficient building design principles",
            "To reduce car dependence and promote start-up businesses that do not duplicate or "
            "detract from the commercial precinct.",
        ],
        "preferred_land_uses": [
            "Mixed-use commercial and residential",
            "Shop Top housing",
        ],
        # Performance Criteria with Acceptable Solutions, the Chapter 1 form. A
        # criterion with "No acceptable solution." is argued on its merits.
        "criteria": {
            "P1": {"topic": "Visual Impact",
                   "verbatim": "P1 Buildings are to be designed in a way that are welcoming and "
                               "do not dominate the streetscape."},
            "A1.1": {"verbatim": "A1.1 Buildings are setback 6m from the front boundary."},
            "A1.2": {"verbatim": "A1.2 High quality, well-articulated front façades are provided "
                                 "that delineate attached ground-level buildings and provide "
                                 "clear entry points."},
            "A1.3": {"verbatim": "A1.3 Building materials are contemporary and incorporate "
                                 "extensive use of glazing to allow for visual interest, natural "
                                 "light and passive solar design."},
            "A1.4": {"verbatim": "A1.4 Roofs are not to have highly reflective surfaces."},
            "A1.5": {"verbatim": "A1.5 Landscaping is incorporated to provide shade and "
                                 "screening."},
            "P2.1": {"topic": "Open Space",
                     "verbatim": "P2.1 The provision of open space for each residential unit "
                                 "shall be well defined, functional, useable, and accessible "
                                 "from living areas with access to natural light."},
            "P2.2": {"verbatim": "P2.2 Any areas of common open space are located to facilitate "
                                 "casual social interaction and provide a focal point for the "
                                 "development."},
            "A2.1": {"verbatim": "A2.1 The minimum size and dimensions of open space areas shall "
                                 "be in accordance with the requirements for secondary dwellings "
                                 "in DCP Chapter 1 (Residential Development)."},
            "A2.2": {"verbatim": "A2.2 No acceptable solution."},
            "P3": {"topic": "Vehicle Access & Parking",
                   "verbatim": "P3 Safe vehicle access and suitable on-site parking is provided."},
            "A3.1": {"verbatim": "A3.1 Vehicle access is provided in accordance with the "
                                 "appropriate Council standard."},
            "A3.2": {"verbatim": "A3.2 A minimum of one covered carparking space is provided for "
                                 "each residential unit."},
            "A3.3": {"verbatim": "A3.3 Public carparking is provided in accordance with DCP "
                                 "Chapter 7 (Off Street Carparking)"},
            "P4": {"topic": "Visual Privacy",
                   "verbatim": "P4 Visual privacy of residential living areas is to be "
                               "maintained by careful design and layout of buildings.",
                   "acceptable_solution": "none"},
            # P5 is split by a page break and the table's repeated header, so it
            # is stored in the two pieces the page actually prints.
            "P5": {"topic": "Service Areas",
                   "verbatim_parts": ["P5 Areas for garbage bin storage and",
                                      "clothes drying are provided without being visually "
                                      "obtrusive."],
                   "acceptable_solution": "none"},
            "P6": {"topic": "Potable Water",
                   "verbatim": "P6 Where no reticulated water supply is available, the "
                               "provision of suitable rainwater tanks for potable water is "
                               "incorporated into the design."},
            "A6.1": {"verbatim": "A6.1 Where no reticulated water supply is available, a "
                                 "rainwater tank/s with a minimum of 45,000 litres capacity per "
                                 "standard dwelling, exclusive of any requirements for bushfire "
                                 "fighting, is to be supplied to provide an adequate potable "
                                 "water supply."},
        },
    },
    "commercial": {
        "name": "Commercial Precinct",
        "section": "2.4",
        "about": [
            "The Commercial Precinct is the hub and the heart at the centre of Nimbin.",
            "The predominant type of commercial building is timber, single storey (at street "
            "level), and painted murals on above awning facades and parapets, with galvanised "
            "iron roofs.",
            "The precinct has considerable streetscape and heritage significance, which warrants "
            "on-going conservation management.",
        ],
        "objectives": [
            "Conserving the streetscape and heritage significance of the precinct.",
            "Encouraging the development of commercial land adjoining the western car parking "
            "area in a co-ordinated manner that provides service vehicle access and public "
            "access to Cullen Street.",
            "Encouraging the development of commercial land adjoining to the east of Cullen "
            "Street in a co-ordinated manner that provides for car parking and service vehicle "
            "access and public pedestrian access to lands to the east of the existing village.",
            "Enhancing and expanding the public domain of Cullen Street with streetscape "
            "improvements.",
        ],
        "preferred_land_uses": [
            "Commercial premises",
            "Restaurants or cafes",
            "Craft studios and art galleries",
            "Medical centres",
            "Entertainment facilities",
            "Markets",
        ],
        "heritage_conservation_area": _COMMERCIAL_HERITAGE,
        "cullen_street": {
            "section": "2.4",
            "controls": [
                "Cullen Street beautification, streetscape and landscape works are to be "
                "generally in accordance with Figure 4.",
                "Pedestrian accesses to and from the western car parking area and Cullen Street "
                "are provided in the following locations:",
                "southern entrance / exit,",
                "Lot B DP 390096 (54 Cullen St),",
                "Lot 2 DP 361154 (68 Cullen St) and",
                "northern entrance / exit.",
                "Council shall seek the provision of legal 'right of footways' over land to "
                "legally enable those pedestrian ways.",
                "The eastern batter of the western car parking area is to be properly retained "
                "and landscaped and suitable provision made for access for cars and small "
                "delivery trucks from the car parking area to the adjoining commercial lands to "
                "the east.",
                "Tree planting within the car parking area is to conform to Chapter 7 (Off "
                "Street Car Parking) of Part A of this DCP.",
                "The Nimbin Parking Strategy 2018 identifies a potential area for the future "
                "expansion of the Western Car Park, which is shown on Figure 6.",
            ],
        },
    },
    "light_industry": {
        "name": "Light Industry Precinct",
        "section": "2.5",
        "about": [
            "This precinct currently includes the service station, the Rainbow Power Company, "
            "Nimbin Furniture and Sculpture and vacant land.",
        ],
        "objectives": [
            "Encouraging the light industrial development of land, which will not compromise "
            "existing light industrial development in the precinct and not affect existing "
            "development in the Commercial Village Precinct.",
            "Enabling the development of lands for uses other than 'preferred uses' where it can "
            "be demonstrated that there is no other suitable alternative site available and that "
            "the proposed use will not detrimentally affect existing light industrial "
            "development.",
            "Requiring new light industrial development to make adequate provision for "
            "landscaping, vegetation conservation and rehabilitation of natural drainage systems",
            "Preserving local residential amenity where existing residential areas abut the "
            "precinct.",
        ],
        "preferred_land_uses": [
            "Light industries",
            "Craft and light manufacturing industries",
            "Plant nurseries",
            "Garden centres",
            "Landscaping material supplies",
            "Vehicle repairs & vehicle body repair workshops",
            "Veterinary hospitals",
        ],
        "performance_criteria": [
            "New developments are in accordance with the relevant sections of DCP Part A Chapter "
            "3 Industrial Development.",
        ],
    },
    "community": {
        "name": "Community Precinct",
        "section": "2.6",
        "about": [
            "It is recognised that there are established commercial uses that are currently "
            "conducted in the Community Precinct.",
            "7 Sibley Street is included in the Heritage Conservation Area, which leads to "
            "heritage conservation considerations for future development.",
            "it is intended that the heritage conservation objectives for development in the "
            "Commercial Precinct will not outweigh objectives for ecologically sustainable "
            "development in the Sustainable Living Hub that includes demonstrating the use of "
            "alternate building materials and technologies that are ecologically sustainable.",
        ],
        "objectives": [
            "To ensure suitable land remains available for passive and active recreational "
            "activities and support the implementation of the Rainbow Road Walking Track.",
            "To add to the visitor experience through provision of high-quality tourism product "
            "that showcases village culture through the Rainbow Road Walking Track and community "
            "precinct generally.",
            "To ensure the ongoing use of the land for community activities.",
            "To ensure future development within the precinct is compatible with existing and "
            "surrounding land uses",
            "To conserve the significance of heritage items and landscapes in the precinct.",
        ],
        "preferred_land_uses": [
            "Provision of new community services and infrastructure",
            "Child-care centres",
            "Community facilities",
            "Respite day care centres",
            "Information and education facilities",
            "Recreation areas",
            "Recreation facilities (indoor and outdoor) that do not interfere with the amenity of "
            "the surrounding area",
        ],
    },
}

# Plain-English names for the precincts, as an applicant or Figure 2 says them.
PRECINCT_SYNONYMS = {
    "south of sibley street": "residential_south_of_sibley",
    "south of sibley": "residential_south_of_sibley",
    "residential character": "residential_character",
    "historic residential": "residential_character",
    "investigation": "investigation_area",
    "south of cecil street": "investigation_area",
    "live work": "live_work",
    "live/work": "live_work",
    "mixed use": "live_work",
    "cullen street": "commercial",
    "main street": "commercial",
    "commercial precinct": "commercial",
    "light industrial": "light_industry",
    "industrial": "light_industry",
    "community precinct": "community",
}

# --------------------------------------------------------------------------
# §3 General provisions — every precinct
# --------------------------------------------------------------------------

FLOOD = {
    "section": "3.1",
    "about": [
        "Nimbin village is bordered by Mulgum Creek to the north which is subject to flooding. "
        "The most contemporary flood hazard analysis was undertaken by BMT WBM in 2013 which "
        "provides a broad indication of flood hazard as shown in Figure 5. For lot scale hazard "
        "definition, refined modelling should be undertaken where required. For determining "
        "minimum fill and floor levels, it is recommended that a 1m freeboard be applied.",
        "The flood hazard mapping does not significantly impact the future growth of Nimbin "
        "with the main area affected by flooding located on the north eastern edge of the "
        "village. This area comprises part of the community precinct, including sports fields "
        "and the Rainbow Road Walking Track and the light industrial and mixed use areas.",
    ],
    "why_it_matters": "The recommended freeboard here is not Chapter 8's figure, and §1.3(b) "
                      "makes this chapter prevail over the rest of the DCP. It is expressed as a "
                      "recommendation for fill and floor levels generally, and as a requirement "
                      "only for residential extensions in the High Flood Hazard area. Ask Council "
                      "which level it will apply before a floor level is designed. The Light "
                      "Industry and Live / Work precincts are the ones the chapter names as "
                      "flood affected.",
    "hazard_categories": {
        "extreme": {
            "name": "Extreme Flood Hazard",
            "section": "3.1.2",
            "controls": [
                "No new buildings or structures of any type are to be permitted in the area "
                "designated as Extreme Flood Hazard in Figure 5.",
            ],
        },
        "high": {
            "name": "High Flood Hazard",
            "section": "3.1.3",
            "residential": {
                "section": "3.1.4",
                "controls": [
                    "No new residential development is permitted in the area designated as High "
                    "Flood Hazard in Figure 4 unless the application is accompanied by a flood "
                    "report prepared by a suitably qualified consultant providing site specific "
                    "detail regarding predicted depths and velocities in the 1 in 100 year Annual "
                    "Recurrence Interval (ARI) flood.",
                    "This report should demonstrate to the satisfaction of Council that the "
                    "flooding characteristics of the site are less hazardous than the criteria "
                    "for depth and velocity adopted for the High Flood Hazard area.",
                    "Where extensions or additions to existing residential development are "
                    "proposed, all habitable floor areas are to be at or above a 1m freeboard, "
                    "except where in the opinion of Council such a floor level is impractical.",
                ],
            },
            "commercial_and_industrial": {
                "section": "3.1.4.1",
                "controls": [
                    "Any development application for new commercial or industrial development is "
                    "to be accompanied by a risk analysis report prepared by a structural "
                    "engineer addressing the design criteria adopted for the building and its "
                    "relative merits in the 1 in 100 year Annual Recurrence Interval (ARI) flood.",
                ],
            },
        },
        "medium": {
            "name": "Medium Flood Hazard",
            "section": "3.1.5",
            "controls": [
                "Any development application for new residential, commercial or industrial "
                "development is to be accompanied by a risk analysis report prepared by a "
                "structural engineer addressing the design criteria adopted for the building and "
                "its relative merits in the 1 in 100 Annual Recurrence Interval (ARI) flood.",
            ],
        },
        "low": {
            "name": "Low Flood Hazard",
            "section": "3.1.6",
            "controls": [
                "The areas designated as 'Low Hazard' refer to flood liable land within the "
                "Probable Maximum Flood (PMF), but outside of the 1 in 100 Annual Recurrence "
                "Interval (ARI) year inundation area.",
                "No development controls apply to residential, commercial or industrial "
                "development within the Low Flood Hazard area.",
            ],
        },
    },
}

FLOOD_HAZARD_SYNONYMS = {
    "extreme flood hazard": "extreme",
    "extreme hazard": "extreme",
    "high flood hazard": "high",
    "high hazard": "high",
    "medium flood hazard": "medium",
    "medium hazard": "medium",
    "low flood hazard": "low",
    "low hazard": "low",
}

SIGNIFICANT_VEGETATION = {
    "section": "3.2",
    "about": [
        "The following table identifies significant vegetation that is not to be ringbarked, cut "
        "down, lopped, removed, injured, or destroyed without the prior consent of Council. Any "
        "development application proposing to remove or disturb vegetation is required to "
        "address the relevant requirements contained in Part A DCP Chapter 14 – Vegetation "
        "Protection.",
    ],
    "plain": "Table 1 lists trees by location (High Street, the showground, the soccer grounds, "
             "Silky Oak Drive, Tareeda Way, 81 Cullen Street and several lots). Read it with "
             "read_dcp_section if the site has large trees.",
}

INFRASTRUCTURE = {
    "section": "3.3",
    "about": [
        "Village infrastructure, including water supply, wastewater disposal, roads, stormwater "
        "drainage, telecommunications and electricity shall be provided in accordance with Part "
        "A Chapter 6 of the DCP, Subdivision and Infrastructure (Village, Large Lot Residential "
        "and Rural).",
    ],
}

# --------------------------------------------------------------------------
# What the audit holds the data to
# --------------------------------------------------------------------------

# Every numbered heading in the chapter body is either cited by a `section`
# above or named here with the reason it is not carried.
SECTIONS_NOT_CARRIED = {
    "1": "Part heading; its sections are carried.",
    "2.1": "Precinct heading; its two parts are carried as residential_south_of_sibley and "
           "residential_character.",
    "2.2": "Precinct heading; its text is carried under investigation_area (§2.2.1).",
    "2.6.1": "Describes the Sustainable Living Hub masterplan at 7 Sibley Street. Its one "
             "development consideration is carried in the Community Precinct's `about`.",
    "2.6.2": "Describes the proposed Rainbow Road Walking Track. No development control.",
    "3": "Part heading; its sections are carried.",
    "3.1.1": "One sentence introducing the hazard categories that follow, which are carried.",
}

# Figures in the chapter deliberately not carried in any quote. Every figure
# with a unit that the document prints must be carried or named here.
FIGURES_NOT_CARRIED = {}

# What Chapter 6 does not set, with what governs instead. The audit checks each
# pattern is still absent from the chapter — a presence check cannot see an
# invention, and these are the figures most likely to be invented.
NOT_SET_BY_THIS_CHAPTER = {
    "building_height": {
        "absent_pattern": r"\d+(\.\d+)?\s?m(etres)?\s+(high|in height|height)|maximum height",
        "what_governs": "The LEP Height of Buildings Map — lookup_site_constraints reads it by "
                        "address. The chapter speaks of single storey character and of split "
                        "levels not appearing as two storeys, but sets no height in metres.",
    },
    "parking_rate": {
        "absent_pattern": r"spaces? per \d|per \d+\s?m2|\d+ spaces",
        "what_governs": "DCP Chapter 7 Schedule 1 — get_parking_rates. The chapter's only "
                        "parking figure is one covered space per residential unit in the Live / "
                        "Work Precinct (A3.2); the Commercial Precinct has no parking rate of its "
                        "own.",
    },
    "site_coverage_or_fsr": {
        "absent_pattern": r"site coverage|floor space ratio|\bFSR\b",
        "what_governs": "Nothing in this chapter. For residential work, Chapter 1's landscaping "
                        "and open space control (get_residential_standards).",
    },
    "side_or_rear_setback_figure": {
        "absent_pattern": r"rear setback|side setback of|\d+(\.\d+)?\s?m(etres)? from the (side|rear)",
        "what_governs": "In the heritage area, 'the established pattern of front and side "
                        "setback should be retained' — a pattern, not a figure. Outside it, "
                        "Chapter 1 (get_setback_requirements).",
    },
}

# Defects in the source text itself, recorded rather than silently corrected.
SOURCE_TEXT_DEFECTS = {
    "3.1.4 cites Figure 4 for the High Flood Hazard area": (
        "Figure 4 is the Nimbin Beautification Plan; the flood map is Figure 5, which §3.1 and "
        "§3.1.2 both cite. Quoted as printed; the tool points at Figure 5."
    ),
    "2.4 'infill or verandahs'": (
        "The residential version of the same sentence (§2.1.2) says 'infill of verandahs'. "
        "Quoted as printed."
    ),
}
