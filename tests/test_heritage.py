"""Heritage is stated the way the source states it.

ROADMAP.md S4. Nine places asserted *"a Heritage Impact Statement is required
(DCP Chapter 12)"*. Chapter 12 requires no document — it mentions a heritage
impact statement twice, both in its definitions — and the provision that does,
LEP cl 5.10(5), says the consent authority **may** require a **heritage
management document**, of which a HIS is one of three forms.

The interesting test here is `TestTheClaimStaysCorrected`, which greps the whole
package. Nothing pinned this language before, which is exactly why one wrong
sentence propagated to nine files: each copy looked like the others and none of
them looked like the LEP.
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_heritage import (  # noqa: E402
    chapter_12_findings,
    chapter_12_text,
    lep_text,
    modality_findings,
    normalise,
    quote_findings,
)

from lismore_da_mcp.data.heritage import (  # noqa: E402
    CONSERVATION_INCENTIVES,
    HERITAGE_ASSESSMENT,
)

SRC = ROOT / "src" / "lismore_da_mcp"
PYTHON_FILES = sorted(SRC.rglob("*.py"))


@pytest.fixture(scope="module")
def lep():
    return lep_text()


@pytest.fixture(scope="module")
def chapter():
    return chapter_12_text()


class TestTheProvisionsAreQuoted:
    def test_every_quote_is_in_the_lep(self, lep):
        assert quote_findings(lep) == []

    def test_the_clause_still_says_may(self, lep):
        """The whole item is one word. If cl 5.10(5) ever becomes mandatory,
        every hedge this repo now carries is wrong in the other direction."""
        assert modality_findings(lep) == []

    def test_the_vicinity_paragraph_is_carried(self):
        """cl 5.10(5)(c) reaches land near an item, not only the item. A site
        `lookup_site_constraints` reports as unlisted can still be caught."""
        assert "within the vicinity of" in HERITAGE_ASSESSMENT["quote"]

    def test_the_conservation_incentive_is_carried(self):
        """cl 5.10(10) is how a café opens in an old bank — a use the land use
        table prohibits, approved because it funds the building's conservation."""
        assert "otherwise not be allowed by this Plan" in CONSERVATION_INCENTIVES["quote"]


class TestChapter12StillRequiresNothing:
    """The absence check. A presence check cannot verify a negative, and this
    file's whole correction rests on one — the same reason
    `audit_standards.py` asserts what Chapter 1 does *not* contain."""

    def test_the_chapter_contains_no_requirement(self, chapter):
        assert chapter_12_findings(chapter) == []

    def test_both_mentions_are_definitions(self, chapter):
        """If a third mention appears, the chapter was reissued and the
        correction needs re-reading before it is trusted."""
        assert len(re.findall(r"heritage impact statement", chapter, re.I)) == 2

    def test_the_chapter_defers_to_clause_5_10(self, chapter):
        assert "apply whenever development consent is required under clause 5.10" in chapter


class TestTheClaimStaysCorrected:
    """A repo-wide grep, because the failure mode was propagation.

    One sentence copied into nine files, none of which had a test. Pinning the
    phrasing at each call site would need nine tests that drift; pinning its
    *absence* everywhere needs one that cannot.
    """

    # "is required" / "must be prepared" attached to a heritage document. The
    # LEP's own quoted text is exempt — cl 5.10(4) genuinely says "must", about
    # Council's duty to consider rather than about producing a document.
    FORBIDDEN = re.compile(
        r"(?:heritage impact statement|heritage management document)[^.]{0,40}"
        r"\b(?:is|are) required\b"
        r"|\ba heritage impact statement is required\b",
        re.I,
    )

    @pytest.mark.parametrize("path", PYTHON_FILES, ids=lambda p: p.name)
    def test_no_module_asserts_a_heritage_document_is_required(self, path):
        source = path.read_text(encoding="utf-8")
        if path.name == "heritage.py":
            return  # it quotes the claim in order to correct it
        offenders = [m.group(0) for m in self.FORBIDDEN.finditer(source)]
        assert offenders == [], (
            f"{path.relative_to(ROOT)} states a heritage document as required: {offenders}. "
            "LEP cl 5.10(5) says the consent authority *may* require a heritage management "
            "document. See data/heritage.py."
        )

    @pytest.mark.parametrize("path", PYTHON_FILES, ids=lambda p: p.name)
    def test_no_module_credits_chapter_12_with_requiring_one(self, path):
        """The citation was wrong even where the modality was hedged —
        `signage.py` and `addresses.py` both said 'may'/'likely' and both
        pointed at a chapter that requires nothing."""
        source = path.read_text(encoding="utf-8")
        if path.name == "heritage.py":
            return
        pattern = re.compile(
            r"heritage impact statement[^.]{0,60}(?:required|under)[^.]{0,20}"
            r"(?:DCP )?Chapter 12", re.I)
        offenders = [m.group(0) for m in pattern.finditer(source)]
        assert offenders == [], (
            f"{path.relative_to(ROOT)} credits DCP Chapter 12 with requiring a heritage "
            f"document: {offenders}. The power is LEP cl 5.10(5)."
        )


class TestTheToolsSayIt:
    def test_a_prohibited_use_is_offered_the_heritage_pathway(self, call):
        """cl 5.10(10) sits beside the SEPP caveat: both are reasons a
        prohibited land use table result is not a settled refusal."""
        result = call("check_permissibility",
                      {"land_use": "industry", "zone_code": "R2"})
        assert "5.10(10)" in result["if_the_building_is_heritage_listed"]

    def test_a_permitted_use_is_not_lectured_about_heritage(self, call):
        result = call("check_permissibility",
                      {"land_use": "home business", "zone_code": "R2"})
        assert "if_the_building_is_heritage_listed" not in result

    def test_readiness_says_may_not_must(self):
        """Called directly rather than through the tool, because the canned
        address fixtures are not heritage-affected and this is about what is
        said when they are."""
        from lismore_da_mcp.readiness import Proposal, _site

        findings = _site(Proposal(proposed_use="cafe", zone_code="E2", heritage=True))
        heritage = [f for f in findings if "heritage" in f["finding"].lower()]
        assert heritage, "no heritage finding for a heritage-affected site"
        for finding in heritage:
            assert "*may* require" in finding["why"]
            assert "5.10(5)" in finding["source"] or "5.10" in finding["why"]
            assert "is required" not in finding["finding"]

    def test_an_unestablished_heritage_status_mentions_the_vicinity_rule(self):
        """cl 5.10(5)(c) — a site that is not itself listed can still be
        assessed, which is the part an applicant will not think to ask about."""
        from lismore_da_mcp.readiness import Proposal, _site

        findings = _site(Proposal(proposed_use="cafe", zone_code="E2", heritage=None))
        heritage = [f for f in findings if "heritage" in f["finding"].lower()]
        assert any("vicinity" in f["why"] for f in heritage)

    def test_the_see_draft_does_not_claim_a_document_is_attached(self, call):
        """It used to write 'A Heritage Impact Statement accompanies this
        application' into text going to Council over the applicant's name."""
        result = call("generate_see_draft", {
            "property_address": "12 Keen Street, Lismore NSW 2480",
            "zone_code": "E2", "proposed_use": "restaurant or cafe",
            "development_type": "change_of_use", "is_heritage": True,
        })
        draft = result if isinstance(result, str) else str(result)
        assert "Statement accompanies" not in draft


class TestTheAuditCanFail:
    """PLAN.md item 0.2 — a checker that cannot detect a fault manufactures
    confidence rather than providing it."""

    def test_a_drifted_quote_is_caught(self, lep):
        import audit_heritage

        broken = dict(audit_heritage.QUOTED)
        broken["cl 5.10(5) heritage assessment"] = {
            "clause": "cl 5.10(5)",
            "quote": "The consent authority must require a heritage impact statement.",
        }
        original = audit_heritage.QUOTED
        try:
            audit_heritage.QUOTED = broken
            assert quote_findings(lep), "a quote that is not in the LEP passed the check"
        finally:
            audit_heritage.QUOTED = original

    def test_a_requirement_appearing_in_chapter_12_is_caught(self):
        fabricated = normalise(
            "12.5 Documentation. A Heritage Impact Statement is required for all "
            "development on a heritage item."
        )
        assert chapter_12_findings(fabricated), (
            "Chapter 12 was given a heritage document requirement and the absence "
            "check did not notice"
        )
