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

    def test_whichever_is_greater_takes_the_greater(self):
        """80m² café: 40 seats + 6 staff = 16.34 → 17; area basis gives 12."""
        result = estimate_spaces(PARKING_RATES["cafe"], 80, {"seats": 40, "employees": 6})
        assert result["spaces_required"] == 17
        assert any("greater" in b for b in result["basis"])

    def test_whichever_is_greater_falls_back_to_area_alone(self):
        """With no seat or staff count the seats basis cannot be evaluated, so
        the area alternative carries it — 15 per 100m² of 80m² = 12."""
        assert estimate_spaces(PARKING_RATES["cafe"], 80)["spaces_required"] == 12

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
