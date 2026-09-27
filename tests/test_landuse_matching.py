"""check_permissibility agrees with the land use tables it reads.

ROADMAP.md item S1. Every other audit here checks that the *data* matches the
source; `tests/test_zone_transcription.py` is the one for these tables and it
passes — all 21 match the LEP exactly. This is the layer above: given a table
that is right, does the tool report what it says?

On 2026-08-09 it did for every one of the 991 rows asked in the table's own
spelling, and for none of the 287 asked in the spelling the LEP Dictionary
defines. That split was the finding, and it is what made the fix small: the data
was never in question and neither was the handler's logic once a term was found.
The entire defect was resolving 'centre-based child care facility' to
'Centre-based child care facilities', and it was silent because an unresolved
term fell through to the table's catch-all and was reported as an answer.

S1 landed on 2026-08-20 and the counts are now zero, so this file asserts zero
rather than a baseline. Two things it checks are worth keeping in view if a
future change makes them fail:

- `test_every_table_spelling_is_answered_correctly` has never failed and is the
  unarguable half — the string is in the list, the list has a heading.
- `TestTheAuditCanFail` is the check on the checker. An audit that reports zero
  because it stopped asking looks exactly like one that reports zero because the
  code is right.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_landuse_matching import (  # noqa: E402
    audit,
    counterpart_forms,
    coverage,
    dictionary_terms,
    grade,
    hierarchy_audit,
    lep_text,
    spelling_table_findings,
    table_rows,
    type_of_findings,
    type_of_notes,
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

    def test_the_dictionary_spelling_is_answered_correctly_too(self, findings):
        """Zero, not a baseline.

        This file was written against 287 known disagreements and carried their
        counts as a constant. S1 landed, the constant went, and what replaces it
        is the only assertion worth making: every land use row in every zone
        table gets the table's own answer, asked either way the LEP spells it.
        """
        assert findings == [], "\n" + "\n".join(
            f"{f['zone']} {f['asked']!r} ({f['class']}): table says {f['expected']}, "
            f"tool says {f['got']} via {f['match_type']}"
            for f in findings
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


class TestTheCasesTheRoadmapNames:
    """Named separately from the sweep, because these four were verified by hand
    against the LEP in ROADMAP.md S1 and should keep working for reasons a
    reader can check without running anything."""

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


class TestTheStoredPairingMatchesTheDocument:
    """S1 moved the pairing from a regex into `data/definitions.py`, which makes
    it transcribed data — and transcribed data in this repository has an audit
    behind it or it drifts."""

    def test_the_spelling_table_is_what_the_document_yields(self):
        problems = spelling_table_findings()
        assert problems == [], "\n" + "\n".join(problems)

    def test_the_matcher_actually_uses_the_stored_pairing(self, monkeypatch):
        """The check on the check.

        Everything above would pass if `landuse.py` reverted to inflecting words
        by rule and happened to get the same answers, so this empties the stored
        pairing and requires the sweep to notice. It is the same argument as
        `test_a_broken_matcher_is_detected`, aimed at the data rather than the
        matcher: `-ies` and `-a` and the moving possessive are exactly what no
        rule reaches, so removing the data must break them.
        """
        import lismore_da_mcp.landuse as landuse

        monkeypatch.setattr(landuse, "_CANONICAL_SPELLING", {})
        findings = audit(["E4"])
        assert findings, (
            "the Dictionary/table pairing was emptied and every question still "
            "passed — the matcher is not reading it, so the audit above proves "
            "nothing about the tool."
        )


class TestTheCatchAllIsNotAnAnswer:
    """ROADMAP.md S1 item 3. Falling through to 'any other development not
    specified' has two readings — a use the LEP names and this table omits, and
    a term nothing here could identify — and they are not the same fact."""

    def test_an_unrecognised_term_is_not_reported_as_permitted(self):
        """The 120-wrong-yes shape. E2's catch-all permits unlisted development
        with consent, so anything unresolved used to come back permitted."""
        from audit_landuse_matching import ask
        answer = ask("E2", "quantum widget emporium")
        assert answer["permissibility"] == "not_found"
        assert answer["match_type"] == "unrecognised"

    def test_an_unrecognised_term_is_not_reported_as_prohibited_either(self):
        """The mirror, and the reason `permissible` is None rather than False:
        this is the field `readiness.py` raises a 'stop' on."""
        from lismore_da_mcp.data.zones import ZONES
        from lismore_da_mcp.landuse import classify_land_use
        classified = classify_land_use("quantum widget emporium", ZONES["R2"], "R2")
        assert classified["permissible"] is None
        assert classified["match_type"] == "unrecognised"

    @pytest.mark.parametrize("zone", ["RU2", "RU3", "SP2", "C1"])
    def test_the_other_wording_of_the_catchall_is_recognised(self, zone):
        """These four word the row 'Any development not specified in item 2 or
        3', without the 'other' the substring test looked for, so their
        prohibiting catch-all was invisible and a use they do not list came back
        'not found' rather than prohibited."""
        from audit_landuse_matching import ask
        answer = ask(zone, "industry")
        assert answer["permissibility"] == "likely_prohibited", (
            f"{zone} prohibits anything its table does not list, and it does not "
            f"list industry — got {answer['permissibility']}"
        )

    def test_a_recognised_use_the_table_omits_still_gets_the_catchall(self):
        """The other side of the line. 'industry' is a use the LEP names, R2's
        table does not list it, and R2 prohibits anything unlisted — so the
        catch-all is the LEP's own answer and withholding it would be its own
        kind of wrong."""
        from audit_landuse_matching import ask
        answer = ask("R2", "industry")
        assert answer["permissibility"] == "likely_prohibited"
        assert answer["match_type"] == "catchall"

    def test_every_unsettled_answer_carries_the_sepp_caveat(self):
        """The caveat was gated to prohibited-shaped verdicts, so the wrong
        'yes' shipped bare. Anything that is not a settled permission needs it."""
        from audit_landuse_matching import ask
        for zone, term in [("E2", "quantum widget emporium"), ("R2", "industry"),
                           ("E4", "centre-based child care facility"), ("C1", "pottery studio")]:
            answer = ask(zone, term)
            assert "scope_of_this_answer" in answer, (
                f"{zone} + {term!r} came back {answer['permissibility']} with no SEPP caveat"
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


class TestUsesTheLEPPlacesUnderAParent:
    """SCENARIOS.md run 2, R1. `audit()` asks only about the terms a table names,
    and passed clean while 161 answers about uses the tables reach only through
    the Dictionary's "X is a type of Y" notes were a wrong "yes" — a medical
    centre in E4, a dwelling house in E4, a B&B in E3. The hand-written hierarchy
    covered the commercial premises family and nothing else."""

    @pytest.mark.parametrize("zone,term,expected", [
        ("E4", "medical centre", "prohibited"),                   # Health services facilities
        ("E4", "dwelling house", "prohibited"),                   # Residential accommodation
        ("E4", "shop top housing", "prohibited"),
        ("E3", "bed and breakfast accommodation", "prohibited"),  # Tourist and visitor accommodation
        ("R1", "garden centre", "prohibited"),                    # retail -> Commercial premises
        ("RU5", "business identification sign", "permitted_with_consent"),  # Signage
        ("R1", "hazardous industry", "prohibited"),               # heavy industry -> Industries
        ("E3", "Residential care facilities", "prohibited"),      # the note's own plural
        ("E4", "backpackers' accommodation", "prohibited"),       # a curly apostrophe in the LEP
    ])
    def test_the_named_cases(self, zone, term, expected):
        import json

        from lismore_da_mcp.tools.zoning import check_permissibility

        answer = json.loads(check_permissibility({"land_use": term, "zone_code": zone})[0].text)
        assert answer["permissibility"] == expected, answer
        assert answer["match_type"] == "hierarchy"

    def test_every_zone_agrees_with_the_chain(self):
        found = hierarchy_audit(CURRENT_ZONES)
        assert found == [], "\n".join(
            f"{f['zone']} {f['asked']!r}: {f['got']} ({f['class']}), table via "
            f"{f['table_term']} says {f['expected']}" for f in found[:20])

    def test_the_stored_notes_are_the_documents(self):
        assert type_of_findings() == []

    def test_every_note_is_read_including_the_curly_apostrophes(self, dictionary):
        """The note pattern accepted only a straight apostrophe, and the document
        writes them curly, so 'Backpackers' accommodation' and 'Rural workers'
        dwellings' were silently not read — 106 of 108."""
        notes = type_of_notes(lep_text(), dictionary)
        assert len(notes) == 108
        assert "backpackers' accommodation" in notes
        assert "rural worker's dwelling" in notes

    def test_the_nearest_listed_parent_decides(self):
        """LEP cl 2.3(3)(b). Checking the table's sections before the chain let a
        distant ancestor under 'permitted' beat a nearer one under 'prohibited'."""
        from lismore_da_mcp.landuse import classify_land_use

        zone = {
            "permitted_without_consent": [],
            "permitted_with_consent": ["Commercial premises"],
            "prohibited": ["Food and drink premises"],
        }
        result = classify_land_use("cafe", zone, "TEST")
        assert result["permissible"] is False
        assert result["matched_use"] == "Food and drink premises"

    def test_the_derivation_is_shown(self):
        from lismore_da_mcp.landuse import classify_land_use

        result = classify_land_use("medical centre", ZONES["E4"], "E4")
        assert "medical centre -> health services facility" in result["basis"]
        assert "cl 2.3(3)(b)" in result["basis"]

    def test_the_audit_fails_when_the_chain_is_cut(self, monkeypatch):
        """The check on the checker. With no ancestors the named cases fall back
        to the catch-all, and E4's catch-all permits, so they read as a yes."""
        import lismore_da_mcp.landuse as landuse

        monkeypatch.setattr(landuse, "ancestors", lambda term: [])
        found = hierarchy_audit(["E4"])
        assert any(f["class"] == "wrong_yes" for f in found)


class TestWordsResolveThroughTheLEP:
    """ROADMAP.md A2. check_permissibility and get_parking_rates both refused
    "hairdresser" while get_definition answered it — the same word, adjacent
    questions, opposite outcomes. The LEP Dictionary names hairdressers inside
    business premises, and Chapter 7 carries a business premises rate. They now
    share one path, and say whose reading it is."""

    @staticmethod
    def ask(tool, arguments):
        import json

        from lismore_da_mcp.registry import registered

        return json.loads(registered()[tool].handler(arguments)[0].text)

    @pytest.mark.parametrize("word,zone,expected", [
        ("hairdresser", "E2", "permitted_with_consent"),
        ("hairdresser", "E4", "prohibited"),   # E4 prohibits Commercial premises
        ("bank", "E1", "permitted_with_consent"),
        ("barber", "E2", "permitted_with_consent"),
    ])
    def test_permissibility_answers_through_the_lep_term(self, word, zone, expected):
        answer = self.ask("check_permissibility", {"land_use": word, "zone_code": zone})
        assert answer["permissibility"] == expected
        assert "business premises" in answer["interpreted_as"]

    def test_it_says_whether_the_lep_names_the_word(self):
        named = self.ask("check_permissibility", {"land_use": "hairdresser", "zone_code": "E2"})
        assert "names it" in named["interpreted_as"]
        unnamed = self.ask("check_permissibility", {"land_use": "barber", "zone_code": "E2"})
        assert "this server's reading, not the LEP's words" in unnamed["interpreted_as"]

    @pytest.mark.parametrize("word", ["hairdresser", "barber", "dry cleaner", "bank"])
    def test_parking_reaches_the_business_premises_rate(self, word):
        answer = self.ask("get_parking_rates", {"development_type": word, "floor_area_sqm": 60,
                                                "location": "outside_cbd"})
        assert answer["development_type"] == "business_premises"
        assert "business premises" in answer["interpreted_as"]

    @pytest.mark.parametrize("word,row", [("funeral home", "Funeral home"), ("pub", "Pub")])
    def test_a_use_schedule_1_rates_separately_does_not_inherit(self, word, row):
        """'Business premises (other than funeral homes)': walking up from a
        funeral home would charge it the wrong rate. And a pub was charged the
        hotel or motel *accommodation* rate through a synonym, until A2."""
        answer = self.ask("get_parking_rates", {"development_type": word})
        assert "error" in answer
        assert f"'{row}'" in answer["schedule_1_has_its_own_rate"]

    def test_no_uncarried_schedule_1_use_is_walked_up(self):
        from lismore_da_mcp.data.parking import UNCARRIED_SCHEDULE_1_USES
        from lismore_da_mcp.parking import resolve_parking_use

        for use in UNCARRIED_SCHEDULE_1_USES:
            match, _, _ = resolve_parking_use(use)
            assert not (match and match.how == "lep"), use

    def test_a_word_nothing_places_still_refuses(self):
        assert self.ask("check_permissibility",
                        {"land_use": "tattoo studio", "zone_code": "E2"})["permissibility"] == "not_found"
        assert "error" in self.ask("get_parking_rates", {"development_type": "tattoo studio"})

    def test_a_fuzzy_spelling_is_never_read_as_a_land_use(self):
        from lismore_da_mcp.landuse import lep_term_for

        assert lep_term_for("hairdreser") is None

    def test_the_composed_tools_agree(self):
        """The point of one shared path: the readiness check and the SEE draft
        now reach the same parking rate the parking tool does."""
        from lismore_da_mcp.readiness import Proposal
        from lismore_da_mcp.tools.readiness import _parking

        parking = _parking(Proposal(proposed_use="hairdresser", floor_area_sqm=90,
                                    in_cbd=False), None)
        assert parking and parking["rate_matched"] == "business_premises"

    def test_no_synonym_contradicts_the_lep(self):
        from audit_definitions import check_synonyms_follow_the_lep

        assert check_synonyms_follow_the_lep() == []
