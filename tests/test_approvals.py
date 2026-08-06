"""The approvals that are not the DA.

PLAN.md item 2.4. A business that gets development consent has finished the part
everyone talks about. The consent says the use is allowed; it is not permission
to build, connect to the sewer, serve food or alcohol, occupy the building or put
a table on the footpath. Each is a separate approval and several are issued by
someone other than Council's planners.

The selection rule here is the inverse of the rest of the repo: **over-list**.
A wrongly included approval costs a sentence of reading; a missing one costs
weeks. So the tests below check that uncertainty produces an inclusion plus a
question, not an omission.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lismore_da_mcp.approvals import relevant  # noqa: E402
from lismore_da_mcp.data.approvals import APPROVALS, BY_ACTIVITY, SEQUENCE, TIMING  # noqa: E402


@pytest.fixture(scope="module")
def source_text():
    """The two documents the fee figures are cited against.

    Module-scoped and defined at module level: a class-scoped fixture written as
    an instance method is deprecated in pytest, and these PDFs are slow enough
    to parse that re-reading them per test is worth avoiding.
    """
    from audit_approvals import DINING_POLICY, SCHEDULE, pdf_text
    return pdf_text(SCHEDULE) + " " + pdf_text(DINING_POLICY)


class TestFeeFiguresComeFromTheSchedule:
    """Council reissues its fees every July and this repo has already missed
    that refresh twice (PLAN.md 0.1). Every dollar figure quoted must still
    appear in the document it is cited against."""

    @pytest.mark.parametrize("key", sorted(k for k, v in APPROVALS.items() if v.get("fee")))
    def test_every_quoted_figure_is_in_the_source(self, key, source_text):
        import re
        for amount in re.findall(r"\$[\d,]+(?:\.\d{2})?", APPROVALS[key]["fee"]):
            assert amount in source_text, (
                f"{key} quotes {amount}, which is not in the cited source. Council's schedule "
                "is reissued every July — read the new one rather than editing this test."
            )

    def test_a_quoted_figure_always_cites_a_source(self):
        import re
        for key, entry in APPROVALS.items():
            if entry.get("fee") and re.search(r"\$[\d,]", entry["fee"]):
                assert entry.get("fee_source"), f"{key} quotes a figure with no fee_source"

    def test_state_agency_charges_are_named_without_a_figure(self):
        """The Section 64 treatment. A liquor licence fee and the long service
        levy rate are real and are not in any document here, so they are named
        and left unquantified rather than estimated."""
        import re
        for key in ("liquor_licence", "long_service_levy"):
            assert not re.search(r"\$[\d,]", APPROVALS[key]["fee"])
            assert "not quoted here" in APPROVALS[key]["fee"].lower()


class TestTheDataHangsTogether:
    def test_sequence_covers_every_approval_exactly_once(self):
        assert sorted(SEQUENCE) == sorted(APPROVALS)
        assert len(SEQUENCE) == len(set(SEQUENCE))

    def test_every_activity_mapping_resolves(self):
        for activity, keys in BY_ACTIVITY.items():
            assert set(keys) <= set(APPROVALS), f"{activity} references an unknown approval"

    def test_every_approval_names_who_issues_it(self):
        """The single most useful field. "You also need a liquor licence" is
        half an answer; "from Liquor & Gaming NSW, not Council" is the answer."""
        for key, entry in APPROVALS.items():
            assert entry["issued_by"].strip(), key
            assert entry["legislation"].strip(), key
            assert entry["timing"] in TIMING, key


class TestUncertaintyIncludesRatherThanOmits:
    def test_building_work_is_assumed_unless_ruled_out(self):
        keys, unresolved = relevant("hairdresser")
        assert "construction_certificate" in keys
        assert "occupation_certificate" in keys
        assert any("building work" in q["question"].lower() for q in unresolved)

    def test_ruling_out_building_work_drops_the_certificates(self):
        keys, _ = relevant("office", building_work=False)
        assert "construction_certificate" not in keys
        assert "occupation_certificate" not in keys

    def test_an_unanswered_question_still_lists_the_approval(self):
        """The failure this tool exists to prevent is an approval left off
        because nobody asked. Every question must name what was listed anyway."""
        _, unresolved = relevant("restaurant")
        assert unresolved
        for question in unresolved:
            assert question["listed_anyway"]
            assert question["why_it_matters"]

    def test_answering_narrows_the_list_rather_than_growing_it(self):
        broad, _ = relevant("restaurant")
        narrow, unresolved = relevant(
            "restaurant", building_work=False, serves_alcohol=False,
            outdoor_dining=False, connected_to_sewer=True)
        assert set(narrow) < set(broad)
        assert unresolved == []


class TestFoodBusinessesGetTheFoodApprovals:
    @pytest.mark.parametrize("use", [
        "cafe", "café", "restaurant", "bakery", "takeaway", "coffee shop", "brewery",
    ])
    def test_a_food_use_is_recognised(self, use):
        keys, _ = relevant(use)
        assert "food_business_notification" in keys
        assert "food_safety_supervisor" in keys

    def test_a_non_food_use_is_not_given_food_approvals(self):
        keys, _ = relevant("accountant's office", building_work=False)
        assert "food_business_notification" not in keys

    def test_trade_waste_is_raised_for_a_commercial_kitchen(self, call):
        result = call("get_other_approvals", {"proposed_use": "cafe",
                                              "connected_to_sewer": True})
        trade_waste = next(a for a in result["approvals"] if "Trade Waste" in a["approval"])
        assert "grease arrestor" in trade_waste["watch_out_for"]
        assert "Local Government Act 1993 section 68" in trade_waste["legislation"]

    def test_an_unsewered_site_is_not_told_to_get_a_trade_waste_approval(self):
        """The one place the over-list rule is wrong: trade waste is approval to
        discharge *to the sewer*. On a septic site it points at the wrong
        approval entirely, rather than merely at an unnecessary one."""
        keys, _ = relevant("cafe", connected_to_sewer=False)
        assert "liquid_trade_waste" not in keys
        assert "onsite_sewage_management" in keys


class TestTheThingsIssuedByPeopleWhoAreNotCouncil:
    def test_a_liquor_licence_is_attributed_to_the_state_not_council(self, call):
        result = call("get_other_approvals", {"proposed_use": "pub"})
        licence = next(a for a in result["approvals"] if "Liquor" in a["approval"])
        assert "not Council" in licence["issued_by"]
        assert "until development consent exists" in licence["when"]

    def test_the_long_service_levy_is_flagged_as_absent_from_councils_schedule(self, call):
        result = call("get_other_approvals", {"proposed_use": "shop", "building_work": True})
        levy = next(a for a in result["approvals"] if "Long Service" in a["approval"])
        assert "not Council" in levy["issued_by"]
        assert "not Council's charge" in levy["watch_out_for"]

    def test_outdoor_dining_is_a_service_nsw_application_not_a_da(self, call):
        result = call("get_other_approvals", {"proposed_use": "cafe", "outdoor_dining": True})
        dining = next(a for a in result["approvals"] if "Outdoor dining" in a["approval"])
        assert "Service NSW" in dining["what_it_is"]
        assert "waived" in dining["fee"]

    def test_permanent_outdoor_structures_are_distinguished_from_temporary(self, call):
        """The line that costs money, and it reaches back into the parking rate:
        an enclosed area becomes gross floor area under DCP 7.7.3.1(ii)."""
        result = call("get_other_approvals", {"proposed_use": "cafe", "outdoor_dining": True})
        dining = next(a for a in result["approvals"] if "Outdoor dining" in a["approval"])
        assert "$85.25" in dining["fee"] and "$113.65" in dining["fee"]
        assert "enclosed" in dining["watch_out_for"]


class TestToolSurface:
    def test_the_da_s_limits_are_stated_before_the_list(self, call):
        """The list only makes sense once the reader has stopped assuming the
        consent covered all of it."""
        result = call("get_other_approvals", {"proposed_use": "cafe"})
        keys = list(result)
        assert keys.index("what_the_da_does_not_cover") < keys.index("approvals")
        assert "not permission to build" in result["what_the_da_does_not_cover"]

    def test_approvals_are_grouped_by_when_they_happen(self, call):
        result = call("get_other_approvals", {"proposed_use": "cafe"})
        stages = result["when_each_one_happens"]
        assert any("before the DA is lodged" in s for s in stages)
        assert any("until development consent exists" in s for s in stages)

    def test_it_says_what_it_does_not_cover(self, call):
        result = call("get_other_approvals", {"proposed_use": "cafe"})
        assert "get_signage_requirements" in result["not_included_here"]
        assert "Section 64" in result["not_included_here"]

    def test_it_points_at_environmental_health_not_the_duty_planner(self, call):
        """For a food business the EHO conversation is worth more than the
        planning one, and businesses do not know that role exists."""
        result = call("get_other_approvals", {"proposed_use": "cafe"})
        assert "Environmental Health Officers" in result["who_to_ask"]["advice"]

    def test_the_listing_names_the_issuer_of_every_approval(self, call):
        result = call("list_other_approvals", {})
        assert len(result["approvals"]) == len(APPROVALS)
        assert all(a["issued_by"] for a in result["approvals"])
