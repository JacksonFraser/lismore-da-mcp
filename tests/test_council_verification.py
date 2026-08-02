"""The council-verification harness, minus the network.

PLAN.md item 0.4. `verify_against_council.py` needs a browser and the live
council site, so it cannot run in CI. What *can* be tested is the part that
decides whether a published document is one we already hold — and that part had
a real bug: an underscore is a word character, so `part_b_chapter_1` failed a
`\\b` lookahead, defaulted to Part A, and matched Part B chapter 1 to the Part A
chapter 1 file. A matcher that silently mis-identifies documents turns the
report into confident noise.

Also pinned here: every manifest entry points at a file that actually exists.
The manifest is the only record of where a document came from, so an entry that
names a file the repo does not have means the verifier silently skips it.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from council_sources import DOCUMENTS, KNOWN_NOT_CARRIED  # noqa: E402
from verify_against_council import (  # noqa: E402
    FIGURE_CHECKS,
    already_held,
    chapter_identity,
    normalise,
    similar,
)

DOCS = ROOT / "documents"


class TestChapterIdentity:
    @pytest.mark.parametrize("name,expected", [
        # Council's two naming conventions for the same document.
        ("part_b_chapter_1_lismore_urban_area_lep_2000.pdf", ("b", "1", "2000")),
        ("part-b-chapter-1-lismore-urban-area-lep2000.pdf", ("b", "1", "2000")),
        ("part_a_chapter_1_residential_development_lep_2000.pdf", ("a", "1", "2000")),
        ("chapter-1-residential-lep2000.pdf", ("a", "1", "2000")),
        ("new-part_b_chapter_10_north_lismore_plateau_lep_2012.pdf", ("b", "10", "2012")),
        ("chapter-5a-urban-residential-subdivision.pdf", ("a", "5a", "2012")),
        ("new-part-a-chapter-7-off-street-carparking-with-amd-34.pdf", ("a", "7", "2012")),
    ])
    def test_identity(self, name, expected):
        assert chapter_identity(name) == expected

    def test_underscore_does_not_swallow_the_part(self):
        """The regression. `\\b` after 'b' fails when the next character is '_',
        because underscore is a word character."""
        assert chapter_identity("part_b_chapter_1_x.pdf")[0] == "b"
        assert chapter_identity("part_a_chapter_1_x.pdf")[0] == "a"

    def test_part_b_never_matches_part_a(self):
        assert chapter_identity("part_b_chapter_1_x_lep_2000.pdf") != \
               chapter_identity("part_a_chapter_1_x_lep_2000.pdf")

    def test_lep_edition_separates_otherwise_identical_chapters(self):
        assert chapter_identity("part_a_chapter_7_carparking_lep_2000.pdf") != \
               chapter_identity("new-part-a-chapter-7-carparking.pdf")

    def test_a_non_chapter_document_has_no_identity(self):
        assert chapter_identity("2026-2027-fees-and-charges.pdf") is None
        assert chapter_identity("land-use-matrix-august-2023_1.pdf") is None


@pytest.fixture(scope="module")
def committed():
    return sorted(p for p in DOCS.rglob("*.pdf") if p.is_file())


class TestAlreadyHeld:

    @pytest.mark.parametrize("published,expected", [
        ("part_b_chapter_1_lismore_urban_area_lep_2000.pdf",
         "part-b-chapter-1-lismore-urban-area-lep2000.pdf"),
        ("part_a_chapter_1_residential_development_lep_2000.pdf",
         "chapter-1-residential-lep2000.pdf"),
        ("new-part_a_chapter_9_-_signage.pdf", "chapter-9-signage.pdf"),
        ("new-part_a_chapter_8_flood_prone_lands_lep_2012.pdf",
         "chapter-8-flood-prone-lands.pdf"),
    ])
    def test_recognises_a_document_held_under_another_name(self, published, expected, committed):
        held = already_held(published, committed)
        assert held is not None, f"{published} should have matched {expected}"
        assert held.name == expected

    @pytest.mark.parametrize("published", [
        "new-part_a_chapter_16_rural_landsharing_communities_lep_2012.pdf",
        "new-part_b_chapter_10_north_lismore_plateau_urban_release_area_lep_2012.pdf",
        "part-b-chapter-11-urban-release-area-at-1055-bruxner-highway.pdf",
    ])
    def test_a_document_we_do_not_have_is_reported(self, published, committed):
        """These four are genuinely absent — chapters CLAUDE.md's own tables name
        but the repo does not carry. If one is added, delete its row here."""
        assert already_held(published, committed) is None

    def test_similarity_is_not_so_loose_that_anything_matches(self, committed):
        assert already_held("some-unrelated-council-newsletter.pdf", committed) is None


class TestTheManifest:
    def test_every_entry_names_a_file_that_exists(self):
        missing = [f"documents/{c}/{f}" for _u, c, f in DOCUMENTS
                   if not (DOCS / c / f).exists()]
        assert not missing, (
            "The manifest is the only record of where a document came from. An entry "
            f"naming a file the repo does not have is silently skipped: {missing}"
        )

    def test_no_duplicate_local_filenames(self):
        names = [f for _u, _c, f in DOCUMENTS]
        assert len(names) == len(set(names))

    def test_every_url_is_absolute_and_council(self):
        for url, _c, _f in DOCUMENTS:
            assert url.startswith("https://www.lismore.nsw.gov.au/"), url

    def test_figure_checks_point_at_manifest_documents(self):
        """A figure check on a document with no source URL never runs."""
        known = {f for _u, _c, f in DOCUMENTS}
        assert set(FIGURE_CHECKS) <= known, (
            f"not in the manifest: {set(FIGURE_CHECKS) - known}"
        )

    def test_documents_decided_against_carry_a_reason(self):
        for name, why in KNOWN_NOT_CARRIED.items():
            assert len(why) > 40, f"{name}: 'decided against' needs a reason, not a note"


class TestFigureExtraction:
    """The checks derive figures from data/ rather than restating them, so this
    guards that they actually produce something to check."""

    @pytest.mark.parametrize("filename", sorted(FIGURE_CHECKS))
    def test_produces_figures(self, filename):
        _label, produce = FIGURE_CHECKS[filename]
        figures = produce()
        assert figures, f"{filename} check produces nothing — it would pass vacuously"
        for what, value in figures:
            assert what and value

    def test_normalise_matches_the_typography_the_pdfs_use(self):
        assert normalise("15 per 100m² GFA") == normalise("15 PER  100m2   gfa")

    def test_similar_is_a_ratio(self):
        assert similar("chapter-9-signage.pdf", "chapter-9-signage.pdf") == 1.0
        assert similar("chapter-9-signage.pdf", "totally-different.pdf") < 0.65
