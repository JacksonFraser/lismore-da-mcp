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

import json
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
# The one file allowed to state the claim, because it quotes it to correct it.
# Matched by path, not by name: ROADMAP.md C1 added two more files called
# heritage.py, and a name match would have exempted the very modules that now
# talk most about heritage documents.
CORRECTION_FILE = SRC / "data" / "heritage.py"


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
        if path == CORRECTION_FILE:
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
        if path == CORRECTION_FILE:
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


class TestOnlyTheStateRegisterGoesToTheHeritageCouncil:
    """SCENARIOS.md run 2, R3. check_referrals mapped every heritage word to the
    Heritage Council, with a Heritage Impact Statement as a required document.
    A locally listed item — which is what LEP Schedule 5 mostly holds — is
    assessed by Council under cl 5.10; the Heritage Council's role is the State
    Register and the cl 5.10(7) and (9) notifications. The claim this file
    exists to correct had survived as a list item, which no grep for a sentence
    could see."""

    def test_a_heritage_item_is_councils_assessment(self, call):
        referrals = call("check_referrals",
                         {"development_characteristics": ["heritage_item"]})["triggered_referrals"]
        assert list(referrals) == ["council_heritage_assessment"]
        assert "internal" in referrals["council_heritage_assessment"]["approval"]

    def test_a_state_listed_item_reaches_both(self, call):
        """Council still assesses an SHR item under cl 5.10; the Heritage
        Council's approval is needed as well."""
        referrals = call("check_referrals",
                         {"development_characteristics": ["state_heritage"]})["triggered_referrals"]
        assert set(referrals) == {"council_heritage_assessment", "heritage_council"}

    def test_no_referral_lists_a_heritage_document_as_required(self):
        from lismore_da_mcp.data.referrals import REFERRAL_REQUIREMENTS

        for key, entry in REFERRAL_REQUIREMENTS.items():
            for document in entry.get("documents", []):
                lowered = document.lower()
                if "heritage" in lowered and ("statement" in lowered or "plan" in lowered
                                              or "document" in lowered):
                    assert "may" in lowered or "ask" in lowered, (
                        f"{key}: {document!r} lists a heritage document without saying "
                        "Council may require it (LEP cl 5.10(5)).")

    def test_a_mapped_heritage_flag_is_not_sent_to_the_heritage_council(self):
        """The layer cannot tell a local item from a State-listed one, so it gets
        Council's assessment and the integrated development question, never the
        Heritage Council referral as though the answer were known."""
        from lismore_da_mcp.readiness import Proposal, referral_triggers

        result = referral_triggers(Proposal(proposed_use="cafe", heritage=True))
        assert "heritage_council" not in result["triggered"]
        assert "council_heritage_assessment" in result["triggered"]
        assert result["integrated_in_question"]

    def test_readiness_collects_both_bodies_for_state_heritage(self):
        """It took the first matching trigger only, which once 'heritage' and
        'state_heritage' reached different bodies would have dropped the one that
        makes the DA integrated."""
        from lismore_da_mcp.readiness import Proposal, referral_triggers

        result = referral_triggers(Proposal(
            proposed_use="cafe", development_characteristics=["state_heritage"]))
        assert {"council_heritage_assessment", "heritage_council"} <= set(result["triggered"])


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


# --- ROADMAP.md C1: DCP Chapter 12 itself ------------------------------------

@pytest.fixture(scope="module")
def body():
    import audit_heritage

    return audit_heritage.chapter_12_body()


@pytest.fixture(scope="module")
def lep_raw():
    import audit_heritage

    return audit_heritage.LEP_PATH.read_text(encoding="utf-8")


class TestChapter12IsTranscribed:
    """Both directions, as `audit_flood.py` does for Chapter 8: every stored
    string is in the chapter, and everything countable in the chapter is
    stored."""

    def test_every_quote_is_in_the_chapter(self, body):
        import audit_heritage

        assert audit_heritage.chapter_quote_findings(body) == []

    def test_every_bullet_in_the_chapter_is_carried(self, body):
        import audit_heritage

        missed, noise = audit_heritage.uncarried_bullets(body)
        assert missed == []
        assert noise == audit_heritage.KNOWN_NON_TEXT_BULLETS

    def test_headings_and_numbered_items_are_carried(self, body):
        import audit_heritage

        assert audit_heritage.structure_findings(body) == []

    def test_every_figure_in_the_chapter_is_carried(self, body):
        """The chapter has five figures with a unit. An invented one fails the
        presence check; an omitted one fails this."""
        import audit_heritage

        assert audit_heritage.uncarried_figures(body) == []

    def test_the_conservation_areas_are_schedule_5s(self, lep_raw):
        import audit_heritage

        assert audit_heritage.conservation_area_findings(lep_raw) == []
        assert len(audit_heritage.schedule_5_part_2_rows(lep_raw)) == 7

    def test_the_refusal_phrases_are_the_chapters(self, body):
        import audit_heritage

        assert audit_heritage.refusal_findings(body) == []


class TestTheChapterAuditCanFail:
    """PLAN.md item 0.2 again: each new check is shown to catch its fault."""

    def test_a_dropped_bullet_is_caught(self, body, monkeypatch):
        import audit_heritage
        from lismore_da_mcp.data import heritage as data

        fences = dict(data.DESIGN_GUIDELINES["fences"])
        fences["not_encouraged"] = fences["not_encouraged"][:1]  # drop the 1.2m/1.8m bullet
        guidelines = dict(data.DESIGN_GUIDELINES, fences=fences)
        monkeypatch.setattr(audit_heritage, "DESIGN_GUIDELINES", guidelines)
        missed, _ = audit_heritage.uncarried_bullets(body)
        assert any("fencing higher than 1.2 metres" in m.lower() for m in missed)
        assert audit_heritage.uncarried_figures(body) == ["1.2 metres", "1.8 metres"]

    def test_a_drifted_chapter_quote_is_caught(self, body, monkeypatch):
        import audit_heritage
        from lismore_da_mcp.data import heritage as data

        signage = dict(data.DESIGN_GUIDELINES["signage"])
        signage["not_encouraged"] = ["Internally illuminated signs are discouraged."]
        monkeypatch.setattr(audit_heritage, "DESIGN_GUIDELINES",
                            dict(data.DESIGN_GUIDELINES, signage=signage))
        assert audit_heritage.chapter_quote_findings(body)

    def test_a_relabelled_conservation_area_is_caught(self, lep_raw, monkeypatch):
        import audit_heritage
        from lismore_da_mcp.data import heritage as data

        nimbin = dict(data.CONSERVATION_AREAS["nimbin"], heritage_map_label="C1")
        monkeypatch.setattr(audit_heritage, "CONSERVATION_AREAS",
                            dict(data.CONSERVATION_AREAS, nimbin=nimbin))
        assert any("nimbin" in p for p in audit_heritage.conservation_area_findings(lep_raw))

    def test_a_missing_conservation_area_is_caught(self, lep_raw, monkeypatch):
        import audit_heritage
        from lismore_da_mcp.data import heritage as data

        fewer = {k: v for k, v in data.CONSERVATION_AREAS.items() if k != "eltham"}
        monkeypatch.setattr(audit_heritage, "CONSERVATION_AREAS", fewer)
        assert any("Eltham" in p for p in audit_heritage.conservation_area_findings(lep_raw))


class TestStatusIsNeverInferred:
    """ROADMAP.md C1's first rule, carried from flood: a conservation area is a
    boundary on a map, and an empty layer result does not clear a site."""

    def test_no_status_returns_every_case(self, call):
        result = call("get_heritage_requirements", {})
        assert result["heritage_status"] == "not established"
        assert set(result["by_status"]) == {
            "heritage_item", "conservation_area", "item_in_conservation_area",
            "vicinity", "none_known"}
        assert "applies" not in result

    def test_the_state_layer_confirms_but_cannot_clear(self, call):
        result = call("get_heritage_requirements", {"heritage_status": "none_known"})
        layer = result["state_layer"]
        assert "does not clear" in layer["rule"]
        assert any("vicinity" in reason for reason in layer["why_it_cannot_clear"])
        assert "not the same as none" in result["applies"]["not_cleared"]

    def test_none_known_still_mentions_the_vicinity_rule(self, call):
        result = call("get_heritage_requirements", {"heritage_status": "none known"})
        assert "5.10(5)(c)" in result["applies"]["not_cleared"]

    def test_the_duty_planner_question_it_points_to_exists(self):
        from lismore_da_mcp.data.readiness import DUTY_PLANNER_QUESTIONS
        from lismore_da_mcp.heritage import STATE_LAYER_CONFIRMS_BUT_CANNOT_CLEAR

        assert "`heritage_status`" in STATE_LAYER_CONFIRMS_BUT_CANNOT_CLEAR["how_to_settle_it"]
        assert "heritage_status" in {q["key"] for q in DUTY_PLANNER_QUESTIONS}

    def test_naming_an_area_is_stating_the_status(self, call):
        result = call("get_heritage_requirements", {"conservation_area": "Girards Hill"})
        assert result["heritage_status"] == "conservation_area"
        assert result["applies"]["conservation_area"]["name"] == "Girards Hill Conservation Area"

    def test_an_item_in_a_named_area_is_both(self, call):
        result = call("get_heritage_requirements",
                      {"heritage_status": "heritage_item", "conservation_area": "St Andrew's"})
        assert result["heritage_status"] == "item_in_conservation_area"

    def test_a_contradiction_is_refused(self, call):
        result = call("get_heritage_requirements",
                      {"heritage_status": "vicinity", "conservation_area": "Nimbin"})
        assert "error" in result

    def test_an_unknown_status_is_refused_with_the_way_forward(self, call):
        result = call("get_heritage_requirements", {"heritage_status": "sort of"})
        assert "error" in result
        assert "Omit heritage_status" in result["if_you_do_not_know"]

    def test_a_heritage_map_label_is_not_taken_for_an_area(self, call):
        """C1–C3 are zone codes in this LEP as well as Heritage Map labels."""
        result = call("get_heritage_requirements", {"conservation_area": "C1"})
        assert "error" in result


class TestTheDcpDoesNotGoBackAlone:
    def test_cl_5_10_comes_back_with_every_answer(self, call):
        for args in ({}, {"heritage_status": "vicinity"}, {"conservation_area": "Eltham"}):
            lep = call("get_heritage_requirements", args)["lep_2012"]
            assert {"cl_5_10_2", "cl_5_10_3", "cl_5_10_4", "cl_5_10_5"} <= set(lep)

    def test_the_documents_are_may_not_must(self, call):
        documents = call("get_heritage_requirements",
                         {"heritage_status": "heritage_item"})["documents"]
        assert documents["what_council_may_ask_for"]["clause"] == "cl 5.10(5)"
        assert "may" in documents["say_instead"].lower()

    @pytest.mark.parametrize("args", [
        {}, {"heritage_status": "heritage_item", "works": ["rear extension"]},
        {"conservation_area": "Nimbin", "works": ["new sign"], "is_change_of_use": True},
    ])
    def test_no_answer_says_a_heritage_document_is_required(self, call, args):
        text = json.dumps(call("get_heritage_requirements", args))
        assert not TestTheClaimStaysCorrected.FORBIDDEN.search(text)


class TestTheConservationIncentiveGoesOnlyToItems:
    """cl 5.10(10) is 'a building that is a heritage item'. A building that is
    only inside a conservation area — even one §12.6 calls contributory — is not
    one, and telling a business otherwise sends it after a pathway it lacks."""

    def test_available_for_an_item(self, call):
        result = call("get_heritage_requirements",
                      {"heritage_status": "heritage_item", "is_change_of_use": True})
        assert result["applies"]["conservation_incentive_cl_5_10_10"].startswith("Available")
        assert "cl_5_10_10" in result["lep_2012"]
        assert "if_the_land_use_table_prohibits_the_use" in result["change_of_use"]

    def test_not_available_in_a_conservation_area_alone(self, call):
        result = call("get_heritage_requirements",
                      {"conservation_area": "Girards Hill", "is_change_of_use": True})
        assert result["applies"]["conservation_incentive_cl_5_10_10"].startswith("Not available")
        assert "cl_5_10_10" not in result["lep_2012"]
        assert "if_the_land_use_table_prohibits_the_use" not in result["change_of_use"]

    def test_a_change_of_use_is_told_cl_5_10_2_lists_works(self, call):
        result = call("get_heritage_requirements",
                      {"heritage_status": "heritage_item", "is_change_of_use": True})
        assert "lists works" in result["change_of_use"]["reading_of_cl_5_10_2"]
        assert "Duty Planner" in result["change_of_use"]["reading_of_cl_5_10_2"]


class TestTheWorksSelectTheGuidelines:
    def test_a_sign_gets_the_signage_guideline_and_the_refusal(self, call):
        result = call("get_heritage_requirements",
                      {"heritage_status": "conservation_area", "works": ["illuminated box sign"]})
        assert "signage" in result["dcp_chapter_12"]["design_guidelines"]
        refusals = [p["quote"] for p in result["worded_as_a_refusal"]["policies"]]
        assert any("Internally illuminated signs" in q for q in refusals)
        assert "get_signage_requirements" in result["signage"]

    def test_design_is_not_a_sign(self):
        from lismore_da_mcp.heritage import classify_works

        matched, unmatched = classify_works(["redesign"])
        assert "signage" not in matched
        assert unmatched == ["redesign"]

    def test_unrecognised_words_are_reported_not_dropped(self, call):
        result = call("get_heritage_requirements",
                      {"heritage_status": "heritage_item", "works": ["repaint", "xyzzy"]})
        assert result["dcp_chapter_12"]["words_not_recognised"]["your_words"] == ["xyzzy"]
        assert list(result["dcp_chapter_12"]["design_guidelines"]) == ["colours"]

    def test_no_works_returns_every_guideline(self, call):
        from lismore_da_mcp.data.heritage import DESIGN_GUIDELINES

        result = call("get_heritage_requirements", {"heritage_status": "heritage_item"})
        assert list(result["dcp_chapter_12"]["design_guidelines"]) == list(DESIGN_GUIDELINES)

    def test_every_guideline_is_reachable_and_every_target_exists(self):
        from lismore_da_mcp.data.heritage import DESIGN_GUIDELINES
        from lismore_da_mcp.heritage import WORKS

        targets = {g for work in WORKS.values() for g in work["guidelines"]}
        assert targets <= set(DESIGN_GUIDELINES)
        assert set(DESIGN_GUIDELINES) <= targets

    def test_a_precincts_refusals_come_with_it(self, call):
        result = call("get_heritage_requirements",
                      {"conservation_area": "Dalley Street", "works": ["front fence"]})
        refusals = " ".join(p["quote"] for p in result["worded_as_a_refusal"]["policies"])
        assert "will not be permitted" in refusals
        assert "should not be approved" in refusals

    def test_nimbin_brings_part_b_chapter_6(self, call):
        area = call("get_heritage_requirements",
                    {"conservation_area": "Nimbin Village"})["applies"]["conservation_area"]
        assert "Chapter 6 (Nimbin Village) of Part B" in area["also_applies"]
        assert any("stall risers" in p for p in area["precinct_policies"])

    @pytest.mark.parametrize("name", [
        "Dalley Street Conservation Area", "St Carthage’s Conservation Area", "st carthages",
        "SPINKS PARK AND CIVIC PRECINCT/HERITAGE CONSERVATION AREA", "Spinks Park",
        "St Andrews", "Eltham", "girards hill",
    ])
    def test_every_way_of_naming_an_area_resolves(self, name):
        from lismore_da_mcp.heritage import resolve_conservation_area

        assert resolve_conservation_area(name)


class TestWhatChapter12DoesAskFor:
    """S4 said the chapter requires no document at all. Reading it whole for C1
    found two things it does ask for — neither a heritage management document,
    so S4's correction stands, but the sentence was one clause too strong."""

    def test_both_are_carried_and_quoted(self, body):
        import audit_heritage
        from lismore_da_mcp.data.heritage import WHAT_CHAPTER_12_DOES_ASK_FOR

        haystack = audit_heritage.fold(body)
        assert len(WHAT_CHAPTER_12_DOES_ASK_FOR) == 2
        for entry in WHAT_CHAPTER_12_DOES_ASK_FOR:
            assert audit_heritage.fold(entry["quote"]) in haystack

    def test_the_tool_reports_them(self, call):
        asks = call("get_heritage_requirements", {})["documents"]["what_chapter_12_asks_for"]
        assert any("Colour scheme details" in a["quote"] for a in asks)
        assert any("justification must be provided" in a["quote"] for a in asks)
