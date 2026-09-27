"""The interpretation register (ROADMAP.md B1).

Three things are pinned here. The register's quotes are the documents' words —
re-run from `scripts/audit_interpretations.py`, the way every other audit is
wired into the suite. The tools cite a reading inside the answer that depends
on it, and *only* there — a citation on an answer it does not affect is the
standing caveat item 0.1 diagnosed. And the costs each entry states are what
the tools actually compute, so the register cannot drift into describing a
different tool from the one that ships.
"""

import asyncio
import json
import math
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_interpretations import (  # noqa: E402
    link_findings,
    quote_findings,
    shape_findings,
)
from render_interpretations import render  # noqa: E402

from lismore_da_mcp.contributions import estimate_contribution  # noqa: E402
from lismore_da_mcp.data.interpretations import BY_KEY, INTERPRETATIONS  # noqa: E402
from lismore_da_mcp.data.parking import PARKING_RATES  # noqa: E402
from lismore_da_mcp.data.readiness import DUTY_PLANNER_QUESTIONS  # noqa: E402
from lismore_da_mcp.interpretations import cite  # noqa: E402
from lismore_da_mcp.parking import estimate_spaces  # noqa: E402
from lismore_da_mcp.server import call_tool  # noqa: E402

PACKAGE = ROOT / "src" / "lismore_da_mcp"


def call(name, arguments):
    return json.loads(asyncio.run(call_tool(name, arguments))[0].text)


def cited(node) -> list[str]:
    """Every interpretation id cited anywhere in a response."""
    return re.findall(r'"id": "([a-z0-9_]+)"', json.dumps(node))


class TestTheRegisterQuotesTheDocuments:
    def test_every_quote_is_where_the_register_says(self):
        assert quote_findings(INTERPRETATIONS) == []

    def test_every_entry_has_what_the_planner_review_needs(self):
        assert shape_findings(INTERPRETATIONS) == []

    def test_every_link_resolves(self):
        assert link_findings(INTERPRETATIONS) == []

    def test_the_audit_catches_a_quote_on_the_wrong_page(self):
        moved = [{**BY_KEY["cafe_whichever_is_greater"],
                  "provision": [{**BY_KEY["cafe_whichever_is_greater"]["provision"][0],
                                 "page": 13}]}]
        (finding,) = quote_findings(moved)
        assert "found on page [14]" in finding

    def test_the_audit_catches_a_misquote(self):
        entry = BY_KEY["heritage_document_is_discretionary"]
        misquoted = [{**entry, "provision": [{**entry["provision"][0],
                                              "verbatim": "The consent authority must, before "
                                                          "granting consent to any development—"}]}]
        assert quote_findings(misquoted)


class TestCitationsStayShort:
    """A citation is one line and a cost. The reasoning lives in the register."""

    @pytest.mark.parametrize("entry", INTERPRETATIONS, ids=lambda e: e["key"])
    def test_the_cited_fields_are_short(self, entry):
        assert len(entry["in_one_line"]) <= 200
        assert len(entry["cost_if_council_disagrees"]) <= 300

    def test_an_unknown_key_fails_at_the_call_site(self):
        with pytest.raises(KeyError):
            cite("no_such_reading")

    def test_every_key_the_code_cites_is_registered(self):
        source = "\n".join(p.read_text(encoding="utf-8") for p in PACKAGE.rglob("*.py")
                           if p.name != "interpretations.py")
        used = set(re.findall(r'"([a-z0-9]+(?:_[a-z0-9]+)+)"', source)) & set(BY_KEY)
        # The inverse: keys that look like readings but are not registered.
        for literal in re.findall(r'cite\("([^"]+)"\)', source):
            assert literal in BY_KEY
        assert used, "no tool cites the register"


class TestTheParkingToolCitesItsReadings:
    """ROADMAP.md B1: at least parking, contributions and flood cite theirs."""

    def test_a_cbd_cafe_cites_the_fixed_rate_reading(self):
        answer = call("get_parking_rates", {"development_type": "cafe", "location": "cbd",
                                            "floor_area_sqm": 80})
        assert cited(answer["readings_relied_on"]) == ["cbd_fixed_rate_replaces_schedule_1"]

    def test_an_unplaced_cafe_cites_both_readings_its_figures_rest_on(self):
        answer = call("get_parking_rates", {"development_type": "cafe", "floor_area_sqm": 80})
        assert cited(answer["readings_relied_on"]) == [
            "cbd_fixed_rate_replaces_schedule_1", "cafe_whichever_is_greater"]

    def test_a_credit_cites_the_credit_readings(self):
        answer = call("get_parking_rates", {"development_type": "cafe", "location": "cbd",
                                            "floor_area_sqm": 80, "existing_gfa_sqm": 80})
        assert {"cbd_credit_on_change_of_use", "cbd_rounding"} <= set(
            cited(answer["readings_relied_on"]))

    def test_a_citation_carries_the_cost(self):
        answer = call("get_parking_rates", {"development_type": "cafe", "location": "cbd",
                                            "floor_area_sqm": 80})
        (citation,) = answer["readings_relied_on"]
        assert citation["if_council_disagrees"] == BY_KEY[
            "cbd_fixed_rate_replaces_schedule_1"]["cost_if_council_disagrees"]

    def test_the_outdoor_dining_lever_cites_its_reading(self):
        answer = call("get_parking_rates", {"development_type": "cafe", "location": "cbd",
                                            "floor_area_sqm": 80, "spaces_provided": 0})
        options = answer["addressing_the_shortfall"]["options"]
        assert "unenclosed_dining_generates_no_parking" in cited(options)

    def test_an_answer_that_takes_no_reading_cites_none(self):
        """No standing caveat: a shop placed outside the CBD rests on no registered reading."""
        answer = call("get_parking_rates", {"development_type": "shop",
                                            "location": "outside_cbd", "floor_area_sqm": 80})
        assert "readings_relied_on" not in answer


class TestTheContributionCitesItsReadings:
    def test_a_cafe_cites_the_retail_classification_and_pro_rata(self):
        answer = estimate_contribution("cafe", {"gross_floor_area_m2": 80}, "urban")
        assert cited(answer["readings_relied_on"]) == [
            "food_and_drink_charged_as_retail", "contribution_pro_rata"]

    def test_a_warehouse_cites_the_industry_classification(self):
        """It resolves 'exact', so nothing else in the answer flagged the judgement."""
        answer = estimate_contribution("warehouse or distribution centre",
                                       {"gross_floor_area_m2": 200}, "urban")
        assert cited(answer["readings_relied_on"]) == ["warehouse_charged_as_industry"]

    def test_an_assumed_previous_floor_area_is_cited(self):
        answer = estimate_contribution("cafe", {"gross_floor_area_m2": 140}, "urban",
                                       existing_use="office")
        assert "allowance_same_floor_area" in cited(answer["readings_relied_on"])

    def test_a_house_to_cafe_cites_the_netting_reading(self):
        answer = estimate_contribution("cafe", {"gross_floor_area_m2": 80}, "urban",
                                       existing_use="dwelling house",
                                       existing_counts={"dwellings": 1})
        ids = cited(answer["readings_relied_on"])
        assert "allowance_netted_as_totals" in ids
        assert "allowance_same_floor_area" not in ids

    def test_whole_units_of_a_named_row_cite_nothing(self):
        answer = estimate_contribution("shop", {"gross_floor_area_m2": 100}, "urban")
        assert "readings_relied_on" not in answer

    def test_the_citation_reaches_the_budget(self):
        answer = call("calculate_da_fees", {"development_cost": 50000, "development_type": "cafe",
                                            "gross_floor_area_m2": 80, "catchment": "urban"})
        assert "food_and_drink_charged_as_retail" in cited(
            answer["parts"]["section_7_11_contributions"])


class TestTheFloodToolCitesItsReadings:
    def test_the_exemption_cites_its_reading(self):
        answer = call("get_flood_requirements", {"development_type": "cafe",
                                                 "flood_area": "flood_fringe",
                                                 "is_change_of_use": True})
        exemption = answer["applies"]["change_of_use_exemption"]
        assert cited(exemption["readings_relied_on"]) == ["flood_change_of_use_with_fitout"]

    def test_the_cbd_flood_liable_area_cites_the_extension_too(self):
        answer = call("get_flood_requirements", {"development_type": "cafe", "flood_area": "cbd",
                                                 "is_change_of_use": True})
        exemption = answer["applies"]["change_of_use_exemption"]
        assert cited(exemption["readings_relied_on"]) == [
            "flood_change_of_use_with_fitout", "flood_exemption_reaches_cbd_flood_liable"]

    def test_new_development_cites_nothing(self):
        answer = call("get_flood_requirements", {"development_type": "cafe",
                                                 "flood_area": "flood_fringe"})
        assert "readings_relied_on" not in json.dumps(answer)


class TestTheStatedCostsAreWhatTheToolsCompute:
    """Each cost in the register is a worked figure. If a tool changes, so must its entry."""

    CAFE = PARKING_RATES["cafe"]

    def spaces(self, seats, employees, area=80):
        return estimate_spaces(self.CAFE, area, {"seats": seats, "employees": employees})[
            "spaces_required"]

    def test_cbd_fixed_rate_cost(self):
        cbd = call("get_parking_rates", {"development_type": "cafe", "location": "cbd",
                                         "floor_area_sqm": 80})["calculation"]
        assert cbd["spaces_required"] == 3
        assert self.spaces(40, 6) == 17
        assert "17 spaces rather than 3" in BY_KEY[
            "cbd_fixed_rate_replaces_schedule_1"]["cost_if_council_disagrees"]

    def test_cafe_reading_costs(self):
        assert self.spaces(40, 6) == 17
        assert self.spaces(20, 6) == 15
        # Reading A: greater of (seats + staff) and floor area. Reading B: seats plus the
        # greater of staff and floor area. Worked by hand here, since the tool implements C.
        assert math.ceil(max(20 / 3 + 6 / 2, 80 * 15 / 100)) == 12
        assert math.ceil(40 / 3 + max(6 / 2, 80 * 15 / 100)) == 26
        cost = BY_KEY["cafe_whichever_is_greater"]["cost_if_council_disagrees"]
        assert "26 spaces, not 17" in cost and "(12 against 15)" in cost

    def test_credit_cost(self):
        with_credit = call("get_parking_rates", {"development_type": "cafe", "location": "cbd",
                                                 "floor_area_sqm": 80, "existing_gfa_sqm": 80})
        assert with_credit["calculation"]["spaces_required"] == 1
        assert "3 spaces rather than 1" in BY_KEY[
            "cbd_credit_on_change_of_use"]["cost_if_council_disagrees"]

    def test_same_floor_area_cost(self):
        assumed = estimate_contribution("cafe", {"gross_floor_area_m2": 140}, "urban",
                                        existing_use="office")
        stated = estimate_contribution("cafe", {"gross_floor_area_m2": 140}, "urban",
                                       existing_use="office",
                                       existing_counts={"gross_floor_area_m2": 100})
        assert round(assumed["net_contribution"]["urban"]) == 21543
        assert round(stated["net_contribution"]["urban"]) == 23428
        cost = BY_KEY["allowance_same_floor_area"]["cost_if_council_disagrees"]
        assert "$21,543" in cost and "$23,428" in cost

    def test_netting_cost(self):
        answer = estimate_contribution("cafe", {"gross_floor_area_m2": 80}, "urban",
                                       existing_use="dwelling house",
                                       existing_counts={"dwellings": 1})
        assert round(answer["net_contribution"]["urban"]) == 9029
        assert "$9,029" in BY_KEY["allowance_netted_as_totals"]["cost_if_council_disagrees"]

    def test_pro_rata_cost(self):
        answer = estimate_contribution("cafe", {"gross_floor_area_m2": 80}, "urban")
        assert round(answer["contribution"]["urban"]) == 16081
        whole = estimate_contribution("cafe", {"gross_floor_area_m2": 100}, "urban")
        assert round(whole["contribution"]["urban"]) == 20102
        cost = BY_KEY["contribution_pro_rata"]["cost_if_council_disagrees"]
        assert "$16,081" in cost and "$20,102" in cost

    def test_tourist_cost(self):
        from lismore_da_mcp.data.contributions import KNOWN_TABLE_DISCREPANCIES
        (discrepancy,) = [d for d in KNOWN_TABLE_DISCREPANCIES
                          if d["development_type"] == "tourist_accommodation"]
        assert f"${discrepancy['difference']:.2f}" in BY_KEY[
            "tourist_rural_published_figure"]["cost_if_council_disagrees"]

    def test_nearest_type_example_is_what_the_tool_answers(self):
        answer = call("check_permissibility", {"zone_code": "MU1",
                                               "land_use": "artisan food and drink industry"})
        assert answer["permissibility"] == "permitted_with_consent"
        assert answer["matched_use"] == "Light industries"


class TestTheRegisterIsLinkedAndPrintable:
    def test_disputed_reading_questions_exist(self):
        keys = {q["key"] for q in DUTY_PLANNER_QUESTIONS}
        linked = {e["duty_planner_question"] for e in INTERPRETATIONS} - {None}
        assert linked <= keys

    def test_every_reading_that_can_hurt_a_parking_contribution_or_flood_answer_is_cited(self):
        """The done-when of B1: those three tools cite theirs. A reading that understates the
        burden, relied on by one of them, must be cited by some code path."""
        source = "\n".join(p.read_text(encoding="utf-8") for p in PACKAGE.rglob("*.py")
                           if p.name != "interpretations.py")
        for entry in INTERPRETATIONS:
            if entry["if_wrong_this_tool"] == "overstates the burden" and \
                    entry["key"] != "cbd_credit_not_for_schedule_1_uses":
                continue
            if not {"get_parking_rates", "calculate_da_fees", "get_flood_requirements"} & set(
                    entry["relied_on_by"]):
                continue
            if entry["key"] == "fee_schedule_column":
                continue  # about 4% of a lodgement fee — every fee answer would carry it
            assert f'"{entry["key"]}"' in source, f"{entry['key']} is never cited"

    def test_the_review_packet_carries_every_entry(self):
        packet = render()
        for entry in INTERPRETATIONS:
            assert f"`{entry['key']}`" in packet
        assert packet.count("Planner's mark") == len(INTERPRETATIONS)
