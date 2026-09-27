"""Applying DCP Chapter 15's waste requirements to one proposal.

ROADMAP.md D2. `data/waste.py` is the chapter; this selects from it and does
the one piece of arithmetic the chapter invites — Appendix C's generation rates
applied to a floor area.

Three rules:

**A change of use is inside the chapter, and says so first.** §1.3 lists
"Change of use" alongside demolition and building work, and §2.1 puts the plan
in the Statement of Environmental Effects. A café taking over a shop is the
commonest business DA there is, and the old checklist asked it only for
"waste storage and collection arrangements".

**An estimate is a floor-area rate applied, never a volume invented.** Only
Appendix C's floor-area rates are computed, only from a floor area the caller
gave, and only per day unless the caller says how many days a week the premises
trades. "Variable" is the chapter's answer for several recyclables cells, and it
stays "Variable" — the reply says so rather than substituting a number. Rates
per bed space, bar area or unit are returned as rates.

**What the chapter excludes is said, not left out.** Grease and liquid trade
waste are outside Chapter 15 and need their own s68 approval; a food business
that reads a Chapter 15 answer and hears nothing about its grease arrestor has
been told something false by omission.
"""

import math
import re

from lismore_da_mcp.data.waste import (
    APPENDICES,
    BIN_SIZES,
    CHAPTER,
    CONSTRUCTION_RULE_OF_THUMB,
    DEMOLITION_MATERIALS,
    FOOD_SHOPS,
    GENERATION_RATES,
    HOW_TO_READ_THIS_CHAPTER,
    NOT_SET_BY_THIS_CHAPTER,
    SCOPE,
    SECTIONS,
    SOURCE_PDF,
    SUBMISSION,
    TRUCK_DIMENSIONS,
)
from lismore_da_mcp.vocabulary import resolve

DEVELOPMENT_TYPES = ("dwellings", "multi_dwelling", "commercial_and_retail", "mixed_use",
                     "industrial")

DEVELOPMENT_SYNONYMS = {
    "dwelling": "dwellings",
    "dwelling house": "dwellings",
    "house": "dwellings",
    "dual occupancy": "dwellings",
    "semi-detached dwelling": "dwellings",
    "secondary dwelling": "dwellings",
    "granny flat": "dwellings",
    "multi dwelling housing": "multi_dwelling",
    "townhouses": "multi_dwelling",
    "villas": "multi_dwelling",
    "units": "multi_dwelling",
    "apartments": "multi_dwelling",
    "residential flat building": "multi_dwelling",
    "commercial": "commercial_and_retail",
    "retail": "commercial_and_retail",
    "shop": "commercial_and_retail",
    "cafe": "commercial_and_retail",
    "café": "commercial_and_retail",
    "coffee shop": "commercial_and_retail",
    "restaurant": "commercial_and_retail",
    "restaurant or cafe": "commercial_and_retail",
    "takeaway": "commercial_and_retail",
    "take away": "commercial_and_retail",
    "food premises": "commercial_and_retail",
    "food and drink premises": "commercial_and_retail",
    "bakery": "commercial_and_retail",
    "butcher": "commercial_and_retail",
    "office": "commercial_and_retail",
    "office premises": "commercial_and_retail",
    "business premises": "commercial_and_retail",
    "hairdresser": "commercial_and_retail",
    "salon": "commercial_and_retail",
    "pub": "commercial_and_retail",
    "hotel": "commercial_and_retail",
    "motel": "commercial_and_retail",
    "registered club": "commercial_and_retail",
    "showroom": "commercial_and_retail",
    "supermarket": "commercial_and_retail",
    "change of use": "commercial_and_retail",
    "fitout": "commercial_and_retail",
    "mixed use": "mixed_use",
    "shop top housing": "mixed_use",
    "industry": "industrial",
    "warehouse": "industrial",
    "factory": "industrial",
    "workshop": "industrial",
    "light industry": "industrial",
}

PREMISES_SYNONYMS = {
    "cafe": "restaurant_or_cafe",
    "café": "restaurant_or_cafe",
    "coffee shop": "restaurant_or_cafe",
    "restaurant": "restaurant_or_cafe",
    "restaurant or cafe": "restaurant_or_cafe",
    "takeaway": "takeaway_food_and_drink_premises",
    "take away": "takeaway_food_and_drink_premises",
    "takeaway food": "takeaway_food_and_drink_premises",
    "deli": "delicatessen",
    "fishmonger": "fish_shop",
    "greengrocer": "green_grocer",
    "fruit shop": "green_grocer",
    "grocery": "supermarket",
    "hairdresser": "hairdresser_beauty_salon",
    "barber": "hairdresser_beauty_salon",
    "beauty salon": "hairdresser_beauty_salon",
    "salon": "hairdresser_beauty_salon",
    "nail salon": "hairdresser_beauty_salon",
    "pub": "pub_club_hotel_motel",
    "hotel": "pub_club_hotel_motel",
    "motel": "pub_club_hotel_motel",
    "registered club": "pub_club_hotel_motel",
    "club": "pub_club_hotel_motel",
    "office": "office_premises",
    "backpackers": "backpackers_accommodation",
    "hostel": "backpackers_accommodation",
    "boarding house": "boarding_house_tourist_visitor_accommodation",
    "units": "multi_dwelling_residential_flat",
    "residential flat building": "multi_dwelling_residential_flat",
    "multi dwelling housing": "multi_dwelling_residential_flat",
}

# Appendix C splits "shop" at 100m²; which row applies is decided by the floor
# area, so a bare "shop" resolves here rather than to either row.
SHOP_WORDS = {"shop", "retail", "retail shop", "shops"}

FOOD_ROWS = {k for k, e in GENERATION_RATES.items() if e.get("group") == FOOD_SHOPS}
FOOD_ROWS.add("pub_club_hotel_motel")

RATE = re.compile(
    r"^(?P<litres>\d+(?:\.\d+)?)L/(?:(?P<per>\d+(?:\.\d+)?)m² )?(?P<basis>[a-z ]+?)/ ?"
    r"(?P<period>day|week)$")


def resolve_development_type(term: str):
    return resolve(term, DEVELOPMENT_TYPES, DEVELOPMENT_SYNONYMS)


def resolve_premises(term: str, floor_area_m2: float | None = None):
    """An Appendix C row key, 'shop' (needs a floor area to choose), or None."""
    text = (term or "").strip().lower()
    if text in SHOP_WORDS:
        # "Less than 100m²" and "greater than 100m²": exactly 100 is in neither
        # row, and picking one would be a choice the chapter did not make.
        if floor_area_m2 is None or floor_area_m2 == 100:
            return "shop"
        return "shop_under_100m2" if floor_area_m2 < 100 else "shop_over_100m2"
    match = resolve(text, GENERATION_RATES, PREMISES_SYNONYMS)
    # Only an exact or synonym match. A fuzzy one would hand a business the
    # neighbouring row's rate, which is the failure the audit exists to catch.
    if match and match.how in ("exact", "squashed", "synonym"):
        return match.key
    return None


def parse_rate(cell: str) -> dict | None:
    """'10L/1.5m² floor area/day' → litres 10 per 1.5m² of floor area per day."""
    found = RATE.match(cell.strip())
    if not found:
        return None
    return {
        "litres": float(found["litres"]),
        "per_m2": float(found["per"]) if found["per"] else None,
        "basis": found["basis"].strip(),
        "period": found["period"],
    }


def _litres(cell: str, floor_area_m2: float | None) -> dict:
    parsed = parse_rate(cell)
    if cell.strip().lower() == "variable":
        return {"rate": cell, "litres_per_day": None,
                "why": "Appendix C gives this as 'Variable'. The chapter sets no figure; estimate "
                       "it for your own operation in the SWMMP."}
    if not parsed:
        return {"rate": cell, "litres_per_day": None}
    if parsed["basis"] != "floor area" or parsed["per_m2"] is None:
        return {"rate": cell, "litres_per_day": None,
                "why": f"This rate is per {parsed['basis']}, not per floor area. Apply it to "
                       "your own count."}
    if floor_area_m2 is None:
        return {"rate": cell, "litres_per_day": None, "supply": "floor_area_m2"}
    per_day = parsed["litres"] * floor_area_m2 / parsed["per_m2"]
    if parsed["period"] == "week":
        return {"rate": cell, "litres_per_day": None, "litres_per_week": round(per_day, 1)}
    return {"rate": cell, "litres_per_day": round(per_day, 1)}


def generation_estimate(premises: str, floor_area_m2: float | None,
                        days_open_per_week: int | None = None,
                        collections_per_week: int | None = None) -> dict:
    """Appendix C applied to a floor area, with the chapter's caveat attached."""
    if premises == "shop":
        return {
            "premises": "shop",
            "which_row": "Appendix C has two shop rows, 'less than' and 'greater than' 100m² of "
                         "floor area. Supply floor_area_m2 to choose; at exactly 100m² the "
                         "chapter names neither, so both are shown.",
            "rows": {k: GENERATION_RATES[k] for k in ("shop_under_100m2", "shop_over_100m2")},
        }
    entry = GENERATION_RATES[premises]
    answer: dict = {
        "premises": entry["premises"],
        "source": "DCP Chapter 15, Appendix C (p27)",
        "is_a_default": SUBMISSION["generation_rates"]["verbatim"],
    }
    if entry.get("group"):
        answer["group"] = entry["group"]
    streams = {}
    for stream in ("waste", "recyclables"):
        cells = [_litres(c, floor_area_m2) for c in entry[stream]]
        streams[stream] = cells if len(cells) > 1 else cells[0]
    answer["general_waste"] = streams["waste"]
    answer["recyclables"] = streams["recyclables"]

    def per_day(stream):
        return stream.get("litres_per_day") if isinstance(stream, dict) else None

    waste_day, recyclables_day = per_day(streams["waste"]), per_day(streams["recyclables"])
    if premises == "restaurant_or_cafe":
        answer["read_the_base"] = (
            "This row is per 1.5m² of floor area, not per 100m² like most of the table, so it "
            "comes out large. It is the chapter's default; §2.3 allows a project-specific "
            "calculation instead, and for a small café one may be more realistic — say how you "
            "worked it out in the SWMMP."
        )
    if days_open_per_week is not None and waste_day is not None:
        waste_week = waste_day * days_open_per_week
        answer["general_waste_litres_per_week"] = round(waste_week, 1)
        if recyclables_day is not None:
            answer["recyclables_litres_per_week"] = round(recyclables_day * days_open_per_week, 1)
        if collections_per_week:
            between = waste_week / collections_per_week
            answer["general_waste_between_collections_litres"] = round(between, 1)
            answer["bins_to_hold_it"] = {
                row.split(" Bin")[0]: math.ceil(between / _bin_litres(row))
                for row in BIN_SIZES["rows"]
                if "W" in row.rsplit("mm", 1)[1]
            }
            answer["bins_note"] = (
                "Number of bins of each size that would hold one collection period's general "
                "waste at the Appendix C rate — the test §4.3 criterion 7 sets for the storage "
                "area. Bin sizes are Appendix D's; a private contractor's may differ."
            )
    elif waste_day is not None:
        answer["per_week"] = ("Supply days_open_per_week for a weekly figure — the SWMMP "
                              "template asks for litres per week.")
    return answer


def _bin_litres(row: str) -> float:
    return float(row.split("L Bin")[0].replace(",", ""))


def requirements(development_type: str, premises: str | None = None, *,
                 floor_area_m2: float | None = None, days_open_per_week: int | None = None,
                 collections_per_week: int | None = None, is_change_of_use: bool | None = None,
                 involves_building_work: bool | None = None,
                 involves_demolition: bool | None = None) -> dict:
    answer: dict = {
        "source": f"Lismore {CHAPTER} — Waste Minimisation ({SOURCE_PDF})",
        "development_type": development_type,
        "how_to_read_this": HOW_TO_READ_THIS_CHAPTER["what_it_means"],
    }

    applies = {
        "verbatim": SCOPE["applies_verbatim"],
        "covered": SCOPE["numbered"]["covered"],
        "exempt_and_complying": SCOPE["exempt_and_complying"]["verbatim"],
    }
    if is_change_of_use:
        applies["your_change_of_use"] = (
            "A change of use is item 3 of §1.3, so Chapter 15 applies even with no building work, "
            "and the plan belongs in the Statement of Environmental Effects (§2.1)."
        )
    answer["does_it_apply"] = applies

    stages = SUBMISSION["the_plan"]["numbered"]["stages"]
    answer["what_to_lodge"] = {
        "in_the_see": SUBMISSION["documentation"]["verbatim"],
        "on_the_plans": SUBMISSION["documentation"]["plans_verbatim"],
        "level_of_detail": SUBMISSION["the_plan"]["level_of_detail_verbatim"],
        "stages": stages,
        "the_plan_must_nominate": SUBMISSION["the_plan"]["numbered"]["must_nominate"],
        "and_specify": SUBMISSION["the_plan"]["provider_verbatim"],
        "template": (APPENDICES["B"] if development_type == "dwellings" else
                     {"appendix": "A", **APPENDICES["A"]}),
    }

    controls: dict = {}
    if involves_demolition:
        controls["demolition"] = {**SECTIONS["demolition"], "table_1": DEMOLITION_MATERIALS}
    if involves_building_work is not False:
        controls["construction"] = {**SECTIONS["construction"],
                                    "rule_of_thumb": CONSTRUCTION_RULE_OF_THUMB}
        if involves_building_work is None:
            answer["building_work_not_stated"] = (
                "§3.3 applies to any building work — a fitout counts. Included because "
                "involves_building_work was not given; pass false for a change of use with no "
                "works at all."
            )
    controls["bins_and_collection"] = SECTIONS["bins_and_collection"]
    if development_type == "mixed_use":
        controls["mixed_use"] = SECTIONS["mixed_use"]
        controls["multi_dwelling"] = SECTIONS["multi_dwelling"]
        controls["commercial_and_retail"] = SECTIONS["commercial_and_retail"]
    else:
        controls[development_type] = SECTIONS[development_type]
    if involves_demolition is None:
        answer["demolition_not_stated"] = (
            "§3.2 adds its own requirements for any demolition, including stripping out an old "
            "fitout if it is demolition work. Pass involves_demolition to include them."
        )
    answer["controls"] = {k: _strip(v) for k, v in controls.items()}

    if development_type in ("commercial_and_retail", "industrial", "mixed_use"):
        answer["storage_area_design"] = {"appendix": "G", **APPENDICES["G"]}
    if development_type in ("multi_dwelling", "mixed_use"):
        answer["storage_room_design"] = {"appendix": "E", **APPENDICES["E"]}
        answer["council_truck"] = TRUCK_DIMENSIONS
    answer["bin_sizes"] = BIN_SIZES

    if premises:
        answer["how_much_waste"] = generation_estimate(
            premises, floor_area_m2, days_open_per_week, collections_per_week)
    if premises in FOOD_ROWS or (premises is None and development_type == "commercial_and_retail"):
        answer["food_waste"] = {
            "criterion_14": SECTIONS["commercial_and_retail"]["numbered"]["outcomes"][13],
            "note": (
                "Appendix C's rates are total general waste, not food waste, so they cannot say "
                "whether a business crosses 240 litres a week of food waste. A café, butcher, "
                "fish shop or restaurant should assume it may, and plan for twice-weekly "
                "collection or refrigerated storage."
            ),
        }

    answer["not_covered_by_this_chapter"] = {
        "liquid_trade_waste": SCOPE["liquid_waste_excluded_verbatim"],
        "where_instead": SCOPE["cross_reference"],
    }
    answer["what_the_chapter_does_not_set"] = {
        key: {"question": e["the_question"], "answer": e["answer"]}
        for key, e in NOT_SET_BY_THIS_CHAPTER.items()
    }
    return answer


def _strip(entry: dict) -> dict:
    return {k: v for k, v in entry.items() if k not in ("applies_to",)}
