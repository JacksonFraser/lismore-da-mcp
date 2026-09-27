"""Applying DCP Chapter 12 and LEP cl 5.10 to one proposal.

ROADMAP.md C1. `data/heritage.py` is the chapter and the clause; this selects
and composes, on the template `flood.py` set for Chapter 8. Three rules hold it
together, and each is carried over from flood because the failure it prevents
is the same shape:

**Heritage status is never inferred.** A heritage item is a Schedule 5 listing
and a conservation area is a boundary on the Heritage Map; neither can be read
off a zone or an address here. Without a stated status the answer carries every
case side by side — heritage item, conservation area, the vicinity of either,
and none known — and says what settles it. The state ePlanning heritage layer
behind `lookup_site_constraints` can *confirm* a listing; it cannot *clear* one,
for the reasons `STATE_LAYER_CONFIRMS_BUT_CANNOT_CLEAR` gives. That is the same
trap the flood layer sets, pointing the other way.

**The DCP never goes back alone.** Chapter 12 applies "whenever development
consent is required under clause 5.10", so cl 5.10(2) decides whether it applies
at all, cl 5.10(3) is the way out for minor work, cl 5.10(4) is Council's duty,
cl 5.10(5) is the discretion to ask for a document, and cl 5.10(10) is the
pathway for a use the zone prohibits. They come back with every answer.

**"May" stays "may".** cl 5.10(5) says the consent authority *may* require a
heritage management document, and §12.3 lets a proposal depart from a policy
with justification. A PREFERRED / NOT ENCOURAGED guideline is reported under the
chapter's own label; only the policies the chapter itself words as a refusal are
reported as one, and those are found by phrase in the stored quotes rather than
listed by hand.
"""

import re

from lismore_da_mcp.data.heritage import (
    CHAPTER_12,
    CHAPTER_12_SCOPE,
    CONSENT_NOT_REQUIRED,
    CONSENT_REQUIRED,
    CONSERVATION_AREAS,
    CONSERVATION_INCENTIVES,
    CONSERVATION_MANAGEMENT_PLAN,
    CONSIDERATION_IS_MANDATORY,
    DESIGN_GUIDELINES,
    HERITAGE_ASSESSMENT,
    HERITAGE_IMPACT_STATEMENT_DEFINITION,
    HERITAGE_MANAGEMENT_DOCUMENT,
    HOW_THE_CHAPTER_APPLIES,
    PRECINCT_POLICIES_INTRO,
    PRINCIPLES,
    REFUSAL_PHRASES,
    WHAT_CHAPTER_12_DOES_ASK_FOR,
    WHAT_CHAPTER_12_DOES_NOT_SAY,
)
from lismore_da_mcp.data.heritage_items import ARCHAEOLOGICAL_SITES, HERITAGE_ITEMS
from lismore_da_mcp.vocabulary import resolve

STATUSES = {
    "heritage_item": "The site is a heritage item listed in LEP Schedule 5 Part 1 (or an "
                     "archaeological site in Part 3).",
    "conservation_area": "The site is within a heritage conservation area (LEP Schedule 5 "
                         "Part 2, shown on the Heritage Map).",
    "item_in_conservation_area": "The site is a heritage item and is also within a heritage "
                                 "conservation area.",
    "vicinity": "The site is not itself listed, but is near a heritage item or conservation "
                "area.",
    "none_known": "No heritage listing is known for the site or its surroundings.",
}

STATUS_SYNONYMS = {
    "item": "heritage_item",
    "listed": "heritage_item",
    "heritage listed": "heritage_item",
    "heritage building": "heritage_item",
    "schedule 5": "heritage_item",
    "archaeological site": "heritage_item",
    "hca": "conservation_area",
    "heritage conservation area": "conservation_area",
    "in a conservation area": "conservation_area",
    "both": "item_in_conservation_area",
    "item and conservation area": "item_in_conservation_area",
    "near": "vicinity",
    "nearby": "vicinity",
    "adjacent": "vicinity",
    "next door": "vicinity",
    "neighbour": "vicinity",
    "near a heritage item": "vicinity",
    "none": "none_known",
    "no": "none_known",
    "not listed": "none_known",
    "not heritage": "none_known",
    "unlisted": "none_known",
}

# Everyday names for the seven areas, beside the LEP's and the DCP's own. The
# LEP's Heritage Map labels (C1–C7) are deliberately not accepted: C1–C3 are
# also zone codes in this LEP, and "C1" is far likelier to be a zone.
AREA_SYNONYMS = {
    "dalley": "dalley_street",
    "dalley street": "dalley_street",
    "spinks park": "spinks_park_civic",
    "civic precinct": "spinks_park_civic",
    "spinks park civic precinct": "spinks_park_civic",
    "st carthages": "st_carthages",
    "st carthage": "st_carthages",
    "saint carthages": "st_carthages",
    "st andrews": "st_andrews",
    "st andrew": "st_andrews",
    "saint andrews": "st_andrews",
    "court house precinct": "st_andrews",
    "girards hill": "girards_hill",
    "nimbin": "nimbin",
    "nimbin village": "nimbin",
    "eltham": "eltham",
}
for _key, _area in CONSERVATION_AREAS.items():
    AREA_SYNONYMS[_area["lep_name"]] = _key
    AREA_SYNONYMS[_area["dcp_heading"]] = _key

# What an applicant says they are doing, mapped to the §12.5 elements that speak
# to it. Matched by substring on the caller's words; over-listing is the safe
# direction, as in `approvals.py` — an extra guideline costs a paragraph, a
# missing one costs a refusal.
WORKS = {
    "signage": {
        "words": ("sign", "advertis", "lettering", "illuminat", "neon", "logo"),
        "guidelines": ("signage",),
    },
    "shopfront": {
        "words": ("shopfront", "shop front", "facade", "façade", "shop window", "stall riser",
                  "plate glass", "shutter", "entry", "entrance"),
        "guidelines": ("sympathetic_change", "windows_and_doors", "building_materials",
                       "colours"),
    },
    "painting": {
        "words": ("paint", "repaint", "colour", "color"),
        "guidelines": ("colours",),
        "principles": ("Beware of irreversible changes such as painting of brickwork.",),
    },
    "roof": {"words": ("roof", "reroof", "gutter"), "guidelines": ("roof",)},
    "windows_and_doors": {"words": ("window", "door", "glazing"),
                          "guidelines": ("windows_and_doors",)},
    "materials": {"words": ("clad", "reclad", "material", "brick", "render", "weatherboard"),
                  "guidelines": ("building_materials",)},
    "verandah_or_awning": {"words": ("verandah", "veranda", "awning", "balcony"),
                           "guidelines": ("verandahs",)},
    "extension": {
        "words": ("extension", "addition", "alteration", "extend", "renovat"),
        "guidelines": ("sympathetic_change", "roof", "windows_and_doors", "building_materials",
                       "colours", "setbacks"),
    },
    "new_building": {
        "words": ("new building", "infill", "erect", "construct", "new development", "rebuild"),
        "guidelines": ("streetscape_context", "sympathetic_change", "roof", "verandahs",
                       "windows_and_doors", "building_materials", "colours", "setbacks"),
    },
    "fence": {"words": ("fence", "fencing"), "guidelines": ("fences",)},
    "garage_or_carport": {"words": ("garage", "carport", "car port", "car park", "parking"),
                          "guidelines": ("garages_and_carports",)},
    "outbuilding_or_pool": {"words": ("pool", "outbuilding", "shed"),
                            "guidelines": ("outbuildings_and_pools",)},
    "demolition": {
        "words": ("demoli", "knock down", "relocat", "move the building"),
        "guidelines": (),
        "note": (
            "Chapter 12 has no demolition guideline, and this does not invent one. Demolishing "
            "or moving a heritage item, or a building within a conservation area, needs consent "
            "under cl 5.10(2)(a). The chapter's §12.4 principles say relocation is a last "
            "resort, and cl 5.10(9) requires the Heritage Council to be notified before consent "
            "is granted to demolish a nominated State heritage item."
        ),
        "principles": (
            "keep a building, work or other component in its historical location, because the "
            "physical location of a heritage item or place is part of its heritage significance, "
            "relocation is a last resort to ensure survival of the building;",
        ),
    },
    "interior_or_fitout": {
        "words": ("interior", "internal", "fitout", "fit-out", "fit out", "mezzanine",
                  "kitchen", "partition"),
        "guidelines": (),
        "note": (
            "Chapter 12 gives no guidance on interiors. The LEP reaches inside a heritage item "
            "only for structural changes, or for anything Schedule 5 specifically lists inside "
            "the item (cl 5.10(2)(b)) — so a non-structural fitout of a heritage item may not "
            "need consent under cl 5.10, though it may still need it for other reasons. Inside "
            "a building that is only within a conservation area, cl 5.10(2) is concerned with "
            "the exterior. Read Schedule 5 for the item: a few listings name an interior."
        ),
    },
    "maintenance_or_repair": {
        "words": ("maintenance", "maintain", "repair", "restor", "restump", "like for like"),
        "guidelines": (),
        "note": (
            "Maintenance and minor work can proceed without consent under cl 5.10(3)(a) — but "
            "only once Council has been notified and has confirmed in writing, before work "
            "starts, that it is minor or maintenance and would not adversely affect "
            "significance. The §12.4 original fabric principles are the chapter's guidance."
        ),
        "principles": tuple(PRINCIPLES["original_fabric"]),
    },
    "subdivision": {
        "words": ("subdivi",),
        "guidelines": (),
        "note": (
            "Subdividing land on which a heritage item is located, or within a conservation "
            "area, needs consent under cl 5.10(2)(f). Chapter 12 has no subdivision guideline; "
            "§12.4 names inappropriate subdivision among the ways heritage value is lost."
        ),
    },
    "change_of_use": {
        "words": ("change of use", "change use", "new use", "change the use"),
        "guidelines": (),
    },
}


# The rule this module exists to keep. Worded for both directions a caller can
# go wrong: reading an empty layer result as "not heritage", and reading an
# unlisted site as unaffected when its neighbour is listed.
STATE_LAYER_CONFIRMS_BUT_CANNOT_CLEAR = {
    "rule": (
        "lookup_site_constraints reads the NSW ePlanning heritage layer at the address. A "
        "positive result confirms the site is mapped as heritage. An empty result does not "
        "clear it."
    ),
    "why_it_cannot_clear": [
        "It is a point query at the address point. A lot whose listed building or "
        "conservation area boundary does not sit under that point reads as unlisted.",
        "The vicinity of a heritage item — which cl 5.10(5)(c) brings within Council's power "
        "to ask for a heritage document — is not mapped anywhere.",
        "The layer is a state dataset, not the instrument. LEP Schedule 5 and the Heritage "
        "Map are, and a s10.7 planning certificate states the site's heritage status in "
        "writing.",
    ],
    "how_to_settle_it": (
        "A s10.7 planning certificate for the property, the LEP Heritage Map on the NSW "
        "Planning Portal, or the question at the free Duty Planner session. "
        "prepare_prelodgement_brief carries it as the `heritage_status` question."
    ),
}


# --- LEP Schedule 5, offline (ROADMAP.md C2) ----------------------------------

STREET_TYPES = {
    "st": "street", "street": "street", "rd": "road", "road": "road",
    "ave": "avenue", "av": "avenue", "avenue": "avenue", "pde": "parade", "parade": "parade",
    "hwy": "highway", "highway": "highway", "ln": "lane", "lane": "lane",
    "cres": "crescent", "crescent": "crescent", "dr": "drive", "drive": "drive",
    "pl": "place", "place": "place", "ct": "court", "court": "court",
    "tce": "terrace", "terrace": "terrace", "way": "way", "cl": "close", "close": "close",
}
# A house number or range; a unit prefix ("1/115") is consumed and dropped, so
# the unit is not read as a house number in its own right.
_NUMBER = re.compile(r"(?:\d+[a-z]?/)?(\d+)([a-z]?)(?:\s*[–-]\s*(\d+)[a-z]?)?")
_PLURAL_TYPES = {"streets": "street", "roads": "road"}


def _words(text: str) -> list[str]:
    text = text.lower().replace("’", "'").replace("'", "")
    return [STREET_TYPES.get(w) or w for w in re.findall(r"[a-z0-9]+(?:/[0-9a-z]+)?|[–-]", text)]


def parse_address(address: str) -> dict | None:
    """(number, street name, street type, suburb) from a written address.

    Deliberately modest: it reads '12 Keen Street, Lismore NSW 2480' and its
    abbreviations, and returns None rather than guessing at anything else. The
    street name is everything between the number and the first street type.
    """
    lowered = re.sub(r"\b(nsw|new south wales)\b|\b\d{4}\s*$", " ", address.lower())
    words = _words(lowered.replace(",", " , "))
    words = [w for w in words if w not in ("-", "–")]
    number = unit = None
    if words and re.fullmatch(r"(\d+[a-z]?/)?\d+[a-z]?", words[0]):
        token = words.pop(0)
        if "/" in token:
            unit, token = token.split("/", 1)
        number = token
    type_at = next((i for i, w in enumerate(words) if w in STREET_TYPES.values() and i > 0), None)
    if type_at is None:
        return None
    name = " ".join(w for w in words[:type_at] if w != ",")
    rest = [w for w in words[type_at + 1:] if w != ","]
    if not name:
        return None
    return {"number": number, "unit": unit, "street": name, "street_type": words[type_at],
            "suburb": " ".join(rest) or None}


def _numbers_before(text: str) -> list[tuple[int, str, int]]:
    """(low, suffix, high) for each house number or range in a run of text."""
    found = []
    for low, suffix, high in _NUMBER.findall(text.lower()):
        found.append((int(low), suffix, int(high) if high else int(low)))
    return found


def _number_matches(wanted: str, candidates: list[tuple[int, str, int]]) -> bool:
    match = re.fullmatch(r"(\d+)([a-z]?)", wanted)
    if not match:
        return False
    value, suffix = int(match.group(1)), match.group(2)
    for low, their_suffix, high in candidates:
        if low == high:
            if value == low and suffix == their_suffix:
                return True
        elif low <= value <= high and not suffix:
            return True
    return False


def _street_mentions(row_address: str, street: str, street_type: str) -> list[str]:
    """For each mention of the street in a Schedule 5 address, the text naming
    its house numbers — the run since the previous street name, or the start.

    '8 and 14 Zadoc Street and 21 Keen Street' gives '8 and 14 ' for Zadoc and
    ' and 21 ' for Keen. The word after the name must be the same street type
    (Keen Lane is not Keen Street, and Leycester Creek is not Leycester
    Street), or nothing at all — the LEP prints I49 as '188 Keen' — or the
    'Bridge and Woodlark Streets' form, where one plural type serves two names.
    """
    lowered = row_address.lower().replace("’", "").replace("'", "")
    runs = []
    pattern = re.compile(r"\b" + re.escape(street) + r"\b(?:\s+(\w+))?")
    previous_end = 0
    for m in pattern.finditer(lowered):
        word = m.group(1)
        if word == "and":
            shared = re.match(r"\s+\w+\s+(\w+)", lowered[m.end():])
            word = shared.group(1) if shared else word
        if word:
            following = _PLURAL_TYPES.get(word, STREET_TYPES.get(word))
        else:
            # Untyped only at the very end ('188 Keen'); 'Eltham Railway Bridge,
            # Johnston Road' is not a mention of Bridge Street.
            following = street_type if not lowered[m.end():].strip() else None
        if following != street_type:
            continue
        runs.append(lowered[previous_end:m.start()])
        previous_end = m.end()
    return runs


def _row(entry: tuple, kind: str) -> dict:
    number, suburb, name, address, description, significance = entry
    return {"item_no": number, "item_name": name, "address": address, "suburb": suburb,
            "property_description": description, "significance": significance,
            "schedule_5_part": kind}


def schedule_5_cross_check(address: str) -> dict:
    """What LEP Schedule 5 says about an address, read offline from the LEP.

    Positive-only by construction. It can find the address or its street in the
    schedule; it can never say a site is unaffected, because a conservation
    area is a map boundary and the vicinity rule crosses streets.
    """
    parsed = parse_address(address)
    answer: dict = {"address_as_given": address}
    if not parsed:
        answer["not_read"] = (
            "The address could not be read as a number, street and suburb, so Schedule 5 was "
            "not searched. Give it as '12 Keen Street, Lismore'."
        )
        answer["this_is_not_a_clearance"] = SCHEDULE_5_NO_MATCH
        return answer
    answer["read_as"] = parsed

    at_address, on_street, elsewhere = [], [], []
    rows = [(r, "Part 1 heritage items") for r in HERITAGE_ITEMS]
    rows += [(r, "Part 3 archaeological sites") for r in ARCHAEOLOGICAL_SITES]
    for entry, kind in rows:
        runs = _street_mentions(entry[3], parsed["street"], parsed["street_type"])
        if not runs:
            continue
        row = _row(entry, kind)
        same_suburb = not parsed["suburb"] or entry[1].lower() == parsed["suburb"]
        if not same_suburb:
            elsewhere.append(row)
        elif parsed["number"] and any(_number_matches(parsed["number"], _numbers_before(run))
                                      for run in runs):
            at_address.append(row)
        else:
            on_street.append(row)

    answer["schedule_5_names_this_address"] = at_address
    answer["listed_on_the_same_street"] = on_street
    if elsewhere:
        answer["same_street_name_in_another_suburb"] = {
            "rows": elsewhere,
            "note": "Schedule 5 gives these a different suburb from the one you gave. Long roads "
                    "cross suburbs, and applicants often write 'Lismore' for a Girards Hill or "
                    "East Lismore address — check whether any is yours or next to it.",
        }
    if at_address:
        answer["what_this_means"] = (
            "Schedule 5 names this address. If the listing is your building or land, it is a "
            "heritage item — pass heritage_status 'heritage_item'. This tool does not set that "
            "for you: a Schedule 5 address can be a range, several lots, grounds, street trees "
            "or a road reserve, so read the item name and property description against your "
            "own lot and DP."
        )
        if any(r["schedule_5_part"].startswith("Part 3") for r in at_address):
            answer["archaeological_site"] = (
                "A Part 3 archaeological site: disturbing or excavating it knowing a relic is "
                "likely to be affected needs consent (cl 5.10(2)(c)), and Council must notify "
                "the Heritage Council before granting consent (cl 5.10(7))."
            )
    elif on_street:
        answer["what_this_means"] = (
            "A listed item is on the same street. If your site is near it, cl 5.10(5)(c) lets "
            "Council require a heritage management document for your proposal too — consider "
            "heritage_status 'vicinity'. Whether you are 'in the vicinity' is Council's call, "
            "not a distance anyone has set."
        )
    answer["this_is_not_a_clearance"] = SCHEDULE_5_NO_MATCH
    answer["source"] = "Lismore LEP 2012 Schedule 5 Parts 1 and 3, read from the LEP text"
    return answer


SCHEDULE_5_NO_MATCH = (
    "Schedule 5 is searched by the address as the LEP writes it, and a match is evidence. No "
    "match is not: a conservation area is a boundary on the Heritage Map, not a list of "
    "addresses; an item round the corner or across a lane is as near as one on your street; "
    "and the LEP writes some addresses as ranges, road reserves or place names. Settle the "
    "status with a s10.7 planning certificate."
)


def resolve_status(term: str):
    return resolve(term, STATUSES, STATUS_SYNONYMS)


def resolve_conservation_area(term: str):
    return resolve(term, CONSERVATION_AREAS, AREA_SYNONYMS)


def classify_works(works: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    """Map each of the caller's phrases to the work types it names.

    Returns ({work type: [the caller's phrases]}, [phrases that matched none]).
    Phrases that match nothing are returned rather than dropped — the rule
    `readiness.py` keeps for documents, and for the same reason.
    """
    matched: dict[str, list[str]] = {}
    unmatched: list[str] = []
    for phrase in works:
        lowered = str(phrase).lower()
        # A word boundary at the start only: "sign" must reach "signage" but not
        # "design", which would put the signage guideline on every redesign.
        hits = [key for key, work in WORKS.items()
                if any(re.search(r"\b" + re.escape(w), lowered) for w in work["words"])]
        if not hits:
            unmatched.append(phrase)
        for key in hits:
            matched.setdefault(key, []).append(phrase)
    return matched, unmatched


def _guideline(key: str) -> dict:
    element = DESIGN_GUIDELINES[key]
    answer = {"heading": element["heading"], "source": f"DCP Chapter 12 §12.5 {element['heading']}"}
    for field in ("intro", "guidance_label", "guidance", "preferred", "not_encouraged"):
        if field in element:
            answer[field] = element[field] if isinstance(element[field], str) else list(element[field])
    return answer


def _precinct(key: str) -> dict:
    area = CONSERVATION_AREAS[key]
    answer = {
        "name": area["lep_name"],
        "heritage_map_label": area["heritage_map_label"],
        "lep_significance": area["lep_significance"],
        "source": f"DCP Chapter 12 §12.6 {area['dcp_heading'].title()}; LEP Schedule 5 Part 2",
        "policies_must_be_addressed": PRECINCT_POLICIES_INTRO["quote"],
        "precinct_policies": list(area["policies"]),
        "characteristics": list(area["characteristics"]),
        "statement_of_significance": list(area["statement_of_significance"]),
    }
    if "also_applies" in area:
        answer["also_applies"] = area["also_applies"]
    if "note" in area:
        answer["note"] = area["note"]
    return answer


def refusals_in(texts: list[tuple[str, str]]) -> list[dict]:
    """The policies among `texts` the chapter words as a flat refusal."""
    return [
        {"source": source, "quote": text}
        for source, text in texts
        if any(phrase in text.lower() for phrase in REFUSAL_PHRASES)
    ]


def _case(status: str, area_key: str | None) -> dict:
    """What applies if the site has this heritage status."""
    item = status in ("heritage_item", "item_in_conservation_area")
    area = status in ("conservation_area", "item_in_conservation_area")

    if status == "vicinity":
        return {
            "meaning": STATUSES[status],
            "consent_under_cl_5_10": (
                "cl 5.10(2) does not by itself require consent for work on a site that is only "
                "near a heritage item — its triggers are the item, the conservation area, and "
                "land on which an item is located. The work may still need consent for other "
                "reasons."
            ),
            "heritage_document": (
                "Council may still require a heritage management document assessing the effect "
                "on the nearby item or area: cl 5.10(5)(c) reaches land 'within the vicinity'."
            ),
            "chapter_12": (
                "Chapter 12's policies bind development applications for Schedule 5 items "
                "(§12.3). For a neighbouring site, the parts that reach it are about setting: "
                "§12.5 Setbacks says minimum setbacks may need to be increased where new "
                "development is adjacent to a heritage item, and §12.4 asks that heritage "
                "places keep an appropriate visual setting."
            ),
            "setting_guidance": [
                DESIGN_GUIDELINES["setbacks"]["guidance"][1],
                PRINCIPLES["burra_charter_principles"][8],
            ],
            "conservation_incentive_cl_5_10_10": "Not available — it applies to a building "
                                                 "that is itself a heritage item.",
        }

    if status == "none_known":
        return {
            "meaning": STATUSES[status],
            "consent_under_cl_5_10": "Not required under cl 5.10 if the site genuinely has no "
                                     "listing.",
            "chapter_12": (
                "Chapter 12 applies to what Schedule 5 lists, but Council may recommend it to "
                "owners of similar unlisted historic properties: "
                f"\"{CHAPTER_12_SCOPE['non_listed_properties']}\""
            ),
            "not_cleared": (
                "'None known' is not the same as none. The vicinity rule (cl 5.10(5)(c)) can "
                "reach an unlisted site, and an empty result from lookup_site_constraints does "
                "not clear it — see `state_layer`."
            ),
        }

    triggers = []
    if item:
        triggers += [
            "(a)(i) demolishing, moving or altering the exterior of the heritage item — "
            "including changes to its detail, fabric, finish or appearance",
            "(b) structural changes to its interior, or changes to anything inside it that "
            "Schedule 5 specifies",
            "(e)(i) erecting a building on the land",
            "(f)(i) subdividing the land",
        ]
    if area:
        triggers += [
            "(a)(iii) demolishing, moving or altering the exterior of a building, work, relic "
            "or tree within the conservation area",
            "(e)(i) erecting a building within the conservation area",
            "(f)(i) subdividing land within the conservation area",
        ]
    answer = {
        "meaning": STATUSES[status],
        "consent_under_cl_5_10": {
            "triggered_by": list(dict.fromkeys(triggers)),
            "chapter_12_on_external_changes": CHAPTER_12_SCOPE["external_changes_note"],
        },
        "heritage_document": (
            "Council may require a heritage management document "
            f"(cl 5.10(5)({'a' if item else 'b'})) — not automatically, and not necessarily a "
            "Heritage Impact Statement."
            + (" For a heritage item it may instead require a conservation management plan "
               "(cl 5.10(6))." if item else "")
        ),
        "chapter_12": {
            "applies": CHAPTER_12_SCOPE["applies_to"],
            "binding_with_a_variation_route": [HOW_THE_CHAPTER_APPLIES["must_comply"],
                                               HOW_THE_CHAPTER_APPLIES["variation"]],
        },
    }
    if item:
        answer["conservation_incentive_cl_5_10_10"] = (
            "Available — a use the zone prohibits can be approved in a heritage-item building "
            "where it facilitates the building's conservation. See `lep_2012.cl_5_10_10`."
        )
    else:
        answer["conservation_incentive_cl_5_10_10"] = (
            "Not available. cl 5.10(10) applies to 'a building that is a heritage item'. Being "
            "within a conservation area — including as a building Chapter 12 calls "
            "contributory — does not make a building a heritage item."
        )
    if area:
        if area_key:
            answer["conservation_area"] = _precinct(area_key)
        else:
            answer["conservation_area"] = {
                "not_named": (
                    "Each of the seven areas has its own precinct policies, which §12.6 says "
                    "must be addressed. Pass `conservation_area` to get them."
                ),
                "the_seven": {a["lep_name"]: f"Heritage Map {a['heritage_map_label']}"
                              for a in CONSERVATION_AREAS.values()},
            }
    return answer


def _change_of_use(status: str | None) -> dict:
    answer = {
        "reading_of_cl_5_10_2": (
            "cl 5.10(2) lists works — demolishing, altering, erecting, subdividing, disturbing — "
            "not uses. So a change of use with no external change, no structural interior work "
            "and no new building may not need consent under cl 5.10 itself, and Chapter 12 "
            "applies 'whenever development consent is required under clause 5.10'. A change of "
            "use still needs whatever consent the land use table requires. In practice a "
            "business opening usually brings a sign, a repaint or a shopfront change, and each "
            "of those alters the exterior under cl 5.10(2)(a). This is a reading of the clause, "
            "not a ruling: put it to the Duty Planner."
        ),
        "chapter_12_on_new_uses": [
            PRINCIPLES["burra_charter_principles"][6],
            PRINCIPLES["burra_charter_principles"][7],
        ],
    }
    if status in (None, "heritage_item", "item_in_conservation_area"):
        answer["if_the_land_use_table_prohibits_the_use"] = (
            "cl 5.10(10) lets the consent authority approve a use the Plan would otherwise "
            "disallow, in a building that is a heritage item, on five cumulative conditions — "
            "one of which is an approved heritage management document. Check the use with "
            "check_permissibility first; this matters only if the answer is prohibited."
            + (" It applies only if the site turns out to be a heritage item." if status is None
               else "")
        )
    return answer


def requirements(status: str | None = None, area_key: str | None = None,
                 works: list[str] | None = None, is_change_of_use: bool = False) -> dict:
    """The heritage answer for one proposal.

    `status` is never guessed. Without it, every case comes back side by side.
    `area_key` implies nothing about status on its own — the handler decides
    that, because a named conservation area is something the caller stated.
    """
    works = list(works or [])
    matched, unmatched = classify_works(works)
    if is_change_of_use and "change_of_use" not in matched:
        matched["change_of_use"] = ["is_change_of_use"]

    answer: dict = {}
    if status:
        answer["heritage_status"] = status
        answer["heritage_status_established_by"] = "supplied by the caller"
        answer["applies"] = _case(status, area_key)
    else:
        answer["heritage_status"] = "not established"
        answer["why_not_established"] = (
            "A heritage item is a Schedule 5 listing and a conservation area is a boundary on "
            "the Heritage Map. Neither can be worked out from a zone, and this tool does not "
            "guess. Every case is below; they differ in what needs consent, whether Chapter "
            "12 binds, and whether cl 5.10(10) is available."
        )
        answer["by_status"] = {key: _case(key, area_key) for key in STATUSES}
    answer["state_layer"] = STATE_LAYER_CONFIRMS_BUT_CANNOT_CLEAR

    # The design guidance selected by the work described. With no works named,
    # every element comes back: the chapter is short enough, and picking a subset
    # for a proposal nobody described would be a guess.
    if matched:
        keys = [g for work in matched for g in WORKS[work]["guidelines"]]
        keys = list(dict.fromkeys(keys))
    else:
        keys = list(DESIGN_GUIDELINES)
    guidelines = {key: _guideline(key) for key in keys}

    reading = []
    for work, phrases in matched.items():
        entry = {"your_words": phrases, "read_as": work.replace("_", " "),
                 "guidelines": list(WORKS[work]["guidelines"])}
        if "note" in WORKS[work]:
            entry["note"] = WORKS[work]["note"]
        if "principles" in WORKS[work]:
            entry["chapter_12_principles"] = list(WORKS[work]["principles"])
        reading.append(entry)

    answer["dcp_chapter_12"] = {
        "source": CHAPTER_12,
        "applies_whenever": CHAPTER_12_SCOPE["trigger"],
        "how_to_read_it": HOW_THE_CHAPTER_APPLIES["in_plain_words"],
        "design_guidelines": guidelines,
        "which_guidelines_and_why": reading or (
            "No works were described, so every §12.5 guideline is returned. Pass `works` — "
            "'new sign', 'repaint', 'shopfront', 'rear extension' — to narrow it."),
        "burra_charter_approach": PRINCIPLES["burra_charter_approach"],
    }
    if unmatched:
        answer["dcp_chapter_12"]["words_not_recognised"] = {
            "your_words": unmatched,
            "note": "These matched no Chapter 12 element and were not guessed at. Rephrase, "
                    "or omit `works` to see every §12.5 guideline.",
        }

    texts = [(g["source"], q) for g in guidelines.values()
             for q in g.get("preferred", []) + g.get("not_encouraged", []) + g.get("guidance", [])]
    precinct_keys = [area_key] if area_key else []
    texts += [(f"DCP Chapter 12 §12.6 {CONSERVATION_AREAS[k]['lep_name']}", q)
              for k in precinct_keys for q in CONSERVATION_AREAS[k]["policies"]]
    refusals = refusals_in(texts)
    if refusals:
        answer["worded_as_a_refusal"] = {
            "why_listed_separately": (
                "Most of Chapter 12 is preference, and §12.3 lets a proposal depart from it "
                "with justification. These are the policies the chapter words as a flat "
                "refusal — a variation argument against them is much harder."
            ),
            "policies": refusals,
        }

    if "change_of_use" in matched:
        answer["change_of_use"] = _change_of_use(status)

    if "signage" in matched:
        answer["signage"] = (
            "Chapter 12's guidance is about how a sign looks. Whether it is allowed at all is "
            "DCP Chapter 9: §9.2 lists a 'heritage area' among the places the SEPP prohibits "
            "advertisements, with exceptions that include building and business identification "
            "signs. Call get_signage_requirements with is_heritage."
        )

    answer["documents"] = {
        "what_council_may_ask_for": {
            "clause": HERITAGE_ASSESSMENT["clause"],
            "in_plain_words": HERITAGE_ASSESSMENT["in_plain_words"],
            "heritage_management_document_means": HERITAGE_MANAGEMENT_DOCUMENT["quote"],
            "conservation_management_plan": CONSERVATION_MANAGEMENT_PLAN["quote"],
            "if_asked_for_a_heritage_impact_statement": {
                "what_it_contains": HERITAGE_IMPACT_STATEMENT_DEFINITION["quote"],
                "source": "DCP Chapter 12 §12.2",
            },
        },
        "what_chapter_12_asks_for": list(WHAT_CHAPTER_12_DOES_ASK_FOR),
        "say_instead": WHAT_CHAPTER_12_DOES_NOT_SAY["say_instead"],
    }

    answer["lep_2012"] = {
        "cl_5_10_2": {"quote": CONSENT_REQUIRED["quote"],
                      "in_plain_words": CONSENT_REQUIRED["in_plain_words"]},
        "cl_5_10_3": {"quote": CONSENT_NOT_REQUIRED["quote"],
                      "exempt_development": CONSENT_NOT_REQUIRED["exempt_development_quote"],
                      "in_plain_words": CONSENT_NOT_REQUIRED["in_plain_words"]},
        "cl_5_10_4": {"quote": CONSIDERATION_IS_MANDATORY["quote"],
                      "in_plain_words": CONSIDERATION_IS_MANDATORY["in_plain_words"]},
        "cl_5_10_5": {"quote": HERITAGE_ASSESSMENT["quote"]},
    }
    if status in (None, "heritage_item", "item_in_conservation_area"):
        answer["lep_2012"]["cl_5_10_10"] = {
            "quote": CONSERVATION_INCENTIVES["quote"],
            "in_plain_words": CONSERVATION_INCENTIVES["in_plain_words"],
        }
    answer["over_the_dcp"] = (
        "LEP 2012 cl 5.10 sits over Chapter 12, and Schedule 5 is the list. The chapter is "
        "guidance written under the clause: it decides how a proposal should look, not whether "
        "consent is needed or whether a document can be demanded."
    )
    answer["guidance_only"] = (
        "This is guidance, not a determination. Heritage is assessed on merit. Ask at the free "
        "Duty Planner session what Council wants before commissioning any report — §12.4 itself "
        "suggests asking Council about access to a Heritage Advisor/Officer."
    )
    return answer
