"""Tool calls must not block the event loop.

Every handler in this server is synchronous and blocking: PDF text extraction,
SQLite reads, and — since the address tools — HTTPS round trips with an
8-second timeout. Dispatched inline they hold the single event loop thread for
their whole duration, so the public deployment served one caller at a time and
`/health` stalled behind whatever tool was running. Measured before the fix:
five concurrent calls to a 0.3s handler took 1.51s, a clean 5x.

`call_tool` runs handlers via `asyncio.to_thread`. These tests pin that, and
pin the thread-safety it depends on — the failure mode of getting this wrong is
not an exception but corrupted output under load, which no other test would
notice.
"""

import asyncio
import dataclasses
import json
import time

import mcp.types as types
import pytest
from mcp.types import TextContent

from lismore_da_mcp import registry
from lismore_da_mcp.server import _on_call_tool

SEE = {
    "applicant_name": "A Person",
    "property_address": "12 Keen Street, Lismore NSW 2480",
    "lot_dp": "Lot 12 DP 758651",
    "zone_code": "R2",
    "proposed_use": "dwelling house",
    "development_type": "dwelling",
    "floor_area_sqm": 180,
    "minor_development_type": "dwelling_single_storey",
}


async def _call(name: str, arguments: dict):
    result = await _on_call_tool(
        None, types.CallToolRequestParams(name=name, arguments=arguments)
    )
    return result.content[0].text


@pytest.fixture
def slow_tool(monkeypatch):
    """Swap one handler for a blocking sleep.

    Stands in for a network round trip or a large PDF read without the variance
    of either, so the test measures the dispatcher rather than the tool.
    """
    delay = 0.25
    entry = registry._REGISTRY["get_contact_info"]

    def blocking(_arguments):
        time.sleep(delay)
        return [TextContent(type="text", text="{}")]

    monkeypatch.setitem(
        registry._REGISTRY,
        "get_contact_info",
        dataclasses.replace(entry, handler=blocking),
    )
    return delay


class TestEventLoopIsNotBlocked:
    def test_concurrent_calls_overlap(self, slow_tool):
        """Five 0.25s calls should take about 0.25s, not 1.25s."""

        async def run():
            started = time.perf_counter()
            await asyncio.gather(*[_call("get_contact_info", {}) for _ in range(5)])
            return time.perf_counter() - started

        elapsed = asyncio.run(run())
        # Generous ceiling: the point is 5x serialisation, not a precise timing.
        assert elapsed < slow_tool * 2.5, (
            f"5 concurrent calls took {elapsed:.2f}s against a {slow_tool}s handler — "
            "handlers look serialised on the event loop again"
        )

    def test_the_loop_stays_responsive_during_a_call(self, slow_tool):
        """A blocking handler must not stall unrelated loop work.

        This is what made /health stall behind a slow tool: the health route and
        the tool call share one thread.
        """

        async def run():
            ticks = 0

            async def heartbeat():
                nonlocal ticks
                while True:
                    await asyncio.sleep(0.01)
                    ticks += 1

            beat = asyncio.create_task(heartbeat())
            await _call("get_contact_info", {})
            beat.cancel()
            return ticks

        assert asyncio.run(run()) > 5, "event loop made no progress during a tool call"


class TestThreadSafety:
    """Concurrency is only safe because nothing is shared between handlers.

    sqlite3 connections and fitz documents are opened per call and never cross
    threads; the data dicts are read-only. If that stops being true, these fail
    as wrong output rather than as an exception.
    """

    def test_pdf_and_index_reads_are_consistent_under_load(self):
        calls = [
            ("search_dcp", {"query": "setback residential", "chapter": "chapter-1"}),
            ("read_dcp_section", {
                "chapter": "chapter-7-off-street-carparking.pdf",
                "start_page": 1, "end_page": 3,
            }),
            ("preview_see_form", SEE),
            ("get_parking_rates", {"development_type": "restaurant"}),
        ]

        async def run():
            jobs = [_call(name, args) for _ in range(6) for name, args in calls]
            return await asyncio.gather(*jobs, return_exceptions=True)

        results = asyncio.run(run())
        failures = [r for r in results if isinstance(r, BaseException)]
        assert failures == [], f"{len(failures)} concurrent calls raised: {failures[:2]}"

        # Each argument set must give one answer, however many ran at once.
        for offset, (name, _) in enumerate(calls):
            answers = {results[offset + i * len(calls)] for i in range(6)}
            assert len(answers) == 1, f"{name} returned {len(answers)} different answers"

    def test_concurrent_fills_leave_a_readable_pdf(self, tmp_path):
        """fill_see_pdf writes to a fixed default filename outside PUBLIC_MODE.

        Two fills in flight would interleave in one file with a direct save, so
        the write stages beside the target and renames atomically.
        """
        import fitz

        from lismore_da_mcp.config import DOCS_DIR

        async def run():
            return await asyncio.gather(
                *[_call("fill_see_pdf", dict(SEE)) for _ in range(5)],
                return_exceptions=True,
            )

        results = asyncio.run(run())
        failures = [r for r in results if isinstance(r, BaseException)]
        assert failures == [], f"concurrent fills raised: {failures[:2]}"
        assert all(json.loads(r)["success"] for r in results)

        output = DOCS_DIR / "output" / "SEE_filled.pdf"
        document = fitz.open(str(output))
        try:
            assert document.page_count > 0
        finally:
            document.close()

        leaked = list((DOCS_DIR / "output").glob(".SEE_filled.pdf.*"))
        assert leaked == [], f"staging files left behind: {leaked}"
