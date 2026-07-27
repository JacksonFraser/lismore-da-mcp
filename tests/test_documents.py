"""Document discovery, scoring and section extraction.

Guards the coverage fix in commit 7f6cbc7: exempt-development/ and the .txt LEP
extracts must stay reachable, and .txt must keep being addressed by line while
PDFs are addressed by page.
"""

import pytest

from lismore_da_mcp.server import (
    DOC_CATEGORIES,
    LISTABLE_SUFFIXES,
    SEARCHABLE_SUFFIXES,
    _score_lines,
    extract_document_section,
    extract_text_section,
    find_document,
    list_available_documents,
    search_document,
    searchable_documents,
)


class TestScoring:
    def test_scores_by_distinct_token_count(self):
        lines = ["flood planning level", "flood", "nothing relevant here"]
        hits = _score_lines(lines, ["flood", "planning", "level"], "flood planning level")
        by_index = {i: score for i, score, _, _ in hits}
        assert by_index[0] > by_index[1]

    def test_exact_phrase_gets_a_bonus_but_partials_still_match(self):
        lines = ["food and drink premises", "premises"]
        hits = _score_lines(lines, ["food", "drink", "premises"], "food and drink premises")
        assert len(hits) == 2, "partial match should still be returned"

    def test_non_matching_lines_are_dropped(self):
        hits = _score_lines(["nothing here"], ["flood"], "flood")
        assert hits == []

    def test_context_window_included(self):
        lines = [f"line {i}" for i in range(10)]
        hits = _score_lines(lines, ["5"], "5")
        assert "line 4" in hits[0][3] and "line 6" in hits[0][3]


class TestDiscovery:
    def test_all_categories_present_on_disk(self, docs_dir):
        missing = [c for c in DOC_CATEGORIES if not (docs_dir / c).exists()]
        assert missing == [], f"configured categories with no directory: {missing}"

    def test_exempt_development_is_searchable(self):
        names = [p.name for p in searchable_documents()]
        assert any("fences" in n for n in names), "exempt-development fact sheets unreachable"

    def test_text_extracts_are_searchable(self):
        suffixes = {p.suffix.lower() for p in searchable_documents()}
        assert ".txt" in suffixes, "LEP text extracts unreachable"

    def test_chapter_filter_narrows_results(self):
        filtered = searchable_documents("chapter-7")
        assert filtered and all("chapter-7" in p.name for p in filtered)

    def test_listing_covers_every_category(self):
        categories = {d["category"] for d in list_available_documents()}
        assert categories == set(DOC_CATEGORIES)

    def test_listing_marks_how_each_file_is_addressed(self):
        for doc in list_available_documents():
            expected = "line number" if doc["filename"].endswith(".txt") else "page number"
            assert doc["addressed_by"] == expected

    def test_searchable_is_subset_of_listable(self):
        assert SEARCHABLE_SUFFIXES <= LISTABLE_SUFFIXES


class TestFindDocument:
    def test_exact_filename_wins_over_fragment(self):
        found = find_document("chapter-1-residential-development.pdf")
        assert found is not None
        assert found.name == "chapter-1-residential-development.pdf"

    def test_fragment_resolves(self):
        assert find_document("off-street-carparking") is not None

    def test_unknown_returns_none(self):
        assert find_document("no-such-document-anywhere") is None

    def test_resolves_outside_dcp(self):
        """read_dcp_section used to look only in dcp/, so a hit in lep/ or
        exempt-development/ could not be opened at all."""
        assert find_document("lep-2012-nsw-full.txt") is not None
        assert find_document("fences.pdf") is not None


class TestSectionExtraction:
    def test_text_addressed_by_line(self, docs_dir):
        out = extract_text_section(docs_dir / "lep" / "lep-2012-nsw-full.txt", 1, 3)
        assert "lines 1-3" in out

    def test_text_line_range_is_inclusive(self, docs_dir):
        path = docs_dir / "lep" / "lep-2012-nsw-full.txt"
        body = extract_text_section(path, 5, 7).split("\n", 1)[1]
        assert len(body.split("\n")) == 3

    def test_out_of_range_start_does_not_raise(self, docs_dir):
        out = extract_text_section(docs_dir / "lep" / "lep-2012-nsw-full.txt", 10**9, None)
        assert isinstance(out, str)

    def test_dispatch_by_suffix(self, docs_dir):
        pdf = extract_document_section(docs_dir / "dcp" / "chapter-7-off-street-carparking.pdf", 1, 1)
        assert "--- Page 1 ---" in pdf

    @pytest.mark.xfail(strict=True, reason="10k truncation is silent; IMPROVEMENT_PLAN T9")
    def test_truncation_is_signalled(self, docs_dir):
        out = extract_text_section(docs_dir / "lep" / "lep-2012-nsw-full.txt", 1, 100_000)
        assert len(out) >= 10_000
        assert "truncat" in out.lower()


class TestSearchResults:
    def test_pdf_hit_reports_page(self, docs_dir):
        hits = search_document(docs_dir / "dcp" / "chapter-8-flood-prone-lands.pdf", "flood")
        assert hits and "page" in hits[0] and hits[0]["location"].startswith("page ")

    def test_text_hit_reports_line(self, docs_dir):
        hits = search_document(docs_dir / "lep" / "lep-2012-nsw-full.txt", "subdivision")
        assert hits and "line" in hits[0] and hits[0]["location"].startswith("line ")

    def test_reported_line_can_be_read_back(self, docs_dir):
        """The location a search returns must be one read_dcp_section accepts."""
        path = docs_dir / "lep" / "lep-2012-nsw-full.txt"
        hit = search_document(path, "minimum subdivision lot size")[0]
        section = extract_document_section(path, hit["line"], hit["line"])
        assert section.strip()
