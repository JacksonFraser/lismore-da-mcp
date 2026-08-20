"""Developer contributions match the plan, and the total is the whole total.

PLAN.md item 2.1. `calculate_da_fees` used to answer "what is the DA lodgement
fee" to a business asking "what will this cost me", and the gap between those is
not a rounding error: for an 80m2 cafe fitout the fee is a few hundred dollars
and the Section 7.11 contribution is around $16,000.

The Section 7.11 rates get a stronger check than the other transcriptions in
this repo. Table E2 is re-derivable from Table E1, so `TestTableE2Derives`
rebuilds all 30 published cells from their components rather than only searching
for them in the PDF — which catches a transposed digit that a presence check
cannot. `TestTheAuditCanFail` then checks the check, because a checker that
cannot detect a fault manufactures confidence rather than providing it.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_contributions import (  # noqa: E402
    DERIVATION_TOLERANCE,
    derive,
    known_discrepancy,
    money_on_page,
    page_text,
    PLAN_PDF,
    TABLE_E1_PAGE,
    TABLE_E2_PAGE,
    formats,
)

from lismore_da_mcp.contributions import (  # noqa: E402
    estimate_contribution,
    resolve_development_type,
)
from lismore_da_mcp.data.contributions import (  # noqa: E402
    CATCHMENTS,
    DEVELOPMENT_TYPE_RATES,
    INFRASTRUCTURE_RATES,
    KNOWN_TABLE_DISCREPANCIES,
    SECTION_64_CHARGES,
)
from lismore_da_mcp.data.fees import DA_FEE_NO_BUILDING_WORK  # noqa: E402
from lismore_da_mcp.fees import calculate_da_fee, estimate_total_cost  # noqa: E402

CELLS = [(key, catchment) for key in DEVELOPMENT_TYPE_RATES for catchment in CATCHMENTS]


@pytest.fixture(scope="module")
def e2_figures():
    return money_on_page(page_text(PLAN_PDF, TABLE_E2_PAGE))


@pytest.fixture(scope="module")
def e1_figures():
    return money_on_page(page_text(PLAN_PDF, TABLE_E1_PAGE))


class TestRatesAreInThePlan:
    @pytest.mark.parametrize("key,catchment", CELLS)
    def test_table_e2_rate_appears(self, key, catchment, e2_figures):
        rate = DEVELOPMENT_TYPE_RATES[key]["rates"][catchment]
        assert any(f in e2_figures for f in formats(rate)), (
            f"{key} ({catchment}) = {rate} is not printed in Table E2. Either the plan has "
            f"been amended or the transcription has drifted — check p7 of {PLAN_PDF.name}."
        )

    @pytest.mark.parametrize("row", range(len(INFRASTRUCTURE_RATES)))
    def test_table_e1_rate_appears(self, row, e1_figures):
        entry = INFRASTRUCTURE_RATES[row]
        for catchment in CATCHMENTS:
            rate = entry["rates"][catchment]
            assert any(f in e1_figures for f in formats(rate)), (
                f"{entry['category']} ({entry['basis']}, {catchment}) = {rate} is not "
                f"printed in Table E1 on p6."
            )

    def test_section_64_charges_carry_no_current_figure(self):
        """The DSP is in 2016 dollars and has no non-residential ET table, so a
        current charge cannot be produced. Storing rates is fine; quoting a total
        would not be."""
        result = estimate_total_cost(50_000)
        s64 = result["parts"]["section_64_water_and_wastewater"]
        assert s64["amount"] is None
        assert "2016" in s64["rates_are_in"]
        assert "only Council can quote it" in s64["why_no_figure"]
        assert set(s64["rates_per_ET"]) == set(SECTION_64_CHARGES)


class TestTableE2Derives:
    """Every published rate rebuilt from its components."""

    @pytest.mark.parametrize("key,catchment", CELLS)
    def test_cell(self, key, catchment):
        published = DEVELOPMENT_TYPE_RATES[key]["rates"][catchment]
        derived = derive(DEVELOPMENT_TYPE_RATES[key], catchment)
        known = known_discrepancy(key, catchment)
        gap = abs(derived - published)
        if known:
            assert gap == pytest.approx(known["difference"], abs=DERIVATION_TOLERANCE), (
                f"{key} ({catchment}) is a recorded discrepancy of "
                f"${known['difference']:.2f} but now differs by ${gap:.2f}."
            )
        else:
            assert gap <= DERIVATION_TOLERANCE, (
                f"{key} ({catchment}) publishes ${published:,.2f} but Table E1 derives "
                f"${derived:,.2f}. Either a figure is mistranscribed or this is a genuine "
                f"discrepancy in the plan — if the latter, add it to "
                f"KNOWN_TABLE_DISCREPANCIES with an explanation."
            )

    def test_the_only_known_discrepancy_is_the_tourist_rural_cell(self):
        """Recorded so it stays a named exception rather than a widened tolerance."""
        recorded = {
            (d["development_type"], c)
            for d in KNOWN_TABLE_DISCREPANCIES for c in d["catchments"]
        }
        assert recorded == {
            ("tourist_accommodation", "rural_north"),
            ("tourist_accommodation", "rural_south"),
        }


class TestTheAuditCanFail:
    """A checker that cannot detect a fault manufactures confidence rather than
    providing it. Each of these corrupts the data the way a real transcription
    error would and asserts the audit notices."""

    def _audit_gap(self, entry, catchment="urban"):
        """What the audit compares: the published figure against its derivation."""
        return abs(derive(entry, catchment) - entry["rates"][catchment])

    def test_a_transposed_digit_in_a_published_rate_is_caught(self):
        real = DEVELOPMENT_TYPE_RATES["retail_premises"]
        assert self._audit_gap(real) <= DERIVATION_TOLERANCE

        # $20,101.55 mistyped as $21,001.55 — two digits swapped, still a
        # plausible-looking figure, and invisible to a text search if the digits
        # happen to appear elsewhere on the page.
        corrupted = dict(real, rates=dict(real["rates"], urban=21_001.55))
        assert self._audit_gap(corrupted) > DERIVATION_TOLERANCE

    def test_a_misplaced_decimal_point_is_caught(self):
        real = DEVELOPMENT_TYPE_RATES["industry"]
        corrupted = dict(real, rates=dict(real["rates"], urban=20_755.70))
        assert self._audit_gap(corrupted) > DERIVATION_TOLERANCE

    def test_a_wrong_occupancy_or_pvt_figure_is_caught(self):
        real = DEVELOPMENT_TYPE_RATES["retail_premises"]
        assert self._audit_gap(dict(real, occupancy=21.7)) > DERIVATION_TOLERANCE
        assert self._audit_gap(dict(real, pvts=1.7)) > DERIVATION_TOLERANCE

    def test_a_rate_absent_from_the_pdf_is_caught(self, e2_figures):
        """The presence half of the audit, shown failing on a figure that is not
        in the document."""
        assert not any(f in e2_figures for f in formats(99_999.99))


class TestResolvingAUseToARate:
    @pytest.mark.parametrize("term,expected", [
        ("cafe", "retail_premises"),
        ("restaurant", "retail_premises"),
        ("shop", "retail_premises"),
        ("takeaway", "retail_premises"),
        ("office", "business_or_office_premises"),
        ("business premises", "business_or_office_premises"),
        ("industry", "industry"),
        ("dwelling house", "dwelling_house"),
        ("retail_premises", "retail_premises"),
    ])
    def test_resolves(self, term, expected):
        key, _ = resolve_development_type(term)
        assert key == expected

    def test_a_use_table_e2_does_not_list_gets_no_rate(self):
        """Table E2 note E sends these to a per-PVT assessment needing a traffic
        report. Quoting the nearest-looking rate instead would be a wrong number
        in a business's budget."""
        result = estimate_contribution("gym", {"gross_floor_area_m2": 200})
        assert result["contribution"] is None
        assert "1.5" in result["why_not"] and "traffic report" in result["why_not"]
        assert "Retail premises" in result["listed_development_types"]

    def test_an_inferred_classification_says_so(self):
        result = estimate_contribution("cafe", {"gross_floor_area_m2": 80}, catchment="urban")
        assert "food and drink premises" in result["interpreted_as"]


class TestTheCatchmentIsNeverGuessed:
    """Rural retail is charged 20% more than urban, so a default would understate."""

    def test_all_catchments_returned_when_none_given(self):
        result = estimate_contribution("cafe", {"gross_floor_area_m2": 100})
        assert set(result["contribution"]) == set(CATCHMENTS)
        assert "Figures 2 and 3" in result["catchment"]

    def test_rural_retail_costs_more_than_urban(self):
        result = estimate_contribution("cafe", {"gross_floor_area_m2": 100})
        assert result["contribution"]["rural_north"] > result["contribution"]["urban"]

    def test_an_unknown_catchment_is_refused(self, call):
        error = call("calculate_da_fees", {"development_cost": 1000, "catchment": "cbd"})
        assert "error" in error
        assert set(error["catchments"]) == set(CATCHMENTS)

    def test_an_unpriced_catchment_is_left_out_of_the_total(self):
        result = estimate_total_cost(
            50_000, development_type="cafe", counts={"gross_floor_area_m2": 80})
        assert "section_7_11_contributions" not in result["what_that_covers"]
        assert "not_added_to_total" in result["parts"]["section_7_11_contributions"]


class TestChangeOfUseAllowance:
    """Section 2.7 — the contribution is charged on the increase in demand only.
    This is the commonest business DA and the provision most likely to decide
    whether a tenancy is viable."""

    def test_shop_to_cafe_attracts_nothing(self):
        result = estimate_contribution(
            "cafe", {"gross_floor_area_m2": 80}, catchment="urban", existing_use="shop")
        assert result["net_contribution"]["urban"] == 0
        assert "no contribution is payable" in (
            result["existing_development_allowance"]["effect"])

    def test_office_to_cafe_is_charged_on_the_step_up(self):
        gfa = 80
        result = estimate_contribution(
            "cafe", {"gross_floor_area_m2": gfa}, catchment="urban", existing_use="office")
        retail = DEVELOPMENT_TYPE_RATES["retail_premises"]["rates"]["urban"] * gfa / 100
        office = DEVELOPMENT_TYPE_RATES["business_or_office_premises"]["rates"]["urban"] * gfa / 100
        assert result["net_contribution"]["urban"] == pytest.approx(retail - office, abs=0.01)

    def test_the_allowance_is_never_negative(self):
        """A move to a lower-demand use does not produce a refund."""
        result = estimate_contribution(
            "office", {"gross_floor_area_m2": 80}, catchment="urban", existing_use="cafe")
        assert result["net_contribution"]["urban"] == 0

    def test_the_same_floor_area_is_assumed_and_the_assumption_is_stated(self):
        result = estimate_contribution(
            "cafe", {"gross_floor_area_m2": 80}, catchment="urban", existing_use="office")
        assert "same floor area" in result["existing_development_allowance"]["assumption"]

    def test_the_evidence_requirement_is_stated(self):
        """The allowance is not automatic — it has to be evidenced with the DA."""
        result = estimate_contribution(
            "cafe", {"gross_floor_area_m2": 80}, catchment="urban", existing_use="shop")
        must_do = result["existing_development_allowance"]["what_you_must_do"]
        assert "1 January 2024" in (
            result["existing_development_allowance"]["existing_lawful_development"])
        assert "lodge the evidence" in must_do

    def test_a_commercial_proposal_without_an_existing_use_is_prompted(self):
        result = estimate_contribution("cafe", {"gross_floor_area_m2": 80}, catchment="urban")
        assert "increase" in result["ask_about_the_allowance"]

    def test_an_expansion_is_charged_on_the_increase_not_netted_to_nothing(self):
        """ROADMAP.md S3. A restaurant going 100m² -> 140m² netted to $0, because
        the previous use was assumed to occupy the same area as the proposal and
        the caller had no argument to say otherwise. The increase is 40m²."""
        result = estimate_contribution(
            "restaurant", {"gross_floor_area_m2": 140}, catchment="urban",
            existing_use="restaurant", existing_counts={"gross_floor_area_m2": 100},
        )
        assert result["net_contribution"]["urban"] == 8040.62
        assert "assumption" not in result["existing_development_allowance"], (
            "the previous area was stated, so nothing about it is assumed"
        )

    def test_the_assumption_still_applies_when_the_area_is_not_stated(self):
        """The default is kept because it is right for the ordinary case — a
        change of use in the same tenancy, which is the commonest business DA
        there is. What changed is that it can now be corrected."""
        result = estimate_contribution(
            "restaurant", {"gross_floor_area_m2": 140}, catchment="urban",
            existing_use="restaurant",
        )
        assert result["net_contribution"]["urban"] == 0.0
        assert "same floor area" in result["existing_development_allowance"]["assumption"]


class TestTheNoWorksFee:
    """Schedule 4 item 2.7. A pure change of use priced off the cost brackets
    with a $0 cost of works returned $153; the fee is $395."""

    def test_flat_fee_applies(self):
        result = calculate_da_fee(0, involves_building_work=False)
        assert result["estimated_fee"] == DA_FEE_NO_BUILDING_WORK == 395.00
        assert "Item 2.7" in result["basis"]

    def test_it_does_not_vary_with_cost(self):
        fees = {calculate_da_fee(c, involves_building_work=False)["estimated_fee"]
                for c in (0, 5_000, 250_000)}
        assert fees == {DA_FEE_NO_BUILDING_WORK}

    def test_building_work_still_uses_the_brackets(self):
        assert calculate_da_fee(0)["estimated_fee"] == 153.00

    def test_the_tool_exposes_it(self, call):
        result = call("calculate_da_fees",
                      {"development_cost": 0, "involves_building_work": False})
        assert result["estimated_fee"] == 395.00


class TestTheTotalIsTheTotal:
    def test_budget_matches_the_parts_it_names(self):
        result = estimate_total_cost(
            50_000, development_type="cafe", counts={"gross_floor_area_m2": 80},
            catchment="urban", existing_use="office")
        parts = result["parts"]
        expected = parts["da_lodgement_fee"]["amount"]
        expected += parts["information_technology_service_charge"]["amount"]
        expected += parts["section_7_11_contributions"]["net_contribution"]["urban"]
        assert result["budget_at_least"] == pytest.approx(expected, abs=0.01)
        assert set(result["what_that_covers"]) == {
            "da_lodgement_fee", "information_technology_service_charge",
            "section_7_11_contributions"}

    def test_what_it_leaves_out_is_stated_rather_than_omitted(self):
        result = estimate_total_cost(50_000)
        assert "section_64_water_and_wastewater" in result["what_it_leaves_out"]
        assert "advertising_and_notification" in result["what_it_leaves_out"]
        charges = {c["charge"] for c in result["not_estimated"]}
        assert any("Long service levy" in c for c in charges)
        for entry in result["not_estimated"]:
            assert entry["why_no_figure"]

    def test_the_contribution_dominates_the_fee(self, call):
        """The finding that motivated all of this, pinned so it stays visible."""
        result = call("calculate_da_fees", {
            "development_cost": 50_000, "development_type": "cafe",
            "gross_floor_area_m2": 80, "catchment": "urban"})
        contribution = result["parts"]["section_7_11_contributions"]["contribution"]["urban"]
        assert contribution == pytest.approx(16_081.24, abs=0.01)
        assert contribution > 40 * result["estimated_fee"]

    def test_the_it_service_charge_is_not_forgotten(self):
        result = estimate_total_cost(250_000)
        assert result["parts"]["information_technology_service_charge"]["amount"] == 250.00

    def test_without_a_development_type_the_gap_is_named(self):
        result = estimate_total_cost(50_000)
        why = result["parts"]["section_7_11_contributions"]["why_not"]
        assert "largest single charge" in why
