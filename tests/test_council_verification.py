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

import asyncio
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import verify_against_council as verify  # noqa: E402
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
        # Chapter 7 prints curly apostrophes; data/parking.py stores straight ones.
        assert normalise("manager’s/owner’s") == normalise("manager's/owner's")

    def test_similar_is_a_ratio(self):
        assert similar("chapter-9-signage.pdf", "chapter-9-signage.pdf") == 1.0
        assert similar("chapter-9-signage.pdf", "totally-different.pdf") < 0.65


# --------------------------------------------------------------------------
# ROADMAP E2. The scheduled workflow decides what issue to open from the
# --json status (and the exit code carries the same thing), so that contract is
# tested here without a browser: download_all is replaced by one that hands
# back files from disk.
# --------------------------------------------------------------------------

WORKFLOW = ROOT / ".github" / "workflows" / "verify-against-council.yml"


def run_with(monkeypatch, tmp_path, serve, *extra):
    """Run main() with each manifest document 'downloaded' by serve()."""
    async def fake_download_all(targets, into, give_up_after=verify.GIVE_UP_AFTER):
        return {filename: serve(category, filename, into)
                for _url, category, filename in targets}

    monkeypatch.setattr(verify, "download_all", fake_download_all)
    out = tmp_path / "report.json"
    body = tmp_path / "issue.md"
    code = asyncio.run(verify.main(["--no-crawl", "--json", str(out),
                                    "--issue-body", str(body), *extra]))
    return code, json.loads(out.read_text()), body.read_text()


def committed_copy(category, filename, into):
    target = into / filename
    shutil.copy(DOCS / category / filename, target)
    return target, None


def blocked(category, filename, into):
    return None, "download failed (TimeoutError)"


class TestTheExitCodeContract:
    def test_the_codes_are_distinct_and_leave_2_to_argparse(self):
        codes = [verify.EXIT_CLEAN, verify.EXIT_DRIFT, verify.EXIT_UNVERIFIED, verify.EXIT_ERROR]
        assert len(set(codes)) == 4
        assert 2 not in codes

    def test_the_committed_documents_verify_clean(self, monkeypatch, tmp_path):
        """Serving the repo's own copies as 'live' is the no-change case, and it
        runs every real figure check against every real PDF."""
        code, report, body = run_with(monkeypatch, tmp_path, committed_copy)
        assert (code, report["status"]) == (verify.EXIT_CLEAN, "clean")
        assert report["identical"] == [f for _u, _c, f in DOCUMENTS]
        assert set(report["figures"]) == set(FIGURE_CHECKS)
        assert "Every recorded figure" in body

    def test_a_block_is_unverified_not_drift_and_not_clean(self, monkeypatch, tmp_path):
        code, report, body = run_with(monkeypatch, tmp_path, blocked)
        assert (code, report["status"]) == (verify.EXIT_UNVERIFIED, "unverified")
        assert report["drift"] == []
        assert len(report["unreachable"]) == len(DOCUMENTS)
        assert "not drift" in body and "not a clean result" in body

    def test_a_partial_block_is_still_unverified(self, monkeypatch, tmp_path):
        def serve(category, filename, into):
            if category == "dcp":
                return blocked(category, filename, into)
            return committed_copy(category, filename, into)
        code, report, _ = run_with(monkeypatch, tmp_path, serve)
        assert code == verify.EXIT_UNVERIFIED
        assert report["identical"]

    def test_a_missing_figure_is_drift(self, monkeypatch, tmp_path):
        """The fee schedule 'reissued' as last year's: this year's figures are gone."""
        def serve(category, filename, into):
            if filename == "fees-and-charges-2026-27.pdf":
                target = into / filename
                shutil.copy(DOCS / "fees" / "fees-and-charges-2025-26.pdf", target)
                return target, None
            return committed_copy(category, filename, into)
        code, report, body = run_with(monkeypatch, tmp_path, serve)
        assert (code, report["status"]) == (verify.EXIT_DRIFT, "drift")
        assert report["figures"]["fees-and-charges-2026-27.pdf"]["missing"]
        assert "### Findings" in body

    def test_drift_outranks_a_block(self):
        report = {"drift": ["x"], "unreachable": [{"file": "y", "reason": "z"}], "crawl": None}
        assert verify.verdict(report) == ("drift", verify.EXIT_DRIFT)

    def test_a_failed_crawl_is_not_clean(self):
        report = {"drift": [], "unreachable": [], "crawl": {"failed_pages": ["https://x"]}}
        assert verify.verdict(report) == ("unverified", verify.EXIT_UNVERIFIED)

    def test_the_verifier_failing_is_its_own_status(self, monkeypatch, tmp_path):
        """An uncaught exception exits 1 — the drift code. A missing browser
        must not open a drift issue."""
        async def broken(args):
            raise ModuleNotFoundError("No module named 'playwright'")
        monkeypatch.setattr(verify, "run", broken)
        out = tmp_path / "r.json"
        code = asyncio.run(verify.main(["--json", str(out)]))
        assert code == verify.EXIT_ERROR
        assert json.loads(out.read_text())["status"] == "error"

    def test_an_unknown_category_is_a_usage_error(self):
        with pytest.raises(SystemExit) as exit_:
            asyncio.run(verify.main(["--only", "nope"]))
        assert exit_.value.code == 2


class TestABlockPageIsNotADocument:
    """A challenge page saved under a PDF's name would differ from the committed
    copy and contain none of its figures — a block reported as drift."""

    def test_a_real_pdf_is_recognised(self):
        assert verify.looks_like_pdf(DOCS / "fees" / "fees-and-charges-2026-27.pdf")

    def test_a_challenge_page_saved_as_pdf_is_not(self, tmp_path):
        fake = tmp_path / "fees-and-charges-2026-27.pdf"
        fake.write_text("<!DOCTYPE html><title>Just a moment...</title>")
        assert not verify.looks_like_pdf(fake)

    def test_a_missing_file_is_not(self, tmp_path):
        assert not verify.looks_like_pdf(tmp_path / "absent.pdf")


class TestTheScheduledWorkflow:
    """The workflow is YAML nothing executes in CI, so its load-bearing lines are
    pinned: when it runs, what it may do, and that it cannot write documents/."""

    @pytest.fixture
    def workflow(self):
        return WORKFLOW.read_text()

    def test_it_runs_quarterly_and_on_demand(self, workflow):
        cron = re.search(r"cron:\s*['\"]([^'\"]+)['\"]", workflow).group(1).split()
        assert len(cron[3].split(",")) == 4, "not quarterly"
        assert "workflow_dispatch" in workflow

    def test_it_holds_only_the_default_token_with_issues_write(self, workflow):
        assert "issues: write" in workflow
        assert "contents: read" in workflow
        assert "secrets." not in workflow
        for broader in ("contents: write", "pull-requests: write", "write-all"):
            assert broader not in workflow

    def test_it_never_commits_or_pushes(self, workflow):
        assert "git commit" not in workflow and "git push" not in workflow
        assert "persist-credentials: false" in workflow

    def test_it_checks_documents_was_not_touched(self, workflow):
        assert "git status --porcelain -- documents/" in workflow

    def test_it_installs_the_scraping_extra_and_a_browser(self, workflow):
        assert '".[scraping]"' in workflow
        assert "playwright install" in workflow and "chromium" in workflow

    def test_it_decides_from_the_report(self, workflow):
        assert "--json" in workflow and "--issue-body" in workflow
        for status in ("clean", "drift", "unverified", "error"):
            assert status in workflow

    def test_drift_and_a_block_open_different_issues(self, workflow):
        assert "council-drift" in workflow and "council-verify-blocked" in workflow
