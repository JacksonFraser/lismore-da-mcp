#!/usr/bin/env python3
"""Diff the transcribed zone land use tables against the LEP text.

PLAN.md item 0.2. Every permissibility answer this server gives rests on
`data/zones.py`, which was transcribed by hand, and **nothing checked it against
the source**. The test suite pins that the data has not *changed*, not that it is
*right* — and the 21-zone list in `tests/test_tools.py` is itself a second hand
copy, so a slip would be invisible and permanently blessed by the test that makes
the data look verified.

The source is `documents/lep/lep-2012-nsw-full.txt`, which sets each table out as

    Zone E2   Commercial Centre
    1   Objectives of zone
    2   Permitted without consent
    <uses, semicolon separated>
    3   Permitted with consent
    <uses, semicolon separated>
    4   Prohibited
    <uses, semicolon separated>

This reports differences. **It does not correct anything** — some differences will
be deliberate (the catch-all phrasing, a normalised apostrophe), and a
"correction" made from a misread source is the failure this is meant to prevent.

    .venv/bin/python scripts/audit_zone_tables.py            # all zones
    .venv/bin/python scripts/audit_zone_tables.py --business # E1-E4, MU1, RU5
    .venv/bin/python scripts/audit_zone_tables.py --zone E2
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEP = ROOT / "documents" / "lep" / "lep-2012-nsw-full.txt"

BUSINESS_ZONES = ["E1", "E2", "E3", "E4", "MU1", "RU5"]

SECTIONS = {
    "2": "permitted_without_consent",
    "3": "permitted_with_consent",
    "4": "prohibited",
}

# What ends a land use table. The last zone in the sequence (W2) is followed by
# "Part 3 Exempt and complying development" rather than another Zone header, so
# without this the parser swallowed the rest of the instrument — it reported 488
# prohibited uses for W2, including Schedule entries and clause text.
END_OF_TABLE = re.compile(r"^(Part\s+\d|Schedule\s+\d|\d+\.\d+\s{2,}\S)")

# The catch-all that closes every "permitted with consent" list. It is a rule,
# not a land use, and the transcription may reasonably render or omit it.
CATCHALL = re.compile(r"any other development not specified", re.I)

# Defects in the extracted source text, not in the transcription.
#
# `lep-2012-nsw-full.txt` was scraped from legislation.nsw.gov.au and in three
# places lost the semicolon between two land uses, so they read as one invented
# use. Verified by hand on 2026-08-02 against the surrounding list in each case;
# `data/zones.py` has them right and the text has them wrong.
#
# These are listed rather than repaired by a general heuristic because "two
# capitalised uses juxtaposed" would also split legitimate multi-word uses. And
# they are listed rather than tolerated silently because an audit that always
# reports the same ten differences teaches its reader to ignore it — which is
# exactly how the fee scale sat two years stale behind a standing caveat.
SOURCE_TEXT_DEFECTS = {
    "Aquaculture Boat launching ramps": ["Aquaculture", "Boat launching ramps"],
    "Oyster aquaculture Research stations": ["Oyster aquaculture", "Research stations"],
}

# "Nil" is what the LEP prints when a list is empty (Zone C1 permits nothing
# with consent). It is not a land use, and the transcription correctly holds an
# empty list.
NOT_A_USE = {"nil"}


def normalise(use: str) -> str:
    """Compare on meaning, not typography.

    The source uses curly apostrophes (Backpackers’) where the transcription
    uses straight ones, and case and spacing vary. Neither changes which use is
    being named, and flagging them would bury the differences that matter.
    """
    text = unicodedata.normalize("NFKD", use)
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"[^a-z0-9()' ]", " ", text.lower())
    return " ".join(text.split())


def split_uses(blob: str) -> list[str]:
    """Split a semicolon-separated list of land uses.

    Splits on commas too, but only where the source has plainly used one in
    place of a semicolon — the E2 prohibited list contains "Cemeteries,
    Correctional centres", which without this reads as a single invented use.
    Commas *inside* a use, as in "Recreation facilities (indoor)", are not
    affected because the split needs a following capital letter.
    """
    parts = []
    for chunk in blob.split(";"):
        parts.extend(re.split(r",\s+(?=[A-Z])", chunk))

    uses = []
    for part in parts:
        cleaned = part.strip(" .;\n")
        if not cleaned or cleaned.lower() in NOT_A_USE:
            continue
        uses.extend(SOURCE_TEXT_DEFECTS.get(cleaned, [cleaned]))
    return uses


def parse_lep() -> dict[str, dict[str, list[str]]]:
    """Zone code -> section -> list of uses, straight out of the LEP text."""
    lines = LEP.read_text(errors="replace").splitlines()
    tables: dict[str, dict[str, list[str]]] = {}
    zone = None
    section = None
    buffer: list[str] = []

    def flush():
        if zone and section and buffer:
            tables.setdefault(zone, {}).setdefault(section, []).extend(
                split_uses(" ".join(buffer)))

    for line in lines:
        stripped = line.strip()
        header = re.match(r"^Zone\s+([A-Z]{1,2}\d|MU1|SP\d|RE\d|W\d|C\d)\s{2,}(.+)$", stripped)
        if header:
            flush()
            buffer = []
            zone, section = header.group(1), None
            continue
        item = re.match(r"^([1-4])\s{2,}(.+)$", stripped)
        if item and zone:
            flush()
            buffer = []
            section = SECTIONS.get(item.group(1))
            continue
        if section and END_OF_TABLE.match(stripped):
            flush()
            buffer = []
            zone, section = None, None
            continue
        if section and stripped and not stripped.startswith("•"):
            buffer.append(stripped)
    flush()
    return tables


def compare(zone: str, source: dict[str, list[str]], transcribed: dict) -> list[str]:
    findings = []
    for section in SECTIONS.values():
        want = source.get(section, [])
        got = transcribed.get(section, []) or []

        want_map = {normalise(u): u for u in want if not CATCHALL.search(u)}
        got_map = {normalise(u): u for u in got if not CATCHALL.search(u)}

        missing = [want_map[k] for k in want_map.keys() - got_map.keys()]
        extra = [got_map[k] for k in got_map.keys() - want_map.keys()]

        for use in sorted(missing):
            findings.append(
                f"  {section}: MISSING from data/zones.py — LEP lists {use!r}")
        for use in sorted(extra):
            findings.append(
                f"  {section}: EXTRA in data/zones.py — not in the LEP table: {use!r}")

        # The catch-all decides everything the table does not name, so whether
        # it is present is not cosmetic.
        want_catchall = any(CATCHALL.search(u) for u in want)
        got_catchall = any(CATCHALL.search(u) for u in got)
        if want_catchall and not got_catchall:
            findings.append(
                f"  {section}: LEP closes this list with the 'any other development' "
                "catch-all; the transcription does not")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--business", action="store_true", help="only E1-E4, MU1, RU5")
    parser.add_argument("--zone", help="a single zone code")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.data.zones import ZONES

    source = parse_lep()
    if not source:
        print("Parsed no tables from the LEP text — the source layout has changed.")
        return 2

    if args.zone:
        zones = [args.zone.upper()]
    elif args.business:
        zones = BUSINESS_ZONES
    else:
        zones = [z for z in ZONES if "redirect_to" not in ZONES[z]]

    total = 0
    unparsed = []
    for zone in zones:
        if zone not in source:
            unparsed.append(zone)
            continue
        if zone not in ZONES:
            print(f"\n{zone}: in the LEP text but absent from data/zones.py")
            total += 1
            continue
        findings = compare(zone, source[zone], ZONES[zone])
        counts = {s: len(source[zone].get(s, [])) for s in SECTIONS.values()}
        if findings:
            total += len(findings)
            print(f"\n{zone} — {ZONES[zone]['name']}  (LEP lists "
                  f"{counts['permitted_without_consent']}/{counts['permitted_with_consent']}/"
                  f"{counts['prohibited']} without/with/prohibited)")
            print("\n".join(findings))
        else:
            print(f"{zone:4} ✓ matches the LEP table "
                  f"({counts['permitted_without_consent']}/{counts['permitted_with_consent']}/"
                  f"{counts['prohibited']} uses)")

    if unparsed:
        print(f"\nNo table found in the LEP text for: {', '.join(unparsed)}")
        print("  Either the zone has no land use table in this LEP, or the parser missed it —")
        print("  check by hand before concluding anything.")

    print(f"\n{len(zones)} zone(s) checked, {total} difference(s).")
    if total:
        print("\nDifferences are reported, not corrected. Some are deliberate; read the LEP\n"
              "passage before changing data/zones.py.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
