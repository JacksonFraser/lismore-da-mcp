"""Flood controls, Lismore DCP Chapter 8, with the LEP 2012 clauses over them.

Re-transcribed 2026-08-08 from `documents/dcp/chapter-8-flood-prone-lands.pdf`
(11 pages) and `documents/lep/lep-2012-nsw-full.txt`. PLAN.md item 0.5.

**What was here before was not a transcription.** The file asserted a
Flood Planning Level of "1% AEP + 500mm freeboard". §8.2 says the freeboard is
**300mm**, three times, and the chapter says "1 in 100 year ARI" throughout and
never uses "1% AEP" at all. A 200mm error is the difference between a compliant
slab and a non-compliant one, in the LGA that went 14m under in 2022. Two other
fields — a "1% AEP 2090 climate change level (~13.4m)" and a "CBD Development
Exemption Precinct" allowing shop-top housing — appear nowhere in the chapter,
nowhere in the LEP, and nowhere else in `documents/`. They are gone. If they
came from a real Council policy, that policy is not in this repo and has to be
carried before it can be quoted.

Three things reading the chapter properly turned up, none of which the old
one-line-per-development-type model could express:

**The controls are per flood hazard area, and there are five.** Floodway
(§8.4), High Flood Risk (§8.5), Flood Fringe (§8.6), Low Flood Risk (§8.7),
plus CBD Flood Liable, which §8.3 gives the same controls as the Flood Fringe.
Rural land (§8.8) is separate again. They differ sharply: a commercial building
in the High Flood Risk Area needs a mezzanine refuge above the 1-in-500 level
and one in the Flood Fringe does not; Low Flood Risk has no controls at all.
Answering "commercial" with one requirement was wrong four times out of five.

**§8.3 exempts a change of use from the commercial and industrial controls**
in both the High Flood Risk and Flood Fringe areas. That is the single most
valuable sentence in the chapter for this repo's audience, because a change of
use is the commonest business DA there is — and the old data would have told a
café taking over a CBD shop that it needed 25% of its floor area above the
Flood Planning Level. That requirement does not apply to it.

**The area is never inferred.** Map 1 defines the boundaries and is a bitmap on
page 10 with no extractable text — the same wall `parking.py` hit with the CBD
boundary, and it gets the same treatment: `flood_area` is an argument, and
without it every applicable area's controls are returned rather than one being
picked. Zone is not a proxy: the CBD Flood Liable area is drawn on flood
behaviour, not on zoning.

Each area carries controls per development type, verbatim, with the section and
page. `scripts/audit_flood.py` checks every stored string still appears in the
source, the same guarantee `audit_signage.py` gives Chapter 9.

Two staleness notes, flagged rather than corrected, because correcting them
needs a document this repo does not hold:

  * The chapter's controls "apply only where such development is permissible in
    the zone under the Lismore Local Environmental Plan 2000" (§8.3). LEP 2000
    was superseded by LEP 2012 for most of the LGA. The flood controls are
    plainly still applied; the cross-reference is stale.
  * Map 1 and Map 2 were printed in 2007 and 2003, and the modelling behind them
    predates the 2022 flood. LEP 2012 cl 5.21(3)(a) separately requires the
    consent authority to consider projected changes to flood behaviour from
    climate change, which the DCP's fixed levels do not account for.
"""

CHAPTER = "DCP Chapter 8"
SOURCE_PDF = "documents/dcp/chapter-8-flood-prone-lands.pdf"

# §8.2. The two numbers everything else is built from.
FREEBOARD_MM = 300
ARI_500_OFFSET_M = 1.03

DEFINITIONS = {
    "flood_planning_level": {
        "term": "Flood Planning Level",
        "verbatim": (
            "is the equivalent of the 1 in 100 year ARI flood level plus freeboard. 1 in 100 "
            "year ARI flood levels for the Lismore urban area are shown on Map 2. The freeboard "
            "adopted for the purposes of this Plan is 300mm. Therefore the Flood Planning Level "
            "may be calculated by adding 300mm to the 1 in 100 ARI level for the relevant area "
            "as shown on Map 2."
        ),
        "section": "8.2",
        "page": 2,
    },
    "freeboard": {
        "term": "Freeboard",
        "verbatim": (
            "is a factor of safety typically used in relation to the setting of floor levels, "
            "levee crest levels etc. Freeboard provides a factor of safety to compensate for "
            "uncertainties in the estimation of flood levels across the floodplain, such as wave "
            "action, localised hydraulic behaviour and effects such as \"greenhouse\" and climate "
            "change. Freeboard is adopted as 300mm in this Plan."
        ),
        "section": "8.2",
        "page": 2,
    },
    "habitable_floor_area": {
        "term": "Habitable floor area",
        "verbatim": (
            "is that part of a residential development that is used for the purposes of a lounge "
            "or living room, dining room, rumpus room, kitchen, bedroom or workroom."
        ),
        "section": "8.2",
        "page": 2,
        # Worth stating to a business: the term is defined for residential
        # development only, which is why the commercial controls are written
        # against gross floor area instead.
    },
    "flood_compatible_materials": {
        "term": "Flood compatible materials",
        "verbatim": (
            "are materials used in building construction that can withstand inundation without "
            "suffering any form of damage and which can be readily cleaned when floodwaters "
            "subside."
        ),
        "section": "8.2",
        "page": 2,
    },
    "flood_liable_land": {
        "term": "Flood liable land",
        "verbatim": (
            "is synonymous with flood prone land, i.e. land susceptible to flooding by the "
            "probable maximum flood (PMF) event."
        ),
        "section": "8.2",
        "page": 2,
    },
    "floodplain": {
        "term": "Floodplain",
        "verbatim": (
            "is the area of land which is subject to inundation by floods up to and including the "
            "probable maximum flood event, that is all flood prone land."
        ),
        "section": "8.2",
        "page": 2,
    },
    "preferred_excavation_area": {
        "term": "Preferred Excavation Area",
        "verbatim": (
            "is an area within the floodplain in which the greatest flood velocities and flood "
            "gradients are experienced, and where, when fill material is won, the greatest "
            "benefit to floodplain management can be obtained. The identified preferred "
            "excavation area is located at the western end of Three Chain Road and is identified "
            "in the Lismore Floodplain Management Plan."
        ),
        "section": "8.2",
        "page": 2,
    },
    "probable_maximum_flood": {
        "term": "Probable Maximum Flood (PMF)",
        "verbatim": (
            "is the largest flood that could conceivably occur at a particular location, usually "
            "estimated from probably maximum precipitation. Generally, it is not physically or "
            "economically possible to provide complete protection against this event. The PMF "
            "defines the extent of flood prone land, that is, the floodplain."
        ),
        "section": "8.2",
        "pages": [2, 3],
    },
}

# Controls repeated word for word across several areas and development types.
# Stored once so the audit checks one string rather than five copies of it, and
# so a reissued chapter cannot leave four of them updated and one behind.
BULK_FILL = (
    "Bulk fill to within 300mm of finished surfaced level is to be sourced from on-site, from "
    "the preferred excavation area or from another area on the floodplain. Minor increases in "
    "the depth of imported fill will be considered where it can be demonstrated that this is "
    "necessary to complement the design of the footings of a future building. If bulk fill "
    "cannot be obtained on-site, from the preferred excavation area or from another area on the "
    "floodplain, Council may approve fill imported from another source providing a flood impact "
    "assessment has been prepared by a suitably qualified consultant which demonstrates that "
    "the fill will have no adverse effects upon flood levels upstream or on flooding behaviour "
    "on adjacent properties."
)

RISK_ANALYSIS_500_AND_PMF = (
    "A risk analysis report prepared by a structural engineer addressing the design criteria "
    "adopted for the building and its relative merits in each of the 1 in 500 year ARI and PMF "
    "flood events. Such report to be satisfactory to Council."
)

MEZZANINE_REFUGE = (
    "A mezzanine level (with emergency exit for evacuation purposes) above the 1 in 500 yr ARI "
    "flood level as an emergency flood refuge for employees."
)

# §8.5.3 "all other areas" drops the "ARI" from the mezzanine control and
# §8.5.3 measures its 25% against the 1 in 100 year ARI level rather than the
# Flood Planning Level. Both look like drafting slips beside their §8.6
# counterparts, but they are what the chapter says, so they are carried as
# their own strings rather than folded into the constants above.
MEZZANINE_REFUGE_NO_ARI = (
    "A mezzanine level (with emergency exit for evacuation purposes) above the 1 in 500 yr flood "
    "level as an emergency flood refuge for employees."
)

INDUSTRIAL_FILL_SOUTH = (
    "Lots to be filled equivalent to the 1 in 100yr ARI flood level, subject to maintaining "
    "existing flood flow paths. For infill development in existing industrial areas, Council "
    "prefers that lots be filled to a level equivalent to the 1 in 100yr ARI flood level but "
    "will consider on its merits a fill level equivalent to that of surrounding lots or in "
    "accordance with any previous Council consent for filling. Where buildings are constructed "
    "on land that has not been filled to the 1 in 100 yr ARI flood level, an equivalent of at "
    "least 10% of gross floor area is to be at or above Flood Planning Level and those parts of "
    "the building below the 1 in 100 yr ARI flood level are to be constructed of flood "
    "compatible materials. Grading of site fill to street and/or to adjoining property boundary "
    "levels will be permitted where appropriate."
)

SOUTH_LISMORE_REASONING = (
    "South Lismore (south of Hollingworth Creek) is isolated in the event of the South Lismore "
    "levee overtopping and has a lengthy evacuation route via Union Street, the Ballina St "
    "Bridge and Ballina Street or Conway Street to Wyrallah Road."
)

# §8.3. The paragraph that decides whether any of this applies to the reader.
SCOPE = {
    "categories_verbatim": (
        "Areas affected by the various hazard categories are shown on Map 1 - Lismore Flood "
        "Hazard Categories. The four flood hazard categories are:"
    ),
    "fifth_category_verbatim": (
        "A fifth category - CBD Flood Liable, also shown on Map 1, has the same planning "
        "controls as the Flood Fringe Area."
    ),
    "applies_verbatim": (
        "Controls in this Plan are listed for new residential, commercial and industrial "
        "development on flood prone land and apply only where such development is permissible "
        "in the zone under the Lismore Local Environmental Plan 2000."
    ),
    "change_of_use_verbatim": (
        "The controls applying to new commercial and industrial development in the High Flood "
        "Risk Area and the Flood Fringe Area are not applicable where a change of use is "
        "proposed."
    ),
    "minor_extensions_verbatim": (
        "Where minor extensions to the existing floor space are proposed, the proposal will be "
        "considered on its merits."
    ),
    "section": "8.3",
    "page": 3,
}

# Which (area, development type) pairs §8.3 lifts the controls from on a change
# of use. Deliberately a data structure rather than a string match in the
# handler: the exemption is narrow, and reading it wider than it is written
# would tell an applicant a control does not apply when it does.
CHANGE_OF_USE_EXEMPT = {
    ("high_flood_risk", "commercial"),
    ("high_flood_risk", "industrial"),
    ("flood_fringe", "commercial"),
    ("flood_fringe", "industrial"),
    ("cbd_flood_liable", "commercial"),
    ("cbd_flood_liable", "industrial"),
}

ALL_DEVELOPMENT_CONTROLS = {
    "surveyor_certificate": (
        "Where a minimum floor level is specified, a certificate from a registered surveyor will "
        "be required certifying that the floor has been constructed to the required level."
    ),
    "structural_adequacy": (
        "All applications involving new building work are to be accompanied by a certificate of "
        "structural adequacy prepared by a qualified structural/civil engineer stating that the "
        "building has been designed to withstand structural damage from the forces of "
        "floodwaters and associated debris."
    ),
    "non_habitable_below_fpl": (
        "For non-habitable floors constructed below the Flood Planning Level, the applicant will "
        "be required to demonstrate that: a) the new structure will not have an adverse affect "
        "upon the existing flow of floodwaters, and b) that all materials used below the Flood "
        "Planning Level are flood compatible."
    ),
}

# §8.6.4(2) carries a small-works exemption that §8.5.4(2) does not. Cheap to
# miss and worth real money to a fitout.
STRUCTURAL_ADEQUACY_EXEMPTION = (
    "Developments under $50 000 other than restumping of dwellings are exempt from this "
    "requirement."
)

FLOOD_AREAS = {
    "floodway": {
        "name": "Floodway",
        "section": "8.4",
        "pages": [3, 4],
        "definition_verbatim": (
            "Floodway is that area of the floodplain where a significant discharge of water "
            "occurs during floods and hence velocities and depths are high. Floodways are "
            "usually aligned with naturally defined channels, and include areas that even if "
            "partially blocked, would cause a significant redistribution of flood flow or a "
            "significant increase in flood levels."
        ),
        "headline": (
            "No new buildings or structures of any type are permitted in a Floodway, subject to "
            "three narrow exceptions."
        ),
        "prohibition_verbatim": (
            "No new buildings or structures of any type are permitted in the area designated as "
            "Floodway except:"
        ),
        "exceptions": [
            (
                "where such buildings or structures are to be used for the purpose of providing "
                "utility installations or community facilities; or"
            ),
            (
                "if the building or structure is proposed to be located within 10 metres of the "
                "boundary of the Floodway as marked on the map and a hydraulic study has been "
                "carried out for the land on which the building is proposed which demonstrates, "
                "to Council's satisfaction, that the flood impacts of the proposed building or "
                "structure and any associated works will not adversely effect flood behaviour or "
                "increase the flooding impacts on any other land; or"
            ),
            (
                "where the building or structure is located on land that forms part of the "
                "Lismore Airport and"
            ),
        ],
        # The two airport limbs, which apply to a handful of sites and are
        # carried so the exception is not reported as narrower than it is.
        "airport_limbs": [
            (
                "will form part of the commercial aviation area developed in the northern "
                "precinct of the airport and such development is consistent with the adopted "
                "plan of management for the Lismore Airport and maintains the cross sectional "
                "integrity of the respective floodway; or"
            ),
            (
                "is development of a non-residential nature, located on the western side the "
                "Bruxner Highway between Habib Drive and the Lismore Airport passenger terminal, "
                "that has been developed consistent with the concept plan as shown in the "
                "Lismore Floodplain Management Plan and an evacuation plan has been prepared for "
                "each development. The area closest to the airport terminal is to be developed "
                "for uses that are ancillary to the airport."
            ),
        ],
        "controls": {},
    },
    "high_flood_risk": {
        "name": "High Flood Risk Area",
        "section": "8.5",
        "pages": [4, 5, 6],
        "definition_verbatim": (
            "High Flood Risk Area is the area in which there is a potential for flooding to "
            "cause danger to personal safety and/or loss or damage to light structures. Able "
            "bodied adults could have difficulty wading to safety."
        ),
        "headline": (
            "The most restrictive area in which development is contemplated at all. New "
            "residential development is prohibited unless a flood report displaces the hazard "
            "categorisation, and commercial buildings need a mezzanine refuge above the 1 in 500 "
            "year level."
        ),
        "ari_500_note_verbatim": (
            "Note: For 1 in 500 year ARI flood levels ADD 1.03m to the 1 in 100 year ARI flood "
            "level"
        ),
        "boundary_variation_verbatim": (
            "Any application that seeks to vary the boundary line between the High Flood Risk "
            "Area and the Flood Fringe Area must be justified by a flood report prepared by a "
            "suitably qualified consultant providing site specific detail relating to predicted "
            "depths and velocities in the 1 in 100 year ARI flood, with specific reference to "
            "the criteria for depth and velocity adopted for the High Flood Risk Area in this "
            "Plan."
        ),
        "boundary_variation_section": "8.5.5",
        "all_developments": list(ALL_DEVELOPMENT_CONTROLS.values()),
        "controls": {
            "residential": {
                "section": "8.5.1",
                "page": 4,
                "requirements": [
                    (
                        "No new residential development is permitted in the area designated as "
                        "High Flood Risk on Map 1 unless the application is accompanied by a "
                        "flood report prepared by a suitably qualified consultant providing site "
                        "specific detail relating to predicted depths and velocities in the 1 in "
                        "100 ARI flood, which demonstrates to the satisfaction of Council that "
                        "the flooding characteristics of the site are less hazardous than the "
                        "criteria for depth and velocity adopted for the high flood risk area in "
                        "the Lismore Floodplain Management Plan."
                    ),
                    (
                        "Where extensions or additions to existing residential development are "
                        "proposed, all habitable floor areas are to be at or above the Flood "
                        "Planning Level, except where in the opinion of Council such a floor "
                        "level requirement is impractical or unreasonable."
                    ),
                    (
                        "Where replacement of an existing residential development is proposed, "
                        "all habitable floor areas are to be at or above the Flood Planning "
                        "Level."
                    ),
                    (
                        "New motels, and other forms of development providing temporary "
                        "accommodation only, may be permitted where a minimum of 90% of the "
                        "habitable floor area is at or above the Flood Planning Level and a "
                        "flood evacuation plan is approved for the development."
                    ),
                    "No new caravan parks are permitted in the High Flood Risk Area.",
                ],
            },
            "commercial": {
                "section": "8.5.2",
                "pages": [4, 5],
                "requirements": [
                    (
                        "An equivalent of 25% of the gross floor area of the building to be at "
                        "or above the Flood Planning Level."
                    ),
                    MEZZANINE_REFUGE,
                    BULK_FILL,
                    RISK_ANALYSIS_500_AND_PMF,
                ],
            },
            "industrial": {
                "section": "8.5.3",
                "pages": [5, 6],
                "reasoning": SOUTH_LISMORE_REASONING,
                "sub_cases": {
                    "south_of_hollingworth_creek": {
                        "label": "South Lismore, on the southern side of Hollingworth Creek",
                        "requirements": [
                            "A Minimum floor level at or above Flood Planning Level is preferred.",
                            MEZZANINE_REFUGE,
                            INDUSTRIAL_FILL_SOUTH,
                            BULK_FILL,
                            RISK_ANALYSIS_500_AND_PMF,
                        ],
                    },
                    "all_other_areas": {
                        "label": "All areas other than south of Hollingworth Creek",
                        "requirements": [
                            (
                                "An equivalent of 25% of gross floor area to be at or above the "
                                "1 in 100 year ARI flood level."
                            ),
                            MEZZANINE_REFUGE_NO_ARI,
                            BULK_FILL,
                            RISK_ANALYSIS_500_AND_PMF,
                        ],
                    },
                },
            },
        },
    },
    "flood_fringe": {
        "name": "Flood Fringe Area (including the CBD Flood Liable)",
        "section": "8.6",
        "pages": [6, 7, 8],
        "definition_verbatim": (
            "Flood Fringe Area is defined by the limit of the 1 in 100 year ARI flood level "
            "contour but excludes areas within the Floodway or High Flood Risk Area."
        ),
        "headline": (
            "The area most Lismore businesses are in, and the one the CBD Flood Liable category "
            "is given the controls of. Commercial development needs 25% of its gross floor area "
            "above the Flood Planning Level and an engineer's risk analysis, but no mezzanine "
            "refuge."
        ),
        "ari_500_note_verbatim": (
            "(N.B: For 1 in 500 year ARI flood levels ADD 1.03m to the 1 in 100 year ARI flood "
            "level)."
        ),
        "boundary_variation_verbatim": (
            "Any application that seeks to vary the boundary line between the Flood Fringe Area "
            "and the Low Flood Risk Area must be justified by a flood report prepared by a "
            "suitably qualified consultant providing site specific detail relating to the "
            "predicted probable maximum flood level contour on the property."
        ),
        "boundary_variation_section": "8.6.5",
        "all_developments": list(ALL_DEVELOPMENT_CONTROLS.values()),
        "all_developments_exemption": STRUCTURAL_ADEQUACY_EXEMPTION,
        "controls": {
            "residential": {
                "section": "8.6.1",
                "pages": [6, 7],
                "requirements": [
                    (
                        "Site filling is permitted to the equivalent of the Flood Planning Level "
                        "provided material is sourced from the preferred excavation area or "
                        "on-site. If fill cannot be obtained from the preferred excavation area, "
                        "Council may approve fill imported from a source another source "
                        "providing a flood impact assessment has been prepared by a suitably "
                        "qualified consultant which demonstrates that the fill will have no "
                        "adverse effects upon flood levels upstream or on flooding behaviour on "
                        "adjacent properties."
                    ),
                    (
                        "Habitable floor areas for new residential development are to be at or "
                        "above the Flood Planning Level."
                    ),
                    (
                        "New motels permitted where a minimum of 90% of the habitable floor area "
                        "is at or above the Flood Planning Level and a flood evacuation plan is "
                        "approved for the development."
                    ),
                ],
            },
            "commercial": {
                "section": "8.6.2",
                "page": 7,
                "requirements": [
                    (
                        "An equivalent of 25% of gross floor area of the building to be at or "
                        "above the Flood Planning Level"
                    ),
                    (
                        "A risk analysis report prepared by a structural engineer certifying "
                        "that the design criteria adopted for the building will withstand the "
                        "impact of flood waters and debris up to the 1 in 500 year flood ARI "
                        "event. Such report to be submitted to Council with the Construction "
                        "Certificate."
                    ),
                    BULK_FILL,
                ],
            },
            "industrial": {
                "section": "8.6.3",
                "pages": [7, 8],
                "reasoning": SOUTH_LISMORE_REASONING,
                "sub_cases": {
                    "south_of_hollingworth_creek": {
                        "label": "South Lismore, on the southern side of Hollingworth Creek",
                        "requirements": [
                            "A Minimum floor level at or above Flood Planning Level is preferred.",
                            MEZZANINE_REFUGE,
                            INDUSTRIAL_FILL_SOUTH,
                            BULK_FILL,
                            RISK_ANALYSIS_500_AND_PMF,
                        ],
                    },
                    "all_other_areas": {
                        "label": "All areas other than south of Hollingworth Creek",
                        "requirements": [
                            (
                                "An equivalent of 25% of gross floor area to be at or above the "
                                "Flood Planning Level."
                            ),
                            MEZZANINE_REFUGE,
                            BULK_FILL,
                            RISK_ANALYSIS_500_AND_PMF,
                        ],
                    },
                },
            },
        },
    },
    "low_flood_risk": {
        "name": "Low Flood Risk Area",
        "section": "8.7",
        "pages": [8, 9],
        "definition_verbatim": (
            "Low Flood Risk Area is defined by the limit of the probable maximum flood (PMF) "
            "level contour but excludes areas within the Floodway, High Flood Risk Area or Flood "
            "Fringe Area."
        ),
        "headline": (
            "No development controls apply — but the land is still flood prone, and evacuation "
            "and emergency response are still assessed."
        ),
        "no_controls_verbatim": (
            "No development controls apply to residential, commercial or industrial development "
            "within the Low Flood Risk Area however the safety of people and associate emergency "
            "response management still needs to be considered and may result in:"
        ),
        "considerations": [
            (
                "Restrictions on certain types of development that may be particularly "
                "vulnerable to emergency response such as aged care developments; and"
            ),
            (
                "Restrictions on critical emergency response and recovery facilities and "
                "infrastructure such as evacuation centres, hospitals and major utility "
                "facilities to ensure such facilities and infrastructure can fulfil their "
                "emergency response and recovery functions during and after a flood event."
            ),
        ],
        "controls": {},
    },
    "rural": {
        "name": "Rural Areas",
        "section": "8.8",
        "page": 9,
        "definition_verbatim": (
            "Flood modelling data is not available for the 1 in 100 year ARI flood in rural "
            "areas."
        ),
        "headline": (
            "Outside the modelled urban area there is no mapped flood level, so establishing one "
            "is the applicant's job before anything else can be assessed."
        ),
        "requirements_verbatim": (
            "Where development is proposed on rural land that may be considered flood prone, the "
            "applicant will be required to submit a report from a registered surveyor "
            "establishing a level at the site equivalent to the estimated 1 in 100 year ARI "
            "flood level. The habitable floor level of all new dwellings is to be at or above "
            "the Flood Planning Level."
        ),
        "controls": {},
    },
}

# §8.3: CBD Flood Liable is a distinct category on Map 1 that takes the Flood
# Fringe controls. An alias rather than a copy, so the two can never diverge.
AREA_ALIASES = {
    "cbd_flood_liable": "flood_fringe",
    "cbd": "flood_fringe",
    "cbd flood liable": "flood_fringe",
    "flood fringe": "flood_fringe",
    "fringe": "flood_fringe",
    "high flood risk": "high_flood_risk",
    "high": "high_flood_risk",
    "low flood risk": "low_flood_risk",
    "low": "low_flood_risk",
    "floodway": "floodway",
    "rural": "rural",
}

# Why the tool will not work the area out for the applicant. Same shape as the
# CBD parking boundary in `parking.py`, and for the same reason.
AREA_NOT_INFERABLE = {
    "why": (
        "The flood hazard areas are drawn on Map 1 of DCP Chapter 8, which is a scanned image on "
        "the last page of the chapter with no readable text. Nothing in this repository can tell "
        "which area a given address falls in."
    ),
    "not_a_proxy": (
        "The zone is not a substitute. The areas are drawn on flood depth and velocity modelling, "
        "so a single street can span two of them, and the CBD Flood Liable area is not the same "
        "shape as the E2 zone."
    ),
    "how_to_settle": [
        "Ask Council for the flood hazard category and the 1 in 100 year ARI flood level for the "
        "site — this is what a Flood Information Request or a s10.7 planning certificate answers.",
        "The free Duty Planner drop-in can read it off Map 1 in the session.",
        "Both figures are needed: the category decides which controls apply, and the 1 in 100 "
        "year ARI level from Map 2 is what the Flood Planning Level is calculated from.",
    ],
}

# The state mapping gap, stated wherever flood is answered. `addresses.py`
# carries the same warning for the same reason: the NSW Flood Planning layer
# holds no features at all for this LGA, so an empty result is not an all-clear.
STATE_MAPPING_GAP = (
    "The NSW ePlanning Flood Planning Map contains no data for the Lismore LGA, so an automated "
    "lookup can never establish that a site is unaffected. Absence of a mapped constraint is not "
    "evidence the land does not flood. Lismore's flood information comes from Council."
)

# LEP 2012 clauses 5.21 and 5.22, from documents/lep/lep-2012-nsw-full.txt.
# These sit over the DCP: the DCP is a control plan, the LEP is the statutory
# instrument, and cl 5.21(2) is a prohibition on granting consent rather than a
# design standard. A proposal can meet every DCP figure and still fail it.
LEP_FLOOD_CLAUSES = {
    "5.21": {
        "title": "Flood planning",
        "instrument": "Lismore LEP 2012",
        "effect": (
            "Development consent must not be granted for development in the flood planning area "
            "unless the consent authority is satisfied of five things — this is a bar on consent, "
            "not a standard to design to."
        ),
        "verbatim": (
            "Development consent must not be granted to development on land the consent "
            "authority considers to be within the flood planning area unless the consent "
            "authority is satisfied the development-"
        ),
        "tests": [
            "is compatible with the flood function and behaviour on the land, and",
            (
                "will not adversely affect flood behaviour in a way that results in detrimental "
                "increases in the potential flood affectation of other development or "
                "properties, and"
            ),
            (
                "will not adversely affect the safe occupation and efficient evacuation of "
                "people or exceed the capacity of existing evacuation routes for the surrounding "
                "area in the event of a flood, and"
            ),
            (
                "incorporates appropriate measures to manage risk to life in the event of a "
                "flood, and"
            ),
            (
                "will not adversely affect the environment or cause avoidable erosion, "
                "siltation, destruction of riparian vegetation or a reduction in the stability "
                "of river banks or watercourses."
            ),
        ],
        "climate_change_verbatim": (
            "the impact of the development on projected changes to flood behaviour as a result "
            "of climate change,"
        ),
        "note": (
            "cl 5.21(3)(a) makes projected climate change a mandatory consideration. DCP "
            "Chapter 8's levels come from modelling completed in 2001 and mapped in 2003 and "
            "2007, and do not account for it. Meeting the DCP figure does not discharge this.",
        ),
    },
    "5.22": {
        "title": "Special flood considerations",
        "instrument": "Lismore LEP 2012",
        "effect": (
            "Applies between the flood planning area and the probable maximum flood for "
            "'sensitive and hazardous development', and anywhere a flood may create a particular "
            "risk to life or require evacuation. Land outside the flood planning area is not "
            "outside the flood provisions."
        ),
        "verbatim": (
            "for sensitive and hazardous development-land between the flood planning area and "
            "the probable maximum flood, and"
        ),
        "sensitive_and_hazardous_examples": [
            "boarding houses",
            "caravan parks",
            "correctional centres",
            "early education and care facilities",
            "eco-tourist facilities",
            "educational establishments",
        ],
        "note": (
            "The full list is in cl 5.22(5). Several are businesses — a childcare centre or a "
            "tourist facility is caught by this clause where an ordinary shop is not."
        ),
    },
}
