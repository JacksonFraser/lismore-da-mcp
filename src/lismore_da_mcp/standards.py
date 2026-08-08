"""Applying DCP Chapter 1's residential standards to one proposal.

PLAN.md item 0.6. Separate from `data/standards.py` for the reason CLAUDE.md
gives: this selects and composes, and computation belongs where it can be tested
without a handler.

Two rules, both inverted from what the old handler did:

**The front setback is decided by the zone, not by the number of storeys.**
A1.1 sets 6m in R1/R2/R3/RU5 and A1.4 sets 15m in RU1/R5/E3, rising to 28m on an
RMS road. The old tool asked for `storeys` and `lot_configuration` and never for
the zone, so it could not reach the right figure by any route — and its
side/rear branches returned numbers the chapter does not contain.

**Where the chapter sets no standard, say so.** There is no side setback, no
rear setback and no site coverage maximum for an ordinary lot. That is a real
answer, and the previous file filled all three with invented figures. `absent()`
returns the chapter's actual position plus what does govern instead.

Everything here also carries the Performance Criterion the figure sits against,
because §1.3 makes an Acceptable Solution a safe harbour rather than a limit —
an applicant told "you must have 6m" has been talked out of an argument the
chapter expressly invites.
"""

from lismore_da_mcp.data.standards import (
    DEFINITIONS,
    ELEMENTS,
    HEALTH_PRECINCT,
    HOUSING_TYPES,
    HOW_THIS_CHAPTER_WORKS,
    NOT_SET_BY_THIS_CHAPTER,
)
from lismore_da_mcp.vocabulary import resolve

SETBACK_ZONES = ("R1", "R2", "R3", "RU5", "RU1", "R5", "E3")

STANDARD_TOPICS = tuple(ELEMENTS) + tuple(HOUSING_TYPES) + ("health_precinct",)

# The old tool's vocabulary, plus what applicants say. `site_coverage` and
# `landscaping` both land on the open space element, which is where the chapter
# actually controls them — from the other direction, as a 40% minimum.
STANDARD_SYNONYMS = {
    "site_coverage": "open_space_and_landscaping",
    "site coverage": "open_space_and_landscaping",
    "private_open_space": "open_space_and_landscaping",
    "private open space": "open_space_and_landscaping",
    "open space": "open_space_and_landscaping",
    "landscaping": "open_space_and_landscaping",
    "car_parking_design": "car_parking",
    "parking": "car_parking",
    "garage": "car_parking",
    "carport": "car_parking",
    "driveway": "car_parking",
    "driveways": "car_parking",
    "height": "building_height",
    "storeys": "building_height",
    "privacy": "visual_privacy",
    "overlooking": "visual_privacy",
    "noise": "acoustic_privacy",
    "fence": "fences",
    "fencing": "fences",
    "cut and fill": "earthworks",
    "retaining wall": "earthworks",
    "retaining walls": "earthworks",
    "waste": "service_areas_and_waste",
    "bins": "service_areas_and_waste",
    "clothes line": "service_areas_and_waste",
    "solar": "orientation_and_shade",
    "solar access": "orientation_and_shade",
    "orientation": "orientation_and_shade",
    "shade": "orientation_and_shade",
    "septic": "on_site_sewage",
    "sewage": "on_site_sewage",
    "granny flat": "secondary_dwelling",
    "secondary dwellings": "secondary_dwelling",
    "small lot": "small_lot_housing",
    "shop top": "shop_top_housing",
    "shop top housing": "shop_top_housing",
    "health precinct": "health_precinct",
    "hospital": "health_precinct",
}

HOW_TO_READ_A_FIGURE = HOW_THIS_CHAPTER_WORKS["what_it_means"]


def resolve_topic(term: str):
    return resolve(term, STANDARD_TOPICS, STANDARD_SYNONYMS)


def absent(key: str) -> dict:
    """The chapter's position where it sets no standard.

    Returned in full rather than as a bare "not specified", because the
    follow-up question is always "then what governs it?" and the chapter has an
    answer — usually a performance criterion, sometimes another instrument.
    """
    entry = NOT_SET_BY_THIS_CHAPTER[key]
    return {
        "the_dcp_sets_no_figure": True,
        "question": entry["the_question"],
        "what_the_chapter_says": entry["answer"],
        "do_not_substitute": (
            "Do not fill this with a figure from another council's DCP or a general rule of "
            "thumb. If a number is needed, it comes from the Codes SEPP for exempt and complying "
            "development, or from Council on the merits."
        ),
    }


def front_setback(zone: str | None = None, lot_configuration: str | None = None,
                  fronts_rms_road: bool | None = None) -> dict:
    """The A1.x front setback, which depends on the zone."""
    element = ELEMENTS["setbacks"]
    solutions = element["acceptable_solutions"]
    answer: dict = {
        "performance_criterion": {"P1": element["performance_criteria"]["P1"]},
        "how_to_read_this": HOW_TO_READ_A_FIGURE,
    }

    zone_key = (zone or "").strip().upper()
    if zone_key not in SETBACK_ZONES:
        answer["applicable"] = None
        answer["why"] = (
            "The front setback is set by zone and no zone was supplied. Chapter 1 gives 6m in "
            "R1, R2, R3 and RU5 and 15m in RU1, R5 and E3 — a difference of nine metres, so it "
            "is not something to assume. lookup_zone_by_address derives the zone from an address."
        )
        answer["by_zone"] = dict(element["front_setback_by_zone"])
        answer["all_cases"] = dict(solutions)
        if zone_key:
            answer["zone_not_recognised"] = (
                f"'{zone}' is not a zone Chapter 1 sets a front setback for. It sets one for "
                f"{', '.join(SETBACK_ZONES)}."
            )
        return answer

    answer["zone"] = zone_key
    is_corner = (lot_configuration or "").strip().lower() in ("corner", "corner_lot")
    rural_like = zone_key in ("RU1", "R5", "E3")

    if rural_like and fronts_rms_road:
        answer["applicable"] = "28m"
        answer["because"] = f"{zone_key} with frontage to an RMS road"
        answer["acceptable_solution"] = {"A1.5": solutions["A1.5"]}
        answer["rms_roads"] = DEFINITIONS["rms_roads"]
    elif rural_like:
        answer["applicable"] = "15m"
        answer["because"] = zone_key
        answer["acceptable_solution"] = {"A1.4": solutions["A1.4"]}
        if fronts_rms_road is None:
            answer["check_this"] = (
                "If the site fronts an RMS road the setback is 28m, not 15m. The RMS roads are "
                f"named in the chapter: {DEFINITIONS['rms_roads']}. Pass fronts_rms_road to "
                "settle it."
            )
    elif is_corner:
        answer["applicable"] = "6m from the primary street, 3m from the secondary road"
        answer["because"] = f"corner allotment in {zone_key}"
        answer["acceptable_solution"] = {"A1.2": solutions["A1.2"]}
    else:
        answer["applicable"] = "6m"
        answer["because"] = zone_key
        answer["acceptable_solution"] = {"A1.1": solutions["A1.1"]}
        answer["if_corner"] = (
            "On a corner allotment the secondary road setback is 3m (A1.2). Pass "
            "lot_configuration='corner' if that is the site."
        )

    answer["excluded_from_the_setback"] = (
        "A1.1 measures the setback to buildings and expressly excludes earthworks, retaining "
        "walls and fencing elements."
    )
    answer["rear_lane"] = {"A1.3": solutions["A1.3"]}
    return answer


def setbacks(setback_type: str = "all", zone: str | None = None,
             lot_configuration: str | None = None,
             fronts_rms_road: bool | None = None) -> dict:
    """Front, side and rear — two of which the chapter does not set."""
    wanted = (setback_type or "all").strip().lower()
    answer: dict = {"setback_type": wanted}

    if wanted in ("front", "all"):
        answer["front"] = front_setback(zone, lot_configuration, fronts_rms_road)
    if wanted in ("side", "all"):
        answer["side"] = absent("side_setback")
        answer["side"]["performance_criterion"] = {
            "A4.2": ELEMENTS["building_height"]["acceptable_solutions"]["A4.2"]}
        answer["side"]["small_lot_housing"] = {
            "A26.3": HOUSING_TYPES["small_lot_housing"]["acceptable_solutions"]["A26.3"],
            "applies_to": "Lots under 400m² only.",
        }
    if wanted in ("rear", "all"):
        answer["rear"] = absent("rear_setback")
        answer["rear"]["performance_criterion"] = {
            "A4.2": ELEMENTS["building_height"]["acceptable_solutions"]["A4.2"]}

    if wanted not in ("front", "side", "rear", "all"):
        return {
            "error": f"Setback type '{setback_type}' not found",
            "available_types": ["front", "side", "rear", "all"],
        }

    answer["applies_to"] = (
        "DCP Chapter 1 controls residential development, including ancillary structures (sheds, "
        "pools, garages), in any zone where such development is permitted. Commercial setbacks "
        "are in Chapter 2 and industrial in Chapter 3 — except A1.4, which sets a 15m front "
        "setback in E3 Productivity Support."
    )
    answer["source"] = "Lismore DCP Chapter 1 - Residential Development, §4.1"
    return answer


def topic(name: str) -> dict:
    """Everything the chapter says about one element or housing type."""
    if name == "health_precinct":
        return {"topic": "health_precinct", "provisions": HEALTH_PRECINCT,
                "how_to_read_this": HOW_TO_READ_A_FIGURE}
    if name in ELEMENTS:
        answer = {"topic": name, "provisions": ELEMENTS[name],
                  "how_to_read_this": HOW_TO_READ_A_FIGURE}
        # Where the element is the one an applicant reached for by a name the
        # chapter does not use, say what it does and does not control.
        if name == "open_space_and_landscaping":
            answer["site_coverage"] = absent("site_coverage")
            answer["deep_soil"] = absent("deep_soil_percentage")
        if name == "car_parking":
            answer["widths"] = absent("garage_and_driveway_widths")
            answer["rates_note"] = (
                "These are Chapter 1's residential rates. get_parking_rates reads DCP Chapter 7 "
                "Schedule 1, which covers every development type — the two agree on residential."
            )
        if name == "setbacks":
            answer["side_and_rear"] = {
                "side": absent("side_setback"), "rear": absent("rear_setback")}
        return answer
    if name in HOUSING_TYPES:
        return {"topic": name, "provisions": HOUSING_TYPES[name],
                "how_to_read_this": HOW_TO_READ_A_FIGURE}
    raise KeyError(name)


def everything() -> dict:
    return {
        "how_this_chapter_works": HOW_THIS_CHAPTER_WORKS,
        "definitions": DEFINITIONS,
        "elements": ELEMENTS,
        "housing_types": HOUSING_TYPES,
        "health_precinct": HEALTH_PRECINCT,
        "what_this_chapter_does_not_set": NOT_SET_BY_THIS_CHAPTER,
    }
