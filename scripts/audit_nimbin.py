#!/usr/bin/env python3
"""Check the Nimbin Village chapter data against DCP Part B Chapter 6.

ROADMAP D3. `data/nimbin.py` is a fresh transcription, which is the activity
that produced every invented figure this repository has had to remove — so this
checks four directions rather than one:

  1. **Presence.** Every stored quote still appears in the chapter (and the
     three quotes from the DCP Introduction appear in it).
  2. **Completeness, read off the document.** Every numbered section heading in
     the body is cited by the data or named in `SECTIONS_NOT_CARRIED`; every
     precinct's "Preferred land uses" list matches the data item for item, in
     both directions; every Live / Work criterion label (P1, A1.1, ...) is
     carried; and every figure the chapter prints with a unit (45,000 litres,
     1m, 750-1400mm, ...) is inside a stored quote at each place it occurs, or
     named in `FIGURES_NOT_CARRIED`.
  3. **No invention.** A figure with a unit in the data's *guidance* text —
     anything that is not a quote — must be one the chapter prints.
  4. **Recorded absences.** Each pattern in `NOT_SET_BY_THIS_CHAPTER` must still
     be absent from the chapter, because a presence check cannot see an
     invented height limit or parking rate.

    .venv/bin/python scripts/audit_nimbin.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lismore_da_mcp.data import nimbin  # noqa: E402

CHAPTER_PDF = ROOT / nimbin.SOURCE_DOC
INTRODUCTION_PDF = ROOT / nimbin.INTRODUCTION_DOC

BODY_FIRST_PAGE = 2              # zero-based: p3. Pp1-2 are the cover and contents.
RUNNING_HEADER = re.compile(r"^\s*(Lismore Development Control Plan – Part B.*|Page \d+)\s*$")
BULLETS = ("•", "", "")
FIGURE = re.compile(
    r"\d[\d,]*(?:\.\d+)?(?:\s?-\s?\d[\d,]*)?\s?(?:m2|mm|m|metres?|litres|%)(?![a-z])|¼ acre")
# A heading is a number alone on its line ('2.4', title on the next line) or a
# dotted number with its title ('2.1.1 South of Sibley Street'). An undotted
# number with text after it is a street address ('7 Sibley Street is ...').
HEADING = re.compile(r"^(\d+(?:\.\d+)*)$|^(\d+(?:\.\d+)+)\s+(\S.*)$")
LIVE_WORK_LABEL = re.compile(r"^([PA]\d+(?:\.\d+)?) \S")


def normalise(text: str) -> str:
    """Compare on wording, not typography or layout."""
    for bullet in BULLETS:
        text = text.replace(bullet, " ")
    text = text.replace("’", "'").replace("‘", "'")
    return " ".join(text.lower().split())


def body_lines(pdf: Path = CHAPTER_PDF) -> list[str]:
    """The chapter body line by line, without the running header and page number."""
    import fitz

    with fitz.open(pdf) as doc:
        lines = []
        for index in range(BODY_FIRST_PAGE, doc.page_count):
            lines += [line for line in doc[index].get_text().splitlines()
                      if not RUNNING_HEADER.match(line)]
    return lines


def joined(lines: list[str]) -> str:
    """The body as one normalised string. A word hyphenated across a line break
    ('on-' / 'site', 'co-' / 'ordinated') is rejoined as the hyphenated word."""
    text = ""
    for line in lines:
        if re.search(r"[a-z]-\s*$", text):
            text = text.rstrip() + line.lstrip()
        else:
            text = f"{text} {line}"
    return normalise(text)


def document_text(pdf: Path) -> str:
    import fitz

    with fitz.open(pdf) as doc:
        return normalise(" ".join(page.get_text() for page in doc))


# --------------------------------------------------------------------------
# What the data stores
# --------------------------------------------------------------------------

def quotes(node=None, path: str = "") -> list[tuple[str, str]]:
    """Every (label, quote) in the data: `verbatim` strings, `verbatim_parts`
    elements, and elements of the lists named in QUOTED_LISTS."""
    if node is None:
        found = []
        for name in ("APPLICATION", "RELATIONSHIP_TO_OTHER_PLANS", "DEFINITIONS",
                     "CHAPTER_OBJECTIVES", "WATER_SUPPLY", "PRECINCT_RULES", "PRECINCTS",
                     "FLOOD", "SIGNIFICANT_VEGETATION", "INFRASTRUCTURE"):
            found += quotes(getattr(nimbin, name), name)
        return found
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            label = f"{path}.{key}"
            if key == "verbatim" and isinstance(value, str):
                found.append((path, value))
            elif key == "verbatim_parts":
                found += [(f"{label}[{i}]", part) for i, part in enumerate(value)]
            elif key in nimbin.QUOTED_LISTS and isinstance(value, list):
                found += [(f"{label}[{i}]", item) for i, item in enumerate(value)]
            else:
                found += quotes(value, label)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found += quotes(value, f"{path}[{i}]")
    return found


def guidance(node=None, path: str = "") -> list[tuple[str, str]]:
    """Every string in the data that is *not* a quote — the repository's own words."""
    if node is None:
        found = []
        for name in dir(nimbin):
            if name.isupper() and name not in ("NOT_SET_BY_THIS_CHAPTER", "SOURCE_TEXT_DEFECTS",
                                               "QUOTED_LISTS", "OTHER_VILLAGES"):
                found += guidance(getattr(nimbin, name), name)
        return found
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("verbatim", "verbatim_parts") or key in nimbin.QUOTED_LISTS:
                continue
            found += guidance(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found += guidance(value, f"{path}[{i}]")
    elif isinstance(node, str):
        found.append((path, node))
    return found


def cited_sections() -> set[str]:
    found = set()

    def walk(node):
        if isinstance(node, dict):
            if isinstance(node.get("section"), str):
                found.add(node["section"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for name in dir(nimbin):
        if name.isupper():
            walk(getattr(nimbin, name))
    return found


# --------------------------------------------------------------------------
# What the document holds, read off it
# --------------------------------------------------------------------------

def section_headings(lines: list[str]) -> list[str]:
    """Numbered headings in the body: '2.4' alone on a line with its title on the
    next, or '2.1.1 South of Sibley Street' on one line. A numbered list item
    carries a trailing full stop ('1.') and is not a heading."""
    found = []
    for i, line in enumerate(lines):
        match = HEADING.match(line.strip())
        if not match:
            continue
        number = match.group(1) or match.group(2)
        title = match.group(3)
        if title is None:
            following = next((l.strip() for l in lines[i + 1:i + 3] if l.strip()), "")
            if not following or not following[0].isupper():
                continue
        elif not title[0].isupper():
            continue
        if number not in found:
            found.append(number)
    return found


def preferred_land_use_lists(lines: list[str]) -> list[list[str]]:
    """Each 'Preferred land uses' list in document order, item by item."""
    stops = ("Performance Criteria", "Development standards and guidelines")
    lists, current, collecting = [], None, False
    for line in lines:
        text = line.strip()
        if text == "Preferred land uses":
            current, collecting = [], True
            lists.append(current)
            continue
        if not collecting:
            continue
        if text in stops or HEADING.match(text):
            collecting = False
            continue
        if text == "•":
            current.append("")
        elif text and current:
            current[-1] = f"{current[-1]} {text}".strip()
    return [[item.rstrip(" ,.") for item in found if item] for found in lists]


def live_work_labels(lines: list[str]) -> list[str]:
    """P1, A1.1, ... in the §2.3 table."""
    start = next(i for i, l in enumerate(lines) if l.strip() == "Live / Work Precinct")
    end = next(i for i, l in enumerate(lines) if l.strip() == "Commercial Precinct" and i > start)
    return [m.group(1) for l in lines[start:end] if (m := LIVE_WORK_LABEL.match(l.strip()))]


# --------------------------------------------------------------------------
# The checks
# --------------------------------------------------------------------------

def presence_problems(haystack: str, introduction: str) -> list[str]:
    problems = [f"not in the chapter: {label}: {quote[:90]}"
                for label, quote in quotes() if normalise(quote) not in haystack]
    for key, entry in nimbin.OTHER_VILLAGES.items():
        if isinstance(entry, dict) and normalise(entry["verbatim"]) not in introduction:
            problems.append(f"not in the DCP Introduction: OTHER_VILLAGES.{key}")
    return problems


def heading_problems(lines: list[str]) -> list[str]:
    in_document = section_headings(lines)
    cited = cited_sections()
    named = set(nimbin.SECTIONS_NOT_CARRIED)
    problems = [f"§{h} is in the chapter but neither cited by the data nor named in "
                f"SECTIONS_NOT_CARRIED" for h in in_document if h not in cited | named]
    problems += [f"the data cites §{h}, which the chapter does not have"
                 for h in sorted(cited - set(in_document))]
    problems += [f"SECTIONS_NOT_CARRIED names §{h}, which the chapter does not have"
                 for h in sorted(named - set(in_document))]
    problems += [f"§{h} is both cited and named in SECTIONS_NOT_CARRIED"
                 for h in sorted(named & cited)]
    return problems


def preferred_use_problems(lines: list[str]) -> list[str]:
    """The stored lists, in precinct order, against the document's, item for item."""
    in_document = preferred_land_use_lists(lines)
    stored = [(key, [normalise(u) for u in precinct["preferred_land_uses"]])
              for key, precinct in nimbin.PRECINCTS.items()]
    if len(in_document) != len(stored):
        return [f"the chapter has {len(in_document)} 'Preferred land uses' lists and the data "
                f"{len(stored)}"]
    problems = []
    for (key, carried), printed in zip(stored, in_document):
        printed = [normalise(u) for u in printed]
        for use in printed:
            if use not in carried:
                problems.append(f"{key}: preferred use {use!r} is in the chapter, not the data")
        for use in carried:
            if use not in printed:
                problems.append(f"{key}: preferred use {use!r} is in the data, not the chapter")
    return problems


def live_work_problems(lines: list[str]) -> list[str]:
    printed = live_work_labels(lines)
    carried = list(nimbin.PRECINCTS["live_work"]["criteria"])
    problems = [f"Live / Work {label} is in the chapter, not the data"
                for label in printed if label not in carried]
    problems += [f"Live / Work {label} is in the data, not the chapter"
                 for label in carried if label not in printed]
    return problems


def figure_problems(haystack: str) -> list[str]:
    """Every figure the chapter prints is inside a stored quote where it occurs."""
    stored = [normalise(q) for _label, q in quotes()]
    problems = []
    for match in FIGURE.finditer(haystack):
        window = haystack[max(0, match.start() - 25):match.end()].strip()
        if match.group() in nimbin.FIGURES_NOT_CARRIED:
            continue
        if not any(window in quote for quote in stored):
            problems.append(f"figure {match.group()!r} is not carried where it occurs: "
                            f"...{window}...")
    for figure in nimbin.FIGURES_NOT_CARRIED:
        if figure not in haystack:
            problems.append(f"FIGURES_NOT_CARRIED names {figure!r}, which the chapter does "
                            f"not print")
    return problems


def invention_problems(haystack: str) -> list[str]:
    printed = {m.group() for m in FIGURE.finditer(haystack)}
    return [f"{label} states {m.group()!r}, which the chapter does not print"
            for label, text in guidance() for m in FIGURE.finditer(normalise(text))
            if m.group() not in printed]


def absence_problems(haystack: str) -> list[str]:
    return [f"NOT_SET_BY_THIS_CHAPTER[{key}] is no longer absent: the chapter now matches "
            f"{entry['absent_pattern']!r}"
            for key, entry in nimbin.NOT_SET_BY_THIS_CHAPTER.items()
            if re.search(entry["absent_pattern"], haystack, re.IGNORECASE)]


def main() -> int:
    for pdf in (CHAPTER_PDF, INTRODUCTION_PDF):
        if not pdf.exists():
            print(f"MISSING: {pdf}")
            return 1

    lines = body_lines()
    haystack = joined(lines)
    introduction = document_text(INTRODUCTION_PDF)

    checks = [
        ("Quotes appear in the chapter", presence_problems(haystack, introduction),
         f"{len(quotes())} quotes"),
        ("Every section heading is carried or explained", heading_problems(lines),
         f"{len(section_headings(lines))} headings"),
        ("Every preferred land use list matches", preferred_use_problems(lines),
         f"{sum(len(p['preferred_land_uses']) for p in nimbin.PRECINCTS.values())} uses in "
         f"{len(nimbin.PRECINCTS)} precincts"),
        ("Every Live / Work criterion is carried", live_work_problems(lines),
         f"{len(live_work_labels(lines))} labels"),
        ("Every figure the chapter prints is carried", figure_problems(haystack),
         f"{len(FIGURE.findall(haystack))} occurrences"),
        ("No figure in the guidance is invented", invention_problems(haystack),
         f"{len(guidance())} guidance strings"),
        ("Recorded absences are still absent", absence_problems(haystack),
         f"{len(nimbin.NOT_SET_BY_THIS_CHAPTER)} absences"),
    ]

    failed = 0
    for title, problems, summary in checks:
        print(f"\n{title} ({summary}):")
        if problems:
            failed += len(problems)
            for problem in problems:
                print(f"  ✗ {problem}")
        else:
            print("  ✓")

    print(f"\n{failed} problem(s).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
