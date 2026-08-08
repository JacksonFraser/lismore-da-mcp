#!/usr/bin/env python3
"""Check the flood controls against DCP Chapter 8 and LEP 2012 cl 5.21-5.22.

PLAN.md item 0.5. The sixth of these, after `audit_parking_rates.py`,
`audit_zone_tables.py`, `audit_contributions.py`, `audit_signage.py`,
`audit_approvals.py`, `audit_timing.py` and `audit_readiness.py` — and the one
with the most direct evidence that it was needed. What it replaced claimed a
500mm freeboard where the chapter says 300mm, three times, and carried two
provisions that appear nowhere in any document in this repository.

Chapter 8's controls are numbered prose under per-area headings, so as with
Chapter 9 there is nothing to diff structurally: every control is stored
verbatim in `data/flood.py` and this checks the stored string still appears in
the source.

It also checks the two things a presence check alone would miss:

  * that the numbers derived from the text — the 300mm freeboard, the 1.03m
    1-in-500 offset — agree with the quotes they were read from, so the
    constants cannot drift away from their own source; and
  * that every numbered control in §8.4 to §8.8 is carried, counted off the
    document rather than a hardcoded expectation. Three commercial requirements
    out of four reads as complete and is not.

    .venv/bin/python scripts/audit_flood.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTER = ROOT / "documents" / "dcp" / "chapter-8-flood-prone-lands.pdf"
LEP = ROOT / "documents" / "lep" / "lep-2012-nsw-full.txt"

# Every page carries this running header. It is not part of any control, and
# leaving it in would break any quote that spans a page break — of which the
# chapter has several, including the whole of §8.5.2.
RUNNING_HEADER = re.compile(
    r"Lismore Development Control Plan\s*[-–—]\s*Part A\s*Chapter 8\s*[-–—]\s*Page \d+")


def chapter_text() -> str:
    import fitz

    with fitz.open(CHAPTER) as doc:
        pages = [doc[i].get_text() for i in range(doc.page_count)]
    stripped = [RUNNING_HEADER.sub(" ", p) for p in pages]
    return " ".join(" ".join(p.split()) for p in stripped)


def normalise(text: str) -> str:
    """Compare on wording, not typography.

    The chapter uses curly quotes around defined terms and an en dash in
    "A fifth category - CBD Flood Liable". The LEP extract uses an en dash
    where the legislation prints a closing dash before a list. Neither changes
    a control.
    """
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("m²", "m2")
    return " ".join(text.lower().split())


def check(label: str, quote: str, haystack: str, problems: list) -> None:
    if normalise(quote) in haystack:
        print(f"  ✓ {label}")
    else:
        problems.append(label)
        print(f"  ✗ {label}")
        print(f"      stored: {quote[:140]}")


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.data.flood import (
        ALL_DEVELOPMENT_CONTROLS, ARI_500_OFFSET_M, DEFINITIONS, FLOOD_AREAS,
        FREEBOARD_MM, LEP_FLOOD_CLAUSES, SCOPE, STRUCTURAL_ADEQUACY_EXEMPTION)

    for path in (CHAPTER, LEP):
        if not path.exists():
            print(f"missing {path}")
            return 2

    haystack = normalise(chapter_text())
    lep = normalise(LEP.read_text(encoding="utf-8", errors="replace"))
    problems: list = []

    print("§8.2 definitions:")
    for key, entry in DEFINITIONS.items():
        check(f"{key:28} ({entry['section']})", entry["verbatim"], haystack, problems)

    print("\n§8.3 scope — who the controls apply to:")
    for key in ("categories_verbatim", "fifth_category_verbatim", "applies_verbatim",
                "change_of_use_verbatim", "minor_extensions_verbatim"):
        check(f"{key:28}", SCOPE[key], haystack, problems)

    print("\nShared controls (§8.5.4 / §8.6.4):")
    for key, quote in ALL_DEVELOPMENT_CONTROLS.items():
        check(f"{key:28}", quote, haystack, problems)
    check("small works exemption      ", STRUCTURAL_ADEQUACY_EXEMPTION, haystack, problems)

    for area_key, area in FLOOD_AREAS.items():
        print(f"\n{area['name']} (§{area['section']}):")
        check("  definition", area["definition_verbatim"], haystack, problems)

        for field in ("prohibition_verbatim", "ari_500_note_verbatim",
                      "boundary_variation_verbatim", "no_controls_verbatim",
                      "requirements_verbatim"):
            if field in area:
                check(f"  {field}", area[field], haystack, problems)

        for field in ("exceptions", "airport_limbs", "considerations"):
            for i, quote in enumerate(area.get(field, []), 1):
                check(f"  {field}[{i}]", quote, haystack, problems)

        for dev_type, control in area.get("controls", {}).items():
            if "reasoning" in control:
                check(f"  {dev_type}: reasoning", control["reasoning"], haystack, problems)
            for i, quote in enumerate(control.get("requirements", []), 1):
                check(f"  {dev_type} [{i}] (§{control['section']})", quote, haystack, problems)
            for case_key, case in control.get("sub_cases", {}).items():
                for i, quote in enumerate(case["requirements"], 1):
                    check(f"  {dev_type}/{case_key} [{i}]", quote, haystack, problems)

    print("\nLEP 2012 flood clauses (against the LEP text, not the DCP):")
    for clause, entry in LEP_FLOOD_CLAUSES.items():
        check(f"  cl {clause} {entry['title']}", entry["verbatim"], lep, problems)
        for i, test in enumerate(entry.get("tests", []), 1):
            check(f"  cl {clause}(2)({chr(96 + i)})", test, lep, problems)
        if "climate_change_verbatim" in entry:
            check(f"  cl {clause}(3)(a) climate change",
                  entry["climate_change_verbatim"], lep, problems)
        for term in entry.get("sensitive_and_hazardous_examples", []):
            check(f"  cl {clause}(5) {term}", term, lep, problems)

    # A presence check cannot tell that a number was read correctly out of the
    # sentence it came from — only that the sentence is still there. These two
    # constants are what every floor level in the LGA is calculated from.
    print("\nDerived constants agree with the text they were read from:")
    fpl = normalise(DEFINITIONS["flood_planning_level"]["verbatim"])
    freeboard = normalise(DEFINITIONS["freeboard"]["verbatim"])
    for label, quote, expected in (
        ("FREEBOARD_MM from the FPL definition", fpl, f"{FREEBOARD_MM}mm"),
        ("FREEBOARD_MM from the freeboard definition", freeboard, f"{FREEBOARD_MM}mm"),
    ):
        if expected in quote:
            print(f"  ✓ {label} = {expected}")
        else:
            problems.append(label)
            print(f"  ✗ {label}: {expected} does not appear in the stored quote")

    offsets = {normalise(a["ari_500_note_verbatim"]) for a in FLOOD_AREAS.values()
               if "ari_500_note_verbatim" in a}
    if all(f"add {ARI_500_OFFSET_M}m" in note for note in offsets):
        print(f"  ✓ ARI_500_OFFSET_M = {ARI_500_OFFSET_M} in all {len(offsets)} notes")
    else:
        problems.append("ARI_500_OFFSET_M")
        print(f"  ✗ ARI_500_OFFSET_M = {ARI_500_OFFSET_M} not in every 1-in-500 note")

    # Count the numbered controls in the document and compare against what is
    # carried. This is the check that catches a requirement nobody transcribed
    # — the failure mode a presence check is structurally blind to.
    print("\nControl counts, read off the document:")
    shared_quotes = list(ALL_DEVELOPMENT_CONTROLS.values()) + [STRUCTURAL_ADEQUACY_EXEMPTION]
    missed = controls_not_carried(haystack, FLOOD_AREAS, shared_quotes)
    if missed:
        problems.append("uncarried controls")
        print(f"  ✗ {len(missed)} numbered control(s) in the chapter with no entry here:")
        for text in missed:
            print(f"      {text[:150]}")
    else:
        print("  ✓ every numbered control in §8.4-§8.8 is carried")

    total = sum(1 for _ in iter_stored(FLOOD_AREAS))
    print(f"\n{total} stored control(s) checked, {len(problems)} not matching the source.")
    if problems:
        print("\nA mismatch means either the chapter was reissued or the transcription drifted.\n"
              "Read the chapter before editing — do not adjust the stored text to make this\n"
              "pass. The freeboard in this file was wrong by 200mm for exactly that reason.")
    return 1 if problems else 0


def iter_stored(areas: dict):
    """Every verbatim control string carried, for the count."""
    for area in areas.values():
        for field in ("exceptions", "airport_limbs", "considerations"):
            yield from area.get(field, [])
        for control in area.get("controls", {}).values():
            yield from control.get("requirements", [])
            for case in control.get("sub_cases", {}).values():
                yield from case["requirements"]


def controls_not_carried(haystack: str, areas: dict, shared: list) -> list:
    """Numbered controls in the chapter that no entry in the data reproduces.

    The chapter numbers its controls "1." to "5." under each heading. Matching
    the first clause of each is enough to tell whether it was transcribed at
    all, and avoids depending on where the next one starts.

    Scoped to §8.4 onward. Before that the numbered lists are the chapter's
    objectives (§8.1), which are not controls and are not carried as such —
    counting them reported three false gaps, and an audit that always reports
    the same false gaps is one nobody reads twice.
    """
    start = haystack.find("8.4 floodway")
    region = haystack[start:] if start != -1 else haystack

    carried = [normalise(q) for q in iter_stored(areas)]
    carried += [normalise(q) for q in shared]

    missed = []
    for match in re.finditer(r"(?:^| )(\d)\. ([a-z][^.]{25,200}\.)", region):
        # "shown on Map 2. The freeboard…" is a sentence, not a list item.
        preceding = region[max(0, match.start() - 4):match.start() + 1].strip()
        if preceding.endswith("map"):
            continue
        control = match.group(2).strip()
        if not any(control[:60] in c for c in carried):
            missed.append(control)
    return missed


if __name__ == "__main__":
    sys.exit(main())
