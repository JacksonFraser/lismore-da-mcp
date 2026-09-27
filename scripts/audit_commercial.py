#!/usr/bin/env python3
"""Check the commercial design controls against DCP Chapter 2.

ROADMAP.md D1. Written before `data/commercial.py`, because every transcription
this repository has done by hand from memory has produced an invented figure,
and the only defence that has ever worked is a check that fails first.

Chapter 2 has two parts that look nothing alike. Part A (the CBD, Map 1) is
design principles written as prose under numbered sections and italic
subheadings; Part B (Brewster Street, Map 2) is a Performance Criteria /
Acceptable Solutions table like Chapter 1's. Neither can be diffed
structurally, so every control is stored verbatim and this checks each stored
string still appears in the chapter.

Four checks beyond presence, each for a failure a presence check cannot see:

  * **Completeness, read off the document.** Every numbered section (A.1-A.13,
    B.1-B.4), every italic subheading in Part A, and every P/A label in Table B1
    is read from the PDF's own typography — bold 12pt, bold italic 11pt and bold
    10pt — and each must either be carried or be named in
    `DESCRIPTIVE_SECTIONS` with the reason it holds no control. Eight
    subheadings out of nine reads as complete and is not.
  * **Figures agree with their quotes.** Each number in `FIGURES` must appear,
    as written, inside the verbatim quote it was read from, and the quote must
    be in the chapter. `audit_flood.py` found a freeboard 200mm wrong this way.
  * **Recorded absences are still absent.** `NOT_SET_BY_THIS_CHAPTER` is the
    answer to "what does Chapter 2 say about X" where the answer is nothing —
    awning clearances, a CBD side setback, change of use. A presence check only
    looks at what is stored, so it is structurally blind to a figure being
    reinvented; this asserts the phrases are not in the chapter.
  * **The reading rule is quoted from where it lives.** Chapter 2 has no
    equivalent of Chapter 1's §1.3, so how a departure from it is treated
    comes from the DCP Introduction's "Variations to the Plan", which is
    checked against that document.

    .venv/bin/python scripts/audit_commercial.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTER = ROOT / "documents" / "dcp" / "chapter-2-commercial-development.pdf"
INTRODUCTION = ROOT / "documents" / "dcp" / "dcp-introduction-may-2025.pdf"

RUNNING_HEADER = re.compile(
    r"Lismore Development Control Plan\s*[-–—]\s*Part A\s*\(applying to land to which LEP 2012 "
    r"applies\)\s*Chapter 2\s*[-–—]\s*Page \d+")
INTRO_HEADER = re.compile(
    r"Lismore Development Control Plan\s*Introduction\s*[-–—]\s*Page \d+")

# Figure captions float: they extract where the text box sits, not in reading
# order. None is part of a control and no stored quote contains one.
FIGURE_CAPTION = re.compile(r"^\s*Figure [AB]?\.?\d+.*$", re.MULTILINE)


def _text(path: Path, header: re.Pattern) -> str:
    import fitz

    with fitz.open(path) as doc:
        pages = [doc[i].get_text() for i in range(doc.page_count)]
    stripped = [header.sub(" ", p) for p in pages]
    return " ".join(" ".join(p.split()) for p in stripped)


def chapter_text() -> str:
    return _text(CHAPTER, RUNNING_HEADER)


def introduction_text() -> str:
    return _text(INTRODUCTION, INTRO_HEADER)


def normalise(text: str) -> str:
    """Compare on wording, not typography.

    Bullets are U+F0B7, a private use glyph that `str.split()` does not treat as
    whitespace (the same artefact as Chapter 1). Otherwise curly quotes, en
    dashes, m² against m2, and a word hyphenated across a line break.
    """
    text = re.sub("[-]", " ", text)
    text = text.replace("m²", "m2").replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = " ".join(text.lower().split())
    return re.sub(r"(?<=[a-z])- (?=[a-z])", "-", text)


def headings() -> dict:
    """The chapter's own structure, read off its typography.

    Returns {"sections": [...], "subheadings": [...], "table_labels": [...]}.
    Bold 12pt spans are the numbered sections; bold italic 11pt are Part A's
    subheadings (the 9pt bold italic spans are map captions); bold 10pt spans
    shaped like P1 or A2.3 are Table B1's labels. Flags, not font names: the
    fonts are anonymous CIDFonts that renumber on any reissue.
    """
    import fitz

    sections, subheadings, labels = [], [], []
    with fitz.open(CHAPTER) as doc:
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        size, flags = round(span["size"]), span["flags"]
                        bold, italic = bool(flags & 16), bool(flags & 2)
                        if bold and not italic and size == 12:
                            number = re.match(r"^([AB]\.\d{1,2})\b", text)
                            if number:
                                sections.append(number.group(1))
                        elif bold and italic and size == 11:
                            subheadings.append(text)
                        elif bold and not italic and size == 10:
                            if re.fullmatch(r"[PA]\d{1,2}(\.\d)?\.?", text):
                                labels.append(text.rstrip("."))
    return {"sections": sections, "subheadings": subheadings, "table_labels": labels}


def check(label: str, quote: str, haystack: str, problems: list) -> None:
    if normalise(quote) in haystack:
        print(f"  ✓ {label}")
    else:
        problems.append(label)
        print(f"  ✗ {label}")
        print(f"      stored: {quote[:140]}")


# Keys whose value is our own commentary rather than the chapter's words —
# skipped wholesale. Everything else is meant to be verbatim, so the default is
# to check it: a field added without thought gets audited, not trusted.
COMMENTARY_KEYS = {
    "note", "answer", "the_question", "what_it_means", "applies_to", "source",
    "name", "map", "how_to_find_it", "why_not_carried", "zone_today", "part",
    "heading", "section", "page", "unit", "as_written", "value", "absent_phrases",
    "element", "cross_reference", "stale_reference",
}


def walk(node, path, haystack, problems, seen):
    if isinstance(node, dict):
        for key, value in node.items():
            if key in COMMENTARY_KEYS:
                continue
            walk(value, f"{path}.{key}" if path else str(key), haystack, problems, seen)
    elif isinstance(node, (list, tuple)):
        for i, value in enumerate(node):
            walk(value, f"{path}[{i}]", haystack, problems, seen)
    elif isinstance(node, str) and len(node) >= 10:
        if node in seen:
            return
        seen.add(node)
        check(path, node, haystack, problems)


def figure_problems(figures: dict, haystack: str) -> list:
    """Each figure must sit, as written, inside its own quote."""
    problems = []
    for key, fig in figures.items():
        quote, written, value = fig["quote"], fig["as_written"], fig["value"]
        if normalise(quote) not in haystack:
            problems.append(f"{key}: quote not in the chapter")
            continue
        if normalise(written) not in normalise(quote):
            problems.append(f"{key}: '{written}' is not in its own quote")
            continue
        number = re.search(r"\d+(?:\.\d+)?", written)
        words = {"two": 2, "three": 3, "one": 1}
        parsed = float(number.group()) if number else words.get(written.split()[0].lower())
        if parsed is None or float(parsed) != float(value):
            problems.append(f"{key}: stored {value} but the quote says '{written}'")
    return problems


def carried_structure() -> dict:
    """What the data claims to carry, in the same shape as `headings()`."""
    from lismore_da_mcp.data.commercial import DESCRIPTIVE_SECTIONS, PART_A, PART_A_FRAME, PART_B_FRAME, TABLE_B1

    sections = set(DESCRIPTIVE_SECTIONS)
    subheadings = set()
    for group in (PART_A, PART_A_FRAME, PART_B_FRAME):
        for entry in group.values():
            sections.add(entry["section"])
            if entry.get("subheading"):
                subheadings.add(entry["heading"])
    labels = set()
    for element in TABLE_B1.values():
        labels.update(element["performance_criteria"])
        labels.update(element["acceptable_solutions"])
    return {"sections": sections, "subheadings": subheadings, "table_labels": labels}


def not_carried() -> dict:
    """Structure the chapter has that the data does not account for."""
    found = headings()
    carried = carried_structure()
    return {kind: sorted(set(found[kind]) - carried[kind]) for kind in found}


def invented_structure() -> dict:
    """Structure the data claims that the chapter does not have."""
    found = headings()
    carried = carried_structure()
    return {kind: sorted(carried[kind] - set(found[kind])) for kind in found}


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.data.commercial import (
        FIGURES,
        HOW_TO_READ_THIS_CHAPTER,
        NOT_SET_BY_THIS_CHAPTER,
        PART_A,
        PART_A_FRAME,
        PART_B_FRAME,
        PRECINCTS,
        SEPARATION_TABLE,
        TABLE_B1,
    )

    for path in (CHAPTER, INTRODUCTION):
        if not path.exists():
            print(f"missing {path}")
            return 2

    haystack = normalise(FIGURE_CAPTION.sub(" ", chapter_text()))
    intro = normalise(introduction_text())
    problems: list = []
    seen: set = set()

    print("How to read the chapter (DCP Introduction, 'Variations to the Plan'):")
    for key in ("variations_verbatim", "not_a_guarantee_verbatim"):
        check(key, HOW_TO_READ_THIS_CHAPTER[key], intro, problems)
    print("\nHow to read the chapter (Chapter 2 itself):")
    for key, value in HOW_TO_READ_THIS_CHAPTER.items():
        if key.endswith("_verbatim") and key not in ("variations_verbatim",
                                                     "not_a_guarantee_verbatim"):
            check(key, value, haystack, problems)

    print("\nWhere each part applies:")
    walk(PRECINCTS, "", haystack, problems, seen)

    print("\nPart A framing (A.1-A.3) and Part B framing (B.1-B.4):")
    walk(PART_A_FRAME, "", haystack, problems, seen)
    walk(PART_B_FRAME, "", haystack, problems, seen)

    print("\nPart A controls:")
    for key, entry in PART_A.items():
        walk(entry, key, haystack, problems, seen)

    print("\nTable B1:")
    walk(TABLE_B1, "", haystack, problems, seen)

    print("\nA10 separation table, row by row:")
    walk(SEPARATION_TABLE, "", haystack, problems, seen)
    header = normalise(SEPARATION_TABLE["columns_verbatim"])
    for row in SEPARATION_TABLE["rows"]:
        row_text = normalise(" ".join(row.values()))
        if f"{header} {row_text}" in haystack:
            print(f"  ✓ {row_text} (in that order, under that header)")
        else:
            problems.append(f"separation row {row_text}")
            print(f"  ✗ {row_text} is not a row of the table as printed")

    print("\nFigures agree with the quotes they were read from:")
    fig_problems = figure_problems(FIGURES, haystack)
    for key in FIGURES:
        bad = [p for p in fig_problems if p.startswith(f"{key}:")]
        print(f"  {'✗' if bad else '✓'} {key}" + (f" — {bad[0]}" if bad else ""))
    problems.extend(fig_problems)

    print("\nClaims recorded as absent really are absent:")
    for key, entry in NOT_SET_BY_THIS_CHAPTER.items():
        hits = [p for p in entry["absent_phrases"] if normalise(p) in haystack]
        if hits:
            problems.append(f"absence {key}")
            print(f"  ✗ {key}: the chapter does contain {hits}")
        else:
            print(f"  ✓ {key}: none of {entry['absent_phrases']}")

    print("\nStructure the chapter has, accounted for:")
    for kind, missing in not_carried().items():
        if missing:
            problems.append(f"not carried {kind}")
            print(f"  ✗ {kind}: {len(missing)} not carried — {', '.join(missing)}")
        else:
            print(f"  ✓ every {kind[:-1].replace('_', ' ')} carried or accounted for")
    for kind, extra in invented_structure().items():
        if extra:
            problems.append(f"invented {kind}")
            print(f"  ✗ {kind}: the data claims {', '.join(extra)}, which the chapter does "
                  "not have")

    found = headings()
    print(f"\n{len(seen)} stored quote(s) and {len(FIGURES)} figure(s) checked against "
          f"{len(set(found['sections']))} sections, {len(set(found['subheadings']))} "
          f"subheadings and {len(set(found['table_labels']))} Table B1 labels; "
          f"{len(problems)} problem(s).")
    if problems:
        print("\nA mismatch means either the chapter was reissued or the transcription drifted.\n"
              "Read the chapter before editing — do not adjust the stored text to make this\n"
              "pass.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
