"""Signage standards, Lismore DCP Chapter 9.

Transcribed 2026-08-06 from `documents/dcp/chapter-9-signage.pdf`.

PLAN.md item 2.3. Almost every business needs a sign and there was no tool for
it, so the only answer available was the DCP prose. Reading the chapter, the
thing a business most needs to hear is not a size limit:

**Most business signage does not need a DA at all.** §9.11 says so directly —
"These Environmental Planning Instruments provide for certain types of signage
as Exempt or Complying Development and the provisions of this DCP chapter are
not applicable." Wall, window, fascia, under-awning and top hamper signs, the
ordinary shopfront set, are Exempt Development if they meet the SEPP's criteria.
Projecting wall signs and pylon/directory boards are Complying Development, so
they take a CDC rather than a DA. Leading with the DCP's size table would answer
a question most businesses do not have, and bury the one they do.

So each entry carries a `pathway` — what approval the sign actually needs — as
well as the DCP standard that applies if it does end up on a DA.

Two traps this chapter sets, both of which catch cafés in particular:

  * **Portable footpath signs — A-frames, sandwich boards — are not permissible**
    unless they meet LEP 2012 Schedule 2. That is the opposite of what most
    operators assume, and they are already on the footpath when they find out.
  * **§9.8: Council will not agree to signage in the road reserve** for
    commercial development other than signage attached to protrusions such as
    awnings. The footpath is Council or RMS land, and the landowner's agreement
    has to be in the DA — so this is refused at the owner's-consent stage, not
    on the merits.

Each entry carries:

  `dcp_name`   the sign as Chapter 9 names it, or None if the chapter has no
               entry for the term
  `definition` the chapter's own definition, verbatim, where it gives one
  `standard`   the numeric or locational control, verbatim
  `pathway`    exempt / complying / consent — which approval it needs
  `source`     page, for anyone checking

`scripts/audit_signage.py` checks every verbatim string still appears in the
PDF, the same guarantee `audit_parking_rates.py` gives the parking rates.
"""

CHAPTER = "DCP Chapter 9"

# What §9.11 and the per-sign notes actually mean for an applicant. The chapter
# states the pathway sign by sign, in a "Note:" under each — these are those
# notes, condensed into one vocabulary.
PATHWAYS = {
    "exempt": {
        "label": "Exempt Development — no application needed",
        "meaning": "No DA and no CDC, provided the sign meets every criterion in the SEPP. "
                   "If it does not, it needs development consent and the DCP standard below "
                   "applies.",
    },
    "complying": {
        "label": "Complying Development — a CDC, not a DA",
        "meaning": "Certified against fixed standards by Council or a private certifier, which "
                   "is faster and cheaper than a DA. A sign that does not meet the SEPP's "
                   "criteria needs a DA lodged with Council instead.",
    },
    "consent": {
        "label": "Development consent — a DA",
        "meaning": "This sign type is assessed on its merits against Chapter 9 and the LEP.",
    },
    "restricted": {
        "label": "Generally not permissible",
        "meaning": "The chapter does not provide for this sign in the ordinary case. Read the "
                   "standard — it says what the narrow exception is.",
    },
}

SEPP_EXEMPT_NOTE = (
    "are Exempt Development if erected in accordance with SEPP (Exempt and Complying "
    "Development Codes) 2008"
)

SIGNAGE = {
    # --- the two that carry the SEPP exception ------------------------------
    #
    # §9.3 defines these but §9.11 gives them no standard, because they are
    # categories rather than shapes — a wall sign or a fascia sign *is* a
    # business identification sign if that is what it says. They matter because
    # they are the exception in §9.2: in a heritage area or a residential zone,
    # these are what a business is still allowed to display.
    "business_identification_sign": {
        "dcp_name": "Business identification sign",
        "definition": "business identification sign means a sign: (a) that indicates: (i) the "
                      "name of the person or business, and (ii) the nature of the business "
                      "carried on by the person at the premises or place at which the sign is "
                      "displayed, and (b) that may include the address of the premises or place "
                      "and a logo or other symbol that identifies the business, but that does "
                      "not contain any advertising relating to a person who does not carry on "
                      "business at the premises or place.",
        "standard": None,
        "pathway": "exempt",
        "source": f"{CHAPTER} §9.3, p3",
        "note": "This is a category, not a shape — the sign itself will also be a wall, window, "
                "fascia or under-awning sign, and that entry sets the size. What matters here "
                "is that a business identification sign is excepted from the §9.2 prohibition, "
                "so it stays available in a heritage area or a residential zone where general "
                "advertising does not. The catch is in the last clause: the moment it "
                "advertises someone who does not trade at the premises, it stops being one.",
    },
    "building_identification_sign": {
        "dcp_name": "Building identification sign",
        "definition": "building identification sign means a sign that identifies or names a "
                      "building and that may include the name of a building, the street name "
                      "and number of a building, and a logo or other symbol but does not "
                      "include general advertising of products, goods or services.",
        "standard": None,
        "pathway": "exempt",
        "source": f"{CHAPTER} §9.3, p3",
        "note": "Also excepted from the §9.2 prohibition. Names the building, not the goods.",
    },

    # --- the ordinary shopfront set: exempt if they meet the SEPP -----------
    "wall_sign": {
        "dcp_name": "Wall signs",
        "definition": "wall sign means a sign that is flat mounted or painted on the surface "
                      "wall of a building, boundary fence or other structure.",
        "standard": "These signs are limited to one per wall, and should not protrude above "
                    "the wall or parapet. Wall signs may also include fence signs.",
        "pathway": "exempt",
        "source": f"{CHAPTER}, pp5, 14",
    },
    "window_sign": {
        "dcp_name": "Window sign",
        "definition": "window sign means a sign painted or displayed on the exterior or "
                      "interior of a shop window or on any glazed surface of a building or "
                      "structure.",
        "standard": "A window sign is painted, attached to, or displayed on the exterior or "
                    "interior of a shop window or on any glazed surface of a building or "
                    "structure.",
        "pathway": "exempt",
        "source": f"{CHAPTER}, pp5, 15",
        "note": "Chapter 9 sets no size limit for window signs. That is not licence to cover "
                "the glass — the §9.4 design guidelines still apply, and in the CBD an "
                "obscured shopfront runs into DCP Chapter 13 (crime prevention) as well.",
    },
    "fascia_sign": {
        "dcp_name": "Facia sign",
        "definition": "fascia sign means a sign that is painted on or attached to the fascia "
                      "or return of an awning, but does not exceed the height of the fascia or "
                      "the return of the awning.",
        "standard": "A facia sign is a sign attached to the facia or return end of an awning, "
                    "but does not exceed the height of the facia or return end of the awning.",
        "pathway": "exempt",
        "source": f"{CHAPTER}, pp4, 10",
    },
    "top_hamper_sign": {
        "dcp_name": "Top hamper sign",
        "definition": "top hamper sign means a sign above a display window or attached to the "
                      "transom of a doorway.",
        "standard": "These signs are attached to the transom of a doorway or above the display "
                    "window of a building.",
        "pathway": "exempt",
        "source": f"{CHAPTER}, pp4, 14",
    },
    "awning_sign_below": {
        "dcp_name": "Awning sign (below)",
        "definition": "awning sign (below) means a sign that is fixed below an awning and "
                      "above the footpath and that does not project above the awning edge and "
                      "is located at least 2.6m above the existing ground level and 600mm from "
                      "the kerbing edge or awning edge.",
        "standard": "These signs should not exceed 2m2 in area as a total per premises, with a "
                    "maximum depth of 500mm, and located a minimum of 600mm from the kerbing "
                    "edge.",
        "pathway": "exempt",
        "max_area_sqm": 2,
        "source": f"{CHAPTER}, pp3, 8",
        "note": "The 2m² is a total per premises, not per sign — two under-awning signs share "
                "the same allowance.",
    },
    "illuminated_sign": {
        "dcp_name": "Illuminated sign",
        "definition": "illuminated sign (external) means a sign in the form of a device (such "
                      "as a reflective or luminous sign) in which a source of light is directed "
                      "to the device in order to make the message readable.",
        "standard": "Neon and animated signs are only considered appropriate in business and "
                    "industrial zones.",
        "pathway": "exempt",
        "source": f"{CHAPTER}, pp4, 11",
        "note": "Any illuminated sign must not be a source of nuisance to neighbours (§9.4 "
                "Amenity). An internally illuminated or animated sign near a residential "
                "boundary is where this is argued.",
    },
    "temporary_sign": {
        "dcp_name": "Temporary sign",
        "definition": "temporary sign means a sign that advertises a commercial, community or "
                      "retail event or private function (including sponsorship of the event or "
                      "function) on a temporary basis and which is erected for no more than two "
                      "consecutive calendar months.",
        "standard": "Any approval for temporary signs will specify the period (no more than two "
                    "consecutive calendar months) the sign may remain.",
        "pathway": "exempt",
        "source": f"{CHAPTER}, pp4, 13",
    },
    "real_estate_sign": {
        "dcp_name": "Real estate sign",
        "definition": "real estate sign means a temporary sign to advertise real property for "
                      "sale or rent, being a sign that is located on the property for sale or "
                      "rent or on the site of the property for sale or rent.",
        "standard": "These signs are only permitted to be erected on the property which is for "
                    "sale or rent and must be removed upon the completion of sale or lease of "
                    "the property.",
        "pathway": "exempt",
        "source": f"{CHAPTER}, pp4, 12",
    },
    "election_sign": {
        "dcp_name": "Election sign",
        "definition": "The sign is not to exceed 1m2 and can only be exhibited 5 weeks prior "
                      "to the election, on the day of the election and 1 week after the "
                      "election.",
        "standard": "Election signs greater than 0.8m2 in area may be permissible, subject to "
                    "development consent.",
        "pathway": "exempt",
        "source": f"{CHAPTER}, pp3, 9",
    },

    # --- complying development: a CDC, not a DA -----------------------------
    "projecting_wall_sign": {
        "dcp_name": "Projecting wall sign",
        "definition": "projecting wall sign means a sign which projects more than 300 "
                      "millimetres from the wall of the building to which it is attached.",
        "standard": "Projecting wall signs must be located a minimum of 600mm from the kerbing "
                    "edge.",
        "pathway": "complying",
        "source": f"{CHAPTER}, pp4, 12",
    },
    "pylon_sign": {
        "dcp_name": "Freestanding pylon and directory board sign",
        "definition": "free standing pylon and directory board sign means a sign which is "
                      "supported by one or more columns, uprights or braces fixed to the ground "
                      "and which is not directly attached to any building or other structure.",
        "standard": "Freestanding pylon and directory board signs should not exceed 7.5m in "
                    "height.",
        "pathway": "complying",
        "max_height_m": 7.5,
        "source": f"{CHAPTER}, pp4, 10",
    },

    # --- these need a DA, and two of them the chapter openly discourages ----
    "awning_sign_above": {
        "dcp_name": "Awning sign (above)",
        "definition": "awning sign (above) means a sign that is located on top of an awning or "
                      "verandah and that does not project above the parapet or ridgeline or "
                      "beyond the awning edge.",
        "standard": "These signs should not exceed 2.5m2 in area as a total per premises. These "
                    "signs are considered to be obtrusive, and can adversely affect streetscapes "
                    "and restrict views of architectural features on a building or buildings.",
        "pathway": "consent",
        "max_area_sqm": 2.5,
        "source": f"{CHAPTER}, pp3, 7",
        "note": "The chapter calls these obtrusive in the same sentence that permits them. "
                "Expect to justify it, particularly on or near a heritage item.",
    },
    "chalkboard_sign": {
        "dcp_name": "Chalkboard sign",
        "definition": "chalkboard sign means a board used for the purpose of describing "
                      "services or goods for sale which vary on a regular basis, such as a "
                      "restaurant menu.",
        "standard": "These signs are not to be placed on footpaths or road reserves, and must "
                    "be affixed to private property and generally not exceed 1.5m2 in area as a "
                    "total per premises.",
        "pathway": "consent",
        "max_area_sqm": 1.5,
        "source": f"{CHAPTER}, pp3, 8",
        "note": "A menu board must be fixed to your own property. It cannot stand on the "
                "footpath — that is a portable footpath sign, which is a different and much "
                "more restricted thing.",
    },
    "sky_roof_fin_sign": {
        "dcp_name": "Sky/roof/fin sign",
        "definition": "sky/roof/fin sign means a sign erected on or above a roof or parapet "
                      "wall of a building and which is supported, wholly or partially, by the "
                      "building, and includes an advertising sign extending above the roof line "
                      "of a building.",
        "standard": "These signs should generally not exceed 8m2 in area, and not exceed the "
                    "height of the highest part of the building on which they are erected.",
        "pathway": "consent",
        "max_area_sqm": 8,
        "source": f"{CHAPTER}, pp4, 13",
        "note": "The chapter calls these unnecessarily obtrusive and singles out the Lismore "
                "precinct, where residents have their principal view over the townscape. A "
                "difficult approval.",
    },
    "advertising_billboard": {
        "dcp_name": "Advertising billboard",
        "definition": "advertising billboard means a structure (such as framework, a signboard, "
                      "a noticeboard, a wall, or a fence) erected or used primarily for the "
                      "display of advertising matter.",
        "standard": "The panel of these signs should generally be greater than 6m2 in area, but "
                    "not exceed 18m2 in area.",
        "pathway": "consent",
        "max_area_sqm": 18,
        "source": f"{CHAPTER}, pp3, 7",
        "note": "The chapter opens by saying these are very obtrusive and generally not "
                "encouraged in Lismore. A billboard also advertises something other than the "
                "business on the premises, so it is not a business identification sign and "
                "loses the SEPP exception in the prohibited zones.",
    },

    # --- the one that catches cafés ----------------------------------------
    "portable_footpath_sign": {
        "dcp_name": "Portable footpath sign",
        "definition": "portable footpath sign means a small, free-standing, portable sign "
                      "located on a footpath or area utilised for pedestrian traffic and "
                      "includes portable weighted signs, sandwich board or A – frame signs and "
                      "retractable signs.",
        "standard": "Portable footpath signs, including portable weighted signs, A–frame signs "
                    "and retractable signs, are not permissible unless they are consistent with "
                    "the criteria listed in Schedule 2 Exempt Development LEP 2012.",
        "pathway": "restricted",
        "source": f"{CHAPTER}, pp4, 11",
        "note": "The commonest signage mistake a Lismore café makes. An A-frame on the footpath "
                "is not permissible unless it meets LEP 2012 Schedule 2, and the footpath is "
                "Council or RMS land besides — §9.8 says Council will not agree to signage in "
                "the road reserve for commercial development other than signage attached to "
                "protrusions such as awnings. Check LEP 2012 Schedule 2 and Council's outdoor "
                "dining approval before buying one.",
    },

    # --- defined in §9.3, given no standard in §9.11 ------------------------
    #
    # Carried with the definition and no invented control. The chapter's own
    # note covers them: where a use is not provided for, it is assessed on
    # merit. Saying "the chapter defines this but sets no standard" is a real
    # answer; making one up is not.
    "animated_sign": {
        "dcp_name": "Animated sign",
        "definition": "animated sign means a sign with movement, or that flashes or changes "
                      "colour, due to the use of electrical or manufactured sources of power.",
        "standard": "Neon and animated signs are only considered appropriate in business and "
                    "industrial zones.",
        "pathway": "consent",
        "source": f"{CHAPTER}, pp3, 11",
        "note": "Confined to business and industrial zones by §9.11. Near a residential "
                "boundary the §9.4 Amenity guideline applies — an animated sign must not be a "
                "source of nuisance to neighbours.",
    },
    "blimp_balloon_sign": {
        "dcp_name": "Blimp/balloon sign",
        "definition": "blimp/balloon sign means a sign which is inflated and suspended above "
                      "the premises, site or event which it is intended to promote or identify "
                      "and which is tethered and displayed at the same premises for a period of "
                      "no more than one calendar month in any one year.",
        "standard": None,
        "pathway": "consent",
        "source": f"{CHAPTER} §9.3, p3",
        "note": "The one-month-per-year limit is in the definition itself, so a blimp displayed "
                "longer than that is not a blimp/balloon sign and is assessed as something "
                "else.",
    },
    "bunting": {
        "dcp_name": "Bunting",
        "definition": "bunting means a sign consisting of a continuous string of lightweight "
                      "coloured material secured so as to allow movement.",
        "standard": None,
        "pathway": "consent",
        "source": f"{CHAPTER} §9.3, p3",
        "note": "Defined but given no standard in §9.11, so it is assessed on merit against the "
                "§9.4 design guidelines. Bunting over a footpath also runs into §9.8 — the road "
                "reserve is Council's land.",
    },
    "integrated_sign": {
        "dcp_name": "Integrated sign",
        "definition": "integrated sign means a sign that is permanent and is an integrated "
                      "design component of a building.",
        "standard": None,
        "pathway": "consent",
        "source": f"{CHAPTER} §9.3, p4",
        "note": "The chapter's preferred outcome: §9.5 encourages applicants to design signage "
                "into the development rather than apply for it separately. If a fitout DA is "
                "being lodged anyway, this is the cheapest route to an approved sign.",
    },
    "tourist_sign": {
        "dcp_name": "Tourist sign",
        "definition": "tourist sign means a sign that directs the travelling public to tourist "
                      "facilities, activities or accommodation or places of scientific, "
                      "historical or scenic interest.",
        "standard": "Directional signage for tourist and visitor accommodation must comply with "
                    "the Tourist Signposting Manual prepared by the former Tourism New South "
                    "Wales and the NSW Roads and Maritime Services, and be approved by the "
                    "Tourist Attraction Signposting Assessment Committee (TASAC).",
        "pathway": "restricted",
        "source": f"{CHAPTER} §9.3, §9.9, pp4, 6-7",
        "note": "Not a Council approval at all — TASAC is a separate committee reached through "
                "NSW Roads and Maritime Services. A tourism business wanting a highway "
                "direction sign is in the wrong queue if it lodges a DA for it.",
    },

    # --- signs a business cannot erect for itself --------------------------
    "directional_sign": {
        "dcp_name": "Directional sign",
        "definition": "directional sign means a sign erected by the Council for the purpose of "
                      "directing vehicular or pedestrian traffic, or advising the public "
                      "(including advising the public about any restrictions), and which does "
                      "not include any information of a commercial nature.",
        "standard": "A directional sign is any advertising device which directs the travelling "
                    "public to tourist facilities, activities, accommodation or places of "
                    "scientific, historical or scenic interest, and which conforms to the "
                    "Australian Standard 1743, and is approved and erected by Council.",
        "pathway": "restricted",
        "source": f"{CHAPTER}, pp3, 9",
        "note": "Erected by Council, not by the business. For tourist directional signage see "
                "§9.9 — it needs TASAC approval under the Tourist Signposting Manual, which is "
                "a separate process from any DA.",
    },
}

# §9.2. This is the provision that decides whether a business in a heritage
# area or a residential zone can have a sign at all — and the exceptions are
# what save it, so they matter more than the prohibition.
SEPP_PROHIBITED_ZONES = {
    "verbatim_intro": "The SEPP prohibits the display of an advertisement within the following "
                      "zones or descriptions:",
    "zones": [
        "environmentally sensitive area",
        "heritage area (excluding railway stations)",
        "natural or other conservation area",
        "open space",
        "waterway",
        "residential (but not including mixed residential/business zones)",
        "national park",
        "nature reserve",
    ],
    "exceptions_verbatim": "with the exception of building identification signs, business "
                           "identification signs, signage on vehicles, and signage which is "
                           "Exempt Development under another SEPP or Lismore LEP 2012.",
    "source": f"{CHAPTER} §9.2, p2",
    # The distinction the whole thing turns on, and it is not obvious from the
    # words: a sign naming your business is excepted; a sign advertising a
    # product or a third party is not.
    "what_it_means_for_a_business": "A sign that names your business and what it does is a "
                                    "business identification sign and is excepted, so a shop in "
                                    "a heritage area or a home business in a residential zone "
                                    "can still identify itself. What is prohibited is general "
                                    "advertising — a product, a brand, or anyone who does not "
                                    "trade at the premises. A billboard is the clear case.",
}

# The chapter cites SEPP 64 throughout. SEPP 64 was repealed and its provisions
# moved into SEPP (Industry and Employment) 2021 Chapter 3 in 2022. No document
# in this repo carries the current instrument, so this is flagged rather than
# relied on — but a business searching "SEPP 64" today will find a repealed
# policy and may conclude the control is gone.
SEPP_CURRENCY_WARNING = {
    "issue": "Chapter 9 cites SEPP 64 Advertising and Signage throughout, including for the "
             "prohibited zones and the 15-year maximum consent period.",
    "status": "SEPP 64 was repealed and its advertising provisions were consolidated into State "
              "Environmental Planning Policy (Industry and Employment) 2021, Chapter 3 "
              "Advertising and Signage. The controls carried forward, but the name did not.",
    "not_verified_here": "No document in this repository carries the current instrument, so "
                         "this is a pointer rather than a citation. Confirm the current "
                         "provision with Council or on the NSW legislation site before relying "
                         "on it in a DA.",
    "why_it_matters": "Searching for 'SEPP 64' today returns a repealed policy, which can read "
                      "as though the control no longer applies. It does.",
}

# §9.4, verbatim headings. These are the assessment criteria, and "Character" is
# the one a CBD or heritage refusal is written under.
DESIGN_GUIDELINES = {
    "source": f"{CHAPTER} §9.4, pp5-6",
    "intro": "The design of all signs should have regard to the following matters:",
    "guidelines": {
        "Appearance": "Signs should be simple, concise and uncluttered in appearance, utilising "
                      "graphics where possible and harmonious colours. The emphasis should be "
                      "on the clarity of communication.",
        "Position": "Signage should be positioned so that it does not unreasonably obscure or "
                    "dominate other existing signs on the same property or neighbouring "
                    "properties.",
        "Character": "Signage should be designed and located so as to be in scale and character "
                     "with the architecture and appearance of the host premises and adjoining "
                     "premises. This principle is of particular importance in the case of "
                     "historic buildings or within historic precincts recognised by Council or "
                     "the National Trust. The design and location of signs should complement "
                     "rather than compromise existing architectural features. No sign shall "
                     "obstruct or block the view of any feature of historic architecture.",
        "Number": "The total number of signs on a particular property should be restricted to "
                  "those necessary to provide reasonable identification of the business or "
                  "businesses established thereon, with duplicate signs to be avoided.",
        "Combination": "Where a number of different signs on a single property are proposed, or "
                       "where a large building complex is involved accommodating a number of "
                       "firms or functions (e.g. shopping centres, factory units, industrial "
                       "estates, etc) a co-ordinated and orderly approach to advertising is to "
                       "be employed, with the signs of uniform or complementary style and "
                       "character.",
        "Amenity": "The size, shape, location, height and message of an advertising device "
                   "should not detract from the amenity of adjacent premises or from the "
                   "locality generally. Rather, the sign should relate to the existing land "
                   "use.",
        "Obstruction": "Signage must be positioned so as not to present a potential obstruction "
                       "to the safe movement of pedestrians, bicycles or motor vehicles, or "
                       "cause confusion with traffic signs, controls or directional signs.",
        "Safety": "Signage must be designed and built in a manner which is structurally and "
                  "electrically sound so that they pose no threat or danger to the public.",
    },
}

# §9.8. The reason a footpath sign fails at owner's consent rather than on
# assessment — you cannot supply the landowner's agreement, because Council is
# the landowner and will not give it.
ROAD_RESERVE = {
    "verbatim": "Development applications for signage must include the agreement of the owner "
                "of the property on which the signage is to be erected. Lismore City Council or "
                "the Roads and Maritime Services are the owners of road reserves, including "
                "footpaths, within Lismore. Council will not agree to the erection of signage "
                "in the road reserve for commercial development other than signage attached to "
                "protrusions of commercial development such as awnings and the like.",
    "source": f"{CHAPTER} §9.8, p7",
}

# §9.5 and §9.7.
APPLICATION_REQUIREMENTS = {
    "verbatim": "Sign applications should be submitted to Council on a Development Application "
                "form, with six (6) copies of accompanying plans of the proposed sign(s). "
                "Applications should address both the advertising content and the structure on "
                "which it is to be displayed.",
    "plans_verbatim": "The plans should be to scale, and clearly show the particulars of sign "
                      "dimensions, type, colour(s), material(s), location, construction and "
                      "method of attachment of the advertisement, and any further information "
                      "deemed necessary or as requested by Council.",
    "not_a_separate_da": "Sign applications need not be a separate application from a "
                         "development application for the whole development of a site. "
                         "Applicants are encouraged to consider the provision of suitable "
                         "integrated signage as part of the overall design of a development.",
    "duration_verbatim": "In accordance with the provisions of SEPP 64 Advertising and Signage, "
                         "Council may grant consent to an application for signage for a maximum "
                         "period of fifteen years.",
    "source": f"{CHAPTER} §9.5, §9.7, p6",
    "note": "Signage does not have to be its own DA. A business already lodging a DA for a "
            "fitout or change of use should include the sign in it rather than lodging twice "
            "and paying twice. Note the consent is time-limited — up to fifteen years — so an "
            "old approved sign may need renewing.",
}

# §9.6.
EXISTING_USE_RIGHTS = {
    "verbatim": "Where signage has been legally approved in the past, existing use rights may "
                "apply. Signs which have not been given approval but existed prior to the "
                "introduction of planning controls or the adoption of Lismore City Council's "
                "original Policy on Outdoor Advertising Signs and Structures on 15 October "
                "1985, may be deemed also as having existing use rights.",
    "source": f"{CHAPTER} §9.6, p6",
    "note": "Relevant when taking over a tenancy with a sign already on it. An existing sign is "
            "not automatically yours to re-face: changing the sign generally means the pathway "
            "for a new sign applies. Ask Council what is approved for the premises before "
            "assuming an existing structure can be reused.",
}
