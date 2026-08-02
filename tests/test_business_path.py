"""The journey a business actually takes, end to end.

PLAN.md Phase 1. Walking *"open a café in a vacant shop at 12 Keen Street"*
found that zone, permissibility, parking and referrals all answered correctly —
and then the three things a business needs in order to *act* all failed:

  1.1  what do I submit?      `change of use` was refused; only `change_of_use` worked
  1.2  write the SEE          the draft mentioned flood zero times on a CBD site
  1.3  can I do this here?    "change of use" was answered as though it were a land use

These pin the fixes at the level a business experiences them, rather than at
the level of the functions underneath.
"""

import json
import re

import pytest

CBD = "12 Keen Street, Lismore NSW 2480"


class TestChecklistTakesBusinessWords:
    """1.1 — the tool never got the loose resolution the others received, and it
    was missed on the most common business DA type of all."""

    @pytest.mark.parametrize("said,expected", [
        ("change of use", "change_of_use"),
        ("Change of Use", "change_of_use"),
        ("change_of_use", "change_of_use"),
        ("fitout", "change_of_use"),
        ("fit out", "change_of_use"),
        ("new tenancy", "change_of_use"),
        ("cafe", "commercial"),
        ("coffee shop", "commercial"),
        ("restaurant", "commercial"),
        ("shop", "commercial"),
        ("office", "commercial"),
        ("hairdresser", "commercial"),
        ("warehouse", "industrial"),
        ("factory", "industrial"),
        ("signage", "signage"),
        ("demolish", "demolition"),
    ])
    def test_plain_words_resolve(self, call, said, expected):
        result = call("get_da_checklist", {"development_type": said})
        assert "error" not in result, f"{said!r} was refused"
        assert result["development_type"] == expected

    def test_nonsense_is_still_refused(self, call):
        """The point was never to accept everything."""
        result = call("get_da_checklist", {"development_type": "nuclear reactor"})
        assert "error" in result
        assert result["available_checklists"]

    def test_a_change_of_use_names_what_businesses_get_caught_by(self, call):
        result = call("get_da_checklist", {"development_type": "change of use"})
        missed = " ".join(result["commonly_missed"]).lower()
        assert "trade waste" in missed
        assert "food act" in missed or "registered with council" in missed
        assert "contamination" in missed

    def test_the_two_commercial_paths_point_at_each_other(self, call):
        """A new building and taking over a tenancy are different questions; a
        caller who picks the wrong one should be told the other exists."""
        for said in ("commercial", "change of use"):
            assert "also_see" in call("get_da_checklist", {"development_type": said})

    def test_lodgement_says_the_clock_does_not_start_until_complete(self, call):
        """An incomplete lodgement is not assessed — the single cheapest place
        for a business paying rent to lose weeks."""
        result = call("get_da_checklist", {"development_type": "cafe"})
        assert "clock" in result["lodgement"].lower()


class TestDraftAddressesItsOwnSite:
    """1.2 — the generator was blind to where the site was."""

    def draft(self, call, **kwargs):
        args = {"property_address": CBD, "zone_code": "E2", "proposed_use": "cafe",
                "development_type": "change_of_use", "floor_area_sqm": 80}
        args.update(kwargs)
        return call("generate_see_draft", args)

    def test_flood_is_always_addressed(self, call):
        """The old draft mentioned flood zero times for a CBD café. Much of the
        LGA is flood affected and the CBD was inundated in 2022, so silence is
        the failure — a SEE that omits flood is one Council comes back on."""
        text = self.draft(call)
        assert len(re.findall(r"flood", text, re.I)) >= 5
        assert "4.1.4" in text

    def test_flood_is_never_reported_as_clear_from_mapping(self, call):
        """The state flood layer holds no Lismore data, so it can confirm
        flooding but never rule it out. Saying otherwise would be the most
        harmful thing this draft could assert."""
        text = self.draft(call)
        section = text[text.find("4.1.4"):text.find("4.1.5")]
        assert "NOT ESTABLISHED" in text or "not been established" in section
        assert "cannot rule" in section.lower() or "cannot be, ruled out" in text

    def test_heritage_and_bushfire_get_sections_too(self, call):
        text = self.draft(call)
        assert "4.1.5 Heritage" in text
        assert "4.1.6 Bushfire" in text

    def test_a_constraints_summary_appears_up_front(self, call):
        text = self.draft(call)
        assert "Site Constraints" in text

    def test_an_asserted_constraint_is_used(self, call):
        text = self.draft(call, is_flood_affected=True)
        section = text[text.find("4.1.4"):text.find("4.1.5")]
        assert "within the flood planning area" in section
        assert "Flood Planning Level" in section

    def test_the_draft_does_not_claim_sepps_were_checked(self, call):
        """It used to assert 'No SEPPs preclude the granting of consent' — a
        claim nothing had verified, in a document going to Council."""
        text = self.draft(call)
        assert "No SEPPs preclude" not in text
        assert "APPLICANT TO COMPLETE" in text[text.find("4.3"):text.find("4.3") + 600]


class TestDraftParkingMatchesTheDCP:
    """The draft used to resolve the parking rate by hand and read the space
    count out of the rate's prose with a substring test for "10m". Every rate
    that was not a plain area rate — the café rule among them — fell through to
    a placeholder, and the compliance line then compared the spaces provided
    against 0, because a string is not an int. So an 80m² café with no parking
    at all was told its parking was "adequate for the proposed use", against a
    real requirement of 14 spaces, in a document that goes to Council over the
    applicant's name. Every test here is that failure from a different angle."""

    def parking(self, call, **kwargs):
        args = {"property_address": CBD, "zone_code": "E2",
                "proposed_use": "restaurant or cafe", "development_type": "fitout",
                "floor_area_sqm": 80, "num_employees": 3}
        args.update(kwargs)
        text = call("generate_see_draft", args)
        return text[text.find("4.2.2"):text.find("4.3")]

    def test_the_space_count_is_the_one_the_parking_tool_gives(self, call):
        """The draft, get_parking_rates and the Council form all run the same
        estimator. Three answers to one question is the thing to prevent."""
        section = self.parking(call, existing_parking_spaces=0)
        expected = call("get_parking_rates", {
            "development_type": "restaurant or cafe",
            "floor_area_sqm": 80, "num_employees": 3,
        })["calculation"]["spaces_required"]
        assert expected == 14
        assert f"Required Spaces:     {expected}" in section

    def test_a_shortfall_is_never_reported_as_adequate(self, call):
        section = self.parking(call, existing_parking_spaces=0)
        assert "Parking Shortfall: 14 space(s)." in section
        assert "adequate" not in section.lower()
        assert "APPLICANT TO ADDRESS" in section

    def test_enough_spaces_is_reported_as_compliant(self, call):
        section = self.parking(call, existing_parking_spaces=20)
        assert "Parking Compliance" in section
        assert "Shortfall" not in section

    def test_unstated_spaces_are_not_assumed_to_be_zero_or_enough(self, call):
        """Omitting the argument used to default to 0, which both invented a
        fact about the site and — via the same isinstance slip — reported it as
        compliant anyway."""
        section = self.parking(call)
        assert "[NOT STATED]" in section
        assert "Parking Compliance" not in section
        assert "Shortfall" not in section
        assert "APPLICANT TO COMPLETE" in section

    def test_the_lep_term_for_a_cafe_resolves(self, call):
        """'restaurant or cafe' is the Standard Instrument's own term and the
        example in the tool's own schema. It matched no parking rate, so the
        flagship case silently lost its space count."""
        assert "Required Spaces:     14" in self.parking(call, existing_parking_spaces=0)

    def test_a_use_with_no_rate_declines_rather_than_guessing(self, call):
        """Declining is the right answer more often than it looks — a confident
        wrong space count is what sends a DA back."""
        section = self.parking(call, proposed_use="crematorium",
                               existing_parking_spaces=0)
        assert "no DCP Chapter 7 rate could be matched" in section
        assert "APPLICANT TO COMPLETE" in section
        assert "Parking Compliance" not in section

    def test_the_basis_for_the_number_is_shown(self, call):
        """A space count with no working is one the applicant cannot check or
        argue with at the counter."""
        section = self.parking(call, existing_parking_spaces=0)
        assert "Basis:" in section
        assert "15 per 100" in section


class TestChangeOfUseIsNotALandUse:
    """1.3 — it was answered as though it were, via the table's catch-all."""

    @pytest.mark.parametrize("said", [
        "change of use", "change use", "fitout", "fit out",
        "alterations and additions", "renovation", "demolition",
    ])
    def test_process_words_are_refused(self, call, said):
        result = call("check_permissibility", {"zone_code": "E2", "land_use": said})
        assert "error" in result, f"{said!r} was answered as a land use"
        assert "permissibility" not in result

    def test_the_refusal_says_what_to_ask_instead(self, call):
        result = call("check_permissibility",
                      {"zone_code": "E2", "land_use": "change of use"})
        assert "restaurant or cafe" in result["ask_instead"]
        also = " ".join(result["for_a_change_of_use_also_check"]).lower()
        assert "existing use rights" in also
        assert "codes sepp" in also
        assert "contamination" in also

    def test_real_land_uses_still_answer(self, call):
        for use in ("cafe", "restaurant or cafe", "shop", "office premises"):
            result = call("check_permissibility", {"zone_code": "E2", "land_use": use})
            assert "permissibility" in result, f"{use!r} should be answerable"


class TestTheWholeJourney:
    """The walk-through from PLAN.md, as one test. If a business can get from an
    address to a lodgeable set of answers, this passes."""

    def test_cafe_in_a_vacant_cbd_shop(self, call):
        zone = call("lookup_zone_by_address", {"address": "12 Keen Street, Lismore"})
        assert zone["zone_code"] == "E2"

        allowed = call("check_permissibility",
                       {"zone_code": zone["zone_code"], "land_use": "cafe"})
        assert allowed["permissibility"].startswith("permitted")

        parking = call("get_parking_rates", {
            "development_type": "cafe", "floor_area_sqm": 80,
            "seats": 40, "num_employees": 6, "spaces_provided": 0})
        assert parking["calculation"]["spaces_required"] == 17

        checklist = call("get_da_checklist", {"development_type": "change of use"})
        assert "error" not in checklist

        fees = call("calculate_da_fees", {"development_cost": 120_000})
        assert fees["fee_schedule_year"] == "2026-27"

        # The cost answer has to be the whole cost, not the lodgement fee. This
        # cafe takes over a tenancy last used as an office, so the Section 7.11
        # contribution is charged on the step from 1.6 to 7 peak vehicle trips
        # per 100m2 — and it dwarfs the fee. A business told only the fee here
        # is a business that meets the contribution as a surprise.
        cost = call("calculate_da_fees", {
            "development_cost": 120_000, "development_type": "cafe",
            "gross_floor_area_m2": 80, "catchment": "urban", "existing_use": "office"})
        contribution = cost["parts"]["section_7_11_contributions"]["net_contribution"]["urban"]
        assert contribution > 10 * cost["estimated_fee"]
        assert cost["budget_at_least"] > contribution
        assert "section_7_11_contributions" in cost["what_that_covers"]

        draft = call("generate_see_draft", {
            "property_address": CBD, "zone_code": "E2", "proposed_use": "cafe",
            "development_type": "change_of_use", "floor_area_sqm": 80})
        assert isinstance(draft, str) and len(draft) > 4000
        assert re.search(r"flood", draft, re.I)
