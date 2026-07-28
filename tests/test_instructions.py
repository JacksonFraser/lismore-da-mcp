"""Server instructions.

A remote agent connecting to the hosted server receives these plus 21 tool
descriptions, and nothing else. Everything an agent needs that it cannot infer
from a schema — the order of work, and the caveats that must accompany planning
advice — is here or is nowhere.

Two kinds of test:

  * the caveats are still present, so a tidy-up cannot quietly drop one
  * the factual claims still match the data, so the text cannot go stale while
    the code moves underneath it
"""

import re

import pytest

import lismore_da_mcp.server  # noqa: F401  (registers the tools)
from lismore_da_mcp.app import server
from lismore_da_mcp.data.zones import ZONES
from lismore_da_mcp.instructions import INSTRUCTIONS
from lismore_da_mcp.registry import registered


class TestDelivery:
    def test_reaches_initialization_options(self):
        assert server.create_initialization_options().instructions == INSTRUCTIONS

    def test_not_empty(self):
        assert INSTRUCTIONS.strip()

    def test_stays_short_enough_to_carry_every_session(self):
        """Injected into every session, so it has to earn its place. This is a
        budget, not a target — if it needs to grow, move detail into tool
        descriptions instead."""
        assert len(INSTRUCTIONS) < 4000, f"{len(INSTRUCTIONS)} chars is getting long"


class TestCaveatsSurvive:
    """Each of these exists because getting it wrong produces bad planning
    advice, not just a worse answer."""

    def test_states_it_is_not_a_determination(self):
        assert "Council decides" in INSTRUCTIONS

    def test_warns_that_the_lep_table_is_not_the_whole_story(self):
        """The single most common question is granny flats, and the LEP table
        alone answers it wrongly."""
        lowered = INSTRUCTIONS.lower()
        assert "sepp" in lowered
        assert "secondary dwelling" in lowered or "granny flat" in lowered
        assert "settled refusal" in lowered or "not report" in lowered

    def test_directs_flood_affected_sites_to_the_duty_planner(self):
        assert "flood" in INSTRUCTIONS.lower()
        assert "duty planner" in INSTRUCTIONS.lower()

    def test_dates_the_fee_scale(self):
        assert "2024-25" in INSTRUCTIONS and "July" in INSTRUCTIONS

    def test_flags_superseded_lep_2000_results(self):
        assert "LEP 2000" in INSTRUCTIONS

    def test_covers_exempt_development_before_assuming_a_da(self):
        assert "exempt" in INSTRUCTIONS.lower()

    def test_says_tools_refuse_rather_than_guess(self):
        """The refusals are deliberate; an agent that papers over them with a
        plausible value undoes the point of them."""
        assert "refuse" in INSTRUCTIONS.lower()


class TestFactsMatchTheData:
    """Claims here must track the code, or the instructions become confidently
    wrong the moment the data changes."""

    def test_zone_count_is_correct(self):
        stated = int(re.search(r"Lismore has (\d+) zones", INSTRUCTIONS).group(1))
        actual = len([z for z in ZONES if not ZONES[z].get("redirect_to")])
        assert stated == actual

    @pytest.mark.parametrize("code", ["RU4", "RU6", "R4", "E5", "C4", "SP1"])
    def test_zones_it_says_do_not_exist_really_do_not(self, code):
        assert code not in ZONES

    @pytest.mark.parametrize("retired,current", [("B3", "E2"), ("IN1", "E4")])
    def test_retired_code_redirects_match(self, retired, current):
        assert f"{retired} is now {current}" in INSTRUCTIONS
        assert ZONES[retired]["redirect_to"] == current

    def test_every_tool_it_names_exists(self):
        """A renamed tool would leave the instructions pointing at nothing."""
        named = set(re.findall(r"\b([a-z_]+(?:_[a-z]+)+)\b", INSTRUCTIONS))
        tool_shaped = {
            n for n in named
            if n.startswith(("get_", "check_", "list_", "search_", "calculate_",
                             "generate_", "preview_", "fill_", "read_"))
        }
        missing = sorted(tool_shaped - set(registered()))
        assert missing == [], f"instructions name tools that do not exist: {missing}"
