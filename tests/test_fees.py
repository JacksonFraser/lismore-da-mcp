"""DA fee calculation.

Bracket base fees and per-$1,000 increments are checked against the bundled
official source: documents/fees/fees-and-charges-2026-27.pdf (page 30), the row
group stating it is "fixed by Schedule 4 Part 2 Item 2.1 of the EP & A
Regulations".

TestScheduleCurrency exists because the scale sat on 2024-25 until 2026-08-01 —
two missed July resets, quoting figures ~6.5% low, on the one number a business
comes here for. Nothing failed, because nothing was checking.
"""

from datetime import date

import pytest

from lismore_da_mcp.data.fees import (
    DA_FEE_SCHEDULE_YEAR,
    current_financial_year,
    financial_years_behind,
    schedule_status,
)
from lismore_da_mcp.fees import estimate_total_cost
from lismore_da_mcp.server import calculate_da_fee


class TestBrackets:
    """Boundary values, where an off-by-one in a bracket condition would show."""

    @pytest.mark.parametrize(
        "cost,expected",
        [
            (0, 153.00),
            (1, 153.00),
            (5_000, 153.00),  # top of the flat bracket
            # $1 above a floor is "part $1,000", so one whole increment applies.
            (5_001, 235.00 + 3.00),
            (250_001, 1_608.00 + 2.34),
            (500_001, 2_420.00 + 1.64),
            (1_000_001, 3_625.00 + 1.44),
            (10_000_001, 22_009.00 + 1.19),
        ],
    )
    def test_bracket_floor(self, cost, expected):
        assert calculate_da_fee(cost)["estimated_fee"] == pytest.approx(expected, abs=0.01)

    @pytest.mark.parametrize(
        "cost,expected",
        [
            (50_000, 235.00 + 3.00 * 45),
            (250_000, 488.00 + 3.64 * 200),
            (500_000, 1_608.00 + 2.34 * 250),
            (1_000_000, 2_420.00 + 1.64 * 500),
            (10_000_000, 3_625.00 + 1.44 * 9_000),
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
            (5_500, 235.00 + 3.00 * 1),      # $500 over → 1 part-thousand
            (5_001, 235.00 + 3.00 * 1),      # $1 over → still 1 part-thousand
            (51_500, 488.00 + 3.64 * 2),     # $1,500 over → 2
            (250_500, 1_608.00 + 2.34 * 1),
        ],
    )
    def test_part_thousand_rounds_up(self, cost, expected):
        assert calculate_da_fee(cost)["estimated_fee"] == pytest.approx(expected, abs=0.01)

    def test_whole_thousands_are_not_rounded_up_further(self):
        """An exact multiple must charge exactly that many, not one extra."""
        assert calculate_da_fee(6_000)["estimated_fee"] == pytest.approx(235.00 + 3.00, abs=0.01)

    def test_never_undercharges_against_linear(self):
        for cost in range(5_001, 50_000, 137):
            linear = 235.00 + 3.00 * ((cost - 5_000) / 1000)
            assert calculate_da_fee(cost)["estimated_fee"] >= linear - 0.01


class TestResponseShape:
    def test_keys_present(self):
        result = calculate_da_fee(250_000)
        assert set(result) >= {"estimated_fee", "development_cost", "cost_estimate_requirement", "note"}

    def test_echoes_cost(self):
        assert calculate_da_fee(123_456)["development_cost"] == 123_456

    def test_states_which_schedule_year(self):
        result = calculate_da_fee(250_000)
        assert result["fee_schedule_year"] == DA_FEE_SCHEDULE_YEAR

    def test_warns_that_fees_reset_annually(self):
        assert "july" in calculate_da_fee(250_000)["currency_warning"].lower()


class TestScheduleCurrency:
    """The scale must not silently go stale again.

    Statutory fees are re-set every July. The previous version carried a
    standing "confirm this figure" caveat on every answer, which is precisely
    why two missed resets went unnoticed — a warning that is always present
    carries no information.
    """

    @pytest.mark.parametrize("today,expected", [
        (date(2026, 8, 1), "2026-27"),
        (date(2026, 7, 1), "2026-27"),    # first day of the new FY
        (date(2026, 6, 30), "2025-26"),   # last day of the old one
        (date(2027, 1, 15), "2026-27"),   # January is still the FY that began in July
    ])
    def test_financial_year_boundaries(self, today, expected):
        assert current_financial_year(today) == expected

    def test_schedule_is_not_two_years_behind(self):
        """Fails when the scale has missed two July resets.

        One year of lag is tolerated: the new schedule is not always published
        the moment the financial year turns. Two means nobody is looking.

        To fix: get the current figures (Council's fees and charges PDF carries
        the Schedule 4 scale — see documents/fees/), update DA_FEE_BRACKETS and
        DA_FEE_SCHEDULE_YEAR in data/fees.py, and record where they came from.
        """
        behind = financial_years_behind()
        assert behind < 2, (
            f"The DA fee scale is {DA_FEE_SCHEDULE_YEAR} but the current financial year is "
            f"{current_financial_year()} — {behind} resets behind. Every fee this server "
            "quotes is wrong. See data/fees.py."
        )

    def test_no_stale_warning_while_current(self):
        assert schedule_status(date(2026, 8, 1)) is None
        assert "⚠️ FEE SCHEDULE OUT OF DATE" not in calculate_da_fee(250_000)

    def test_stale_warning_appears_once_behind(self):
        status = schedule_status(date(2028, 8, 1))
        assert status is not None
        assert status["financial_years_behind"] == 2
        assert "likely higher" in status["what_this_means"]
        assert "Do not budget from it" in status["what_this_means"]

    def test_warning_names_both_years_so_the_gap_is_obvious(self):
        status = schedule_status(date(2027, 9, 1))
        assert status["schedule_used"] == DA_FEE_SCHEDULE_YEAR
        assert status["current_financial_year"] == "2027-28"


class TestTheTotalSaysWhatItRestsOn:
    """ROADMAP.md S3, at the surface where the number reaches a budget.

    `estimate_total_cost` folds the Section 7.11 contribution into
    `budget_at_least`, and for a change of use that figure is the *net* of the
    section 2.7 allowance. Where the previous use's size was assumed rather than
    stated, the total was a $0 that looked like a finding.
    """

    def test_an_expansion_reaches_the_budget(self):
        """The restaurant going 100m² -> 140m². Worth about $8,000, and it used
        to be $0 with no way for the caller to correct it."""
        result = estimate_total_cost(
            80_000, development_type="restaurant",
            counts={"gross_floor_area_m2": 140}, catchment="urban",
            existing_use="restaurant",
            existing_counts={"gross_floor_area_m2": 100},
        )
        contribution = result["parts"]["section_7_11_contributions"]
        assert contribution["net_contribution"]["urban"] == 8040.62
        assert result["budget_at_least"] == 8717.82
        assert "what_this_total_assumes" not in contribution

    def test_an_assumed_net_says_so_where_the_number_is(self):
        """Same proposal, previous area not stated. The default stands, but the
        caveat is no longer three levels down under the allowance."""
        result = estimate_total_cost(
            80_000, development_type="restaurant",
            counts={"gross_floor_area_m2": 140}, catchment="urban",
            existing_use="restaurant",
        )
        contribution = result["parts"]["section_7_11_contributions"]
        assert contribution["net_contribution"]["urban"] == 0.0
        assert "existing_gross_floor_area_m2" in contribution["what_this_total_assumes"]

    def test_the_shop_to_cafe_nil_is_unchanged(self):
        """CLAUDE.md's flagship example. A same-tenancy change of use to a
        lower-demand rate genuinely owes nothing, and S3 must not turn that into
        a caveat-laden non-answer."""
        result = estimate_total_cost(
            0, development_type="cafe", counts={"gross_floor_area_m2": 80},
            catchment="urban", existing_use="shop",
        )
        assert result["parts"]["section_7_11_contributions"]["net_contribution"]["urban"] == 0.0
