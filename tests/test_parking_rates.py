"""Parking rates match DCP Chapter 7, and the estimator applies them honestly.

PLAN.md item 0.3. The previous rates did not match the DCP and the errors were
not marginal — `dwelling_house` carried the *dual occupancy* rule, `warehouse`
overstated by 3x, and `restaurant`/`cafe` used a basis that appears nowhere in
Schedule 1. Parking is what a CBD assessment argues about, so understating sends
a DA back and overstating can talk someone out of a viable proposal.

The rates are stored verbatim because Schedule 1 is a three-column PDF table
that cannot be diffed structurally with confidence. `TestRatesAreInTheDCP` is
therefore the real guarantee: every stored string must still appear in the
document.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_parking_rates import normalise, schedule_text  # noqa: E402

from lismore_da_mcp.data.parking import PARKING_RATES  # noqa: E402
from lismore_da_mcp.parking import estimate_spaces  # noqa: E402

SOURCED = {k: v for k, v in PARKING_RATES.items() if v.get("dcp_use")}


@pytest.fixture(scope="module")
def schedule():
    return normalise(schedule_text())


class TestRatesAreInTheDCP:
    @pytest.mark.parametrize("key", sorted(SOURCED))
    def test_rate_appears_verbatim(self, key, schedule):
        entry = PARKING_RATES[key]
        assert normalise(entry["rate"]) in schedule, (
            f"{key}: the stored rate is not in Chapter 7 Schedule 1. Either the chapter was "
            f"reissued or the transcription drifted.\n  stored: {entry['rate']}")

    @pytest.mark.parametrize("key", sorted(SOURCED))
    def test_every_sourced_entry_cites_a_page(self, key):
        assert "p" in PARKING_RATES[key]["source"]

    def test_uses_absent_from_the_schedule_carry_no_number(self):
        """The old file gave take-away and secondary dwellings confident rates
        with no basis in the DCP at all. Saying so beats inventing one."""
        for key in ("take_away", "secondary_dwelling"):
            entry = PARKING_RATES[key]
            assert entry["dcp_use"] is None
            assert entry["spec"] is None
            assert "no entry" in entry["rate"]
            assert entry["note"]


class TestCorrectionsStick:
    """The specific values that were wrong. Named individually so a regression
    reads as the fault it is rather than a diff in a blob."""

    @pytest.mark.parametrize("key,fragment", [
        ("warehouse", "1 per 300m2"),                 # was 1 per 100m2 — overstated 3x
        ("dwelling_house", "2 per dwelling"),         # was the dual occupancy rule
        ("dual_occupancy", "<125m2"),                 # was a flat 1 per dwelling
        ("industry", "1 per 100m2"),                  # was 1 per 75m2
        ("shop", "4.4 per 100m2"),                    # was 1 per 25m2
        ("office", "1 per 30m2"),                     # was a flat 1 per 40m2
        ("gym", "plus 1 per 2 employees"),            # employees component was missing
        ("medical_centre", "plus 1 per employee"),    # employees component was missing
    ])
    def test_value(self, key, fragment):
        assert fragment in PARKING_RATES[key]["rate"]

    def test_restaurant_uses_the_dcp_basis(self):
        """Was "1 per 10m² dining area", which is in no part of Schedule 1."""
        rate = PARKING_RATES["cafe"]["rate"]
        assert "1 per 3 seats" in rate and "15 per 100m2 GFA" in rate
        assert "dining area" not in rate

    def test_unit_tiers_are_the_dcp_tiers(self):
        """Was "1 per 1-bed, 1.5 per 2+ bed, 1 visitor per 4"; the DCP has a
        separate 3-bedroom rate and a 1-per-5 visitor ratio."""
        for key in ("multi_dwelling_housing", "residential_flat_building"):
            rate = PARKING_RATES[key]["rate"]
            assert "2 per 3 bedroom unit" in rate
            assert "1 per 5 units visitor" in rate


class TestEstimator:
    def test_simple_area_rate(self):
        result = estimate_spaces(PARKING_RATES["warehouse"], 600)
        assert result["spaces_required"] == 2

    def test_part_of_a_space_rounds_up(self):
        assert estimate_spaces(PARKING_RATES["warehouse"], 601)["spaces_required"] == 3

    # The café rule: staff spaces are added, and the greater is taken between the
    # two measures of customer capacity. See the note above `_RESTAURANT` in
    # data/parking.py for the evidence, and `TestTheCafeReading` below for what
    # this replaced and why the change is invisible on the first case here.
    @pytest.mark.parametrize("area,seats,staff,expected,carried_by", [
        (80, 40, 6, 17, "seats"),       # seats basis 13.3 beats area basis 12
        (80, 20, 6, 15, "area"),        # area basis 12 beats seats basis 6.7
        (150, 30, 8, 27, "area"),
        (60, 50, 4, 19, "seats"),
    ])
    def test_cafe_adds_staff_to_the_greater_customer_basis(
            self, area, seats, staff, expected, carried_by):
        result = estimate_spaces(
            PARKING_RATES["cafe"], area, {"seats": seats, "employees": staff})
        assert result["spaces_required"] == expected
        basis = " ".join(result["basis"])
        assert "employees at 1 per 2" in basis, "the staff component is always added"
        assert ("seats at 1 per 3" in basis) == (carried_by == "seats")
        assert ("per 100m²" in basis) == (carried_by == "area")

    def test_whichever_is_greater_falls_back_to_what_can_be_evaluated(self):
        """With no seat or staff count only the area measure can be worked out,
        so it carries the customer component alone — 15 per 100m² of 80m² = 12."""
        result = estimate_spaces(PARKING_RATES["cafe"], 80)
        assert result["spaces_required"] == 12
        assert not any("greater" in b for b in result["basis"]), (
            "nothing was compared, so the basis should not claim a comparison"
        )

    def test_a_whole_rule_alternation_still_alternates_wholesale(self):
        """`greater_of` sits inside a sum; `or_alt` replaces the sum entirely.
        The boarding house offers two complete formulas and takes the larger —
        that must not have been changed by the café fix."""
        result = estimate_spaces(PARKING_RATES["boarding_house"], None,
                                 {"beds": 30, "rooms": 20})
        assert result["spaces_required"] == 24   # 20 rooms + 20/5 beats 30/3 + 30/5

    def test_minimum_is_applied(self):
        """A 50m² office computes 1.67 → 2, which is also the DCP minimum."""
        result = estimate_spaces(PARKING_RATES["office"], 20)
        assert result["spaces_required"] == 2
        assert any("minimum" in b for b in result["basis"])

    @pytest.mark.parametrize("area,expected", [
        (400, 12),    # 3 per 100m² tier
        (401, 9),     # tips into the 2 per 100m² tier
        (1000, 20),
    ])
    def test_tiered_rate(self, area, expected):
        assert estimate_spaces(PARKING_RATES["bulky_goods"], area)["spaces_required"] == expected

    def test_counted_components(self):
        """Medical centre: 4 per practitioner plus 1 per employee."""
        result = estimate_spaces(
            PARKING_RATES["medical_centre"], None, {"practitioners": 3, "employees": 4})
        assert result["spaces_required"] == 16

    def test_declines_when_the_rule_cannot_be_applied(self):
        assert estimate_spaces(PARKING_RATES["take_away"], 100) is None
        assert estimate_spaces(PARKING_RATES["dual_occupancy"], 200) is None

    def test_declines_when_the_inputs_are_missing(self):
        assert estimate_spaces(PARKING_RATES["medical_centre"], None, {}) is None

    def test_result_carries_the_rule_and_the_source(self):
        result = estimate_spaces(PARKING_RATES["warehouse"], 600)
        assert result["rate"] == PARKING_RATES["warehouse"]["rate"]
        assert "Schedule 1" in result["source"]

    def test_uncounted_inputs_are_named_not_hidden(self):
        """A gym rate has an employees component; without a count the figure is
        an undercount, and the caller has to be told which part is missing."""
        result = estimate_spaces(PARKING_RATES["gym"], 250)
        assert any("not counted" in b for b in result["basis"])


class TestToolSurface:
    def test_a_business_gets_the_dcp_use_and_page(self, call):
        result = call("get_parking_rates", {"development_type": "cafe"})
        assert result["dcp_land_use"] == "Restaurant or cafe"
        assert "p14" in result["source"]

    def test_an_unsourced_use_explains_rather_than_guessing(self, call):
        result = call("get_parking_rates",
                      {"development_type": "take_away", "floor_area_sqm": 60})
        assert "calculation" not in result
        assert "no_calculation" in result
        assert "Duty Planner" in result["what_to_check"]

    def test_shortfall_is_still_reported(self, call):
        result = call("get_parking_rates", {
            "development_type": "cafe", "floor_area_sqm": 80,
            "seats": 40, "num_employees": 6, "spaces_provided": 4})
        assert result["calculation"]["shortfall"] == 13


class TestTheCafeReading:
    """Why the café rule computes the way it does.

    Schedule 1's wording — "1 per 3 seats, plus 1 per 2 employees or 15 per
    100m2 GFA (whichever is greater)" — does not say what "(whichever is
    greater)" governs. Three readings were on the table:

        A   max(seats + employees, GFA)   used until 2026-08-02
        B   seats + max(employees, GFA)   considered and rejected
        C   employees + max(seats, GFA)   implemented

    C follows Tweed Shire Council's 2018 cross-council review, which cites this
    exact schedule and splits the rate into a staff column (1/2 employees) and a
    customer column (1/3 seats or 15/100m2 GFA whichever is greater), and follows
    the schedule's own drive-through entry, where the two customer measures sit
    adjacent and the wording is unambiguous.

    These tests exist because **A and C agree on the example this repo uses
    everywhere** — 80m², 40 seats, 6 staff returns 17 under both. Nothing in the
    suite would have noticed the change, and nothing would notice it reverting.
    """

    def _spaces(self, area, seats, staff):
        return estimate_spaces(
            PARKING_RATES["cafe"], area, {"seats": seats, "employees": staff}
        )["spaces_required"]

    def test_the_staff_component_is_never_dropped(self):
        """Reading A could discard the staff spaces entirely when the floor-area
        basis won. Under C they are always added."""
        # 80m², 20 seats, 6 staff: area basis 12 wins on the customer side, and
        # A returned exactly 12 — the six staff vanished.
        assert self._spaces(80, 20, 6) == 15
        assert self._spaces(80, 20, 0) == 12
        assert self._spaces(80, 20, 6) - self._spaces(80, 20, 0) == 3

    @pytest.mark.parametrize("area,seats,staff,reading_a", [
        (80, 20, 6, 12),
        (150, 30, 8, 23),
        (200, 10, 10, 30),
    ])
    def test_the_previous_reading_understated(self, area, seats, staff, reading_a):
        """Every case where the two readings differ, they differ in the direction
        that sends a DA back for insufficient parking."""
        assert self._spaces(area, seats, staff) > reading_a

    def test_the_rejected_reading_is_not_what_is_implemented(self):
        """Reading B — seats plus the greater of staff or area — would give 26 on
        the worked example. It was rejected: Tweed's review contradicts it, and it
        compares staff numbers against floor area, which are not measures of the
        same thing."""
        assert self._spaces(80, 40, 6) == 17

    def test_the_ambiguity_is_disclosed_to_the_applicant(self):
        """The reading is defensible but it is still a reading, and the applicant
        is the one who bears a wrong number."""
        note = PARKING_RATES["cafe"]["note"]
        assert "leaves it open" in note
        assert "Confirm with Council" in note

    def test_the_verbatim_rate_still_matches_the_dcp(self, schedule):
        """The interpretation lives in `spec` and `note`. `rate` is the DCP's own
        wording and must never be edited to match an interpretation of it."""
        assert normalise(PARKING_RATES["cafe"]["rate"]) in schedule
