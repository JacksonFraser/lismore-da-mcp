"""Planning instrument labelling.

The DCP has parallel chapters for LEP 2012 land and LEP 2000 land, sitting side
by side in documents/dcp/. Before this, search returned hits from either with
nothing to distinguish them, so a superseded residential setback could be quoted
as a current control. That is the one remaining way this server could give
actively wrong planning advice, hence the coverage.
"""

import re
import sys
from pathlib import Path

import pytest

from lismore_da_mcp.data.instruments import (
    CURRENT_FEE_SCHEDULE,
    FEE_SCHEDULE_COLUMNS_NOTE,
    GENERAL_DOCUMENTS,
    LEP_2000,
    LEP_2000_DOCUMENTS,
    LEP_2000_WITHOUT_COUNTERPART,
    LEP_2012,
    NO_COUNTERPART_NOTE,
    NOT_INSTRUMENT_SPECIFIC,
    STATE,
    SUPERSEDED_FEE_SCHEDULES,
    SUPERSEDED_NOTE,
    instrument_for,
    is_superseded,
    superseded_banner,
    superseded_note_for,
)
from lismore_da_mcp.search import (
    _rank,
    list_available_documents,
    search_all,
    searchable_documents,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


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
            if name in LEP_2000_WITHOUT_COUNTERPART:
                # Declared exception: Council never reissued this chapter under
                # LEP 2012, so there is nothing to point the reader at. It gets
                # NO_COUNTERPART_NOTE instead, which says so. The exception must
                # be declared rather than inferred — a chapter that silently has
                # no counterpart is the bug this test exists to catch.
                continue
            assert chapter_id(name) in current, f"{name} has no current counterpart"

    def test_chapters_without_a_counterpart_say_so(self):
        """The standard note sends the reader to "the LEP 2012 chapter of the
        same number". For these there is no such chapter, so that wording would
        be an instruction to go and find something that does not exist."""
        for name in LEP_2000_WITHOUT_COUNTERPART:
            assert name in LEP_2000_DOCUMENTS, f"{name} is not marked superseded at all"
            note = superseded_note_for(name)
            assert note is NO_COUNTERPART_NOTE
            assert "of the same number" not in note

    def test_ordinary_superseded_chapters_keep_the_standard_note(self):
        assert superseded_note_for("chapter-12-heritage-lep2000.pdf") is SUPERSEDED_NOTE


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
        assert flagged == LEP_2000_DOCUMENTS | set(SUPERSEDED_FEE_SCHEDULES)


class TestFeeSchedules:
    """Old fee schedules match every fee query the current one does, and a
    search for "footpath dining fee" once answered from the 2025-26 schedule
    first with nothing marking it as old."""

    def test_registry_names_files_on_disk(self):
        on_disk = {p.name for p in searchable_documents()}
        assert CURRENT_FEE_SCHEDULE in on_disk
        missing = sorted(set(SUPERSEDED_FEE_SCHEDULES) - on_disk)
        assert missing == [], f"registry names files not present: {missing}"

    def test_every_dated_fee_schedule_is_current_or_superseded(self):
        """The July check. Adding next year's schedule fails here until this
        year's is registered as superseded and CURRENT_FEE_SCHEDULE moves on —
        otherwise two schedules answer every fee query as equals."""
        dated = {
            p.name for p in searchable_documents()
            if p.parent.name == "fees" and re.search(r"\d{4}-\d{2}\.pdf$", p.name)
        }
        unregistered = sorted(dated - {CURRENT_FEE_SCHEDULE} - set(SUPERSEDED_FEE_SCHEDULES))
        assert unregistered == [], f"fee schedules with no status: {unregistered}"

    def test_current_schedule_is_the_one_the_figures_cite(self):
        from audit_approvals import SCHEDULE

        from lismore_da_mcp.data import fees

        assert SCHEDULE.name == CURRENT_FEE_SCHEDULE
        assert CURRENT_FEE_SCHEDULE in fees.__doc__

    def test_the_current_schedule_is_not_superseded(self):
        assert not is_superseded(CURRENT_FEE_SCHEDULE)

    @pytest.mark.parametrize("name", sorted(SUPERSEDED_FEE_SCHEDULES))
    def test_note_names_the_year_and_the_replacement(self, name):
        note = superseded_note_for(name)
        assert SUPERSEDED_FEE_SCHEDULES[name] in note
        assert CURRENT_FEE_SCHEDULE in note
        assert "LEP" not in note, "a fee schedule is not superseded by an LEP"

    def test_banner_is_worded_for_the_kind_of_document(self):
        assert superseded_banner("fees-and-charges-2025-26.pdf").startswith(
            "⚠️ SUPERSEDED FEE SCHEDULE")
        assert superseded_banner("chapter-12-heritage-lep2000.pdf").startswith(
            "⚠️ SUPERSEDED FOR MOST LAND")

    def test_rank_puts_old_schedules_after_every_current_hit(self):
        hits = [
            {"file": "fees-and-charges-2025-26.pdf", "score": 9},
            {"file": CURRENT_FEE_SCHEDULE, "score": 2},
            {"file": "chapter-7-off-street-carparking.pdf", "score": 2},
            {"file": "chapter-1-residential-lep2000.pdf", "score": 5},
        ]
        assert [h["file"] for h in _rank(hits)] == [
            "chapter-1-residential-lep2000.pdf",  # LEP 2000 is labelled, not demoted
            CURRENT_FEE_SCHEDULE,  # ties keep their order
            "chapter-7-off-street-carparking.pdf",
            "fees-and-charges-2025-26.pdf",
        ]

    def test_a_fee_query_answers_from_the_current_schedule(self):
        hits = search_all("footpath dining fee")
        assert hits[0]["file"] == CURRENT_FEE_SCHEDULE
        seen_old = False
        for hit in hits:
            if hit["file"] in SUPERSEDED_FEE_SCHEDULES:
                seen_old = True
                assert CURRENT_FEE_SCHEDULE in hit["superseded"]
            else:
                assert not seen_old, "a current hit ranked below a superseded schedule"

    def test_current_schedule_hits_say_how_to_read_the_columns(self):
        hits = [h for h in search_all("footpath dining fee") if h["file"] == CURRENT_FEE_SCHEDULE]
        assert hits and all(h["reading_the_columns"] == FEE_SCHEDULE_COLUMNS_NOTE for h in hits)

    def test_the_column_note_matches_the_document(self):
        """FEE_SCHEDULE_COLUMNS_NOTE names two years and an order. Both change
        when next July's schedule replaces this one, and a note that names the
        wrong year sends a business to last year's fee."""
        import fitz

        years = re.findall(r"(\d{4})-(\d{2})", FEE_SCHEDULE_COLUMNS_NOTE)
        expected = [f"{a[2:]}/{b}" for a, b in years]  # 2025-26 -> 25/26
        assert len(expected) == 2

        with fitz.open(ROOT / "documents" / "fees" / CURRENT_FEE_SCHEDULE) as doc:
            headed = 0
            for page in doc:
                # The year headers sit in a band at the top of each page (y≈31);
                # body text below it has its own n/n figures ("50/60").
                headers = sorted(
                    (w[0], w[4]) for w in page.get_text("words")
                    if w[1] < 60 and re.fullmatch(r"\d{2}/\d{2}", w[4])
                )
                if headers:
                    headed += 1
                    assert [h for _, h in headers] == expected, f"page {page.number + 1}"
        assert headed, "no year headers found — has the schedule's layout changed?"
