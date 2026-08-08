#!/usr/bin/env python3
"""Check the residential standards against DCP Chapter 1.

PLAN.md item 0.6, and the companion to `audit_flood.py`. These were the two data
files Phase 0 never audited and both were invented rather than transcribed —
this one more comprehensively. Of about nineteen figures in the old
`data/standards.py`, two were recognisably from Chapter 1 and the rest collided
with unrelated numbers elsewhere in the document: the "0.9m side setback" is
small lot housing's, the "4.5m front setback" is a five storey building
separation in the Health Precinct, the "15% deep soil" is land steeper than 15%
excluded from an open space calculation.

Chapter 1 is Performance Criteria and Acceptable Solutions in a two-column
table, so as with Chapters 8 and 9 there is nothing to diff structurally. Every
control is stored verbatim and this checks it still appears in the document.

Two checks beyond presence:

  * every Acceptable Solution reference the chapter defines (A1.1, A26.3, …) is
    counted off the document and reported if the data does not carry it, so a
    control nobody transcribed is visible rather than absent; and
  * the claims in NOT_SET_BY_THIS_CHAPTER really are absent — an audit that
    only checks what *is* there cannot catch a figure being reinvented, which is
    exactly how this file went wrong the first time.

    .venv/bin/python scripts/audit_standards.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTER = ROOT / "documents" / "dcp" / "chapter-1-residential-development.pdf"

RUNNING_HEADER = re.compile(
    r"Lismore Development Control Plan\s*[-–—]\s*Part A\s*Chapter 1\s*[-–—]\s*Page \d+")

# Figure captions are floating text boxes, so they extract wherever they sit on
# the page rather than in reading order — "Figure 21: Fencing" lands in the
# middle of A21.2's sentence, which spans a page break around it. They are not
# part of any control, and no stored quote contains one.
FIGURE_CAPTION = re.compile(r"^\s*Figures?\s+\d+.*$", re.MULTILINE)


def chapter_text() -> str:
    import fitz

    with fitz.open(CHAPTER) as doc:
        pages = [doc[i].get_text() for i in range(doc.page_count)]
    stripped = [FIGURE_CAPTION.sub(" ", RUNNING_HEADER.sub(" ", p)) for p in pages]
    return " ".join(" ".join(p.split()) for p in stripped)


def normalise(text: str) -> str:
    """Compare on wording, not typography.

    Three artefacts of this chapter, none of which changes a control:

      * Bullets are U+F0B7, a **private use** character from the Symbol font,
        not a whitespace bullet. `str.split()` does not touch it, so a criterion
        stored as a flowing sentence never matched the extracted list. The same
        family of glyph as the SEE form's Wingdings tick boxes.
      * Words hyphenate across line breaks — "all-\\nweather", "semi-\\ndetached"
        — which collapses to "all- weather". Rejoined below; the pattern needs a
        letter on both sides so it cannot touch " - " standing for an en dash.
      * The chapter mixes m2 with m² and uses curly apostrophes.
    """
    text = re.sub("[\ue000-\uf8ff]", " ", text)
    text = text.replace("m²", "m2").replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = " ".join(text.lower().split())
    return re.sub(r"(?<=[a-z])- (?=[a-z])", "-", text)


def check(label: str, quote: str, haystack: str, problems: list) -> None:
    if normalise(quote) in haystack:
        print(f"  ✓ {label}")
    else:
        problems.append(label)
        print(f"  ✗ {label}")
        print(f"      stored: {quote[:140]}")


# Keys whose value is our own commentary rather than the chapter's words —
# skipped wholesale, subtree included. Everything else in the data is meant to
# be verbatim, so the default is to check it: a new field added without thought
# gets audited rather than silently trusted.
COMMENTARY_KEYS = {
    "note", "answer", "the_question", "previously_claimed", "what_it_means",
    "applies_to", "source", "sepp_65_note", "the_number_is_not_here", "title",
    "front_setback_by_zone",
}


def walk(node, path, haystack, problems, seen):
    """Check every string in a nested structure that should be verbatim."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in COMMENTARY_KEYS:
                continue
            walk(value, f"{path}.{key}" if path else str(key), haystack, problems, seen)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            walk(value, f"{path}[{i}]", haystack, problems, seen)
    elif isinstance(node, str) and len(node) >= 10:
        if node in seen:
            return
        seen.add(node)
        check(path, node, haystack, problems)


def solutions_not_carried(haystack: str, carried: set) -> list:
    """Acceptable Solution references the chapter has that the data does not.

    The chapter labels them A<n>.<m> or A<n>. Reading the labels off the source
    beats a hardcoded list: eight of nine reads as complete and is not.
    """
    defined = set()
    for match in re.finditer(r"\ba(\d{1,2}(?:\.\d)?)\s+[a-z(]", haystack):
        defined.add("a" + match.group(1))
    return sorted(defined - carried)


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.data.standards import (
        DEFINITIONS, ELEMENTS, HEALTH_PRECINCT, HOUSING_TYPES,
        HOW_THIS_CHAPTER_WORKS, NOT_SET_BY_THIS_CHAPTER)

    if not CHAPTER.exists():
        print(f"missing {CHAPTER}")
        return 2

    haystack = normalise(chapter_text())
    problems: list = []
    seen: set = set()

    print("§1.3 how the chapter works:")
    walk(HOW_THIS_CHAPTER_WORKS, "", haystack, problems, seen)

    print("\n§2 definitions:")
    for key, text in DEFINITIONS.items():
        check(f"  {key}", text, haystack, problems)

    for key, element in ELEMENTS.items():
        print(f"\n§{element['section']} {element['title']}:")
        walk(element, "", haystack, problems, seen)

    print("\n§5-§10 housing types:")
    for key, entry in HOUSING_TYPES.items():
        walk(entry, key, haystack, problems, seen)

    print("\n§11 Lismore Health Precinct:")
    walk(HEALTH_PRECINCT, "", haystack, problems, seen)

    # The inverse check. This file's failure mode was inventing a figure, which
    # a presence check is structurally blind to — it only ever looks at what is
    # stored. So assert the absences are real.
    print("\nClaims recorded as absent really are absent:")
    for key, entry in NOT_SET_BY_THIS_CHAPTER.items():
        stale = entry["previously_claimed"]
        fragments = [f.strip() for f in re.split(r"[;,]", stale) if f.strip()]
        hits = [f for f in fragments if normalise(f) in haystack]
        if hits:
            problems.append(f"absence {key}")
            print(f"  ✗ {key}: the chapter does contain {hits}")
        else:
            print(f"  ✓ {key}: not in the chapter")

    print("\nAcceptable Solutions defined in the chapter but not carried here:")
    carried = set()
    for element in list(ELEMENTS.values()) + list(HOUSING_TYPES.values()):
        for ref in element.get("acceptable_solutions", {}):
            carried.add(normalise(ref.split()[0]))
    for ref in HEALTH_PRECINCT["taller_residential"]:
        carried.add(normalise(ref))
    for ref in HEALTH_PRECINCT["non_residential"]:
        carried.add(normalise(ref))
    missing = solutions_not_carried(haystack, carried)
    if missing:
        print(f"  {len(missing)} not carried: {', '.join(missing)}")
        print("  (a gap, not an error — but it should be visible rather than discovered "
              "by an applicant)")
    else:
        print("  ✓ none")

    print(f"\n{len(seen)} stored quote(s) checked, {len(problems)} not matching the chapter.")
    if problems:
        print("\nA mismatch means either the chapter was reissued or the transcription drifted.\n"
              "Read the chapter before editing — do not adjust the stored text to make this\n"
              "pass. Nearly every figure in this file was invented for exactly that reason.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
