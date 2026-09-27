"""fill_see_pdf on the public HTTP transport.

The filled form carries a named applicant's address, so in PUBLIC_MODE it must
never outlive the call, and it is returned as a binary resource rather than as
base64 inside the JSON text.
"""

import asyncio
import base64
import json
import tempfile

import pytest
from mcp.types import EmbeddedResource

from lismore_da_mcp import server as srv
from lismore_da_mcp.tools import see as see_tools

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


@pytest.fixture
def public_mode(monkeypatch, tmp_path):
    """PUBLIC_MODE on, with temp dirs created somewhere the test can inspect."""
    monkeypatch.setattr(see_tools, "PUBLIC_MODE", True)
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    return tmp_path


def _fill(arguments=None):
    return asyncio.run(srv.call_tool("fill_see_pdf", arguments or dict(SEE)))


class TestTheFilledPdf:
    def test_is_attached_as_a_pdf_resource(self, public_mode):
        text, attachment = _fill()
        assert isinstance(attachment, EmbeddedResource)
        assert attachment.resource.mime_type == "application/pdf"
        assert base64.b64decode(attachment.resource.blob).startswith(b"%PDF")

    def test_is_not_repeated_inside_the_json(self, public_mode):
        text, _ = _fill()
        payload = json.loads(text.text)
        assert payload["success"] is True
        assert "pdf_base64" not in payload
        assert "output_path" not in payload
        assert payload["output_filename"] == "SEE_filled.pdf"

    def test_leaves_nothing_on_disk(self, public_mode):
        _fill()
        assert list(public_mode.iterdir()) == []


class TestAFillThatRaises:
    def test_still_leaves_nothing_on_disk(self, public_mode, monkeypatch):
        """A bug in the field mapping raises past fill_see_pdf's own error
        handling on purpose; the applicant's file must not survive it."""

        def half_written(form_data, output_path):
            output_path.write_bytes(b"%PDF- partial, with an applicant's address")
            raise TypeError("a bug in the field mapping")

        monkeypatch.setattr(see_tools, "fill_see_pdf", half_written)
        with pytest.raises(TypeError):
            _fill()
        assert list(public_mode.iterdir()) == []


class TestLocalMode:
    def test_still_writes_to_documents_output(self):
        (text,) = _fill()
        payload = json.loads(text.text)
        assert payload["output_path"].endswith("documents/output/SEE_filled.pdf")
