#!/usr/bin/env python3
"""Check the waste controls against DCP Chapter 15.

ROADMAP.md D2. Written before `data/waste.py`, for the reason every audit here
now is: the transcriptions this repository made from memory invented figures,
and the only check that has ever caught one is a check that existed first.

Chapter 15 is numbered prose — Objectives, Performance Criteria and Acceptable
Solutions under sections 3.2-4.5, each Acceptable Solution a numbered list —
plus appendices, one of which (Appendix C) is the only table in this repository
that gives a café a number for how much waste it makes. Five checks:

  * **Presence.** Every stored quote still appears in the chapter.
  * **Completeness, counted off the document.** Every numbered section (1. to
    4.5) is read from the PDF's bold spans and must be carried or named in
    `DESCRIPTIVE_SECTIONS`; every appendix heading likewise. For each section
    that sets requirements, the numbered items in the chapter are counted and
    must equal the numbered items carried — fourteen of fifteen reads as
    complete and is not, and the fifteenth in §4.3 is the food waste rule.
  * **Appendix C, rebuilt from geometry.** The generation-rate table is three
    columns that extract out of order, so its rows are rebuilt from each line's
    x and y position and compared with the stored table in both directions. A
    rate filed against the neighbouring premises type passes a presence check.
  * **Figures agree with their quotes**, as in `audit_flood.py`.
  * **Recorded absences are still absent** — no professional is required to
    prepare the plan, no minimum storage room size, no general collection
    frequency. A presence check cannot see an invention.

    .venv/bin/python scripts/audit_waste.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTER = ROOT / "documents" / "dcp" / "chapter-15-waste-minimisation.pdf"

RUNNING_HEADER = re.compile(
    r"Lismore Development Control Plan\s*[-–—]\s*Part A\s*Chapter 15\s*[-–—]\s*Page \d+")
FIRST_BODY_PAGE = 2          # 0-based; pages 1-2 are the cover and contents

# Appendix C's columns, by the x at which each line starts (points). Read off
# the page, 2026-09-27: labels at 80, waste at 258, recyclables at 405.
RATE_COLUMNS = {"label": (70, 250), "waste": (250, 400), "recyclables": (400, 560)}
APPENDIX_C_PAGE = 26         # 0-based
GROUP_GAP = 20               # points; see generation_rates_from_document


def _pages():
    import fitz

    with fitz.open(CHAPTER) as doc:
        return [doc[i].get_text() for i in range(doc.page_count)]


def chapter_text() -> str:
    pages = _pages()[FIRST_BODY_PAGE:]
    return " ".join(" ".join(RUNNING_HEADER.sub(" ", p).split()) for p in pages)


def normalise(text: str) -> str:
    """Compare on wording, not typography.

    Private use bullets, curly quotes, en dashes, m² against m2 and m³ against
    m3, and words hyphenated across a line break.
    """
    text = re.sub("[-•]", " ", text)
    text = text.replace("m²", "m2").replace("m³", "m3")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = " ".join(text.lower().split())
    return re.sub(r"(?<=[a-z])- (?=[a-z])", "-", text)


def headings() -> dict:
    """Numbered sections and appendices, read off the PDF's bold spans."""
    import fitz

    sections, appendices = [], []
    with fitz.open(CHAPTER) as doc:
        for index in range(FIRST_BODY_PAGE, doc.page_count):
            for block in doc[index].get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    spans = [s for s in line["spans"] if s["text"].strip()]
                    if not spans or not spans[0]["flags"] & 16:
                        continue
                    text = "".join(s["text"] for s in spans).strip()
                    if re.fullmatch(r"\d(?:\.\d){0,2}\.?", text):
                        sections.append(text)
                    appendix = re.match(r"Appendix ([A-H]):", text)
                    if appendix:
                        appendices.append(appendix.group(1))
    return {"sections": sections, "appendices": appendices}


def section_slices(haystack: str, numbers: list[str]) -> dict:
    """Each section's normalised text, from its heading to the next heading.

    Headings are found as "<number> <title>" in reading order; the body pages
    carry each exactly once (the contents page is excluded from the haystack).
    """
    from lismore_da_mcp.data.waste import SECTION_TITLES

    positions = []
    cursor = 0
    for number in numbers:
        marker = normalise(f"{number} {SECTION_TITLES[number]}")
        at = haystack.find(marker, cursor)
        if at < 0:
            raise ValueError(f"heading {marker!r} not found after position {cursor}")
        positions.append((number, at, len(marker)))
        cursor = at + len(marker)
    end_of_body = haystack.find(normalise("Appendix A: Site Waste Minimisation"))
    slices = {}
    for i, (number, at, length) in enumerate(positions):
        stop = positions[i + 1][1] if i + 1 < len(positions) else end_of_body
        slices[number] = haystack[at + length:stop]
    return slices


ITEM = re.compile(r"(?:^|(?<=[\s:;,.]))(\d{1,2})\. (?=[a-z'\"(])")


def numbered_items_in(text: str) -> int:
    return len(ITEM.findall(text))


def generation_rates_from_document() -> dict:
    """Appendix C rebuilt from line positions: {label: {"waste": [...], ...}}.

    A row is a waste-column line; its recyclables line and label sit at the
    same height. A waste line with no label beside it continues the row above
    (the pub row has three). A label line with no rate beside it continues the
    label above if it follows within a line's height, and is otherwise a group
    heading ("Food and drink premises/ food shops:").
    """
    import fitz

    with fitz.open(CHAPTER) as doc:
        page = doc[APPENDIX_C_PAGE]
        lines = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = "".join(s["text"] for s in line["spans"]).strip()
                if text:
                    lines.append((round(line["bbox"][1]), round(line["bbox"][0]), text))

    start = next(y for y, _, t in lines if t == "Ongoing Operation")
    body = sorted((y, x, t) for y, x, t in lines
                  if y > start + 40 and not t.startswith(("Lismore Development",
                                                          "Chapter 15")))

    def column(x):
        return next(name for name, (lo, hi) in RATE_COLUMNS.items() if lo <= x < hi)

    rows: dict = {}
    groups: dict = {}
    current = None          # the label currently being continued
    last_label_y = None
    heading = None
    previous_y = None
    for y in sorted({y for y, _, _ in body}):
        if previous_y is not None and y - previous_y <= 2:
            continue        # the same printed line, a point or two off
        at_y = {column(x): t for yy, x, t in body if abs(yy - y) <= 2}
        # A group heading governs the rows packed tightly beneath it. The food
        # shops sit about 17pt apart; the next standalone row is 23pt below the
        # last of them. The gap, not the indent, is what ends the group — every
        # label starts at the same x.
        if heading and previous_y is not None and y - previous_y > GROUP_GAP:
            heading = None
        previous_y = y
        if "label" in at_y and not ({"waste", "recyclables"} & set(at_y)):
            if last_label_y is not None and y - last_label_y <= 14 and current is not None:
                if current == ("heading",):
                    heading = f"{heading} {at_y['label']}"
                else:
                    new = f"{current} {at_y['label']}"
                    rows[new] = rows.pop(current)
                    groups[new] = groups.pop(current)
                    current = new
            else:
                heading = at_y["label"]
                current = ("heading",)
            last_label_y = y
            continue
        if "waste" not in at_y:
            continue
        if "label" in at_y:
            current = at_y["label"]
            rows[current] = {"waste": [], "recyclables": []}
            groups[current] = heading if heading and current != heading else None
            last_label_y = y
        rows[current]["waste"].append(at_y["waste"])
        rows[current]["recyclables"].append(at_y.get("recyclables", ""))
    # A heading applies only to the rows directly beneath it, up to the next row
    # that stands alone; the food shops are the only such group.
    return {"rows": rows, "groups": groups}


def check(label: str, quote: str, haystack: str, problems: list) -> None:
    if normalise(quote) in haystack:
        print(f"  ✓ {label}")
    else:
        problems.append(label)
        print(f"  ✗ {label}")
        print(f"      stored: {quote[:140]}")


COMMENTARY_KEYS = {
    "note", "answer", "the_question", "what_it_means", "applies_to", "source",
    "section", "heading", "page", "unit", "as_written", "value", "absent_phrases",
    "why_not_carried", "stale_references", "key", "group", "premises", "plain",
    "cross_reference", "tool",
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
    elif isinstance(node, str) and len(node) >= 8:
        if node in seen:
            return
        seen.add(node)
        check(path, node, haystack, problems)


def figure_problems(figures: dict, haystack: str) -> list:
    problems = []
    for key, fig in figures.items():
        quote, written, value = fig["quote"], fig["as_written"], fig["value"]
        if normalise(quote) not in haystack:
            problems.append(f"{key}: quote not in the chapter")
            continue
        if normalise(written) not in normalise(quote):
            problems.append(f"{key}: '{written}' is not in its own quote")
            continue
        number = re.search(r"\d+(?:[.,]\d+)?", written)
        words = {"one": 1, "two": 2, "three": 3, "twice": 2}
        parsed = (float(number.group().replace(",", "")) if number
                  else words.get(written.split()[0].lower()))
        if parsed is None or float(parsed) != float(value):
            problems.append(f"{key}: stored {value} but the quote says '{written}'")
    return problems


def carried_numbered() -> dict:
    """Numbered items the data carries, per section."""
    from lismore_da_mcp.data import waste

    counts: dict = {}

    def visit(node):
        if isinstance(node, dict):
            if "section" in node and "numbered" in node:
                total = sum(len(v) for v in node["numbered"].values())
                counts[node["section"]] = counts.get(node["section"], 0) + total
            for value in node.values():
                visit(value)
        elif isinstance(node, (list, tuple)):
            for value in node:
                visit(value)

    for name in waste.__all__:
        visit(getattr(waste, name))
    return counts


def carried_sections() -> set:
    from lismore_da_mcp.data import waste

    found = set(waste.DESCRIPTIVE_SECTIONS)

    def visit(node):
        if isinstance(node, dict):
            if isinstance(node.get("section"), str):
                found.add(node["section"])
            for value in node.values():
                visit(value)
        elif isinstance(node, (list, tuple)):
            for value in node:
                visit(value)

    for name in waste.__all__:
        visit(getattr(waste, name))
    return found


def completeness(haystack: str) -> dict:
    """What the chapter has that the data does not account for, and vice versa."""
    from lismore_da_mcp.data.waste import APPENDICES, COUNTED_SECTIONS

    found = headings()
    sections = set(found["sections"])
    carried = carried_sections()
    slices = section_slices(haystack, found["sections"])
    counted = carried_numbered()
    item_gaps = {}
    for number in COUNTED_SECTIONS:
        in_document = numbered_items_in(slices[number])
        in_data = counted.get(number, 0)
        if in_document != in_data:
            item_gaps[number] = {"document": in_document, "data": in_data}
    uncounted = sorted(n for n in sections
                       if numbered_items_in(slices[n])
                       and n not in COUNTED_SECTIONS and n not in _descriptive_numbered_ok())
    return {
        "sections_not_carried": sorted(sections - carried),
        "sections_invented": sorted(s for s in carried
                                    if re.fullmatch(r"\d(\.\d){0,2}\.?", s) and s not in sections),
        "appendices_not_carried": sorted(set(found["appendices"]) - set(APPENDICES)),
        "appendices_invented": sorted(set(APPENDICES) - set(found["appendices"])),
        "numbered_item_gaps": item_gaps,
        "numbered_sections_not_counted": uncounted,
    }


def _descriptive_numbered_ok() -> set:
    from lismore_da_mcp.data.waste import DESCRIPTIVE_SECTIONS

    return {k for k, v in DESCRIPTIVE_SECTIONS.items() if v.get("lists_are_descriptive")}


def rate_table_problems() -> list:
    from lismore_da_mcp.data.waste import GENERATION_RATES

    document = generation_rates_from_document()
    stored = {normalise(e["premises"]): e for e in GENERATION_RATES.values()}
    problems = []
    for label, cells in document["rows"].items():
        entry = stored.get(normalise(label))
        if entry is None:
            problems.append(f"Appendix C row '{label}' is not carried")
            continue
        for col in ("waste", "recyclables"):
            if [normalise(c) for c in entry[col]] != [normalise(c) for c in cells[col]]:
                problems.append(f"'{label}' {col}: stored {entry[col]}, document {cells[col]}")
        group = document["groups"].get(label)
        if normalise(group or "") != normalise(entry.get("group") or ""):
            problems.append(f"'{label}' group: stored {entry.get('group')!r}, document {group!r}")
    for label in stored:
        if label not in {normalise(k) for k in document["rows"]}:
            problems.append(f"stored row '{label}' is not a row of Appendix C")
    return problems


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.data import waste

    if not CHAPTER.exists():
        print(f"missing {CHAPTER}")
        return 2

    haystack = normalise(chapter_text())
    problems: list = []
    seen: set = set()

    for name in waste.__all__:
        if name in ("FIGURES", "NOT_SET_BY_THIS_CHAPTER", "SECTION_TITLES",
                    "DESCRIPTIVE_SECTIONS", "COUNTED_SECTIONS", "CHAPTER", "SOURCE_PDF"):
            continue
        print(f"\n{name}:")
        walk(getattr(waste, name), name, haystack, problems, seen)

    print("\nSection titles:")
    for number, title in waste.SECTION_TITLES.items():
        check(number, f"{number} {title}", haystack, problems)

    print("\nAppendix C, rebuilt from the page geometry:")
    rate_problems = rate_table_problems()
    for p in rate_problems:
        print(f"  ✗ {p}")
    if not rate_problems:
        print(f"  ✓ all {len(waste.GENERATION_RATES)} rows match, cell by cell, both ways")
    problems.extend(rate_problems)

    print("\nFigures agree with the quotes they were read from:")
    fig_problems = figure_problems(waste.FIGURES, haystack)
    for key in waste.FIGURES:
        bad = [p for p in fig_problems if p.startswith(f"{key}:")]
        print(f"  {'✗' if bad else '✓'} {key}" + (f" — {bad[0]}" if bad else ""))
    problems.extend(fig_problems)

    print("\nClaims recorded as absent really are absent:")
    for key, entry in waste.NOT_SET_BY_THIS_CHAPTER.items():
        hits = [p for p in entry["absent_phrases"] if normalise(p) in haystack]
        if hits:
            problems.append(f"absence {key}")
            print(f"  ✗ {key}: the chapter does contain {hits}")
        else:
            print(f"  ✓ {key}: none of {entry['absent_phrases']}")

    print("\nStructure the chapter has, accounted for:")
    gaps = completeness(haystack)
    for kind, value in gaps.items():
        if value:
            problems.append(kind)
            print(f"  ✗ {kind}: {value}")
        else:
            print(f"  ✓ {kind.replace('_', ' ')}: none")

    found = headings()
    counted = carried_numbered()
    print(f"\n{len(seen)} stored quote(s), {len(waste.FIGURES)} figure(s) and "
          f"{len(waste.GENERATION_RATES)} Appendix C rows checked; "
          f"{len(set(found['sections']))} sections, {len(set(found['appendices']))} appendices "
          f"and {sum(counted.get(n, 0) for n in waste.COUNTED_SECTIONS)} numbered requirements "
          f"accounted for; {len(problems)} problem(s).")
    if problems:
        print("\nA mismatch means either the chapter was reissued or the transcription drifted.\n"
              "Read the chapter before editing — do not adjust the stored text to make this\n"
              "pass.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
