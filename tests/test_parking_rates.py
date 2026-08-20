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
        """The `greater_of` still resolves to the area measure when no seat
        count is given — that fallback is inside the customer component and is
        not what S3 changed."""
        result = estimate_spaces(PARKING_RATES["cafe"], 80, {"employees": 0})
        assert result["spaces_required"] == 12
        assert not any("greater" in b for b in result["basis"]), (
            "nothing was compared, so the basis should not claim a comparison"
        )

    def test_the_80m2_cafe_is_not_told_12_when_staff_are_unknown(self):
        """The case CLAUDE.md records: an 80m² café was told its parking was
        adequate against a real requirement of 14. 12 is the customer component
        alone, and the staff component is added to it — so without a staff count
        there is no total, only a floor that reads like one. ROADMAP.md S3."""
        result = estimate_spaces(PARKING_RATES["cafe"], 80)
        assert result["spaces_required"] is None
        assert result["supply"] == ["num_employees"]
        # 6 staff take it from 12 to 15, which is the whole point.
        assert estimate_spaces(
            PARKING_RATES["cafe"], 80, {"employees": 6})["spaces_required"] == 15

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

    def test_an_uncounted_input_withholds_the_figure(self):
        """A gym rate has an employees component. This used to return the
        area-only total with "not counted: employees" appended to `basis` — an
        undercount presented as the requirement, with the caveat three levels
        down. ROADMAP.md S3: the number is declined and the missing argument
        named, because a part of a sum is not a lower bound."""
        result = estimate_spaces(PARKING_RATES["gym"], 250)
        assert result["spaces_required"] is None
        assert result["supply"] == ["num_employees"]
        assert "cannot be reduced to a number" in result["cannot_calculate"]

    def test_what_was_counted_is_still_shown(self):
        """Declining the total does not mean discarding the work — the caller
        can see the rate was understood and exactly what is outstanding."""
        result = estimate_spaces(PARKING_RATES["gym"], 250)
        assert result["counted_so_far"]
        assert result["rate"] == PARKING_RATES["gym"]["rate"]

    def test_a_supplied_zero_counts_as_zero(self):
        """`employees: 0` is an answer. It used to be filtered out as falsy and
        become indistinguishable from "not supplied", so neither could be
        expressed — the same defect as the arguments that did not exist."""
        result = estimate_spaces(PARKING_RATES["gym"], 250, {"employees": 0})
        assert result["spaces_required"] is not None


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


# ---------------------------------------------------------------------------
# PLAN.md item 2.2 — the CBD is a different rate, and a shortfall is a decision
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def chapter():
    from audit_parking_rates import chapter_text
    return normalise(chapter_text())


class TestCbdProvisionsAreInTheDCP:
    """The §7.7.3 provisions get the same guarantee as the Schedule 1 rates.

    They are hand-transcribed from the same PDF and carry more consequence per
    word — §7.7.3.3 is the difference between building a space and paying for
    it. Two of these strings were wrong when first written and this caught them.
    """

    @pytest.mark.parametrize("label", [
        "fixed_rate", "exclusion", "credit", "credit_alternative",
        "shared", "shared_ordering", "consolidated", "expansion",
        "combined_uses", "on_street_outside", "on_street_cbd", "disability",
    ])
    def test_provision_appears_verbatim(self, label, chapter):
        from lismore_da_mcp.data.parking import (
            CBD_EXPANSION_ALLOWANCE, CBD_FIXED_RATE, CBD_PARKING_CREDIT,
            CBD_REDUCTIONS, COMBINED_USES, DISABILITY_PARKING, ON_STREET_LOSS)
        quotes = {
            "fixed_rate": CBD_FIXED_RATE["verbatim"],
            "exclusion": CBD_FIXED_RATE["exclusion_verbatim"],
            "credit": CBD_PARKING_CREDIT["verbatim"],
            "credit_alternative": CBD_PARKING_CREDIT["evidenced_alternative"],
            "shared": CBD_REDUCTIONS["shared"]["verbatim"],
            "shared_ordering": CBD_REDUCTIONS["shared"]["ordering"],
            "consolidated": CBD_REDUCTIONS["consolidated"]["verbatim"],
            "expansion": CBD_EXPANSION_ALLOWANCE["verbatim"],
            "combined_uses": COMBINED_USES["verbatim"],
            "on_street_outside": ON_STREET_LOSS["outside_cbd"],
            "on_street_cbd": ON_STREET_LOSS["in_cbd"],
            "disability": DISABILITY_PARKING["verbatim"],
        }
        assert normalise(quotes[label]) in chapter, (
            f"{label} is no longer in DCP Chapter 7 verbatim. Read the chapter before "
            "editing — do not adjust the stored text to make this pass."
        )


class TestTheCbdRateReplacesSchedule1:
    """The regression this item exists to fix.

    Schedule 1 is the rate for development *outside* the CBD (§7.7.2). Inside
    it, §7.7.3.1 sets a flat 3.3 spaces/100m² for non-residential use. Every
    answer this server gave a CBD business used the wrong schedule, and for the
    café worked example it overstated the requirement 14 to 3.
    """

    def test_cbd_cafe_is_charged_the_fixed_rate_not_schedule_1(self, call):
        cbd = call("get_parking_rates", {
            "development_type": "cafe", "location": "cbd",
            "floor_area_sqm": 80, "num_employees": 4})
        outside = call("get_parking_rates", {
            "development_type": "cafe", "location": "outside_cbd",
            "floor_area_sqm": 80, "num_employees": 4})
        assert cbd["calculation"]["spaces_required"] == 3      # 80 @ 3.3/100
        assert outside["calculation"]["spaces_required"] == 14  # Schedule 1
        assert "3.3" in cbd["rate_description"]

    def test_the_displaced_schedule_1_rate_is_still_shown(self, call):
        """Overstating is the failure being fixed, but a business that has been
        quoted the Schedule 1 figure by someone else needs to see why it differs
        rather than be told two numbers with no reconciliation."""
        result = call("get_parking_rates", {
            "development_type": "cafe", "location": "cbd", "floor_area_sqm": 80})
        assert "7.7.2" in result["schedule_1_rate_not_applied"]

    def test_accommodation_stays_on_schedule_1_inside_the_cbd(self, call):
        """§7.7.3.1 exception (i). Applying 3.3/100m² to a motel would understate
        it badly, which is the opposite error and just as damaging."""
        result = call("get_parking_rates", {
            "development_type": "motel", "location": "cbd", "floor_area_sqm": 500})
        assert "exception (i)" in result["cbd_treatment"]
        assert "3.3" not in result["rate_description"]


class TestTheCbdBoundaryIsNeverAssumed:
    """Map 1 defines the CBD and is a bitmap with no extractable text.

    So nothing here can decide it, and the repo's rule for the contributions
    catchment applies unchanged: return both readings rather than defaulting to
    one, because a silent default puts a wrong number in a business's plans.
    """

    def test_both_rates_are_returned_when_location_is_unstated(self, call):
        result = call("get_parking_rates", {
            "development_type": "cafe", "floor_area_sqm": 80, "num_employees": 4})
        both = result["which_rate_applies"]
        assert "14 space(s)" in both["outside_the_cbd"]
        assert "3 space(s)" in both["inside_the_cbd"]
        assert "Neither figure" in both["unresolved"]

    def test_it_says_how_to_settle_the_question(self, call):
        result = call("get_parking_rates", {
            "development_type": "shop", "floor_area_sqm": 200})
        assert "Map 1" in result["which_rate_applies"]["how_to_settle_it"]

    def test_zone_is_not_offered_as_a_proxy_for_the_boundary(self):
        """E2 is close to the CBD but is not the same line, and the tool must not
        invite a caller to substitute one for the other."""
        from lismore_da_mcp.registry import registered
        schema = registered()["get_parking_rates"].schema
        assert "not the same line" in schema["properties"]["location"]["description"]


class TestTheParkingCredit:
    """§7.7.3.4. Usually most of a change-of-use requirement, and never automatic."""

    def test_existing_floor_area_earns_a_deemed_credit(self, call):
        result = call("get_parking_rates", {
            "development_type": "cafe", "location": "cbd",
            "floor_area_sqm": 80, "existing_gfa_sqm": 80})
        # 80m² @ 3.3/100 = 2.64 → 3 gross; credit 80 @ 2.5/100 = 2.0; net 1.
        assert result["calculation"]["gross_requirement"] == 3
        assert result["calculation"]["parking_credit"]["credit_spaces"] == 2.0
        assert result["calculation"]["spaces_required"] == 1

    def test_spaces_already_on_site_reduce_the_credit(self, call):
        """The formula subtracts them: the credit is parking the site is deemed
        to have given the CBD, and spaces it kept are not part of that."""
        result = call("get_parking_rates", {
            "development_type": "shop", "location": "cbd",
            "floor_area_sqm": 400, "existing_gfa_sqm": 400,
            "existing_spaces_on_site": 6})
        assert result["calculation"]["parking_credit"]["credit_spaces"] == 4.0

    def test_a_credit_is_never_applied_unasked(self, call):
        result = call("get_parking_rates", {
            "development_type": "cafe", "location": "cbd", "floor_area_sqm": 80})
        assert "parking_credit" not in result["calculation"]
        assert "credit_not_applied" in result["calculation"]

    def test_the_credit_cannot_go_negative(self, call):
        """A site with more spaces than the formula deems does not owe negative
        parking, and must not silently inflate the requirement."""
        result = call("get_parking_rates", {
            "development_type": "shop", "location": "cbd",
            "floor_area_sqm": 200, "existing_gfa_sqm": 100,
            "existing_spaces_on_site": 50})
        assert result["calculation"]["parking_credit"]["credit_spaces"] == 0.0
        assert result["calculation"]["spaces_required"] == 7


class TestShortfallIsADecision:
    """The point of the item: name what the DCP lets a business actually do."""

    def _options(self, result):
        return [o["option"] for o in result["addressing_the_shortfall"]["options"]]

    def test_a_cbd_shortfall_offers_the_dcp_mechanisms(self, call):
        result = call("get_parking_rates", {
            "development_type": "cafe", "location": "cbd",
            "floor_area_sqm": 80, "spaces_provided": 0})
        options = " ".join(self._options(result))
        assert "contribution in lieu" in options.lower()
        assert "Shared parking" in options
        assert "Deemed parking credit" in options

    def test_cbd_only_mechanisms_are_not_offered_outside_the_cbd(self, call):
        """§7.7.3 is expressly the CBD section. Offering a village business a
        contribution in lieu would send it to Council with a request the DCP does
        not support."""
        result = call("get_parking_rates", {
            "development_type": "shop", "location": "outside_cbd",
            "floor_area_sqm": 200, "spaces_provided": 2})
        options = " ".join(self._options(result)).lower()
        assert "contribution in lieu" not in options
        assert "shared parking" not in options
        assert "merits" in options

    def test_a_cafe_is_told_about_unenclosed_outdoor_dining(self, call):
        """Usually the cheapest lever a café has: unenclosed area is not GFA, so
        it generates no requirement at all."""
        result = call("get_parking_rates", {
            "development_type": "cafe", "location": "cbd",
            "floor_area_sqm": 80, "spaces_provided": 0})
        assert any("unenclosed" in o.lower() for o in self._options(result))

    def test_the_merit_criteria_are_the_dcp_s_own(self, call):
        result = call("get_parking_rates", {
            "development_type": "shop", "location": "outside_cbd",
            "floor_area_sqm": 200, "spaces_provided": 0})
        merits = next(o for o in result["addressing_the_shortfall"]["options"]
                      if "merits" in o["option"])
        assert len(merits["what_council_must_consider"]) == 6
        assert "7.5" in merits["source"]

    def test_no_options_are_offered_when_there_is_no_shortfall(self, call):
        result = call("get_parking_rates", {
            "development_type": "cafe", "location": "cbd",
            "floor_area_sqm": 80, "spaces_provided": 10})
        assert "addressing_the_shortfall" not in result

    def test_nearby_public_parking_is_still_not_treated_as_compliance(self, call):
        """The one thing that has to survive making the answer more encouraging."""
        result = call("get_parking_rates", {
            "development_type": "cafe", "location": "cbd",
            "floor_area_sqm": 80, "spaces_provided": 0})
        merits = next(o for o in result["addressing_the_shortfall"]["options"]
                      if "merits" in o["option"])
        assert "not evidence of compliance" in merits["effect"]


class TestTheCashInLieuRateIsNotInvented:
    """PLAN.md 2.1 left open whether a contribution in lieu applies in Lismore.

    Chapter 7 answers it: §7.7.3.3 expressly provides for one, in the CBD. The
    *rate* is a separate question and this repo cannot answer it — the DCP cites
    the repealed Section 94 and a plan section that does not exist in the
    current plan, and the Section 7.11 Plan 2024-2041 has no car parking
    category. Named and sourced, never estimated — the Section 64 treatment.
    """

    def test_the_provision_is_reported_as_existing(self, call):
        result = call("get_parking_rates", {
            "development_type": "cafe", "location": "cbd",
            "floor_area_sqm": 80, "spaces_provided": 0})
        option = next(o for o in result["addressing_the_shortfall"]["options"]
                      if "lieu" in o["option"])
        assert "7.7.3.3" in option["source"]

    def test_no_dollar_figure_is_produced(self, call):
        result = call("get_parking_rates", {
            "development_type": "cafe", "location": "cbd",
            "floor_area_sqm": 80, "spaces_provided": 0})
        option = next(o for o in result["addressing_the_shortfall"]["options"]
                      if "lieu" in o["option"])
        assert option["rate"]["status"].startswith("not quantifiable")
        assert "Duty Planner" in option["rate"]["ask_council"]

    def test_the_reason_it_cannot_be_quantified_is_given(self):
        """A bare 'ask Council' is not actionable. The applicant should know the
        cross-reference is stale so they can ask the right question."""
        from lismore_da_mcp.data.parking import CBD_CASH_IN_LIEU_RATE
        assert "Section 94" in CBD_CASH_IN_LIEU_RATE["why"]
        assert "no car parking contribution category" in CBD_CASH_IN_LIEU_RATE["why"]


class TestEveryCountableIsAskable:
    """ROADMAP.md S3. Ten of the twelve countables had no argument on
    `get_parking_rates`, so a rate that counted practitioners or children could
    never be given them and answered from the terms it could reach."""

    def test_the_schema_offers_every_countable(self):
        """Generated from COUNTABLE rather than written out, so a rate that
        starts counting something new cannot fail to be askable."""
        from lismore_da_mcp.data.parking import COUNTABLE
        from lismore_da_mcp.registry import registered

        properties = set(registered()["get_parking_rates"].schema["properties"])
        missing = sorted(set(COUNTABLE.values()) - properties)
        assert missing == [], f"countables with no argument: {missing}"

    def test_every_countable_has_a_description(self):
        from lismore_da_mcp.data.parking import COUNTABLE, COUNTABLE_DESCRIPTIONS
        assert set(COUNTABLE.values()) == set(COUNTABLE_DESCRIPTIONS)

    def test_the_medical_centre_case_from_the_roadmap(self, call):
        """5 employees answered 5 spaces against '4 per practitioner, plus 1 per
        employee', with 'not counted: practitioners' three levels down. Three
        practitioners make it 17."""
        without = call("get_parking_rates",
                       {"development_type": "medical centre", "num_employees": 5})
        assert without["calculation"]["spaces_required"] is None
        assert without["calculation"]["supply"] == ["practitioners"]

        with_them = call("get_parking_rates", {
            "development_type": "medical centre", "num_employees": 5, "practitioners": 3})
        assert with_them["calculation"]["spaces_required"] == 17

    def test_a_declined_figure_reports_no_shortfall(self, call):
        """A shortfall computed against a number that does not exist is worse
        than no shortfall — it is the reassuring one."""
        result = call("get_parking_rates", {
            "development_type": "medical centre", "num_employees": 5, "spaces_provided": 2})
        assert "shortfall" not in result["calculation"]
        assert "addressing_the_shortfall" not in result
