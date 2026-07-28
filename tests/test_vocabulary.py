"""Term resolution.

The risk here is not failing to match — it is matching the *wrong* thing. A
hairdresser given warehouse parking rates is a confident wrong answer, which is
the failure mode validate_arguments() was written to avoid. So the tests are
weighted toward what must NOT resolve.
"""

import pytest

from lismore_da_mcp.data.definitions import LAND_USE_DEFINITIONS
from lismore_da_mcp.data.parking import PARKING_RATES
from lismore_da_mcp.data.see_templates import SEE_TEMPLATES
from lismore_da_mcp.see.fields import SEE_TEMPLATE_SCOPE
from lismore_da_mcp.vocabulary import (
    DEFINITION_SYNONYMS,
    MINOR_DEVELOPMENT_SYNONYMS,
    PARKING_SYNONYMS,
    SEE_SECTION_SYNONYMS,
    normalise,
    resolve,
    squash,
    unresolved_error,
)


class TestNormalisation:
    @pytest.mark.parametrize("raw,expected", [
        ("Child Care Centre", "child_care_centre"),
        ("  spaced  out  ", "spaced_out"),
        ("take-away", "take_away"),
        ("Section 4.15 matters", "section_4_15_matters"),
        ("already_snake", "already_snake"),
    ])
    def test_normalise(self, raw, expected):
        assert normalise(raw) == expected

    @pytest.mark.parametrize("a,b", [
        ("take away", "take_away"),
        ("takeaway", "take_away"),
        ("child care centre", "childcare_centre"),
    ])
    def test_squash_makes_separator_differences_vanish(self, a, b):
        assert squash(a) == squash(b)


class TestResolution:
    def test_exact(self):
        assert resolve("cafe", PARKING_RATES).how == "exact"

    def test_case_and_spacing_only(self):
        r = resolve("Medical Centre", PARKING_RATES)
        assert r.key == "medical_centre"

    def test_squashed_separator_difference(self):
        r = resolve("takeaway", PARKING_RATES)
        assert (r.key, r.how) == ("take_away", "squashed")

    def test_synonym(self):
        r = resolve("coffee shop", PARKING_RATES, PARKING_SYNONYMS)
        assert (r.key, r.how) == ("cafe", "synonym")

    def test_fuzzy_catches_a_typo(self):
        r = resolve("resturant", PARKING_RATES)
        assert (r.key, r.how) == ("restaurant", "fuzzy")

    def test_empty_term_resolves_to_nothing(self):
        assert not resolve("", PARKING_RATES)

    def test_resolution_is_falsy_when_unmatched(self):
        assert not resolve("definitely not a land use", PARKING_RATES)


class TestRefusesToGuess:
    """The important half."""

    @pytest.mark.parametrize("term", ["hairdresser", "brewery", "abattoir", "data centre"])
    def test_absent_uses_do_not_resolve(self, term):
        """These have no rate in Chapter 7. Inventing one is worse than saying so."""
        assert not resolve(term, PARKING_RATES, PARKING_SYNONYMS)

    def test_does_not_suggest_an_unrelated_nearest_neighbour(self):
        """'hairdresser' scores 0.50 against 'warehouse' — close enough for
        difflib, nowhere near close enough to put in front of an applicant."""
        assert "warehouse" not in resolve("hairdresser", PARKING_RATES).suggestions

    def test_does_not_suggest_shop_for_shed(self):
        assert "shop" not in resolve("shed", PARKING_RATES).suggestions

    def test_ambiguous_terms_produce_suggestions_not_a_pick(self):
        """A term sitting between two candidates must not be resolved by coin toss."""
        r = resolve("dwelling", PARKING_RATES)
        if r:  # if it resolves at all it must be the unambiguous one
            assert r.key == "dwelling_house"

    def test_error_payload_names_alternatives(self):
        r = resolve("hairdresser", PARKING_RATES)
        err = unresolved_error("hairdresser", r, "parking rate", PARKING_RATES)
        assert "hairdresser" in err["error"]
        assert err["available_parking_rates"]


class TestSynonymTablesAreValid:
    """A synonym pointing at a key that no longer exists silently stops working."""

    @pytest.mark.parametrize("table,candidates,label", [
        (PARKING_SYNONYMS, PARKING_RATES, "PARKING_SYNONYMS"),
        (DEFINITION_SYNONYMS, LAND_USE_DEFINITIONS, "DEFINITION_SYNONYMS"),
        (SEE_SECTION_SYNONYMS, SEE_TEMPLATES, "SEE_SECTION_SYNONYMS"),
        (MINOR_DEVELOPMENT_SYNONYMS, SEE_TEMPLATE_SCOPE, "MINOR_DEVELOPMENT_SYNONYMS"),
    ])
    def test_every_target_exists(self, table, candidates, label):
        dangling = sorted({v for v in table.values() if v not in candidates})
        assert dangling == [], f"{label} points at missing keys: {dangling}"

    @pytest.mark.parametrize("table", [
        PARKING_SYNONYMS, DEFINITION_SYNONYMS, SEE_SECTION_SYNONYMS, MINOR_DEVELOPMENT_SYNONYMS,
    ])
    def test_no_alias_shadows_a_real_key(self, table):
        """An alias equal to an existing key is dead weight — exact match wins first."""
        assert not [a for a in table if normalise(a) == table[a]]


class TestPlanningVocabulary:
    """The specific phrasings the evaluation found were being rejected."""

    @pytest.mark.parametrize("term,expected", [
        ("granny flat", "secondary_dwelling"),
        ("coffee shop", "cafe"),
        ("takeaway", "take_away"),
        ("child care centre", "childcare_centre"),
        ("duplex", "dual_occupancy"),
        ("doctors surgery", "medical_centre"),
    ])
    def test_parking_phrasings(self, term, expected):
        assert resolve(term, PARKING_RATES, PARKING_SYNONYMS).key == expected

    @pytest.mark.parametrize("term,expected", [
        ("granny flat", "secondary_dwelling"),
        ("cafe", "restaurant_or_cafe"),
        ("airbnb", "bed_and_breakfast_accommodation"),
        ("mechanic", "vehicle_repair_station"),
        ("corner shop", "neighbourhood_shop"),
    ])
    def test_definition_phrasings(self, term, expected):
        assert resolve(term, LAND_USE_DEFINITIONS, DEFINITION_SYNONYMS).key == expected

    @pytest.mark.parametrize("term,expected", [
        ("site description", "site_description"),
        ("the proposal", "proposal_description"),
        ("section 4.15", "section_4_15_matters"),
        ("mitigation", "mitigation_measures"),
    ])
    def test_see_sections(self, term, expected):
        assert resolve(term, SEE_TEMPLATES, SEE_SECTION_SYNONYMS).key == expected

    @pytest.mark.parametrize("term,expected", [
        ("single storey dwelling", "dwelling_single_storey"),
        ("shed", "ancillary_residential_structure"),
        ("carport", "ancillary_residential_structure"),
        ("extension", "residential_addition_single_storey"),
    ])
    def test_minor_development_types(self, term, expected):
        assert resolve(term, SEE_TEMPLATE_SCOPE, MINOR_DEVELOPMENT_SYNONYMS).key == expected
