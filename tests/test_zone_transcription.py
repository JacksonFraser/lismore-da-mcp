"""The zone land use tables match the LEP text they were transcribed from.

PLAN.md item 0.2. This is the check that did not exist. Every permissibility
answer rests on `data/zones.py`, which was copied by hand out of
`documents/lep/lep-2012-nsw-full.txt`, and until now nothing compared the two:
the rest of the suite pins that the data has not *changed*, and the 21-zone list
in `test_tools.py` is itself a second hand copy. A slip would have been
invisible, and blessed by the tests that made the data look verified.

The audit found zero transcription errors across all 21 zones — the data was
right. What it did find was three places where the *scraped source text* has
lost a semicolon between two land uses, which is recorded in
`scripts/audit_zone_tables.py` rather than papered over.

These tests run the same comparison, so the guarantee survives the next edit to
either side.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_zone_tables import (  # noqa: E402
    BUSINESS_ZONES,
    SOURCE_TEXT_DEFECTS,
    compare,
    normalise,
    parse_lep,
    split_uses,
)

from lismore_da_mcp.data.zones import ZONES  # noqa: E402

CURRENT_ZONES = [z for z in ZONES if "redirect_to" not in ZONES[z]]


@pytest.fixture(scope="module")
def lep_tables():
    tables = parse_lep()
    assert tables, "parsed no tables — the LEP text layout has changed"
    return tables


class TestTranscriptionMatchesSource:
    @pytest.mark.parametrize("zone", CURRENT_ZONES)
    def test_zone_matches_the_lep(self, zone, lep_tables):
        assert zone in lep_tables, (
            f"{zone} has no land use table in lep-2012-nsw-full.txt. Either it does not "
            "belong in ZONES, or the parser missed it — check by hand.")
        findings = compare(zone, lep_tables[zone], ZONES[zone])
        assert findings == [], "\n" + "\n".join(findings)

    @pytest.mark.parametrize("zone", BUSINESS_ZONES)
    def test_business_zones_specifically(self, zone, lep_tables):
        """Called out separately because this tool exists for businesses: a
        wrong entry in E1-E4, MU1 or RU5 is the one that costs someone money."""
        assert compare(zone, lep_tables[zone], ZONES[zone]) == []


class TestTheAuditCanActuallyFail:
    """A checker that cannot detect a fault is worse than none — it manufactures
    confidence. These pin that the comparison really compares."""

    def test_a_missing_use_is_caught(self, lep_tables):
        mutated = dict(ZONES["E2"])
        mutated["permitted_with_consent"] = [
            u for u in mutated["permitted_with_consent"] if u != "Medical centres"
        ]
        findings = compare("E2", lep_tables["E2"], mutated)
        assert any("Medical centres" in f and "MISSING" in f for f in findings)

    def test_an_invented_use_is_caught(self, lep_tables):
        mutated = dict(ZONES["E2"])
        mutated["prohibited"] = mutated["prohibited"] + ["Brothels"]
        findings = compare("E2", lep_tables["E2"], mutated)
        assert any("Brothels" in f and "EXTRA" in f for f in findings)

    def test_a_dropped_catchall_is_caught(self, lep_tables):
        """The catch-all decides everything the table does not name, so losing
        it silently flips the answer for every unlisted use."""
        mutated = dict(ZONES["E2"])
        mutated["permitted_with_consent"] = [
            u for u in mutated["permitted_with_consent"]
            if "any other development" not in u.lower()
        ]
        findings = compare("E2", lep_tables["E2"], mutated)
        assert any("catch-all" in f for f in findings)


class TestParsing:
    def test_semicolon_and_stray_comma_both_split(self):
        """The E2 prohibited list has "Cemeteries, Correctional centres" — a
        comma where the source meant a semicolon."""
        assert split_uses("Cemeteries, Correctional centres; Crematoria") == [
            "Cemeteries", "Correctional centres", "Crematoria"]

    def test_a_comma_inside_a_use_is_not_a_split(self):
        assert split_uses("Recreation facilities (indoor); Roads") == [
            "Recreation facilities (indoor)", "Roads"]

    def test_nil_is_not_a_land_use(self):
        assert split_uses("Nil") == []

    def test_known_source_defects_are_repaired(self):
        for merged, parts in SOURCE_TEXT_DEFECTS.items():
            assert split_uses(merged) == parts

    def test_apostrophes_and_case_do_not_count_as_differences(self):
        assert normalise("Backpackers’ accommodation") == normalise("Backpackers' accommodation")
        assert normalise("Shop top housing") == normalise("SHOP  TOP   HOUSING")

    def test_the_parser_stops_at_the_end_of_the_tables(self, lep_tables):
        """W2 is the last zone and is followed by Part 3, not another Zone
        header. Without a terminator the parser swallowed the rest of the
        instrument and reported 488 prohibited uses for it."""
        assert len(lep_tables["W2"]["prohibited"]) < 20
