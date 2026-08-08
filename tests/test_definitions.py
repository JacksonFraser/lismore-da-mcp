"""The land use definitions match the LEP Dictionary they are quoted from.

PLAN.md item 0.7. `data/definitions.py` was the last data module Phase 0 never
audited, and it turned out not to be a transcription at all — its own docstring
said the definitions were "paraphrased for readability", and the paraphrases had
drifted into invention in the way `data/standards.py` had (item 0.6).

Which defined term a proposal falls under decides permissibility, the DCP
Chapter 7 parking rate, and on a change of use whether a section 7.11
contribution is payable. So a definition that says "whether or not goods are
sold by retail" where the LEP says "but from which no retail sales are made" is
not a wording preference — it is the wrong answer to whether a warehouse can
have a shopfront.

These tests re-run `scripts/audit_definitions.py`'s comparisons so the
guarantee survives the next edit to either side, pin the specific corrections by
name so a regression says what broke rather than showing a diff, and check that
the audit *can* fail. A checker that cannot detect a fault manufactures
confidence rather than providing it.
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_definitions import (  # noqa: E402
    check_absences,
    check_categories,
    check_definition_opens_with_its_term,
    check_hierarchy,
    check_quotes,
    check_related_terms,
    check_table_terms,
    dictionary_parents,
    lep_text,
    normalise,
)

from lismore_da_mcp.data.definitions import (  # noqa: E402
    DEFINITION_CATEGORIES,
    FIGURES_NOT_IN_THE_DEFINITION,
    LAND_USE_DEFINITIONS,
    LAND_USE_HIERARCHY,
)


@pytest.fixture(scope="module")
def lep():
    text = lep_text()
    assert "Dictionary" in text, "the LEP text no longer contains a Dictionary"
    return text


class TestQuotedVerbatim:
    @pytest.mark.parametrize("key", sorted(LAND_USE_DEFINITIONS))
    def test_definition_is_in_the_lep(self, key, lep):
        entry = LAND_USE_DEFINITIONS[key]
        assert normalise(entry["definition"]) in lep, (
            f"{key}'s definition is no longer in the LEP Dictionary verbatim. Read the "
            "Dictionary before changing it — this file was paraphrased from memory once "
            "and every figure in it was wrong."
        )

    @pytest.mark.parametrize("key", sorted(LAND_USE_DEFINITIONS))
    def test_definition_opens_with_its_own_term(self, key):
        entry = LAND_USE_DEFINITIONS[key]
        assert normalise(entry["definition"]).startswith(f"{entry['term']} means")

    @pytest.mark.parametrize(
        "key", sorted(k for k, e in LAND_USE_DEFINITIONS.items() if e.get("additional_controls"))
    )
    def test_clause_5_4_control_is_in_the_lep(self, key, lep):
        control = LAND_USE_DEFINITIONS[key]["additional_controls"]
        assert normalise(control["control"]) in lep, (
            f"{key}'s {control['source']} quote is not in the LEP verbatim — the clause may "
            "have been renumbered or amended."
        )

    def test_audit_reports_nothing(self, lep):
        for label, failures in [
            ("quotes", check_quotes(lep)),
            ("terms", check_definition_opens_with_its_term()),
            ("table terms", check_table_terms()),
            ("hierarchy", check_hierarchy(lep)),
            ("related terms", check_related_terms()),
            ("categories", check_categories()),
            ("absences", check_absences()),
        ]:
            assert failures == [], f"{label}:\n" + "\n".join(failures)


class TestTheCorrections:
    """Each of these was wrong in the file before 2026-08-08.

    Named individually so a regression says which one came back rather than
    printing a diff of a 700-line module.
    """

    def test_a_warehouse_makes_no_retail_sales(self):
        """The old file said "whether or not goods are sold by retail" — the
        exact opposite of the LEP, and the difference between a warehouse that
        may have a shopfront and one that may not."""
        definition = LAND_USE_DEFINITIONS["warehouse_or_distribution_centre"]["definition"]
        assert "but from which no retail sales are made" in definition
        assert "whether or not goods are sold by retail" not in definition

    def test_a_neighbourhood_shop_is_200m2_and_not_in_the_definition(self):
        entry = LAND_USE_DEFINITIONS["neighbourhood_shop"]
        assert not re.search(r"\d", entry["definition"]), (
            "the definition of neighbourhood shop contains no figure — the old file put an "
            "80m² cap in it, and the real control is 200m² in clause 5.4(7)"
        )
        assert "200 square metres" in entry["additional_controls"]["control"]
        assert entry["additional_controls"]["source"] == "Lismore LEP 2012 clause 5.4(7)"

    def test_business_premises_has_no_two_day_rule(self, lep):
        definition = LAND_USE_DEFINITIONS["business_premises"]["definition"]
        assert "2 days per week" not in definition
        assert "days per week" not in lep, (
            "'days per week' now appears in the LEP — the old file's '2+ days per week' may "
            "have had a source after all. Check before deleting this assertion."
        )
        assert "on a regular basis" in definition

    def test_business_premises_excludes_a_medical_centre(self):
        """The old exclusion list was office premises, retail premises and
        warehouses — none of which the LEP excludes — and omitted the medical
        centre, which it does. A zone permitting business premises does not
        thereby permit a doctors' surgery."""
        definition = LAND_USE_DEFINITIONS["business_premises"]["definition"]
        assert "medical centre" in definition
        assert "funeral homes" in definition

    def test_home_business_allows_two_employees(self):
        """The old entry described home *industry* — a different term with a
        different permissibility — and lost the allowance that makes home
        business usable for an actual business."""
        entry = LAND_USE_DEFINITIONS["home_business"]
        assert "the employment of more than 2 persons other than the residents" in entry["definition"]
        assert "manufacture, alteration, servicing or repair" not in entry["definition"]
        assert "50 square metres" in entry["additional_controls"]["control"]

    def test_a_boarding_house_must_be_affordable_housing(self):
        """Paragraphs (d) and (e) are the whole of the modern definition and the
        old entry had neither, which made any lodging house look like one."""
        definition = LAND_USE_DEFINITIONS["boarding_house"]["definition"]
        assert "used to provide affordable housing" in definition
        assert "registered community housing provider" in definition

    def test_out_of_school_hours_care_is_child_care(self):
        """The old entry excluded it. Paragraph (a)(iii) includes it; what is
        excluded is *school-based* child care."""
        definition = LAND_USE_DEFINITIONS["centre_based_child_care_facility"]["definition"]
        assert "out-of-school-hours care (including vacation care)" in definition
        assert "school-based child care" in definition

    def test_bed_and_breakfast_is_five_bedrooms(self):
        entry = LAND_USE_DEFINITIONS["bed_and_breakfast_accommodation"]
        assert "no more than 5 bedrooms" in entry["additional_controls"]["control"]
        assert not re.search(r"\d+\s*(?:bedrooms?|guests?)", entry["definition"])

    def test_secondary_dwelling_area_is_the_greater_of_two(self):
        """The old file said "typically 60m²", which understates it — clause
        5.4(9) is the greater of 60m² or a quarter of the principal dwelling."""
        control = LAND_USE_DEFINITIONS["secondary_dwelling"]["additional_controls"]["control"]
        assert "whichever of the following is the greater" in control
        assert "60 square metres" in control
        assert "25% of the total floor area of the principal dwelling" in control

    def test_restaurant_or_cafe_does_not_turn_on_seating(self):
        """The old entry required "seating and dining facilities". The test is
        the principal purpose. Seats price the DCP parking rate; they do not
        decide the term."""
        definition = LAND_USE_DEFINITIONS["restaurant_or_cafe"]["definition"]
        assert "the principal purpose of which is the preparation and serving" in definition
        assert "seating" not in definition

    def test_an_office_is_not_a_type_of_business_premises(self):
        """Both are types of commercial premises and they are mutually
        exclusive. landuse.py walks this chain to answer permissibility from a
        parent term, so the old chain would have reported an office as permitted
        wherever business premises was."""
        assert LAND_USE_HIERARCHY["office premises"] == ["commercial premises"]
        assert LAND_USE_HIERARCHY["business premises"] == ["commercial premises"]

    def test_a_pub_is_food_and_drink_premises(self):
        """DEFINITION_SYNONYMS used to send "pub" to hotel or motel
        accommodation, which is a different term in a different group with a
        different permissibility."""
        assert LAND_USE_HIERARCHY["pub"][0] == "food and drink premises"
        assert "pub" in LAND_USE_DEFINITIONS

    @pytest.mark.parametrize("key,dictionary,table", [
        ("light_industries", "light industry", "Light industries"),
        ("general_industries", "general industry", "General industries"),
        ("attached_dwellings", "attached dwelling", "Attached dwellings"),
        ("recreation_facility_indoor", "recreation facility (indoor)", "Recreation facilities (indoor)"),
    ])
    def test_the_dictionary_term_and_the_table_term_are_both_carried(self, key, dictionary, table):
        """The Dictionary defines the singular; the land use table lists the
        plural. check_permissibility matches the table, so both are needed."""
        entry = LAND_USE_DEFINITIONS[key]
        assert entry["term"] == dictionary
        assert entry["land_use_table_term"] == table


class TestTheAuditCanFail:
    """Each check, given a fault it is supposed to catch.

    The absence check needed this most: its first version searched for the *old
    wording* of each invented figure, so reinventing the identical 80m² cap as
    "80 square metres" passed silently. A reinvention is written in fresh words
    by definition.
    """

    @pytest.fixture
    def restore(self):
        snapshot = {k: dict(v) for k, v in LAND_USE_DEFINITIONS.items()}
        hierarchy = dict(LAND_USE_HIERARCHY)
        yield
        LAND_USE_DEFINITIONS.clear()
        LAND_USE_DEFINITIONS.update(snapshot)
        LAND_USE_HIERARCHY.clear()
        LAND_USE_HIERARCHY.update(hierarchy)

    def test_catches_a_reworded_definition(self, restore, lep):
        entry = LAND_USE_DEFINITIONS["shop"]
        entry["definition"] = entry["definition"].replace("merchandise", "goods")
        assert check_quotes(lep)

    def test_catches_an_altered_clause_5_4_figure(self, restore, lep):
        control = dict(LAND_USE_DEFINITIONS["neighbourhood_shop"]["additional_controls"])
        control["control"] = control["control"].replace("200", "80")
        LAND_USE_DEFINITIONS["neighbourhood_shop"]["additional_controls"] = control
        assert check_quotes(lep)

    def test_catches_a_real_quote_from_the_wrong_term(self, restore):
        """Verbatim LEP text, wrong entry — check_quotes alone would pass it."""
        LAND_USE_DEFINITIONS["shop"]["definition"] = LAND_USE_DEFINITIONS["pub"]["definition"]
        assert check_definition_opens_with_its_term()

    def test_catches_a_table_spelling_that_is_not_in_the_table(self, restore):
        LAND_USE_DEFINITIONS["light_industries"]["land_use_table_term"] = "Light industry"
        assert check_table_terms()

    def test_catches_the_office_premises_error_returning(self, restore, lep):
        LAND_USE_HIERARCHY["office premises"] = ["business premises", "commercial premises"]
        assert check_hierarchy(lep)

    def test_catches_a_dangling_related_term(self, restore):
        LAND_USE_DEFINITIONS["shop"]["related_terms"] = ["bulky_goods_premises"]
        assert check_related_terms()

    def test_catches_an_uncategorised_definition(self, restore):
        LAND_USE_DEFINITIONS["invented_term"] = {"term": "invented term", "definition": "x"}
        assert check_categories()

    @pytest.mark.parametrize("key,old,new", [
        # the same invented control, in four different wordings
        ("neighbourhood_shop", "local area", "local area, not more than 80m²"),
        ("neighbourhood_shop", "local area", "local area, being not more than 80 square metres"),
        ("bed_and_breakfast_accommodation", "commercial basis", "commercial basis for up to 6 bedrooms"),
        ("home_business", "ancillary to a dwelling", "ancillary to a dwelling of up to 50 sqm"),
    ])
    def test_catches_a_figure_reinvented_in_fresh_words(self, restore, key, old, new):
        entry = LAND_USE_DEFINITIONS[key]
        entry["definition"] = entry["definition"].replace(old, new)
        assert check_absences(), (
            f"a reinvented figure in {key} was not detected — check_absences is matching "
            "specific wording again rather than the kind of figure"
        )

    def test_catches_clause_5_4_controls_being_dropped(self, restore):
        del LAND_USE_DEFINITIONS["secondary_dwelling"]["additional_controls"]
        assert check_absences()

    def test_the_legitimate_numbers_do_not_trip_it(self):
        """"3 or more dwellings", "more than 2 persons", "at least 3 months" are
        all in real definitions. An absence check scoped by unit leaves them."""
        assert check_absences() == []


class TestTheHierarchyComesFromTheLep:
    def test_every_first_link_matches_a_dictionary_note(self, lep):
        parents = dictionary_parents(lep)
        assert parents, "the 'is a type of' scan matched nothing — the regex has rotted"
        lowered = {k.lower(): v for k, v in parents.items()}
        mismatched = [
            f"{term!r} starts at {chain[0]!r}, LEP says {lowered[term.lower()]!r}"
            for term, chain in LAND_USE_HIERARCHY.items()
            if term.lower() in lowered and chain and chain[0] != lowered[term.lower()]
        ]
        assert mismatched == [], "\n".join(mismatched)


class TestCoverage:
    def test_every_definition_is_categorised_exactly_once(self):
        flat = [k for keys in DEFINITION_CATEGORIES.values() for k in keys]
        assert len(flat) == len(set(flat)), "a definition is in two categories"
        assert set(flat) == set(LAND_USE_DEFINITIONS)

    def test_the_recorded_inventions_all_name_a_real_entry(self):
        assert set(FIGURES_NOT_IN_THE_DEFINITION) <= set(LAND_USE_DEFINITIONS)

    def test_each_recorded_invention_points_at_the_real_control(self):
        """Recording that a figure is absent is only half the answer — the
        applicant still needs the number, from the clause that actually sets it."""
        for key, record in FIGURES_NOT_IN_THE_DEFINITION.items():
            assert record["source"].startswith("Lismore LEP 2012 clause 5.4")
            assert LAND_USE_DEFINITIONS[key].get("additional_controls"), (
                f"{key} records an absent figure but carries no clause 5.4 control, so the "
                "tool would answer with no figure at all"
            )
