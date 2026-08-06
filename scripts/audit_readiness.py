#!/usr/bin/env python3
"""Check the lodgement and rejection provisions against the EP&A Regulation 2021.

PLAN.md Phase 3, and the sixth of these. Every quote in `data/readiness.py` is
verbatim from `documents/legislation/epa-regulation-2021-assessment-periods.txt`
and must still appear in it.

Same source and same failure mode as `audit_timing.py`, whose comparison this
reuses rather than reimplementing: that regulation text is a fetched snapshot of
legislation.nsw.gov.au, so a quote that stops matching means the law was
amended, not that a transcription slipped. Sections 24, 25, 27, 35B and 39 are
exactly the sort of provision an amendment moves.

It also checks something audit_timing cannot: that every paragraph of s39(1) is
carried. The tool built on this data tells a business what it can be rejected
for, and a list missing a ground is worse than no list — it reads as complete.

    .venv/bin/python scripts/audit_readiness.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_timing import SOURCE, normalise, walk  # noqa: E402

# s39(1) runs (a) to (f). Read off the source rather than hardcoded, so a new
# paragraph inserted by an amendment is reported instead of silently ignored.
GROUNDS_PATTERN = re.compile(r"^\(([a-f])\)\s", re.MULTILINE)
HEADING = re.compile(r"^39\s+Rejection of development applications\s*$", re.MULTILINE)


def section_39_paragraphs(text: str) -> set[str]:
    """The paragraph letters s39(1) actually has in the source text.

    The fetched page separates a provision number from its text with
    non-breaking spaces, which `normalise` flattens along with everything else —
    but the paragraph letters can only be found while the line breaks are still
    there, so they are replaced here rather than normalising the whole text.
    """
    text = text.replace("\xa0", " ")
    heading = HEADING.search(text)
    if heading is None:
        return set()
    start = heading.end()
    end = text.find("For the purposes of the Act, a development application is taken never", start)
    return set(GROUNDS_PATTERN.findall(text[start:end if end > 0 else start + 4000]))


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.data import readiness

    if not SOURCE.exists():
        print(f"missing {SOURCE}")
        print("Run: .venv/bin/python scripts/fetch_epa_regulation.py")
        return 2

    raw = SOURCE.read_text()
    haystack = normalise(raw)
    problems = 0

    groups = {
        "STATUTORY_CONTENT": readiness.STATUTORY_CONTENT,
        "REJECTION_GROUNDS": readiness.REJECTION_GROUNDS,
        "REJECTION_WINDOW": readiness.REJECTION_WINDOW,
    }

    checked = 0
    for group, node in groups.items():
        for path, quote in walk(node):
            checked += 1
            if normalise(quote) not in haystack:
                problems += 1
                print(f"NOT FOUND  {group}.{path}")
                print(f"           {quote[:110]}...")

    print(f"{checked} quote(s) checked against {SOURCE.name}")

    # Every ground the regulation states must be carried, including the ones
    # that cannot apply in Lismore — those are marked, not omitted.
    in_source = section_39_paragraphs(raw)
    carried = {entry["clause"].removeprefix("s39(1)(").removesuffix(")")
               for entry in readiness.REJECTION_GROUNDS.values()}
    missing = in_source - carried
    if missing:
        problems += 1
        print(f"s39(1) paragraph(s) not carried in REJECTION_GROUNDS: {sorted(missing)}")
    extra = carried - in_source
    if extra:
        problems += 1
        print(f"REJECTION_GROUNDS cites s39(1) paragraph(s) not in the source: {sorted(extra)}")
    if not missing and not extra:
        print(f"s39(1)(a)-({max(in_source)}) all carried")

    # The Duty Planner questions are not quotes and cannot be checked against a
    # document — that is the point of them. What can be checked is that each one
    # says why it cannot be answered here, since a question with no such reason
    # is one that should have been answered by a tool instead.
    for entry in readiness.DUTY_PLANNER_QUESTIONS:
        for field in ("question", "why_it_matters", "cost_if_unresolved",
                      "why_we_cannot_answer_it", "applies", "ask_it_as"):
            if not entry.get(field):
                problems += 1
                print(f"DUTY_PLANNER_QUESTIONS[{entry.get('key')}] missing {field}")
    print(f"{len(readiness.DUTY_PLANNER_QUESTIONS)} duty planner question(s) checked")

    print("OK" if not problems else f"{problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
