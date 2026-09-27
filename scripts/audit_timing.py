#!/usr/bin/env python3
"""Check the assessment-period provisions against the EP&A Regulation 2021.

PLAN.md item 2.5, and the fourth of these. Every quote in `data/timing.py` is
verbatim from `documents/legislation/epa-regulation-2021-assessment-periods.txt`
and must still appear in it.

It also reads every subsection of Part 4 Division 4 — the assessment-period
provisions, ss91-95 — off the source and fails on any that is neither quoted in
the data nor named in `DIVISION_4_NOT_CARRIED` with a reason. A presence check
only looks at what is stored, so on its own it cannot see a period or a limit an
amendment *inserts*, and that is the amendment this audit exists to catch. The
subsection numbers are read off the document, never listed here, the way
`audit_readiness.py` reads the s39(1) paragraph letters. And each quote is
checked against the subsection its `clause` names, not merely the whole text, so
a quote filed under the wrong subsection is reported too.

This one guards something the others do not. That regulation text was fetched
from legislation.nsw.gov.au rather than being a Council PDF, so it can be
re-fetched and silently change when the regulation is amended — and the periods
and the 25-day limit are exactly the sort of thing an amendment moves. A quote
that stops matching means the law changed, not that the transcription slipped.

    .venv/bin/python scripts/audit_timing.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "documents" / "legislation" / "epa-regulation-2021-assessment-periods.txt"


def normalise(text: str) -> str:
    """Compare on wording, not typography.

    The regulation puts each paragraph of a list on its own line, so "if—(a) the
    application" renders as "if—\\n(a)  the application" and collapses to
    "if— (a) the application". Whether there is a space after the em dash is an
    artefact of the source's line breaks, not part of the provision, so both
    sides are flattened — the same allowance `audit_parking_rates.py` makes for
    m² against m2. The words themselves are still compared exactly.
    """
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = " ".join(text.lower().split())
    return text.replace("— ", "—")


def walk(node, path=""):
    """Every ('label', quote) pair under a nested dict or list of dicts."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "verbatim" and isinstance(value, str):
                yield path or "(root)", value
            else:
                yield from walk(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from walk(value, f"{path}[{i}]")


# The Division's heading, as it appears in the body (the table of contents
# carries the same words, so the body is the occurrence followed by section 91).
DIVISION_4 = re.compile(
    r"^Division 4 Time for determining development applications[^\n]*\n(?=\d)", re.MULTILINE)
DIVISION_END = re.compile(r"^(?:Division|Part) \d", re.MULTILINE)
SECTION = re.compile(r"^(\d+[A-Z]?) +\S")
SUBSECTION = re.compile(r"^\((\d+[A-Z]?)\) ")


def division_4_subsections(text: str) -> dict[str, str]:
    """{'s91(1)': text, ...} for every subsection of Part 4 Division 4 in the source.

    Read while the line breaks are still there, since a subsection can only be
    told from a paragraph by starting a line. A section with no subsections is
    keyed by its number alone. Paragraph lines — (a), (b) — belong to the
    subsection above them.
    """
    text = text.replace("\xa0", " ")
    start = DIVISION_4.search(text)
    if start is None:
        return {}
    end = DIVISION_END.search(text, start.end())
    body = text[start.end():end.start() if end else len(text)]

    found: dict[str, list[str]] = {}
    section = key = None
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        if SECTION.match(line):
            section = SECTION.match(line).group(1)
            key = f"s{section}"
            found[key] = []
            continue
        if section and (m := SUBSECTION.match(line)):
            if found.get(f"s{section}") == []:
                del found[f"s{section}"]     # the section has subsections
            key = f"s{section}({m.group(1)})"
            found[key] = []
        if key:
            found[key].append(line)
    return {k: " ".join(v) for k, v in found.items()}


def quoted_clauses(node):
    """Every (clause, quote) pair the data stores together in one dict."""
    if isinstance(node, dict):
        if isinstance(node.get("verbatim"), str) and isinstance(node.get("clause"), str):
            yield node["clause"], node["verbatim"]
        for value in node.values():
            yield from quoted_clauses(value)
    elif isinstance(node, list):
        for value in node:
            yield from quoted_clauses(value)


def division_4_problems(raw: str, groups: dict, not_carried: dict[str, str]) -> list[str]:
    """Subsections of ss91-95 neither carried nor explained, and quotes misfiled.

    Returns human-readable problems; empty means complete.
    """
    subsections = division_4_subsections(raw)
    if not subsections:
        return ["Part 4 Division 4 not found in the source — the heading or layout changed"]
    sections = {k.split("(")[0] for k in subsections}

    problems = []
    carried: set[str] = set()
    for name, group in groups.items():
        for clause, quote in quoted_clauses(group):
            if clause.split("(")[0] not in sections:
                continue
            carried.add(clause)
            if clause not in subsections:
                problems.append(f"{name}: cites {clause}, which Division 4 does not have")
            elif normalise(quote) not in normalise(subsections[clause]):
                problems.append(f"{name}: the quote filed under {clause} is not in {clause}")

    for clause in sorted(set(subsections) - carried - set(not_carried)):
        problems.append(f"{clause} is in the regulation but neither quoted nor named in "
                        f"DIVISION_4_NOT_CARRIED: {subsections[clause][:100]}")
    for clause in sorted(set(not_carried) - set(subsections)):
        problems.append(f"DIVISION_4_NOT_CARRIED names {clause}, which Division 4 does not have")
    for clause in sorted(set(not_carried) & carried):
        problems.append(f"{clause} is both quoted and named in DIVISION_4_NOT_CARRIED")
    for clause, reason in not_carried.items():
        if not reason.strip():
            problems.append(f"DIVISION_4_NOT_CARRIED[{clause}] gives no reason")
    return problems


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.data import timing

    if not SOURCE.exists():
        print(f"missing {SOURCE}")
        print("Run: .venv/bin/python scripts/fetch_epa_regulation.py")
        return 2

    haystack = normalise(SOURCE.read_text())
    problems = 0

    groups = {
        "ASSESSMENT_PERIODS": timing.ASSESSMENT_PERIODS,
        "WHAT_THE_PERIOD_ACTUALLY_IS": timing.WHAT_THE_PERIOD_ACTUALLY_IS,
        "CLOCK_START": timing.CLOCK_START,
        "CLOCK_STOPS": timing.CLOCK_STOPS,
        "INFORMATION_REQUESTS": timing.INFORMATION_REQUESTS,
        "REJECTION": timing.REJECTION,
    }

    checked = 0
    for name, group in groups.items():
        print(f"\n{name}:")
        for label, quote in walk(group):
            checked += 1
            if normalise(quote) in haystack:
                print(f"  ✓ {label}")
            else:
                problems += 1
                print(f"  ✗ {label}")
                print(f"      stored: {quote[:120]}")

    # REJECTION keeps two quotes under names the walker does not reach.
    for label, quote in (("REJECTION.grounds", timing.REJECTION["grounds_verbatim"]),
                         ("REJECTION.consequence", timing.REJECTION["consequence_verbatim"])):
        checked += 1
        if normalise(quote) in haystack:
            print(f"  ✓ {label}")
        else:
            problems += 1
            print(f"  ✗ {label}")
            print(f"      stored: {quote[:120]}")

    # The periods are the numbers people act on, so check the figure and the
    # words agree rather than trusting the transcription of either alone.
    print("\nPeriods stated in the quote match the stored number:")
    for key, entry in timing.ASSESSMENT_PERIODS.items():
        if re.search(rf"\b{entry['days']} days\b", entry["verbatim"]):
            print(f"  ✓ {key:26} {entry['days']} days")
        else:
            problems += 1
            print(f"  ✗ {key:26} stored {entry['days']} but the quote does not say so")

    # Completeness: every subsection of the assessment-period Division.
    raw = SOURCE.read_text()
    print("\nEvery subsection of Part 4 Division 4 (ss91-95) is carried or explained:")
    division = division_4_subsections(raw)
    found = division_4_problems(raw, groups, timing.DIVISION_4_NOT_CARRIED)
    for problem in found:
        print(f"  ✗ {problem}")
    problems += len(found)
    if not found:
        quoted = len(division) - len(timing.DIVISION_4_NOT_CARRIED)
        print(f"  ✓ {len(division)} subsections: {quoted} quoted, "
              f"{len(timing.DIVISION_4_NOT_CARRIED)} named with a reason")

    print(f"\n{checked} quote(s) checked, {problems} not matching the regulation.")
    if problems:
        print("\nThis text is fetched from legislation.nsw.gov.au, so a mismatch most likely\n"
              "means the regulation was amended. Read the current provision before editing —\n"
              "do not adjust the stored text to make this pass.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
