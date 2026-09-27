"""Select what DCP Part B Chapter 6 (Nimbin Village) says for one proposal.

`data/nimbin.py` is the chapter; this decides which of it applies. Three rules,
each the same discipline `flood.py` keeps for Chapter 8's Map 1:

  * **The village is never inferred from the zone.** RU5 covers several
    villages and only Nimbin has a chapter. Without `village`, the answer says
    the chapter applies only if the site is in Nimbin, and still returns it.
  * **The precinct is never inferred.** Figure 2 is an image. Without
    `precinct`, every precinct is returned in summary rather than one picked.
  * **The heritage conservation area and flood hazard are never inferred.**
    Figures 3 and 5 are images. Unknown means the controls are returned with
    the condition they apply under, not dropped.
"""

from lismore_da_mcp.data import nimbin
from lismore_da_mcp.vocabulary import resolve

NIMBIN = "nimbin"


def resolve_precinct(term: str):
    return resolve(term, nimbin.PRECINCTS, nimbin.PRECINCT_SYNONYMS)


def resolve_flood_hazard(term: str):
    return resolve(term, nimbin.FLOOD["hazard_categories"], nimbin.FLOOD_HAZARD_SYNONYMS)


def is_nimbin(village: str | None) -> bool | None:
    """True / False for a named village, None when none was given."""
    if not str(village or "").strip():
        return None
    return str(village).strip().lower().removesuffix(" village") == NIMBIN


def _quoted(entry: dict) -> dict:
    """A data entry as the tool shows it: the chapter's words, labelled."""
    shown = {}
    for key, value in entry.items():
        if key == "verbatim":
            shown["quoted"] = value
        elif key == "section":
            shown["section"] = f"§{value}"
        elif key == "plain":
            shown["guidance"] = value
        else:
            shown[key] = value
    return shown


def other_village(village: str) -> dict:
    """The answer for an RU5 village that is not Nimbin."""
    return {
        "village": village,
        "chapter_applies": False,
        "why": nimbin.OTHER_VILLAGES["plain"],
        "quoted_from_the_dcp_introduction": {
            key: entry for key, entry in nimbin.OTHER_VILLAGES.items() if isinstance(entry, dict)
        },
        "what_applies_instead": [
            "check_permissibility with zone RU5 — whether the use is allowed at all",
            "get_setback_requirements with zone RU5 — DCP Chapter 1 sets the front setback by zone",
            "get_parking_rates, get_signage_requirements and get_flood_requirements — the Part A "
            "chapters, which apply in every village",
            "lookup_site_constraints — height limit, lot size, heritage and bushfire by address",
        ],
    }


def _precinct_summary(key: str) -> dict:
    precinct = nimbin.PRECINCTS[key]
    return {
        "name": precinct["name"],
        "section": f"§{precinct['section']}",
        "preferred_land_uses": precinct["preferred_land_uses"],
        "objectives": precinct["objectives"],
    }


def _heritage(precinct: dict, in_hca: bool | None) -> dict | None:
    hca = precinct.get("heritage_conservation_area")
    if not hca:
        return None
    if in_hca is False:
        return {"omitted": "You said the site is outside the Nimbin Heritage Conservation Area "
                           "(Figure 3), so its controls are left out. Confirm that against the "
                           "figure — most of this precinct is inside it."}
    shown = {
        "applies": _quoted(hca["applies"]),
        "objectives": hca["objectives"],
        "controls": hca["controls"],
    }
    if "why_it_matters" in hca:
        shown["guidance"] = hca["why_it_matters"]
    if in_hca is None:
        shown["applies_if"] = (
            "The site is inside the Nimbin Heritage Conservation Area on Figure 3 of the "
            "chapter. Figure 3 is an image this server cannot read; lookup_site_constraints "
            "reports the State heritage layer, and Council can confirm. Pass "
            "in_heritage_conservation_area once it is known."
        )
    return shown


def precinct_detail(key: str, in_hca: bool | None) -> dict:
    precinct = nimbin.PRECINCTS[key]
    shown = {
        "name": precinct["name"],
        "section": f"§{precinct['section']}",
        "about": precinct["about"],
        "objectives": precinct["objectives"],
        "preferred_land_uses": precinct["preferred_land_uses"],
    }
    for field in ("performance_criteria", "design_guidelines"):
        if field in precinct:
            shown[field] = precinct[field]
    if "criteria" in precinct:
        shown["performance_criteria_and_acceptable_solutions"] = {
            label: entry.get("verbatim") or " ".join(entry["verbatim_parts"])
            for label, entry in precinct["criteria"].items()
        }
        shown["how_to_read_the_table"] = (
            "P-numbers are Performance Criteria and A-numbers the Acceptable Solutions that meet "
            "them. P4 and P5 have no acceptable solution, and A2.2 is printed as 'No acceptable "
            "solution.' — those are argued on their merits."
        )
    heritage = _heritage(precinct, in_hca)
    if heritage:
        shown["heritage_conservation_area"] = heritage
    if "cullen_street" in precinct:
        shown["cullen_street_and_western_car_park"] = {
            "section": "§2.4", "controls": precinct["cullen_street"]["controls"]}
    return shown


def flood_controls(hazard_key: str | None) -> dict:
    categories = nimbin.FLOOD["hazard_categories"]
    shown = {
        "section": "§3.1",
        "about": nimbin.FLOOD["about"],
        "guidance": nimbin.FLOOD["why_it_matters"],
    }
    if hazard_key:
        shown["hazard_category"] = categories[hazard_key]
    else:
        shown["hazard_categories"] = categories
        shown["which_category"] = (
            "Figure 5 (BMT WBM 2013) draws the categories and is an image, so the category is "
            "not guessed. Every category is shown; pass flood_hazard once Council has confirmed "
            "it. Low Flood Hazard has no controls at all."
        )
    if hazard_key in (None, "high"):
        shown["source_text_note"] = (
            "§3.1.4 refers to the High Flood Hazard area 'in Figure 4'. Figure 4 is the "
            "Beautification Plan; the flood map is Figure 5, which §3.1 and §3.1.2 cite."
        )
    return shown


def requirements(village: str | None = None, precinct_key: str | None = None,
                 in_hca: bool | None = None, hazard_key: str | None = None,
                 zone: str | None = None) -> dict:
    """What Chapter 6 says for this proposal, or why it does not apply."""
    nimbin_site = is_nimbin(village)
    if nimbin_site is False:
        return other_village(village or "")

    zone_code = str(zone or "").strip().upper()
    if zone_code and zone_code != "RU5":
        return {
            "zone": zone_code,
            "chapter_applies": False,
            "why": "The chapter applies to land in Nimbin zoned RU5 Village (§2), and this site "
                   f"was given as {zone_code}. Use the Part A tools for it.",
            "quoted": nimbin.APPLICATION[1]["verbatim"],
        }

    answer: dict = {
        "chapter": f"{nimbin.CHAPTER} ({nimbin.EDITION})",
        "source": nimbin.SOURCE_DOC,
        "how_to_read_this": "'quoted', and every list of objectives, uses, criteria and "
                            "controls, is the chapter's own words. 'guidance' is this server's.",
    }
    if nimbin_site is None:
        answer["chapter_applies"] = "only if the site is in Nimbin"
        answer["which_village"] = (
            "Zone RU5 Village covers other villages too, and only Nimbin has a Part B chapter, "
            "so the zone does not settle it. Pass village. The chapter is returned below in "
            "case the site is in Nimbin."
        )
    else:
        answer["chapter_applies"] = "yes, if the site is inside Figure 1"
    answer["where_it_applies"] = {
        "quoted": [entry["verbatim"] for entry in nimbin.APPLICATION],
        "guidance": "Figure 1 draws the boundary and is an image this server cannot read. "
                    "§2 describes it as all land in Nimbin zoned RU5; confirm with Council for "
                    "a site on the edge of the village.",
    }
    answer["relationship_to_other_plans"] = _quoted(nimbin.RELATIONSHIP_TO_OTHER_PLANS)
    answer["preferred_is_not_permissible"] = _quoted(nimbin.PRECINCT_RULES["permissibility"])
    answer["non_preferred_uses"] = _quoted(nimbin.PRECINCT_RULES["non_preferred"])
    answer["water_supply"] = _quoted(nimbin.WATER_SUPPLY)

    if precinct_key:
        answer["precinct"] = precinct_detail(precinct_key, in_hca)
        if precinct_key == "investigation_area":
            answer["investigation_area"] = _quoted(nimbin.PRECINCT_RULES["investigation_area"])
    else:
        answer["precincts"] = {key: _precinct_summary(key) for key in nimbin.PRECINCTS}
        answer["which_precinct"] = (
            "Figure 2 draws the precincts and is an image, so the precinct is not guessed. "
            "Each is summarised; pass precinct for its full controls. For a shop, cafe or "
            "office the Commercial Precinct (Cullen Street) is where those uses are preferred."
        )

    answer["flood"] = flood_controls(hazard_key)
    answer["significant_vegetation"] = _quoted({
        "section": nimbin.SIGNIFICANT_VEGETATION["section"],
        "verbatim": nimbin.SIGNIFICANT_VEGETATION["about"][0],
        "plain": nimbin.SIGNIFICANT_VEGETATION["plain"],
    })
    answer["infrastructure"] = _quoted({
        "section": nimbin.INFRASTRUCTURE["section"],
        "verbatim": nimbin.INFRASTRUCTURE["about"][0],
    })
    answer["not_set_by_this_chapter"] = {
        key: entry["what_governs"] for key, entry in nimbin.NOT_SET_BY_THIS_CHAPTER.items()
    }
    answer["next_steps"] = [
        "check_permissibility with zone RU5 — the precincts say where a use is preferred, not "
        "whether it is allowed",
        "get_parking_rates — this chapter sets no parking rate for commercial uses",
        "prepare_prelodgement_brief — puts the precinct, heritage and flood questions on the "
        "Duty Planner agenda",
    ]
    return answer
