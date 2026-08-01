"""Shared fixtures.

The server module is imported once here so that every test file shares the same
loaded PDF paths and data dicts — importing it is not free (it opens a font via
fitz at module scope) and the data is read-only in tests.
"""

import asyncio
import json
from pathlib import Path

import pytest

from lismore_da_mcp import addresses
from lismore_da_mcp import server as srv

# Canned upstream responses for the one address the smoke tests use. Only
# lookup_zone_by_address goes near the network, and it must not in CI: the
# suite would then fail on an outage, and pass or fail depending on what a
# third party returned that morning. tests/test_addresses.py drives the same
# seam directly to cover the failure paths, and keeps one opt-in live check.
CANNED_GEOCODE = {
    "addressResult": {
        "numRecs": 1,
        "addresses": [{
            "houseNumberString": "12",
            "roadName": "Keen",
            "roadType": "Street",
            "suburbName": "Lismore",
            "postCode": 2480,
            "council": "Lismore",
            "addressString": "12  Keen Street  Lismore 2480",
            "addressPoint": {"centreX": 153.28188744877176, "centreY": -28.804604961354848},
        }],
    }
}

CANNED_ZONE = {
    "features": [{
        "attributes": {
            "EPI_NAME": "Lismore Local Environmental Plan 2012",
            "LGA_NAME": "LISMORE",
            "SYM_CODE": "E2",
            "LAY_CLASS": "Commercial Centre",
            "EPI_TYPE": "LEP",
        }
    }]
}


@pytest.fixture(autouse=True)
def no_outbound_http(monkeypatch):
    """Nothing in the suite reaches a live API unless it opts back in.

    A test that wants a different upstream answer monkeypatches
    `addresses._get_json` itself; this is only the floor.
    """

    def canned(url: str, params: dict) -> dict:
        if url == addresses.GEOCODER_URL:
            return CANNED_GEOCODE
        if url == addresses.ZONING_LAYER_URL:
            return CANNED_ZONE
        # A constraint layer: covered by the dataset, nothing at this point.
        if params.get("returnCountOnly"):
            return {"count": 1}
        return {"features": []}

    monkeypatch.setattr(addresses, "_get_json", canned)
    # Layer coverage is cached for the life of the process; without this a test
    # that stubs a layer as uncovered would leak that into every later test.
    addresses._coverage_cache.clear()
    yield
    addresses._coverage_cache.clear()


@pytest.fixture(scope="session")
def docs_dir() -> Path:
    return srv.DOCS_DIR


@pytest.fixture(scope="session")
def see_template(docs_dir: Path) -> Path:
    path = srv.SEE_TEMPLATE_PATH
    if not path.exists():
        pytest.skip(f"SEE template not present at {path}")
    return path


@pytest.fixture
def call():
    """Call a tool by name and return its parsed JSON payload.

    Mirrors how an MCP client reaches the server: through call_tool, including
    argument validation, rather than by calling handlers directly.
    """

    def _call(name: str, arguments: dict | None = None):
        result = asyncio.run(srv.call_tool(name, arguments or {}))
        assert len(result) == 1, f"{name} returned {len(result)} content blocks"
        text = result[0].text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # read_dcp_section returns plain text rather than JSON
            return text

    return _call
