"""Logging, and the guarantee that it excludes applicant data.

This server handles other people's personal information: fill_see_pdf,
preview_see_form and generate_see_draft all take an applicant's name, street
address and lot/DP. The public deployment is unauthenticated and its logs go to
a third-party platform, so a leak here would be a real disclosure rather than an
untidy log line.

TestNoApplicantDataInLogs is the point of this file.
"""

import asyncio
import logging

import pytest

from lismore_da_mcp import observability as obs
from lismore_da_mcp.server import call_tool

# Distinctive values, so a match in captured output cannot be coincidence.
APPLICANT = "Wilhelmina Farnsworth-Beauchamp"
ADDRESS = "17 Zebediah Crescent, Goonellabah NSW 2480"
LOT_DP = "Lot 4417 DP 998877"

SEE_ARGS = {
    "applicant_name": APPLICANT,
    "minor_development_type": "dwelling_single_storey",
    "property_address": ADDRESS,
    "lot_dp": LOT_DP,
    "zone_code": "R2",
    "proposed_use": "dwelling house",
    "development_type": "dwelling",
    "floor_area_sqm": 180,
}


@pytest.fixture(autouse=True)
def _logging_on():
    obs.configure_logging()
    obs.logger.setLevel(logging.DEBUG)


class TestNoApplicantDataInLogs:
    def test_see_preview_logs_no_personal_information(self, caplog):
        with caplog.at_level(logging.DEBUG, logger=obs.LOGGER_NAME):
            asyncio.run(call_tool("preview_see_form", SEE_ARGS))
        blob = caplog.text
        assert blob, "expected the call to be logged at all"
        for secret in (APPLICANT, ADDRESS, LOT_DP, "Farnsworth", "Zebediah", "998877"):
            assert secret not in blob, f"{secret!r} leaked into logs"

    def test_see_draft_logs_no_personal_information(self, caplog):
        args = {
            "property_address": ADDRESS,
            "lot_dp": LOT_DP,
            "zone_code": "R2",
            "proposed_use": "dwelling house",
            "development_type": "dwelling",
            "floor_area_sqm": 180,
            "applicant_name": APPLICANT,
        }
        with caplog.at_level(logging.DEBUG, logger=obs.LOGGER_NAME):
            asyncio.run(call_tool("generate_see_draft", args))
        for secret in (APPLICANT, ADDRESS, LOT_DP):
            assert secret not in caplog.text

    def test_rejected_arguments_do_not_leak_values(self, caplog):
        """A validation failure names the offending argument — it must not quote
        the value, which is where a mistyped address would end up."""
        with caplog.at_level(logging.DEBUG, logger=obs.LOGGER_NAME):
            asyncio.run(call_tool("preview_see_form", {**SEE_ARGS, "bogus_field": ADDRESS}))
        assert ADDRESS not in caplog.text

    def test_recorder_has_no_parameter_for_argument_values(self):
        """The guarantee is structural: there is no parameter to pass one to."""
        import inspect

        params = set(inspect.signature(obs.record_tool_call).parameters)
        assert params == {"tool_name", "duration_ms", "outcome", "error_type"}


class TestToolCallLogging:
    def test_successful_call_is_logged(self, caplog):
        with caplog.at_level(logging.INFO, logger=obs.LOGGER_NAME):
            asyncio.run(call_tool("get_zone_info", {"zone_code": "R2"}))
        assert "tool=get_zone_info" in caplog.text
        assert "outcome=ok" in caplog.text
        assert "duration_ms=" in caplog.text

    def test_invalid_arguments_logged_as_such(self, caplog):
        with caplog.at_level(logging.INFO, logger=obs.LOGGER_NAME):
            asyncio.run(call_tool("get_zone_info", {"zone": "R2"}))
        assert "outcome=invalid_arguments" in caplog.text

    def test_invalid_arguments_are_a_warning_not_an_error(self, caplog):
        """A caller mistake is not a server fault; conflating them makes error
        rates useless."""
        with caplog.at_level(logging.INFO, logger=obs.LOGGER_NAME):
            asyncio.run(call_tool("get_zone_info", {}))
        levels = {r.levelname for r in caplog.records}
        assert "WARNING" in levels and "ERROR" not in levels

    def test_a_raising_handler_is_still_recorded(self, caplog):
        """Defaults to error, so a handler that raises is logged rather than
        vanishing."""
        with caplog.at_level(logging.INFO, logger=obs.LOGGER_NAME):
            with pytest.raises(RuntimeError):
                with obs.timed_tool_call("exploding_tool"):
                    raise RuntimeError("boom")
        assert "tool=exploding_tool" in caplog.text
        assert "outcome=error" in caplog.text
        assert "error_type=RuntimeError" in caplog.text


class TestOperationalEvents:
    def test_rate_limit_event_logged_without_the_ip(self, caplog):
        """The client IP is personal information and Render's proxy already has
        it; carrying it here would add retention risk for little gain."""
        with caplog.at_level(logging.WARNING, logger=obs.LOGGER_NAME):
            obs.record_rate_limited(60.0, 30)
        assert "event=rate_limited" in caplog.text
        assert "max_requests=30" in caplog.text
        import inspect
        assert "ip" not in inspect.signature(obs.record_rate_limited).parameters

    def test_index_state_logged(self, caplog):
        with caplog.at_level(logging.INFO, logger=obs.LOGGER_NAME):
            obs.record_index_state("present", 904)
        assert "event=search_index" in caplog.text and "segments=904" in caplog.text

    def test_startup_logged(self, caplog):
        with caplog.at_level(logging.INFO, logger=obs.LOGGER_NAME):
            obs.record_startup("http")
        assert "event=startup transport=http" in caplog.text


class TestConfiguration:
    def test_level_comes_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("LISMORE_LOG_LEVEL", "DEBUG")
        assert obs.configure_logging().level == logging.DEBUG

    def test_unknown_level_falls_back_to_info(self, monkeypatch):
        monkeypatch.setenv("LISMORE_LOG_LEVEL", "NONSENSE")
        assert obs.configure_logging().level == logging.INFO

    def test_configuring_twice_does_not_duplicate_handlers(self):
        obs.configure_logging()
        before = len(obs.logger.handlers)
        obs.configure_logging()
        assert len(obs.logger.handlers) == before
