"""check_permissibility agrees with the land use tables it reads.

ROADMAP.md item S1. Every other audit here checks that the *data* matches the
source; `tests/test_zone_transcription.py` is the one for these tables and it
passes — all 21 match the LEP exactly. This is the layer above: given a table
that is right, does the tool report what it says?

On 2026-08-09 it does for every one of the 991 rows asked in the table's own
spelling, and for none of 287 asked in the spelling the LEP Dictionary defines.
That split is the finding. The data is not in question and neither is the
handler's logic once a term is found — what fails is resolving 'centre-based
child care facility' to 'Centre-based child care facilities', and the failure is
silent because an unresolved term falls through to the table's catch-all and is
reported as an answer.

The counts are pinned rather than merely bounded. A fix that reduces them fails
this file until `KNOWN_MATCHING_DEFECTS` comes down with it, so the baseline
cannot quietly rot into a tolerance — the same discipline `TestScheduleCurrency`
applies to the fee scale.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_landuse_matching import (  # noqa: E402
    KNOWN_MATCHING_DEFECTS,
    audit,
    counterpart_forms,
    coverage,
    dictionary_terms,
    grade,
    lep_text,
    table_rows,
)

from lismore_da_mcp.data.zones import ZONES  # noqa: E402

CURRENT_ZONES = [z for z in ZONES if "redirect_to" not in ZONES[z]]


@pytest.fixture(scope="module")
def dictionary():
    return dictionary_terms(lep_text())


@pytest.fixture(scope="module")
def findings():
    return audit(CURRENT_ZONES)


class TestTheToolAgreesWithTheTable:
    def test_every_table_spelling_is_answered_correctly(self):
        """The table's own words must always work. There is no interpretation
        here: the string is in the list, the list has a heading, the heading is
        the answer. This has never failed and must not start."""
        failures = audit(CURRENT_ZONES, verbatim_only=True)
        assert failures == [], "\n" + "\n".join(
            f"{f['zone']} {f['asked']!r}: table says {f['expected']}, tool says {f['got']}"
            for f in failures
        )

    def test_defect_count_matches_the_recorded_baseline(self, findings):
        """Exact, not an upper bound.

        Failing on a *decrease* is deliberate. A baseline that only catches
        regressions becomes a tolerance nobody revisits, which is how the fee
        scale sat two years stale behind a caveat that was always present.
        """
        counted = {cls: 0 for cls in KNOWN_MATCHING_DEFECTS}
        for f in findings:
            counted[f["class"]] = counted.get(f["class"], 0) + 1
        assert counted == KNOWN_MATCHING_DEFECTS, (
            f"\nmeasured {counted}, baseline {KNOWN_MATCHING_DEFECTS}.\n"
            "If a fix landed, bring KNOWN_MATCHING_DEFECTS down to the measured "
            "numbers in the same commit. If nothing was fixed, something regressed."
        )

    def test_every_failure_is_a_resolution_miss(self, findings):
        """Pins the *cause*, so a swap cannot hide inside an unchanged count.

        Every known defect is the term never being recognised — the answer comes
        from the catch-all or from nothing. A failure that found some other term
        and reported it is a different bug and should not pass silently.
        """
        other = [f for f in findings if f["match_type"] not in ("catchall", "none")]
        assert other == [], "\n" + "\n".join(
            f"{f['zone']} {f['asked']!r} matched {f['matched_use']!r} via "
            f"{f['match_type']} — a new kind of defect" for f in other
        )


XFAIL_UNTIL_FIXED = pytest.mark.xfail(
    strict=True,
    reason=(
        "ROADMAP.md S1, unfixed on this branch. This branch lands the guard only; "
        "landuse.py is not touched. strict=True means these fail if they start "
        "passing, so the fix cannot land without removing the marker."
    ),
)


class TestTheCasesTheRoadmapNames:
    """Named separately from the counts, because a count can be preserved by a
    swap and these are the four verified by hand in ROADMAP.md S1."""

    @XFAIL_UNTIL_FIXED
    @pytest.mark.parametrize("zone,term,expected", [
        ("E1", "industry", "prohibited"),                        # E1 item 4: Industries
        ("E4", "centre-based child care facility", "prohibited"),
        ("E4", "business premises", "prohibited"),               # E4 item 4: Commercial premises
        ("R2", "home business", "permitted_with_consent"),       # R2 item 3: Home businesses
    ])
    def test_the_singular_gets_the_table_answer(self, zone, term, expected):
        from audit_landuse_matching import ask
        got = ask(zone, term)["permissibility"]
        assert got == expected, (
            f"{zone} + {term!r} -> {got}, but the land use table says {expected}. "
            "This is the S1 defect; see ROADMAP.md."
        )

    @XFAIL_UNTIL_FIXED
    def test_singular_and_plural_do_not_disagree(self):
        """The sharpest form of the bug: the same tool, the same table, opposite
        answers, decided by whether the caller typed a plural."""
        from audit_landuse_matching import ask
        singular = ask("E4", "centre-based child care facility")["permissibility"]
        plural = ask("E4", "centre-based child care facilities")["permissibility"]
        assert singular == plural, (
            f"singular -> {singular}, plural -> {plural}. Which answer a business "
            "hears depends on how it typed the word."
        )


class TestThePairingComesFromTheDocument:
    def test_the_dictionary_is_actually_read(self, dictionary):
        assert len(dictionary) > 300
        for term in ("restaurant or cafe", "centre-based child care facility",
                     "home business", "industry", "rural worker's dwelling"):
            assert term in dictionary, f"{term!r} not read out of the LEP Dictionary"

    def test_counterparts_are_confirmed_not_invented(self, dictionary):
        """The generator over-produces on purpose; the Dictionary is the filter.
        Nothing it returns may be absent from the document."""
        for _, _, term in table_rows(CURRENT_ZONES):
            for form in counterpart_forms(term, dictionary):
                assert form in dictionary, (
                    f"{form!r} was offered as a spelling of {term!r} but the LEP "
                    "Dictionary does not define it — the filter has been bypassed."
                )

    @pytest.mark.parametrize("table_term,expected", [
        ("Centre-based child care facilities", "centre-based child care facility"),
        ("Restaurants or cafes", "restaurant or cafe"),   # both sides of the 'or'
        ("Cemeteries", "cemetery"),                       # -ies
        ("Crematoria", "crematorium"),                    # -a
        ("Jetties", "jetty"),
        ("Rural workers' dwellings", "rural worker's dwelling"),  # the possessive moves
        ("Recreation facilities (indoor)", "recreation facility (indoor)"),
        ("Places of public worship", "place of public worship"),
    ])
    def test_the_hard_pairings(self, table_term, expected, dictionary):
        """The forms a naive singulariser cannot reach. These are why the pairing
        is read off the document instead of computed."""
        assert expected in counterpart_forms(table_term, dictionary)

    def test_unpaired_terms_are_explained(self):
        """A term the pairing cannot reach is named with a reason, or the
        coverage figure above it means nothing."""
        from audit_landuse_matching import UNPAIRED_TABLE_TERMS
        unexplained = [
            t for t in coverage(CURRENT_ZONES)["unpaired"]
            if t not in UNPAIRED_TABLE_TERMS
        ]
        assert unexplained == [], (
            f"no counterpart and no explanation: {unexplained}. Add it to "
            "UNPAIRED_TABLE_TERMS with why, or fix the pairing."
        )

    def test_coverage_has_not_collapsed(self):
        """Guards the failure this audit could have and not notice: the
        Dictionary regex rots, every pairing silently disappears, and the audit
        reports a clean run because it asked nothing."""
        stats = coverage(CURRENT_ZONES)
        assert len(stats["paired"]) >= 100, (
            f"only {len(stats['paired'])} terms paired to a Dictionary spelling. "
            "The audit is passing because it stopped asking."
        )


class TestTheAuditCanFail:
    """A checker that cannot detect a fault manufactures confidence rather than
    providing it — PLAN.md item 0.2, applied to this file."""

    def test_grade_catches_a_wrong_yes(self):
        assert grade("prohibited", {
            "permissibility": "likely_permitted_with_consent", "match_type": "catchall",
        }) == "wrong_yes"

    def test_grade_catches_a_wrong_no(self):
        assert grade("permitted_with_consent", {
            "permissibility": "likely_prohibited", "match_type": "catchall",
        }) == "wrong_no"

    def test_grade_catches_the_wrong_consent_pathway(self):
        assert grade("permitted_without_consent", {
            "permissibility": "permitted_with_consent", "match_type": "exact",
        }) == "wrong_pathway"

    def test_grade_does_not_pass_a_lucky_catchall(self):
        """The shape agrees, the term was never found. Passing this is what let
        one bug produce both a wrong yes and a wrong no depending on the zone."""
        assert grade("permitted_with_consent", {
            "permissibility": "permitted_with_consent", "match_type": "catchall",
        }) == "unfound"

    def test_grade_passes_a_real_agreement(self):
        assert grade("permitted_with_consent", {
            "permissibility": "permitted_with_consent", "match_type": "exact",
        }) is None

    def test_a_broken_matcher_is_detected(self, monkeypatch):
        """The fault has to go in the *matcher*, not the data.

        The obvious injection — move a use from prohibited to permitted — proves
        nothing, because the audit reads its expectations from the same `ZONES`
        dict the tool answers from, so both sides move together and the run stays
        green. What this audit actually watches is the layer between them, so
        that is where the fault belongs.

        Note the fault must also be *asymmetric*. Truncating `canonical_use` does
        not work either: it is applied to both the query and the table entry, so
        they still meet in the middle and the run stays green. Making the matcher
        find nothing is the fault this audit is for — it is what a term the
        resolver cannot pair already does.
        """
        import lismore_da_mcp.landuse as landuse

        monkeypatch.setattr(landuse, "match_land_use", lambda term, uses, strength: None)
        findings = audit(["E4"], verbatim_only=True)
        assert findings, (
            "the matcher was replaced with one that finds nothing and every "
            "verbatim question still passed — the audit is not exercising the "
            "layer it claims to."
        )
