"""Planning instrument labelling.

The DCP has parallel chapters for LEP 2012 land and LEP 2000 land, sitting side
by side in documents/dcp/. Before this, search returned hits from either with
nothing to distinguish them, so a superseded residential setback could be quoted
as a current control. That is the one remaining way this server could give
actively wrong planning advice, hence the coverage.
"""

import pytest

from lismore_da_mcp.data.instruments import (
    GENERAL_DOCUMENTS,
    LEP_2000,
    LEP_2000_DOCUMENTS,
    LEP_2012,
    NOT_INSTRUMENT_SPECIFIC,
    STATE,
    instrument_for,
    is_superseded,
)
from lismore_da_mcp.search import list_available_documents, search_all, searchable_documents


class TestRegistryMatchesDisk:
    """A registry naming files that no longer exist, or missing ones that do,
    fails silently — the label just stops appearing."""

    def test_every_lep2000_entry_exists_on_disk(self):
        on_disk = {p.name for p in searchable_documents()}
        missing = sorted(LEP_2000_DOCUMENTS - on_disk)
        assert missing == [], f"registry names files not present: {missing}"

    def test_every_general_entry_exists_on_disk(self):
        on_disk = {p.name for p in searchable_documents()}
        missing = sorted(GENERAL_DOCUMENTS - on_disk)
        assert missing == [], f"registry names files not present: {missing}"

    def test_no_lep2000_file_is_unregistered(self):
        """Catches a new -lep2000 document being added without being labelled."""
        looks_superseded = {
            p.name for p in searchable_documents() if "lep2000" in p.name.lower()
        }
        unregistered = sorted(looks_superseded - LEP_2000_DOCUMENTS)
        assert unregistered == [], f"named like LEP 2000 but not registered: {unregistered}"

    def test_each_superseded_chapter_has_a_current_counterpart(self):
        """A LEP 2000 chapter with no LEP 2012 equivalent would mean the warning
        sends the reader nowhere.

        Matched on chapter number, not name: chapter 14 is "Tree Preservation
        Order" under LEP 2000 and "Vegetation Protection" under LEP 2012, so the
        titles do not correspond even though the chapters do. This is why
        SUPERSEDED_NOTE points at the chapter *number* rather than the title.
        """
        import re

        def chapter_id(name):
            match = re.match(r"(part-b-)?chapter-(\d+[a-z]?)", name)
            return (bool(match.group(1)), match.group(2)) if match else None

        current = {chapter_id(p.name) for p in searchable_documents() if "lep2000" not in p.name}
        for name in LEP_2000_DOCUMENTS:
            assert chapter_id(name) in current, f"{name} has no current counterpart"


class TestClassification:
    @pytest.mark.parametrize("name", sorted(LEP_2000_DOCUMENTS))
    def test_lep2000_documents(self, name):
        assert instrument_for(name, "dcp") == LEP_2000
        assert is_superseded(name)

    @pytest.mark.parametrize("name", [
        "chapter-1-residential-development.pdf",
        "chapter-7-off-street-carparking.pdf",
        "part-b-chapter-6-nimbin-village.pdf",
    ])
    def test_current_dcp_documents(self, name):
        assert instrument_for(name, "dcp") == LEP_2012
        assert not is_superseded(name)

    def test_exempt_development_is_state_wide(self):
        assert instrument_for("fences.pdf", "exempt-development") == STATE

    def test_guidance_is_not_instrument_specific(self):
        assert instrument_for("stormwater-drainage-handbook.pdf", "forms") == NOT_INSTRUMENT_SPECIFIC

    def test_unknown_file_does_not_claim_an_instrument(self):
        assert instrument_for("something-new.pdf", "") == NOT_INSTRUMENT_SPECIFIC


class TestSearchResults:
    def test_every_hit_names_its_instrument(self):
        for hit in search_all("residential setback"):
            assert hit["instrument"], hit["file"]

    def test_superseded_hits_carry_a_warning(self):
        hits = [h for h in search_all("residential development") if is_superseded(h["file"])]
        if not hits:
            pytest.skip("query returned no LEP 2000 hits")
        for hit in hits:
            assert "LEP 2000" in hit["superseded"]
            assert "LEP 2012" in hit["superseded"], "must point at the current control"

    def test_current_hits_carry_no_warning(self):
        for hit in search_all("off-street parking"):
            if not is_superseded(hit["file"]):
                assert "superseded" not in hit

    def test_warning_survives_the_full_scan_path(self, monkeypatch):
        """The fallback path builds results separately and must label them too."""
        from lismore_da_mcp import index as idx

        monkeypatch.setattr(idx, "INDEX_PATH", idx.INDEX_PATH.with_name("absent.sqlite3"))
        assert all(h.get("instrument") for h in search_all("heritage conservation"))


class TestDocumentListing:
    def test_listing_names_the_instrument(self):
        assert all(d["instrument"] for d in list_available_documents())

    def test_listing_flags_superseded(self):
        flagged = {d["filename"] for d in list_available_documents() if d.get("superseded")}
        assert flagged == LEP_2000_DOCUMENTS
