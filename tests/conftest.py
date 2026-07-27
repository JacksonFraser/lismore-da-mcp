"""Shared fixtures.

The server module is imported once here so that every test file shares the same
loaded PDF paths and data dicts — importing it is not free (it opens a font via
fitz at module scope) and the data is read-only in tests.
"""

import asyncio
import json
from pathlib import Path

import pytest

from lismore_da_mcp import server as srv


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
