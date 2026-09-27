"""Applying DCP Chapter 2's commercial design controls to one proposal.

ROADMAP.md D1. Separate from `data/commercial.py` for the reason CLAUDE.md
gives: this selects and composes; the chapter is the data.

Three rules, each the Chapter 2 form of one the flood and standards modules
already follow:

**The precinct is never inferred.** Part A applies on Map 1 and Part B on Map 2,
both images with no extractable text. The zone is not a proxy — Part B covers
only the Brewster Street part of the old B3 zone, and Chapter 2's Map 1 is not
Chapter 7's Map 1. Without `precinct` the answer carries both parts and says
which question settles it, exactly as `flood.py` does without `flood_area`.

**A change of use is not silently given the design controls.** The chapter
never mentions a change of use; it is written for new and renovating buildings.
So a change of use with no external work gets the chapter's own scope and the
controls that come in the moment external work is added — never a list of
design rules presented as if they bind an internal fitout. That is the
commonest business DA there is, and reporting a 14m blank wall rule against a
café taking over a shop is this chapter's most likely mistake.

**A figure is compared, never enforced.** Part A's verbs are mostly "should" and
Part B's Acceptable Solutions have no §1.3-style statement behind them; a
departure is a variation under the DCP Introduction. So a comparison says which
side of the figure a proposal falls and what to argue, not that it fails.
"""

from lismore_da_mcp.data.commercial import (
    ALTER,
    CHAPTER,
    FIGURES,
    HOW_TO_READ_THIS_CHAPTER,
    NEW,
    NOT_SET_BY_THIS_CHAPTER,
    PART_A,
    PART_A_FRAME,
    PART_B_FRAME,
    PRECINCTS,
    SEPARATION_TABLE,
    SOURCE_PDF,
    TABLE_B1,
)
from lismore_da_mcp.vocabulary import resolve

CHANGE_OF_USE = "change_of_use_only"
WORK_TYPES = (NEW, ALTER, CHANGE_OF_USE)
PRECINCT_KEYS = ("cbd", "brewster_street", "neither")

PRECINCT_SYNONYMS = {
    "lismore cbd": "cbd",
    "cbd": "cbd",
    "city centre": "cbd",
    "town centre": "cbd",
    "map 1": "cbd",
    "part a": "cbd",
    "the block": "cbd",
    "brewster": "brewster_street",
    "brewster st": "brewster_street",
    "brewster street": "brewster_street",
    "health precinct": "brewster_street",
    "hospital precinct": "brewster_street",
    "map 2": "brewster_street",
    "part b": "brewster_street",
    "none": "neither",
    "outside": "neither",
    "elsewhere": "neither",
    "not in either": "neither",
    "nimbin": "neither",
    "village": "neither",
}

WORK_SYNONYMS = {
    "new": NEW,
    "new building": NEW,
    "infill": NEW,
    "redevelopment": NEW,
    "demolish and rebuild": NEW,
    "addition": ALTER,
    "additions": ALTER,
    "alteration": ALTER,
    "alterations": ALTER,
    "alterations and additions": ALTER,
    "renovation": ALTER,
    "renovating": ALTER,
    "extension": ALTER,
    "shopfront": ALTER,
    "shop front": ALTER,
    "new shopfront": ALTER,
    "awning": ALTER,
    "facade": ALTER,
    "external works": ALTER,
    "change of use": CHANGE_OF_USE,
    "change_of_use": CHANGE_OF_USE,
    "fitout": CHANGE_OF_USE,
    "fit out": CHANGE_OF_USE,
    "internal fitout": CHANGE_OF_USE,
    "internal only": CHANGE_OF_USE,
}

TOPIC_SYNONYMS = {
    "awning": "weather_protection",
    "awnings": "weather_protection",
    "verandah": "weather_protection",
    "veranda": "weather_protection",
    "shade": "weather_protection",
    "canopy": "weather_protection",
    "weather": "weather_protection",
    "shopfront": "shop_fronts",
    "shop front": "shop_fronts",
    "heritage": "heritage_buildings",
    "sign": "signage",
    "signs": "signage",
    "access": "disabled_access",
    "accessibility": "disabled_access",
    "disability": "disabled_access",
    "disabled": "disabled_access",
    "wall": "windows_and_doors",
    "walls": "windows_and_doors",
    "blank wall": "windows_and_doors",
    "glazing": "windows_and_doors",
    "windows": "windows_and_doors",
    "height": "building_heights",
    "parapet": "building_heights",
    "roof": "roof_form",
    "colours": "colour",
    "color": "colour",
    "paint": "colour",
    "painting": "colour",
    "demolition": "additions_to_existing_buildings",
    "trees": "retention_of_trees",
    "tree": "retention_of_trees",
    "setbacks": "setback",
    "cpted": "crime_prevention",
    "crime": "crime_prevention",
    "corner": "corner_buildings",
    "footpath": "street_furniture",
    "site analysis": "site_analysis",
    "traffic": "quality_infrastructure",
    "roads": "quality_infrastructure",
}

# What a change of use meets the moment it adds external work. Chosen for what
# a business taking over a shop actually changes: the front, the awning, the
# sign and the paint — plus heritage, which reaches all four.
EXTERNAL_WORK_TOPICS = ("shop_fronts", "weather_protection", "signage", "colour",
                        "heritage_buildings")


ABOVE_THE_SEPARATION_TABLE = (
    "A10's table has one row, 'Up to 11.5 metres'. Chapter 2 sets no separation for a building "
    "taller than that. DCP Chapter 1 §11 has its own separation table for the Health Precinct, "
    "with rows up to 12m (4 storeys) and 16m (5 storeys) (get_residential_standards, 'health_precinct'); "
    "whether Council would apply it to this building is a question for Council, not something to "
    "assume."
)


def resolve_precinct(term: str):
    return resolve(term, PRECINCT_KEYS, PRECINCT_SYNONYMS)


def resolve_work_type(term: str):
    return resolve(term, WORK_TYPES, WORK_SYNONYMS)


def resolve_topic(term: str):
    return resolve(term, PART_A, TOPIC_SYNONYMS)


def _figure(key: str) -> float:
    return FIGURES[key]["value"]


def _part_a_entry(key: str) -> dict:
    entry = dict(PART_A[key])
    entry.pop("applies_to", None)
    entry.pop("subheading", None)
    return entry


def part_a(work_type: str | None, topic: str | None = None, is_heritage: bool | None = None,
           is_corner: bool | None = None, external_wall_length_m: float | None = None) -> dict:
    """Part A, selected for the work — or, for a change of use, its scope."""
    answer: dict = {
        "precinct": PRECINCTS["cbd"],
        "purpose": PART_A_FRAME["purpose"]["verbatim"],
        "objectives": {
            "primary": PART_A_FRAME["objectives"]["verbatim"],
            "design_should_include": PART_A_FRAME["objectives"]["design_should_include"],
        },
    }

    if topic:
        answer["topic"] = topic
        answer["controls"] = {topic: _part_a_entry(topic)}
        chosen = [topic]
    elif work_type == CHANGE_OF_USE:
        answer["scope"] = NOT_SET_BY_THIS_CHAPTER["change_of_use"]["answer"]
        answer["if_you_change_the_outside"] = {
            key: _part_a_entry(key) for key in EXTERNAL_WORK_TOPICS}
        chosen = []
    else:
        works = (work_type,) if work_type else (NEW, ALTER)
        chosen = [k for k, e in PART_A.items() if set(e["applies_to"]) & set(works)]
        answer["controls"] = {k: _part_a_entry(k) for k in chosen}
        if not work_type:
            answer["work_type_not_given"] = (
                "Selected for both a new building and alterations or additions. A.8 (infill) and "
                "the A.13 site analysis are written for new buildings, A.9 for additions to "
                "existing ones. Pass work_type to narrow it — and if the proposal is a change of "
                "use with no external work, say so: the chapter does not address that case."
            )

    if is_heritage and "heritage_buildings" not in chosen and work_type != CHANGE_OF_USE:
        answer.setdefault("controls", {})["heritage_buildings"] = _part_a_entry(
            "heritage_buildings")
    if is_heritage:
        answer["heritage"] = (
            "Part A adds heritage-specific expectations for signage (discrete panels, heritage "
            "character, details with the DA), colour (published heritage colour guidelines for "
            "Schedule 5 items) and design near an item or in a conservation area. None of it "
            "requires a document: under LEP cl 5.10(5) Council may require a heritage "
            "management document, a discretion — ask before commissioning one."
        )
    if is_corner and "corner_buildings" not in chosen and work_type != CHANGE_OF_USE:
        answer.setdefault("controls", {})["corner_buildings"] = _part_a_entry("corner_buildings")

    if external_wall_length_m is not None:
        answer["external_wall_length"] = wall_length_check(external_wall_length_m, work_type)
    return answer


def wall_length_check(length_m: float, work_type: str | None) -> dict:
    limit = _figure("cbd_external_wall_max_m")
    depth = _figure("cbd_wall_articulation_depth_mm")
    result: dict = {
        "control": PART_A["windows_and_doors"]["wall_length_verbatim"],
        "your_wall_m": length_m,
        "figure_m": limit,
    }
    if work_type == CHANGE_OF_USE:
        result["applies"] = False
        result["why"] = "The control is written for 'new developments in the CBD'."
    elif length_m > limit:
        result["within_the_figure"] = False
        result["what_to_do"] = (
            f"A straight run over {limit:g}m needs a return, buttress, balcony, or a recess at "
            f"least {depth:g}mm deep — 'or some other acceptable design feature' — to break it. "
            "Show the articulation on the elevations, or argue the alternative in the SEE."
        )
    else:
        result["within_the_figure"] = True
    return result


def part_b(work_type: str | None, levels: int | None = None, site_area_m2: float | None = None,
           building_height_m: float | None = None, adjoins_r2_zone: bool | None = None,
           is_corner: bool | None = None) -> dict:
    """Table B1, selected by the questions that change which rows apply."""
    answer: dict = {
        "precinct": PRECINCTS["brewster_street"],
        "health_precinct": PART_B_FRAME["health_precinct"],
        "preferred_design_outcomes": {
            k: v for k, v in PART_B_FRAME["preferred_design_outcomes"].items()
            if k.endswith("_verbatim")},
        "pre_lodgement": PART_B_FRAME["pre_lodgement"]["verbatim"],
    }

    if work_type == CHANGE_OF_USE:
        answer["scope"] = (
            NOT_SET_BY_THIS_CHAPTER["change_of_use"]["answer"]
            + " Part B's own purpose is design principles 'for new buildings'. Its signage row "
            "(P7/A7) and its parking row (P5/A5, which sends you to Chapter 7) are the two most "
            "likely to reach a change of use anyway."
        )
        answer["if_you_change_the_outside"] = {
            "signage": TABLE_B1["signage"],
            "carparking_and_loading": TABLE_B1["carparking_and_loading"],
        }
        return answer

    taller = None if levels is None else levels >= _figure("brewster_taller_levels")
    rows = {}
    skipped = {}
    for key, element in TABLE_B1.items():
        if element.get("taller_only") and taller is False:
            skipped[key] = f"Only for taller buildings (3 levels or more); you gave {levels}."
            continue
        if element.get("adjoining_r2_only") and adjoins_r2_zone is False:
            skipped[key] = "Only where the site adjoins the R2 Low Density Residential zone."
            continue
        rows[key] = element
    answer["table_b1"] = rows
    if skipped:
        answer["rows_not_applying"] = skipped
    if "taller_buildings_residential_interface" in rows:
        answer["a10_separation_table"] = SEPARATION_TABLE

    unknown = []
    if levels is None:
        unknown.append("levels — the site area (A8) and residential interface (P9-P10) rows "
                       "apply only at 3 levels or more")
    if adjoins_r2_zone is None:
        unknown.append("adjoins_r2_zone — the residential interface rows apply only beside R2")
    if unknown:
        answer["included_because_not_ruled_out"] = unknown

    checks = {}
    if levels is not None and levels >= 3:
        checks["upper_storeys"] = {
            "acceptable_solution": TABLE_B1["street_address"]["acceptable_solutions"]["A2.3"],
            "figure_m": _figure("brewster_upper_storey_setback_m"),
        }
    if site_area_m2 is not None and taller is not False:
        minimum = _figure("brewster_taller_site_area_m2")
        checks["site_area"] = {
            "acceptable_solution": TABLE_B1["taller_buildings_site_area"]["acceptable_solutions"][
                "A8"],
            "your_site_m2": site_area_m2,
            "within_the_figure": site_area_m2 >= minimum,
        }
        if site_area_m2 < minimum:
            checks["site_area"]["what_to_do"] = (
                f"Below the {minimum:g}m² Acceptable Solution for a building of 3 levels or more. "
                "Argue it against P8 — offsets from boundaries, orientation and substantial "
                "landscaping — as a variation, or consolidate lots."
            )
    if is_corner:
        checks["corner_setback"] = {
            "acceptable_solution": TABLE_B1["street_setbacks"]["acceptable_solutions"]["A1.2"],
        }
    if building_height_m is not None and adjoins_r2_zone and taller is not False:
        checks["separation"] = separation_check(building_height_m)
    if checks:
        answer["against_your_figures"] = checks
    return answer


def separation_check(height_m: float) -> dict:
    top = _figure("brewster_separation_height_limit_m")
    if height_m <= top:
        return {
            "your_height_m": height_m,
            "habitable_rooms_and_balconies_m": _figure("brewster_separation_habitable_m"),
            "non_habitable_rooms_m": _figure("brewster_separation_non_habitable_m"),
            "measured_from": "side and rear boundaries adjoining the R2 Low Density Residential "
                             "Zone (A10)",
        }
    return {
        "your_height_m": height_m,
        "no_row_for_this_height": ABOVE_THE_SEPARATION_TABLE,
    }


def requirements(precinct: str | None, work_type: str | None = None, topic: str | None = None,
                 *, is_heritage: bool | None = None, is_corner: bool | None = None,
                 external_wall_length_m: float | None = None, levels: int | None = None,
                 site_area_m2: float | None = None, building_height_m: float | None = None,
                 adjoins_r2_zone: bool | None = None) -> dict:
    """Chapter 2's answer for one proposal."""
    answer: dict = {
        "source": f"Lismore {CHAPTER} — Commercial Development ({SOURCE_PDF})",
        "how_to_read_this": HOW_TO_READ_THIS_CHAPTER["what_it_means"],
        "if_you_depart_from_it": HOW_TO_READ_THIS_CHAPTER["variations_verbatim"],
    }
    if work_type:
        answer["work_type"] = work_type

    if precinct == "neither":
        answer["applies"] = False
        answer["why"] = (
            "Chapter 2 applies only on its Map 1 (the Lismore CBD) and Map 2 (Brewster Street in "
            "the Health Precinct). Commercial development elsewhere — a local centre, a village, "
            "E3 or MU1 land outside those maps — has no Chapter 2 controls. Other chapters still "
            "apply: parking (Chapter 7), signage (Chapter 9), flood (Chapter 8), waste (Chapter "
            "15), and for Nimbin, Part B Chapter 6."
        )
        return answer

    if precinct in (None, "cbd"):
        answer["part_a_cbd"] = part_a(work_type, topic, is_heritage, is_corner,
                                      external_wall_length_m)
    if precinct in (None, "brewster_street") and not topic:
        answer["part_b_brewster_street"] = part_b(work_type, levels, site_area_m2,
                                                  building_height_m, adjoins_r2_zone, is_corner)
    if precinct == "brewster_street" and topic:
        answer["topic_not_in_part_b"] = (
            f"'{topic}' is a Part A (CBD) topic. Part B is one table; it is returned whole when "
            "no topic is given."
        )
        answer["part_b_brewster_street"] = part_b(work_type, levels, site_area_m2,
                                                  building_height_m, adjoins_r2_zone, is_corner)

    if precinct is None:
        answer["which_precinct"] = {
            "not_inferred": (
                "Chapter 2 has two parts that apply to two mapped areas, and both maps are images "
                "with no extractable text. Neither the address nor the zone settles it — Part B "
                "covers only the Brewster Street part of what the chapter calls the B3 zone (now "
                "E2), and Chapter 2's Map 1 is a different map from the CBD parking boundary in "
                "Chapter 7. Both parts are returned; pass precinct once it is known."
            ),
            "cbd": PRECINCTS["cbd"]["how_to_find_it"],
            "brewster_street": PRECINCTS["brewster_street"]["how_to_find_it"],
            "ask_it_as": "Is this address within Map 1 or Map 2 of DCP Chapter 2 (Commercial "
                         "Development)?",
        }

    answer["what_the_chapter_does_not_set"] = {
        key: {"question": e["the_question"], "answer": e["answer"]}
        for key, e in NOT_SET_BY_THIS_CHAPTER.items()
    }
    return answer

