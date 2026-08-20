"""Applying DCP Chapter 8's flood controls to one proposal.

PLAN.md item 0.5. Separate from `data/flood.py` for the reason CLAUDE.md gives:
this selects and composes, which is computation, and computation belongs where
it can be tested without going through a handler.

Three rules hold it together, and each exists because the alternative puts a
wrong requirement in front of a business:

**The flood hazard area is never inferred.** Map 1 is a bitmap, so without a
stated area every applicable area's controls are returned side by side and none
is chosen. That is the same discipline `parking.py` follows for the CBD
boundary and `contributions.py` for the catchment. A default to one area would
be wrong four times in five and confidently so.

**A change of use is checked against §8.3 before anything else.** The chapter
lifts the commercial and industrial controls entirely in the High Flood Risk
and Flood Fringe areas where a change of use is proposed. Reporting a 25%
floor-level requirement against a café fitout that does not have to meet it is
this repo's most likely flood-shaped mistake, because that is the commonest
business DA there is.

**The DCP is never returned on its own.** LEP 2012 cl 5.21 is a bar on granting
consent, not a design standard, and a proposal can satisfy every figure in
Chapter 8 and still fail it. So both come back together, always.
"""

from lismore_da_mcp.data.flood import (
    AREA_ALIASES,
    AREA_NOT_INFERABLE,
    ARI_500_OFFSET_M,
    CHANGE_OF_USE_EXEMPT,
    DEFINITIONS,
    FLOOD_AREAS,
    FREEBOARD_MM,
    LEP_FLOOD_CLAUSES,
    SCOPE,
    STATE_MAPPING_GAP,
)
from lismore_da_mcp.vocabulary import resolve

DEVELOPMENT_TYPES = ("residential", "commercial", "industrial")

# What the caller is likely to type, mapped to the three headings Chapter 8
# actually writes its controls under. The chapter has no separate retail,
# hospitality or office category — they are all "commercial development".
DEVELOPMENT_SYNONYMS = {
    "cafe": "commercial",
    "coffee shop": "commercial",
    "restaurant": "commercial",
    "food premises": "commercial",
    "takeaway": "commercial",
    "shop": "commercial",
    "retail": "commercial",
    "store": "commercial",
    "office": "commercial",
    "business": "commercial",
    "business premises": "commercial",
    "gym": "commercial",
    "salon": "commercial",
    "hairdresser": "commercial",
    "medical centre": "commercial",
    "childcare": "commercial",
    "child care": "commercial",
    # `childcare centre` — the phrasing an applicant actually types — resolved
    # to nothing and the tool errored with only [commercial, industrial,
    # residential] and no redirect. It is a commercial building for Chapter 8,
    # and it is also exactly the use LEP cl 5.22 exists for. SCENARIOS.md D12.
    "childcare centre": "commercial",
    "child care centre": "commercial",
    "childcare facility": "commercial",
    "centre-based child care facility": "commercial",
    "day care": "commercial",
    "daycare": "commercial",
    "preschool": "commercial",
    "school": "commercial",
    "educational establishment": "commercial",
    "boarding house": "residential",
    "caravan park": "residential",
    "hostel": "residential",
    "seniors housing": "residential",
    "group home": "residential",
    "bakery": "commercial",
    "brewery": "commercial",
    "pub": "commercial",
    "hotel": "commercial",
    "motel": "commercial",
    "factory": "industrial",
    "warehouse": "industrial",
    "workshop": "industrial",
    "storage": "industrial",
    "manufacturing": "industrial",
    "industry": "industrial",
    "house": "residential",
    "home": "residential",
    "dwelling": "residential",
    "dwelling house": "residential",
    "granny flat": "residential",
    "secondary dwelling": "residential",
    "dual occupancy": "residential",
    "duplex": "residential",
    "apartment": "residential",
    "unit": "residential",
}

FLOOD_AREA_SYNONYMS = dict(AREA_ALIASES)


def flood_planning_level() -> dict:
    """How the FPL is calculated, and what the applicant has to go and get.

    The figure itself is site-specific and comes off Map 2, so this returns the
    method rather than a number. Every level in the LGA is this sum.
    """
    return {
        "how_calculated": (
            f"The 1 in 100 year ARI flood level for the site, from Map 2 of DCP Chapter 8, "
            f"plus {FREEBOARD_MM}mm freeboard."
        ),
        "freeboard_mm": FREEBOARD_MM,
        "definition_verbatim": DEFINITIONS["flood_planning_level"]["verbatim"],
        "source": f"DCP Chapter 8 §{DEFINITIONS['flood_planning_level']['section']}",
        "you_still_need": (
            "The 1 in 100 year ARI flood level for this specific site. It is not in this "
            "repository — Map 2 is a scanned image. Council supplies it, and a s10.7 planning "
            "certificate or a Flood Information Request is how you get it in writing."
        ),
        "one_in_500_year_level": (
            f"Add {ARI_500_OFFSET_M}m to the 1 in 100 year ARI level. Several commercial and "
            f"industrial controls are set against the 1 in 500 year level rather than the Flood "
            f"Planning Level."
        ),
    }


def resolve_development_type(term: str):
    return resolve(term, DEVELOPMENT_TYPES, DEVELOPMENT_SYNONYMS)


def resolve_flood_area(term: str):
    """Resolve an area name to a key in FLOOD_AREAS.

    Aliases resolve first so 'CBD Flood Liable' and 'cbd' reach the Flood
    Fringe entry, which is what §8.3 gives that category.
    """
    if not str(term or "").strip():
        return resolve("", FLOOD_AREAS)
    squashed = str(term).strip().lower().replace("_", " ")
    if squashed in FLOOD_AREA_SYNONYMS:
        target = FLOOD_AREA_SYNONYMS[squashed]
        return resolve(target, FLOOD_AREAS)
    return resolve(term, FLOOD_AREAS, FLOOD_AREA_SYNONYMS)


def is_cbd_flood_liable(term: str) -> bool:
    """Whether the caller named the CBD category specifically.

    It resolves to the Flood Fringe controls, but saying so is part of the
    answer — an applicant told about the 'Flood Fringe Area' when they asked
    about the CBD has been given a different area's name and will not trust it.
    """
    return str(term or "").strip().lower().replace("_", " ") in {"cbd", "cbd flood liable"}


def controls_for(area_key: str, development_type: str, is_change_of_use: bool = False) -> dict:
    """The controls one area applies to one development type."""
    area = FLOOD_AREAS[area_key]
    answer = {
        "flood_area": area["name"],
        "section": f"DCP Chapter 8 §{area['section']}",
        "definition_verbatim": area["definition_verbatim"],
        # An area summary, not an answer about the development type asked for.
        # Under the old key `headline` it read as the latter and was returned
        # unchanged for every type — so an industrial proposal in the High Flood
        # Risk Area was told "commercial buildings need a mezzanine refuge" while
        # its own requirements list, correctly, included one; and a residential
        # proposal was told the same thing while its list, correctly, did not.
        # SCENARIOS.md D12. `requirements` below is the type-specific answer.
        "about_this_flood_area": area["headline"],
    }

    # §8.4: the prohibition is on buildings and structures of any type, so it
    # does not vary by development type and must not be filtered by one.
    if area_key == "floodway":
        answer["prohibition_verbatim"] = area["prohibition_verbatim"]
        answer["exceptions"] = list(area["exceptions"])
        answer["airport_exception_limbs"] = list(area["airport_limbs"])
        answer["applies_to"] = (
            "All development. The prohibition is on new buildings or structures of any type, so "
            "it is not narrowed by what the building would be used for."
        )
        return answer

    if area_key == "low_flood_risk":
        answer["no_controls_verbatim"] = area["no_controls_verbatim"]
        answer["still_considered"] = list(area["considerations"])
        answer["applies_to"] = (
            "All development. §8.7 sets no development controls here, but the land is still "
            "flood prone — it is inside the probable maximum flood contour by definition."
        )
        return answer

    if area_key == "rural":
        answer["requirements_verbatim"] = area["requirements_verbatim"]
        answer["applies_to"] = (
            "Rural land, where no 1 in 100 year ARI modelling exists. Establishing the level is "
            "the applicant's job before the Flood Planning Level can be calculated at all."
        )
        return answer

    control = area.get("controls", {}).get(development_type)
    if control is None:
        answer["no_controls_for_this_type"] = (
            f"§{area['section']} sets no controls for {development_type} development."
        )
        return answer

    exempt = (area_key, development_type) in CHANGE_OF_USE_EXEMPT
    requirements = _requirements(control)

    if is_change_of_use and exempt:
        # The finding this whole item turns on. State the exemption before the
        # controls, and never present the controls as applicable alongside it.
        answer["change_of_use_exemption"] = {
            "applies": True,
            "effect": (
                f"These {development_type} controls do not apply to your proposal. §8.3 lifts "
                f"them where a change of use is proposed in the {area['name']}."
            ),
            "verbatim": SCOPE["change_of_use_verbatim"],
            "source": f"DCP Chapter 8 §{SCOPE['section']}",
            "still_applies": [
                "LEP 2012 cl 5.21 — consent cannot be granted unless the consent authority is "
                "satisfied of the five matters in cl 5.21(2). This is not lifted by §8.3.",
                "Any works you do carry out are still building work: the §8.5.4/§8.6.4 controls "
                "on floor levels, structural adequacy and flood compatible materials bite on "
                "what you build, not on the use.",
                "If the fitout extends the floor space, §8.3 sends that part to be considered on "
                "its merits rather than exempting it.",
            ],
            "minor_extensions_verbatim": SCOPE["minor_extensions_verbatim"],
        }
        answer["would_apply_to_new_development"] = requirements
        answer["note"] = (
            "The requirements are listed so you can see what you are being relieved of, and "
            "because Council may still raise them if it reads the proposal as new development "
            "rather than a change of use. Being able to point at §8.3 is the answer."
        )
    else:
        answer["requirements"] = requirements
        answer["read_the_summary_as_the_area_not_the_proposal"] = (
            f"`about_this_flood_area` describes the {area['name']} generally and names the "
            "commercial case, because that is the one most businesses are in. The list above "
            "is the one that applies to this development type — where the two appear to "
            "disagree, the list governs."
        )
        if exempt:
            answer["if_this_is_a_change_of_use"] = (
                "§8.3 lifts these controls entirely where a change of use is proposed rather "
                "than new development. Say so if it is — it is the difference between meeting "
                "these requirements and not having to."
            )

    if "reasoning" in control:
        answer["why_industrial_is_split"] = control["reasoning"]
    answer["all_development_controls"] = list(area.get("all_developments", []))
    if "all_developments_exemption" in area:
        # The wire key used to read `all_development_controls_exemption`, which
        # promises far more than the constant delivers: §8.6.4(2) exempts small
        # works from the *certificate of structural adequacy* only, not from the
        # floor-level survey or the flood-compatible materials beside it. Naming
        # it after the section it exempts from stops it being read as a general
        # let-off. SCENARIOS.md D12.
        answer["structural_adequacy_certificate_exemption"] = area["all_developments_exemption"]
    if "boundary_variation_verbatim" in area:
        answer["disputing_the_area"] = {
            "section": f"DCP Chapter 8 §{area['boundary_variation_section']}",
            "verbatim": area["boundary_variation_verbatim"],
        }
    return answer


def _requirements(control: dict):
    """A control's requirements, flattened but keeping the sub-case split.

    §8.5.3 and §8.6.3 split industrial development on which side of
    Hollingworth Creek it is, and the two sets differ. Collapsing them would
    require picking one.
    """
    if "sub_cases" in control:
        return {
            case["label"]: list(case["requirements"])
            for case in control["sub_cases"].values()
        }
    return list(control["requirements"])


# The cl 5.22(5) categories, in the words an applicant uses. Kept broad on the
# same principle as `approvals.py`: over-listing costs a paragraph of reading,
# and missing one costs a use that is caught by a clause nobody mentioned.
SENSITIVE_OR_HAZARDOUS_WORDS = (
    "child", "day care", "daycare", "preschool", "pre-school", "school",
    "educational", "education", "boarding house", "caravan park", "camping",
    "hostel", "seniors", "aged care", "nursing", "hospital", "health services",
    "correctional", "detention", "eco-tourist", "group home", "respite",
    "emergency services", "evacuation", "hazardous", "offensive",
)


def is_sensitive_or_hazardous(term: str) -> bool:
    """Is this the kind of use LEP cl 5.22 calls sensitive and hazardous?

    Matched on the applicant's words rather than on the resolved Chapter 8
    category, because Chapter 8 has only three categories and cl 5.22 cuts
    across all of them — a childcare centre is 'commercial' to the DCP and
    sensitive to the LEP.
    """
    text = (term or "").lower()
    return any(word in text for word in SENSITIVE_OR_HAZARDOUS_WORDS)


def requirements(development_type: str, flood_area: str | None = None,
                 is_change_of_use: bool = False, asked_about: str = "") -> dict:
    """The flood answer for one proposal.

    `flood_area` is optional and is never guessed. Without it the answer
    carries every area's controls and says plainly that the area has to be
    settled before any of them is the requirement.

    `asked_about` is the caller's own words. Chapter 8 has three categories and
    cl 5.22 cuts across all of them, so the resolved category cannot tell you
    whether the clause applies — 'childcare centre' resolves to commercial.
    """
    answer = {
        "development_type": development_type,
        "flood_planning_level": flood_planning_level(),
    }

    if flood_area:
        area_key = flood_area
        answer["flood_area_established_by"] = "supplied by the caller"
        answer["applies"] = controls_for(area_key, development_type, is_change_of_use)
    else:
        answer["flood_area"] = "not established"
        answer["why_not_established"] = AREA_NOT_INFERABLE
        answer["controls_by_area"] = {
            area["name"]: controls_for(key, development_type, is_change_of_use)
            for key, area in FLOOD_AREAS.items()
        }
        answer["what_this_means"] = (
            "None of these is your requirement yet. They differ sharply — a commercial building "
            "in the High Flood Risk Area needs a mezzanine refuge above the 1 in 500 year level "
            "and one in the Flood Fringe does not, and the Low Flood Risk Area has no controls "
            "at all. Settle the area before designing to any of them."
        )

    # cl 5.22 was in the data and reached no output that named it. It is the
    # provision that catches a use *outside* the flood planning area — between
    # it and the probable maximum flood — and the uses it catches are businesses
    # a shop is not: childcare, schools, boarding houses, caravan parks. Being
    # one item in the `lep_2012` blob is not raising it. SCENARIOS.md D12.
    if is_sensitive_or_hazardous(asked_about or development_type):
        answer["also_clause_5_22"] = {
            "why_it_applies": (
                f"'{asked_about or development_type}' is the kind of use cl 5.22 calls sensitive and "
                "hazardous development. That clause reaches land *between* the flood planning "
                "area and the probable maximum flood — so a site that is outside the flood "
                "planning area, and therefore outside everything above, can still be caught."
            ),
            **LEP_FLOOD_CLAUSES["5.22"],
        }

    answer["lep_2012"] = LEP_FLOOD_CLAUSES
    answer["over_the_dcp"] = (
        "LEP 2012 cl 5.21 sits over Chapter 8. It is a bar on granting consent, not a standard "
        "to design to, so meeting every figure above does not by itself satisfy it — and cl "
        "5.21(3)(a) requires projected climate change to be considered, which the DCP's levels "
        "predate."
    )
    answer["automated_mapping"] = STATE_MAPPING_GAP
    answer["source"] = "Lismore DCP Chapter 8 — Flood Prone Lands, and Lismore LEP 2012"
    answer["guidance_only"] = (
        "This is guidance, not a determination. Flood is the constraint Council is least likely "
        "to negotiate on in this LGA — take a flood-affected proposal to the free Duty Planner "
        "before you design to it."
    )
    return answer
