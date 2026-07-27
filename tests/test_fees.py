"""DA fee calculation.

Bracket base fees and per-$1,000 increments are checked against the bundled
official source, documents/fees/nsw-planning-fees-2024-25.pdf (page 2), which
sets out Schedule 4 of the EP&A Regulation 2021 for the 2024/25 year.
"""

import pytest

from lismore_da_mcp.server import calculate_da_fee


class TestBrackets:
    """Boundary values, where an off-by-one in a bracket condition would show."""

    @pytest.mark.parametrize(
        "cost,expected",
        [
            (0, 144.00),
            (1, 144.00),
            (5_000, 144.00),  # top of the flat bracket
            # $1 above a floor is "part $1,000", so one whole increment applies.
            (5_001, 220.00 + 3.00),
            (250_001, 1_509.00 + 2.34),
            (500_001, 2_272.00 + 1.64),
            (1_000_001, 3_404.00 + 1.44),
            (10_000_001, 20_667.00 + 1.19),
        ],
    )
    def test_bracket_floor(self, cost, expected):
        assert calculate_da_fee(cost)["estimated_fee"] == pytest.approx(expected, abs=0.01)

    @pytest.mark.parametrize(
        "cost,expected",
        [
            (50_000, 220.00 + 3.00 * 45),
            (250_000, 459.00 + 3.64 * 200),
            (500_000, 1_509.00 + 2.34 * 250),
            (1_000_000, 2_272.00 + 1.64 * 500),
            (10_000_000, 3_404.00 + 1.44 * 9_000),
        ],
    )
    def test_bracket_ceiling(self, cost, expected):
        assert calculate_da_fee(cost)["estimated_fee"] == pytest.approx(expected, abs=0.01)

    def test_brackets_step_up_not_down(self):
        """The NSW scale is genuinely stepped: each bracket's base fee exceeds the
        previous bracket's ceiling. Verify the steps go up, so a rewrite can't
        silently make the fee drop as cost rises."""
        boundaries = [5_000, 50_000, 250_000, 500_000, 1_000_000, 10_000_000]
        for edge in boundaries:
            below = calculate_da_fee(edge)["estimated_fee"]
            above = calculate_da_fee(edge + 1)["estimated_fee"]
            assert above > below, f"fee dropped crossing ${edge:,}"

    def test_fee_is_monotonic(self):
        costs = [0, 4_999, 5_000, 5_001, 20_000, 50_000, 50_001, 100_000, 250_000,
                 250_001, 400_000, 500_000, 500_001, 750_000, 1_000_000, 1_000_001,
                 5_000_000, 10_000_000, 10_000_001, 50_000_000]
        fees = [calculate_da_fee(c)["estimated_fee"] for c in costs]
        assert fees == sorted(fees)


class TestCostEstimateRequirement:
    @pytest.mark.parametrize(
        "cost,expected",
        [
            (0, "Applicant estimate"),
            (100_000, "Applicant estimate"),
            (100_001, "Qualified person estimate"),
            (3_000_000, "Qualified person estimate"),
            (3_000_001, "Registered Quantity Surveyor report"),
        ],
    )
    def test_thresholds(self, cost, expected):
        assert calculate_da_fee(cost)["cost_estimate_requirement"] == expected


class TestPartThousandRounding:
    """Schedule 4 charges the increment 'for each $1,000, or part $1,000' by which
    the cost exceeds the bracket floor, so a partial thousand is charged whole.

    Fixed in IMPROVEMENT_PLAN 1.8; previously interpolated linearly, which
    under-charged every cost that wasn't a round number of thousands.
    """

    @pytest.mark.parametrize(
        "cost,expected",
        [
            (5_500, 220.00 + 3.00 * 1),      # $500 over → 1 part-thousand
            (5_001, 220.00 + 3.00 * 1),      # $1 over → still 1 part-thousand
            (51_500, 459.00 + 3.64 * 2),     # $1,500 over → 2
            (250_500, 1_509.00 + 2.34 * 1),
        ],
    )
    def test_part_thousand_rounds_up(self, cost, expected):
        assert calculate_da_fee(cost)["estimated_fee"] == pytest.approx(expected, abs=0.01)

    def test_whole_thousands_are_not_rounded_up_further(self):
        """An exact multiple must charge exactly that many, not one extra."""
        assert calculate_da_fee(6_000)["estimated_fee"] == pytest.approx(220.00 + 3.00, abs=0.01)

    def test_never_undercharges_against_linear(self):
        for cost in range(5_001, 50_000, 137):
            linear = 220.00 + 3.00 * ((cost - 5_000) / 1000)
            assert calculate_da_fee(cost)["estimated_fee"] >= linear - 0.01


class TestResponseShape:
    def test_keys_present(self):
        result = calculate_da_fee(250_000)
        assert set(result) >= {"estimated_fee", "development_cost", "cost_estimate_requirement", "note"}

    def test_echoes_cost(self):
        assert calculate_da_fee(123_456)["development_cost"] == 123_456

    def test_states_which_schedule_year(self):
        result = calculate_da_fee(250_000)
        assert result["fee_schedule_year"] == "2024-25"

    def test_warns_that_fees_reset_annually(self):
        assert "july" in calculate_da_fee(250_000)["currency_warning"].lower()
