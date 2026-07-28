"""FTS index behaviour.

The index exists purely for speed — a full scan re-extracts 902 PDF pages per
query, measured at 7.4s locally and 16-26s on the hosted free tier. So the thing
worth testing is that it does not change answers, and that where it *does*
differ the difference is known and deliberate.
"""

import sqlite3

import pytest

from lismore_da_mcp import index as IDX
from lismore_da_mcp import search as S


@pytest.fixture(scope="module")
def built_index(tmp_path_factory):
    """A real index over a couple of documents, built once."""
    paths = [p for p in S.searchable_documents() if p.name in {
        "chapter-7-off-street-carparking.pdf",
        "clause-5.21-flood-planning.txt",
    }]
    if len(paths) < 2:
        pytest.skip("expected documents not present")
    db = tmp_path_factory.mktemp("idx") / "index.sqlite3"
    IDX.build_index(paths, index_path=db, force=True)
    return db, paths


class TestBuild:
    def test_reports_what_it_indexed(self, built_index):
        db, paths = built_index
        assert db.exists()
        status = IDX.index_status(db)
        assert status["present"] and status["segments"] > 0

    def test_rebuild_is_skipped_when_corpus_unchanged(self, built_index):
        db, paths = built_index
        assert IDX.build_index(paths, index_path=db)["status"] == "current"

    def test_rebuild_happens_when_corpus_changes(self, built_index, tmp_path):
        db, paths = built_index
        assert IDX.build_index(paths[:1], index_path=db)["status"] == "built"
        IDX.build_index(paths, index_path=db, force=True)  # restore

    def test_fingerprint_ignores_mtime(self, built_index):
        """A git checkout rewrites mtimes; rebuilding on that would mean rebuilding
        on every deploy."""
        db, paths = built_index
        before = IDX.fingerprint(paths)
        paths[0].touch()
        assert IDX.fingerprint(paths) == before

    def test_corrupt_index_is_rebuilt_not_raised(self, tmp_path, built_index):
        _, paths = built_index
        bad = tmp_path / "corrupt.sqlite3"
        bad.write_text("this is not a database")
        assert IDX.build_index(paths, index_path=bad)["status"] == "built"


class TestLookup:
    def test_returns_none_without_an_index(self, tmp_path):
        assert IDX.lookup(["flood"], index_path=tmp_path / "absent.sqlite3") is None

    def test_returns_none_for_empty_tokens(self, built_index):
        db, _ = built_index
        assert IDX.lookup([], index_path=db) is None

    def test_finds_matching_segments(self, built_index):
        db, _ = built_index
        assert IDX.lookup(["flood"], index_path=db)

    def test_chapter_filter_narrows(self, built_index):
        db, _ = built_index
        rows = IDX.lookup(["parking"], chapter="carparking", index_path=db)
        assert rows and all("carparking" in r[0] for r in rows)

    def test_corrupt_index_returns_none_rather_than_raising(self, tmp_path):
        bad = tmp_path / "corrupt.sqlite3"
        bad.write_text("not a database")
        assert IDX.lookup(["flood"], index_path=bad) is None


class TestMatchExpression:
    def test_uses_prefix_terms(self):
        """Prefix, so 'house' still reaches 'houses' — the scorer this feeds does
        substring matching, and plain token matching would silently drop hits."""
        assert IDX._match_expression(["house"]) == '"house"*'

    def test_ors_multiple_tokens(self):
        assert IDX._match_expression(["a", "b"]) == '"a"* OR "b"*'

    def test_quotes_defuse_fts5_operators(self):
        """A query must not be able to smuggle in FTS5 syntax."""
        expr = IDX._match_expression(['a" OR b'])
        with sqlite3.connect(":memory:") as conn:
            conn.execute("CREATE VIRTUAL TABLE t USING fts5(body)")
            conn.execute("INSERT INTO t VALUES ('hello')")
            conn.execute("SELECT * FROM t WHERE t MATCH ?", (expr,)).fetchall()


class TestFallback:
    def test_search_falls_back_to_a_full_scan(self, monkeypatch):
        """A missing index must degrade to slow, not to broken."""
        monkeypatch.setattr(IDX, "INDEX_PATH", IDX.INDEX_PATH.with_name("absent.sqlite3"))
        assert S.search_all("flood planning level")

    def test_no_tokens_yields_no_results(self):
        assert S.search_all("") == []


class TestParityWithFullScan:
    """The equivalence claim, enforced rather than asserted once.

    Each case runs the full scan it replaces, so this is the slowest part of the
    suite (~7s per query). Kept to a few representative queries covering both
    document kinds and the per-document cap; parity was verified over 25 queries
    by hand when the index landed.
    """

    @pytest.fixture
    def without_index(self, monkeypatch):
        def _use(enabled):
            target = IDX.INDEX_PATH if enabled else IDX.INDEX_PATH.with_name("absent.sqlite3")
            monkeypatch.setattr(IDX, "INDEX_PATH", target)
        return _use

    @pytest.mark.parametrize("query", [
        "boarding house",            # exercises prefix growth: 'house' -> 'houses'
        "acid sulfate soils",        # one document would otherwise fill every slot
        "flood planning level",      # spans PDFs and the .txt LEP extract
    ])
    def test_indexed_matches_full_scan(self, query, monkeypatch):
        real = IDX.INDEX_PATH
        monkeypatch.setattr(IDX, "INDEX_PATH", real.with_name("absent.sqlite3"))
        scan = S.search_all(query)
        monkeypatch.setattr(IDX, "INDEX_PATH", real)
        indexed = S.search_all(query)

        def shape(rows):
            return [(r["file"], r.get("page"), r.get("line"), r["context"]) for r in rows]

        assert shape(indexed) == shape(scan)

    def test_per_document_cap_is_preserved(self):
        """Without the cap the LEP text takes 9 of 10 slots for this query."""
        from collections import Counter
        counts = Counter(r["file"] for r in S.search_all("acid sulfate soils"))
        assert max(counts.values()) <= 5


class TestKnownDifference:
    """The one place indexed and unindexed search disagree.

    A full scan matches substrings, so 'house' hits the token 'warehouse'. FTS5
    matches tokens, and prefix matching recovers 'houses'/'housing' but not a
    term embedded mid-token. Dropping those is an improvement — a query for
    'house' surfacing 'warehouse' is a false positive — but it is a difference,
    and it is pinned here so it stays deliberate.
    """

    def test_prefix_growth_is_matched(self, built_index):
        db, _ = built_index
        assert IDX.lookup(["flood"], index_path=db), "'flood' should reach 'flooding'"

    def test_embedded_terms_are_not_matched(self, built_index):
        db, _ = built_index
        rows = IDX.lookup(["arking"], index_path=db)  # inside "parking"
        assert not rows, "mid-token matches are intentionally not indexed"
