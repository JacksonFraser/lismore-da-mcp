"""The fifteen confirmed defects in ROADMAP.md S5 / SCENARIOS.md D5–D12.

One file rather than fifteen additions to nine others, because these are held
together by provenance rather than by subject: each was found by running
`SCENARIOS.md` against the live server and verified by hand against the source.
Split across the existing files they would read as unrelated assertions with no
record of why anyone thought to check.

Two of the fifteen are not here. D7 (confident numbers from inputs the schema
cannot express) landed under S3 and is tested in `test_parking_rates.py` and
`test_readiness.py`. D9 (natural argument names refused by 13 of 14 tools) is
Phase A1 convenience work, and the roadmap is explicit that it waits on the
correctness work rather than shipping beside it.
"""

import json

import pytest


class TestD5AnAddressOutsideLismore:
    """`lookup_zone_by_address` refused correctly and `lookup_site_constraints`
    answered with Lismore-specific reasoning attached. One of the two knew; the
    other did not ask."""

    def test_the_constraints_tool_now_refuses(self, call):
        result = call("lookup_site_constraints", {"address": "1 Jonson Street, Byron Bay NSW 2481"})
        assert "error" in result
        assert "Byron" in json.dumps(result)
        assert "constraints" not in result

    def test_a_lismore_address_still_answers(self, call):
        result = call("lookup_site_constraints", {"address": "12 Keen Street, Lismore"})
        assert "constraints" in result

    def test_the_gate_is_one_function_both_tools_can_use(self):
        """The two diverged because each had its own idea of scope. The check
        lives in one place now so they cannot disagree again."""
        from lismore_da_mcp.addresses import out_of_area

        assert out_of_area({"council": "Byron"}) is not None
        assert out_of_area({"council": "Lismore"}) is None
        # No council in the response is not evidence of being outside the LGA.
        assert out_of_area({}) is None


class TestD6TheSignageFallbackIsNotBiasedToExempt:
    """An above-awning sign needs consent; a below-awning one is exempt. Five
    phrasings of the former failed to resolve and every suggestion offered was
    exempt-pathway, steering a business to "no application needed"."""

    @pytest.mark.parametrize("phrasing", [
        "sign above the awning", "sign above awning", "above the awning",
        "sign on top of the awning", "above awning sign",
    ])
    def test_the_phrasings_resolve(self, call, phrasing):
        result = call("get_signage_requirements", {"sign_type": phrasing})
        assert result.get("sign_type") == "awning_sign_above", (
            f"{phrasing!r} did not reach the sign type that needs consent"
        )

    def test_suggestions_carry_their_pathway(self, call):
        result = call("get_signage_requirements", {"sign_type": "a sign for my shop"})
        assert result["did_you_mean"], "expected suggestions for a vague term"
        for suggestion in result["did_you_mean"]:
            assert "sign_type" in suggestion and "pathway" in suggestion

    def test_an_all_exempt_list_says_so(self, call):
        """The bias is a property of string similarity, not a finding about the
        caller's sign. Saying that is what stops it reading as reassurance."""
        result = call("get_signage_requirements", {"sign_type": "a sign for my shop"})
        pathways = {s["pathway"] for s in result["did_you_mean"]}
        if pathways == {"Exempt Development — no application needed"}:
            assert "do_not_read_these_as_exempt" in result


class TestD8ShopTopHousing:
    """Schedule 1 p14: "CBD (defined in Map 1) - No carparking requirements".
    The tool errored and suggested `shop` at 4.4 per 100m², telling a CBD
    business to build parking the DCP expressly does not require."""

    def test_it_resolves(self, call):
        result = call("get_parking_rates", {"development_type": "shop top housing"})
        assert result.get("dcp_name" if "dcp_name" in result else "dcp_land_use") == "Shop top housing"

    def test_the_cbd_answer_is_no_requirement(self, call):
        result = call("get_parking_rates",
                      {"development_type": "shop top housing", "location": "cbd"})
        assert "No carparking requirements" in result["rate_description"]

    def test_the_fixed_cbd_rate_is_not_applied_to_it(self):
        """Residential accommodation, so §7.7.3.1 exception (i) keeps it on
        Schedule 1 — which here means zero, not 3.3 per 100m²."""
        from lismore_da_mcp.parking import uses_schedule_1_in_cbd

        assert uses_schedule_1_in_cbd("shop_top_housing")

    def test_the_audit_would_now_notice_it_missing(self):
        """The completeness check the audit's docstring promised did not exist,
        which is why "27 entries checked, 0 not matching" was printed while this
        was absent."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from audit_parking_rates import (
            SCHEDULE_1_LAND_USES, UNCARRIED_SCHEDULE_1_USES, check_completeness,
            land_use_column,
        )
        from lismore_da_mcp.data.parking import PARKING_RATES

        assert "Shop top housing" in SCHEDULE_1_LAND_USES
        assert "Shop top housing" not in UNCARRIED_SCHEDULE_1_USES
        assert check_completeness(land_use_column(), PARKING_RATES) == 0

        without = {k: v for k, v in PARKING_RATES.items() if k != "shop_top_housing"}
        assert check_completeness(land_use_column(), without) > 0, (
            "removing the entry did not fail the completeness check"
        )


class TestD10TheFeeSchemaNoLongerRecommendsTheUnderQuote:
    """`development_cost`'s description said "Use 0 for a change of use with no
    works" → $153 under Item 2.1. The correct provision is Item 2.7, a flat
    $395. The schema recommended the path that under-quotes by $242."""

    def test_the_description_points_at_the_right_provision(self):
        from lismore_da_mcp.registry import registered

        description = registered()["calculate_da_fees"].schema["properties"]["development_cost"]["description"]
        assert "involves_building_work" in description
        assert "Use 0 for a change of use" not in description

    def test_a_nil_cost_answer_flags_the_other_provision(self, call):
        """A caller who passes 0 anyway still has to be told, because they will
        not read the schema again before budgeting."""
        result = call("calculate_da_fees", {"development_cost": 0})
        flagged = result["da_lodgement_fee_detail"]["check_the_provision"]
        assert "Item 2.7" in flagged and "395" in flagged

    def test_the_correct_path_gives_the_higher_figure(self, call):
        cheap = call("calculate_da_fees", {"development_cost": 0})["estimated_fee"]
        right = call("calculate_da_fees",
                     {"development_cost": 0, "involves_building_work": False})["estimated_fee"]
        assert right - cheap == 242.0


class TestD11ThePhantomIsGone:
    """"CBD exemption precinct" appears nowhere in DCP Chapter 8, nowhere in LEP
    2012, and nowhere in documents/. CLAUDE.md recorded it as invented and
    deleted on 2026-08-06; two copies survived and reached the Duty Planner
    brief and SEE drafts Council reads."""

    # Recording that the phrase was invented and removed is the opposite of
    # asserting it, and those records are load-bearing — they are why nobody
    # re-adds it from memory. So a mention only counts as an offence if nothing
    # around it says it is gone.
    REMOVAL_LANGUAGE = (
        "gone", "was here until", "appear nowhere", "appears nowhere", "invented",
        "no such", "removed", "deleted", "not in any source",
    )

    def test_no_module_asserts_it(self):
        from pathlib import Path

        src = Path(__file__).resolve().parent.parent / "src"
        offenders = []
        for path in src.rglob("*.py"):
            lines = path.read_text(encoding="utf-8").splitlines()
            for number, line in enumerate(lines, 1):
                if "exemption precinct" not in line.lower():
                    continue
                context = " ".join(lines[max(0, number - 8):number + 8]).lower()
                if not any(word in context for word in self.REMOVAL_LANGUAGE):
                    offenders.append(f"{path.relative_to(src)}:{number}")
        assert offenders == [], (
            f"the invented precinct is asserted at {offenders}. It is in no source document — "
            "the real distinction is the flood hazard area from Map 1 of DCP Chapter 8."
        )

    def test_the_records_of_its_removal_are_still_there(self):
        """Guards the fix to the test above: if the removal notes were deleted,
        the check would pass by finding nothing at all."""
        from pathlib import Path

        src = Path(__file__).resolve().parent.parent / "src"
        mentions = sum(
            path.read_text(encoding="utf-8").lower().count("exemption precinct")
            for path in src.rglob("*.py")
        )
        assert mentions >= 2, (
            "the notes recording that this phrase was invented have themselves gone. "
            "They are why it does not come back."
        )


class TestD12SmallerConfirmedDefects:
    def test_trade_waste_reaches_the_trades_its_trigger_names(self, call):
        """`liquid_trade_waste` names "butcher, hairdresser, mechanic or car
        wash" and was only ever selected by the `food` activity."""
        for use in ("hairdresser", "mechanic", "car wash"):
            result = call("get_other_approvals", {"proposed_use": use})
            assert "Liquid Trade Waste" in json.dumps(result), f"{use} did not get it"

    def test_a_plain_shop_does_not_get_trade_waste(self, call):
        """Over-listing is the house rule here, but not to the point of
        meaninglessness — a retail shop discharges domestic sewage."""
        result = call("get_other_approvals", {"proposed_use": "clothing shop"})
        assert "Liquid Trade Waste" not in json.dumps(result)

    def test_the_flood_exemption_key_matches_its_constant(self, call):
        """The wire key read `all_development_controls_exemption`; the constant
        is `STRUCTURAL_ADEQUACY_EXEMPTION` and only the certificate is exempt."""
        result = call("get_flood_requirements",
                      {"development_type": "commercial", "flood_area": "flood_fringe"})
        applies = result["applies"]
        assert "all_development_controls_exemption" not in applies
        assert "structural_adequacy_certificate_exemption" in applies

    def test_the_area_summary_is_not_read_as_the_type_answer(self, call):
        """The headline was returned unchanged for every development type,
        telling an industrial proposal that "commercial buildings need a
        mezzanine refuge"."""
        result = call("get_flood_requirements",
                      {"development_type": "industrial", "flood_area": "high_flood_risk"})
        applies = result["applies"]
        assert "headline" not in applies
        assert "about_this_flood_area" in applies
        assert "read_the_summary_as_the_area_not_the_proposal" in applies

    def test_s39_1_d_is_not_cited_against_every_application(self):
        """It reads "for an application for integrated development"."""
        from lismore_da_mcp.data.readiness import STATUTORY_CONTENT
        from lismore_da_mcp.readiness import Proposal, _statutory

        findings = _statutory(Proposal(proposed_use="cafe"), ["Construction Certificate"])
        approvals = [f for f in findings if "list the other approvals" in f["finding"]]
        assert approvals
        assert approvals[0]["source"] == STATUTORY_CONTENT["list_of_approvals"]["clause"]
        assert "s39(1)(d)" not in approvals[0]["source"]
        # Still reachable, but conditioned on the development being integrated.
        assert "integrated" in approvals[0]["do_this"]

    def test_the_document_matcher_keeps_two_plans_apart(self):
        """A bare "management plan" is a subset of both and cleared them both,
        short-circuiting the check written to keep them apart."""
        from lismore_da_mcp.readiness import _claims

        assert not _claims("management plan", "Waste management plan — DCP Chapter 15")
        assert not _claims("management plan", "Stormwater management plan")
        assert _claims("waste management plan", "Waste management plan — DCP Chapter 15")
        assert _claims("site plan", "Site plan (1:100 or 1:200 scale)")

    def test_the_cc_preamble_agrees_with_the_cc_entry(self):
        """The preamble said a Construction Certificate "cannot even be applied
        for" before consent; the entry describes it as certifying drawings
        against the consent's conditions, which is about issue."""
        from lismore_da_mcp.data.approvals import WHAT_THE_DA_DOES_NOT_COVER

        assert "cannot even be applied for" not in WHAT_THE_DA_DOES_NOT_COVER
        assert "issued" in WHAT_THE_DA_DOES_NOT_COVER

    def test_the_three_orphaned_fee_figures_reach_an_answer(self, call):
        """All three were transcribed and audited and reached no output. One is
        a $1,532 notice fee, roughly three times a small café's quoted total."""
        from lismore_da_mcp.data.fees import (
            DESIGN_REVIEW_PANEL_FEE, DESIGNATED_DEVELOPMENT_FEE, PRESCRIBED_NOTICE_FEES,
        )

        result = call("calculate_da_fees", {"development_cost": 50_000})
        payload = json.dumps(result)
        assert str(PRESCRIBED_NOTICE_FEES["prohibited_development"]) in payload
        assert str(DESIGNATED_DEVELOPMENT_FEE) in payload
        assert str(DESIGN_REVIEW_PANEL_FEE) in payload

    def test_neither_is_added_to_the_budget(self, call):
        """Both are conditional on facts this server cannot establish, so they
        are named and excluded rather than estimated."""
        result = call("calculate_da_fees", {"development_cost": 50_000})
        assert "prescribed_notice_fees" in result["what_it_leaves_out"]
        assert "designated_or_reviewed_development" in result["what_it_leaves_out"]

    def test_clause_5_22_is_reachable_on_the_natural_path(self, call):
        """`development_type="childcare centre"` errored with only [commercial,
        industrial, residential] and no redirect — for the use cl 5.22 exists
        for."""
        result = call("get_flood_requirements",
                      {"development_type": "childcare centre", "flood_area": "flood_fringe"})
        assert "error" not in result
        assert result["development_type"] == "commercial"
        assert "also_clause_5_22" in result

    def test_an_ordinary_shop_is_not_told_about_5_22(self):
        from lismore_da_mcp.flood import is_sensitive_or_hazardous

        assert not is_sensitive_or_hazardous("shop")
        assert is_sensitive_or_hazardous("childcare centre")
        assert is_sensitive_or_hazardous("boarding house")

    def test_do_i_need_a_da_at_all_is_answered(self, call):
        """A shop→shop change returned the full fourteen-document "not ready"
        workup without once suggesting the application might not be needed."""
        result = call("check_da_readiness", {
            "proposed_use": "shop", "existing_use": "shop",
            "zone_code": "E2", "development_type": "change of use",
        })
        assert "may not need development consent" in result["before_you_read_any_of_this"]

    def test_a_real_change_of_use_is_not_told_that(self, call):
        """A shop becoming a café is a change of use. Both match "Commercial
        premises" in E2's table, so the comparison has to be on the *defined
        term* and not on the row they resolve to."""
        result = call("check_da_readiness", {
            "proposed_use": "cafe", "existing_use": "shop",
            "zone_code": "E2", "development_type": "change of use",
        })
        assert "before_you_read_any_of_this" not in result
