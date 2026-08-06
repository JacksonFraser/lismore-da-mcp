"""Resolving what a caller typed to the key a lookup table actually uses.

Every lookup tool here keys off snake_case planning terms and matched them
exactly, so ordinary words bounced off data that was sitting right there:

    "takeaway"          missed take_away
    "child care centre" missed childcare_centre
    "coffee shop"       missed cafe
    "granny flat"       missed secondary_dwelling
    "site description"  missed site_description

The first two are pure punctuation differences. The next two are vocabulary: an
applicant does not know the Standard Instrument term for what they are building.
The last is the caller having to guess our underscore convention.

Resolution runs in four steps, most confident first:

  1. exact, once both sides are normalised to snake_case
  2. squashed — separators removed entirely, so "take away", "take_away" and
     "takeaway" are the same term
  3. synonym, from an explicit table the caller supplies
  4. fuzzy, and only when clearly ahead of the runner-up

Step 4 is deliberately conservative. This module exists alongside
validate_arguments(), which refuses rather than guesses because a confident
wrong answer about planning law is worse than an error. A fuzzy match that
is not clearly better than its alternatives returns *suggestions* rather than
picking one.
"""

import difflib
import re
from dataclasses import dataclass, field

# Accept a match this close to the query...
FUZZY_CUTOFF = 0.82
# ...but only if it beats the next-best candidate by this much, so a term sitting
# between two entries produces suggestions instead of a coin toss.
FUZZY_MARGIN = 0.08

# Offer a term as "did you mean" only above this. Measured against the real
# vocabularies: genuine typos score 0.88-0.95 ("resturant"/"restaurant" 0.95,
# "offce"/"office" 0.91, "coffe"/"cafe" 0.67), while unrelated words sit at
# 0.18-0.50 ("hairdresser"/"warehouse" 0.50, "shed"/"shop" 0.50). Suggesting
# warehouse parking rates to a hairdresser is worse than admitting we have no
# rate for it, so the threshold sits above that band.
SUGGEST_CUTOFF = 0.62


def normalise(term: str) -> str:
    """Lowercase snake_case: 'Child Care Centre' -> 'child_care_centre'."""
    return re.sub(r"[^a-z0-9]+", "_", str(term).strip().lower()).strip("_")


def squash(term: str) -> str:
    """Alphanumerics only: 'take away' and 'take_away' both -> 'takeaway'."""
    return re.sub(r"[^a-z0-9]+", "", str(term).strip().lower())


@dataclass
class Resolution:
    """The outcome of resolving one term."""

    key: str | None = None
    how: str | None = None          # exact | squashed | synonym | fuzzy
    suggestions: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.key is not None


def resolve(term: str, candidates, synonyms: dict[str, str] | None = None) -> Resolution:
    """Resolve `term` against `candidates`, or return suggestions.

    `synonyms` maps a plain-English phrase to a candidate key. Its keys are
    normalised on the way in, so "Granny Flat" and "granny_flat" both work.
    """
    candidates = list(candidates)
    if not str(term).strip():
        return Resolution(suggestions=sorted(candidates)[:8])

    wanted = normalise(term)

    if wanted in candidates:
        return Resolution(key=wanted, how="exact")

    squashed = {squash(c): c for c in candidates}
    if squash(term) in squashed:
        return Resolution(key=squashed[squash(term)], how="squashed")

    for alias, target in (synonyms or {}).items():
        if normalise(alias) == wanted or squash(alias) == squash(term):
            if target in candidates:
                return Resolution(key=target, how="synonym")

    scored = sorted(
        ((difflib.SequenceMatcher(None, wanted, c).ratio(), c) for c in candidates),
        reverse=True,
    )
    if scored:
        best_score, best = scored[0]
        runner_up = scored[1][0] if len(scored) > 1 else 0.0
        if best_score >= FUZZY_CUTOFF and best_score - runner_up >= FUZZY_MARGIN:
            return Resolution(key=best, how="fuzzy")

    # Nothing confident enough. Suggest only terms sharing a whole word, or
    # scoring above SUGGEST_CUTOFF. An empty list is a valid outcome and better
    # than a misleading nearest neighbour — the caller still gets the full list
    # of what is available.
    words = {w for w in wanted.split("_") if len(w) > 2}
    related = [c for c in candidates if words & set(c.split("_"))]
    close = [c for s, c in scored if s >= SUGGEST_CUTOFF][:5]
    return Resolution(suggestions=list(dict.fromkeys(related + close))[:8])


def unresolved_error(term: str, resolution: Resolution, what: str, candidates) -> dict:
    """A refusal that tells the caller how to succeed next time."""
    error = {"error": f"No {what} found for '{term}'."}
    if resolution.suggestions:
        error["did_you_mean"] = resolution.suggestions
    error[f"available_{what.replace(' ', '_')}s"] = sorted(candidates)
    return error


# --- Synonym tables -------------------------------------------------------
#
# Plain-English phrasing an applicant is likely to use, mapped to the term the
# data is keyed by. These are naming aliases only: nothing here decides whether
# a use is permitted, so a wrong entry produces a wrong lookup, not wrong
# planning advice. Terms an applicant means unambiguously — no guessing at
# whether a "unit" is an apartment or a dual occupancy.

PARKING_SYNONYMS = {
    "coffee shop": "cafe",
    "coffee house": "cafe",
    "coffee": "cafe",
    "takeaway": "take_away",
    "takeaway food": "take_away",
    "fast food": "take_away",
    "child care": "childcare_centre",
    "child care centre": "childcare_centre",
    "childcare": "childcare_centre",
    "daycare": "childcare_centre",
    "day care": "childcare_centre",
    "preschool": "childcare_centre",
    "granny flat": "secondary_dwelling",
    "granny flat unit": "secondary_dwelling",
    "house": "dwelling_house",
    "home": "dwelling_house",
    "duplex": "dual_occupancy",
    "townhouse": "multi_dwelling_housing",
    "townhouses": "multi_dwelling_housing",
    "villa": "multi_dwelling_housing",
    "apartment": "residential_flat_building",
    "apartments": "residential_flat_building",
    "unit block": "residential_flat_building",
    "doctor": "medical_centre",
    "doctors surgery": "medical_centre",
    "surgery": "medical_centre",
    "dentist": "medical_centre",
    "physio": "medical_centre",
    "gymnasium": "gym",
    "fitness centre": "gym",
    "pub": "hotel",
    "bar": "hotel",
    "tavern": "hotel",
    "church": "place_of_worship",
    "mosque": "place_of_worship",
    "temple": "place_of_worship",
    "factory": "industry",
    "workshop": "industry",
    "storage": "warehouse",
    "storage shed": "warehouse",
    "store": "shop",
    "supermarket": "shop",
    "retail shop": "shop",
    "hardware store": "bulky_goods",
    "furniture store": "bulky_goods",

    # Standard Instrument land use terms.
    #
    # The keys in PARKING_RATES are colloquial ("cafe", "gym", "warehouse") but
    # the tool schemas tell callers to use the LEP's own wording — get_definition
    # and check_permissibility read the land use table in exactly these terms,
    # and generate_see_draft passes one `proposed_use` to both. So a term that
    # resolves for permissibility has to resolve for parking, or the SEE quietly
    # loses its parking section: "restaurant or cafe" is the example in
    # generate_see_draft's own schema and it matched nothing here.
    #
    # Only terms whose parking entry names the same use in its `dcp_use` are
    # mapped. Parent categories (retail premises, food and drink premises,
    # commercial premises) are deliberately absent — they span uses with
    # different rates, so resolving them to one would be a guess, and the
    # resolver's suggestions are the better answer.
    "restaurant or cafe": "cafe",
    "take away food and drink premises": "take_away",
    "warehouse or distribution centre": "warehouse",
    "hotel or motel accommodation": "hotel",
    "recreation facility indoor": "gym",
    "recreation facility (indoor)": "gym",
    "centre based child care facility": "childcare_centre",
    "light industries": "industry",
    "general industries": "industry",
}

DEFINITION_SYNONYMS = {
    "granny flat": "secondary_dwelling",
    "cafe": "restaurant_or_cafe",
    "coffee shop": "restaurant_or_cafe",
    "restaurant": "restaurant_or_cafe",
    "takeaway": "take_away_food_and_drink_premises",
    "take away": "take_away_food_and_drink_premises",
    "fast food": "take_away_food_and_drink_premises",
    "house": "dwelling_house",
    "home": "dwelling_house",
    "duplex": "dual_occupancy",
    "townhouse": "multi_dwelling_housing",
    "apartment": "residential_flat_building",
    "apartments": "residential_flat_building",
    "flats": "residential_flat_building",
    "unit block": "residential_flat_building",
    "child care": "centre_based_child_care_facility",
    "childcare": "centre_based_child_care_facility",
    "childcare centre": "centre_based_child_care_facility",
    "daycare": "centre_based_child_care_facility",
    "preschool": "centre_based_child_care_facility",
    "bnb": "bed_and_breakfast_accommodation",
    "b and b": "bed_and_breakfast_accommodation",
    "airbnb": "bed_and_breakfast_accommodation",
    "corner shop": "neighbourhood_shop",
    "milk bar": "neighbourhood_shop",
    "motel": "hotel_or_motel_accommodation",
    "hotel": "hotel_or_motel_accommodation",
    "pub": "hotel_or_motel_accommodation",
    "working from home": "home_occupation",
    "home office": "home_occupation",
    "home based business": "home_business",
    "mechanic": "vehicle_repair_station",
    "panel beater": "vehicle_repair_station",
    "gym": "recreation_facility_indoor",
    "shop top": "shop_top_housing",
    "factory": "general_industries",
    "warehouse": "warehouse_or_distribution_centre",
    "storage": "warehouse_or_distribution_centre",
}

SEE_SECTION_SYNONYMS = {
    "site": "site_description",
    "the site": "site_description",
    "description of the site": "site_description",
    "proposal": "proposal_description",
    "the proposal": "proposal_description",
    "development description": "proposal_description",
    "planning": "planning_framework",
    "planning controls": "planning_framework",
    "statutory planning": "planning_framework",
    "impacts": "environmental_impacts",
    "environmental impact": "environmental_impacts",
    "effects": "environmental_impacts",
    "mitigation": "mitigation_measures",
    "management measures": "mitigation_measures",
    "section 4.15": "section_4_15_matters",
    "s4.15": "section_4_15_matters",
    "4.15": "section_4_15_matters",
    "heads of consideration": "section_4_15_matters",
}

MINOR_DEVELOPMENT_SYNONYMS = {
    "dwelling": "dwelling_single_storey",
    "house": "dwelling_single_storey",
    "single storey dwelling": "dwelling_single_storey",
    "single storey house": "dwelling_single_storey",
    "new dwelling": "dwelling_single_storey",
    "addition": "residential_addition_single_storey",
    "additions": "residential_addition_single_storey",
    "extension": "residential_addition_single_storey",
    "alteration": "residential_addition_single_storey",
    "alterations and additions": "residential_addition_single_storey",
    "renovation": "residential_addition_single_storey",
    "shed": "ancillary_residential_structure",
    "garage": "ancillary_residential_structure",
    "carport": "ancillary_residential_structure",
    "pool": "ancillary_residential_structure",
    "swimming pool": "ancillary_residential_structure",
    "deck": "ancillary_residential_structure",
    "patio": "ancillary_residential_structure",
    "pergola": "ancillary_residential_structure",
    "strata": "strata_subdivision",
}


# Development types for get_da_checklist. This tool never received the loose
# resolution the others got in 3.1/3.2, so "change of use" — with spaces, the
# way anybody writes it — was refused while "change_of_use" worked, on the most
# common business DA type of all. See PLAN.md 1.1.
#
# Business use words point at `commercial` rather than `change_of_use` because
# the two are not the same question: a new building is commercial, taking over
# an existing tenancy is a change of use. Both entries cross-reference the
# other, so a caller who picks the wrong one is told.
CHECKLIST_SYNONYMS = {
    # taking over existing premises
    "change of use": "change_of_use",
    "change use": "change_of_use",
    "use change": "change_of_use",
    "fitout": "change_of_use",
    "fit out": "change_of_use",
    "shop fitout": "change_of_use",
    "new tenancy": "change_of_use",
    "tenancy": "change_of_use",
    "occupy": "change_of_use",
    "existing building": "change_of_use",
    "conversion": "change_of_use",
    "convert": "change_of_use",

    # business uses — a new commercial building or premises
    "business": "commercial",
    "cafe": "commercial",
    "coffee shop": "commercial",
    "restaurant": "commercial",
    "food premises": "commercial",
    "takeaway": "commercial",
    "take away": "commercial",
    "bar": "commercial",
    "pub": "commercial",
    "shop": "commercial",
    "retail": "commercial",
    "store": "commercial",
    "office": "commercial",
    "gym": "commercial",
    "fitness": "commercial",
    "salon": "commercial",
    "hairdresser": "commercial",
    "barber": "commercial",
    "medical centre": "commercial",
    "clinic": "commercial",
    "childcare": "commercial",
    "child care": "commercial",
    "brewery": "commercial",
    "bakery": "commercial",

    # industrial
    "industry": "industrial",
    "industrial": "industrial",
    "factory": "industrial",
    "workshop": "industrial",
    "warehouse": "industrial",
    "storage": "industrial",
    "manufacturing": "industrial",

    # residential
    "house": "dwelling",
    "home": "dwelling",
    "dwelling house": "dwelling",
    "residential": "dwelling",
    "granny flat": "dwelling",
    "secondary dwelling": "dwelling",
    "dual occupancy": "dwelling",
    "duplex": "dwelling",

    # other
    "subdivide": "subdivision",
    "sign": "signage",
    "signs": "signage",
    "advertising": "signage",
    "advertisement": "signage",
    "demolish": "demolition",
    "demolition": "demolition",
    "knock down": "demolition",
}


# What a business calls its sign, mapped to what DCP Chapter 9 calls it.
# Nobody walks in asking for a "portable footpath sign" — they ask about the
# A-frame they have already bought, which is the one Chapter 9 says is not
# permissible. Getting that term to resolve is most of the value here.
SIGNAGE_SYNONYMS = {
    # portable footpath signs — the trap, and the most-used words for it
    "a frame": "portable_footpath_sign",
    "a-frame": "portable_footpath_sign",
    "a frame sign": "portable_footpath_sign",
    "sandwich board": "portable_footpath_sign",
    "sandwich board sign": "portable_footpath_sign",
    "footpath sign": "portable_footpath_sign",
    "pavement sign": "portable_footpath_sign",
    "portable sign": "portable_footpath_sign",
    "street sign": "portable_footpath_sign",

    # the ordinary shopfront set
    "shopfront sign": "wall_sign",
    "shop front sign": "wall_sign",
    "shop sign": "wall_sign",
    "business sign": "business_identification_sign",
    "name sign": "business_identification_sign",
    "identification sign": "business_identification_sign",
    "fence sign": "wall_sign",
    "painted wall": "wall_sign",
    "mural": "wall_sign",
    "window decal": "window_sign",
    "window graphics": "window_sign",
    "window lettering": "window_sign",
    "glass sign": "window_sign",
    "facia sign": "fascia_sign",
    "awning fascia": "fascia_sign",
    "awning sign": "awning_sign_below",
    "under awning": "awning_sign_below",
    "under awning sign": "awning_sign_below",
    "underawning sign": "awning_sign_below",
    "hanging sign": "awning_sign_below",
    "above awning": "awning_sign_above",
    "on awning": "awning_sign_above",
    "verandah sign": "awning_sign_above",
    "door sign": "top_hamper_sign",
    "doorway sign": "top_hamper_sign",
    "transom sign": "top_hamper_sign",

    # menu boards — a café's word, and it matters which one they mean
    "menu board": "chalkboard_sign",
    "menu sign": "chalkboard_sign",
    "blackboard": "chalkboard_sign",
    "blackboard sign": "chalkboard_sign",
    "specials board": "chalkboard_sign",

    # freestanding and projecting
    "pylon": "pylon_sign",
    "pole sign": "pylon_sign",
    "freestanding sign": "pylon_sign",
    "free standing sign": "pylon_sign",
    "directory board": "pylon_sign",
    "directory sign": "pylon_sign",
    "blade sign": "projecting_wall_sign",
    "projecting sign": "projecting_wall_sign",

    # illuminated and moving
    "neon": "illuminated_sign",
    "neon sign": "illuminated_sign",
    "led sign": "illuminated_sign",
    "lit sign": "illuminated_sign",
    "backlit sign": "illuminated_sign",
    "light box": "illuminated_sign",
    "lightbox": "illuminated_sign",
    "digital sign": "animated_sign",
    "flashing sign": "animated_sign",
    "moving sign": "animated_sign",
    "electronic sign": "animated_sign",

    # roof, billboard and the rest
    "roof sign": "sky_roof_fin_sign",
    "sky sign": "sky_roof_fin_sign",
    "fin sign": "sky_roof_fin_sign",
    "billboard": "advertising_billboard",
    "hoarding": "advertising_billboard",
    "banner": "temporary_sign",
    "flag": "temporary_sign",
    "flags": "temporary_sign",
    "event sign": "temporary_sign",
    "balloon": "blimp_balloon_sign",
    "blimp": "blimp_balloon_sign",
    "inflatable": "blimp_balloon_sign",
    "for sale sign": "real_estate_sign",
    "for lease sign": "real_estate_sign",
    "tourist signage": "tourist_sign",
    "highway sign": "tourist_sign",
    "brown sign": "tourist_sign",
}
