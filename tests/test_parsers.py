"""Address, land identifier and parking-rate parsing.

These feed the SEE PDF, where a wrong result is written into a form box that
goes to Council — so the failure mode is a misfiled application, not an
exception.
"""

import pytest

from lismore_da_mcp.server import (
    estimate_parking_requirement,
    parse_land_identifier,
    parse_street_address,
)


class TestStreetAddress:
    def test_plain_address(self):
        assert parse_street_address("12 Keen Street, Lismore NSW 2480") == {
            "unit": "",
            "street_number": "12",
            "street": "Keen Street",
            "suburb": "Lismore",
        }

    def test_tenancy_prefix_as_own_segment(self):
        """'Shop 3, 88 Keen Street' must not shift the number into the unit box —
        the docstring records this as a previously fixed bug."""
        parsed = parse_street_address("Shop 3, 88 Keen Street, Lismore NSW 2480")
        assert parsed["unit"] == "Shop 3"
        assert parsed["street_number"] == "88"
        assert parsed["street"] == "Keen Street"

    def test_tenancy_prefix_inline(self):
        parsed = parse_street_address("Shop 3 88 Keen Street, Lismore")
        assert parsed["unit"] == "Shop 3"
        assert parsed["street_number"] == "88"

    def test_slashed_street_number_kept_together(self):
        parsed = parse_street_address("1/5 Oliver Ave, Goonellabah NSW 2480")
        assert parsed["street_number"] == "1/5"
        assert parsed["street"] == "Oliver Ave"

    def test_explicit_parts_win_over_free_text(self):
        parsed = parse_street_address(
            "99 Wrong Street, Nowhere", street_number="12", street="Keen Street"
        )
        assert parsed["street_number"] == "12"
        assert parsed["street"] == "Keen Street"

    def test_nsw_and_postcode_stripped_from_suburb(self):
        assert parse_street_address("12 Keen Street, Lismore NSW 2480")["suburb"] == "Lismore"

    def test_empty_input_yields_empty_parts(self):
        assert parse_street_address("") == {
            "unit": "",
            "street_number": "",
            "street": "",
            "suburb": "",
        }

    def test_single_segment_does_not_guess_a_suburb(self):
        """With no comma there is nothing identifying a suburb. Blank is honest;
        reusing the street name would write it into a box on a form that goes to
        Council."""
        parsed = parse_street_address("Keen Street")
        assert parsed["street"] == "Keen Street"
        assert parsed["suburb"] == ""

    def test_explicit_suburb_still_wins_for_a_single_segment(self):
        parsed = parse_street_address("12 Keen Street", suburb="Lismore")
        assert parsed["suburb"] == "Lismore"
        assert parsed["street"] == "Keen Street"


class TestLandIdentifier:
    @pytest.mark.parametrize(
        "text,lot,plan_type,plan_number",
        [
            ("Lot 12 DP 758651", "12", "DP", "758651"),
            ("12/758651", "12", "DP", "758651"),
            ("12 DP 758651", "12", "DP", "758651"),
            ("SP 12345", "", "SP", "12345"),
            ("lot 7 dp 999", "7", "DP", "999"),
        ],
    )
    def test_recognised_forms(self, text, lot, plan_type, plan_number):
        parsed = parse_land_identifier(text)
        assert parsed["lot"] == lot
        assert parsed["plan_type"] == plan_type
        assert parsed["plan_number"] == plan_number

    def test_section_not_mistaken_for_lot(self):
        """'Lot 5 Section 3 DP 1234' — each part is claimed by its own keyword."""
        parsed = parse_land_identifier("Lot 5 Section 3 DP 1234")
        assert parsed["lot"] == "5"
        assert parsed["section"] == "3"
        assert parsed["plan_number"] == "1234"

    def test_explicit_parts_win(self):
        parsed = parse_land_identifier("Lot 99 DP 111", lot="12", plan_number="758651")
        assert parsed["lot"] == "12"
        assert parsed["plan_number"] == "758651"

    def test_empty_returns_blanks_not_none(self):
        assert parse_land_identifier("") == {
            "lot": "",
            "plan_type": "",
            "plan_number": "",
            "section": "",
        }

    def test_unparseable_does_not_raise(self):
        assert parse_land_identifier("the paddock behind the servo")["plan_number"] == ""


class TestParkingEstimate:
    def test_area_based_rate(self):
        result = estimate_parking_requirement("1 space per 10m² dining area", 100, 0)
        assert result["spaces_required"] == 10

    def test_area_and_staff_combined(self):
        result = estimate_parking_requirement("1 space per 25m² GFA + 1 per 2 employees", 250, 4)
        assert result["spaces_required"] == 12  # ceil(10 + 2)

    def test_rounds_up_partial_space(self):
        result = estimate_parking_requirement("1 space per 10m²", 105, 0)
        assert result["spaces_required"] == 11

    def test_returns_none_when_rate_not_numeric(self):
        """Refusing beats guessing — the caller omits the estimate entirely."""
        assert estimate_parking_requirement("as determined by Council", 100, 2) is None

    def test_returns_none_when_no_inputs_supplied(self):
        assert estimate_parking_requirement("1 space per 10m²", 0, 0) is None

    def test_carries_caveat_about_area_basis(self):
        result = estimate_parking_requirement("1 space per 10m² dining area", 100, 0)
        assert "caveat" in result and result["caveat"]
