#!/usr/bin/env python3
"""Check the interpretation register against the documents it quotes.

ROADMAP.md B1. `data/interpretations.py` records the readings this repository
has taken where a source admits more than one. The readings themselves cannot
be audited — whether Council agrees is what ROADMAP.md B2's planner review is
for — but the provisions they are readings *of* can, and a register that
misquotes the words it is interpreting is worse than none: the planner reviewing
it would be arguing about text that is not in the document.

Three checks:

**Presence, on the page.** Every `verbatim` string must appear in its source
document — and where the entry names a PDF page, on that page. The page check
is what lets a reviewer turn straight to the provision, and it catches a quote
lifted from the wrong section (the same phrase recurs across Chapter 7).

**Shape.** Every field B2 needs is present and non-empty, `if_wrong_this_tool`
and `planner_review` take one of their stated values, and keys are unique.

**Links resolve.** Every `duty_planner_question` names a real entry in
`DUTY_PLANNER_QUESTIONS`, and every tool in `relied_on_by` is a registered tool.
A link to nothing reads exactly like a link that works.

    .venv/bin/python scripts/audit_interpretations.py
"""

from __future__ import annotations

import sys
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

REQUIRED_FIELDS = (
    "key", "topic", "in_one_line", "provision", "reading", "alternative",
    "why_this_one", "cost_if_council_disagrees", "if_wrong_this_tool",
    "relied_on_by", "planner_review",
)


def normalise(text: str) -> str:
    """Compare on wording, not typography.

    The union of what the other audits allow: curly quotes, en and em dashes
    (Chapter 8 prints "A fifth category – CBD Flood Liable"), m² against m2, and
    the private-use bullet glyphs Chapter 9 prints before each list item.
    Whitespace is collapsed, so a line break in a PDF or the LEP text is not a
    difference. The words are still compared exactly.
    """
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("m²", "m2")
    text = "".join(ch for ch in text if not 0xE000 <= ord(ch) <= 0xF8FF)
    return " ".join(text.lower().split())


@cache
def pdf_pages(source: str) -> tuple[str, ...]:
    import fitz

    with fitz.open(ROOT / source) as doc:
        return tuple(normalise(page.get_text()) for page in doc)


@cache
def document_text(source: str) -> str:
    """The whole document, normalised. PDF pages are joined with a space."""
    if source.endswith(".pdf"):
        return " ".join(pdf_pages(source))
    return normalise((ROOT / source).read_text(encoding="utf-8", errors="replace"))


def quote_findings(entries: list[dict]) -> list[str]:
    problems = []
    for entry in entries:
        for i, quote in enumerate(entry.get("provision") or []):
            label = f"{entry['key']}.provision[{i}] ({quote.get('where')})"
            source = quote.get("source", "")
            if not (ROOT / source).exists():
                problems.append(f"{label}: source {source!r} does not exist")
                continue
            needle = normalise(quote.get("verbatim", ""))
            if not needle:
                problems.append(f"{label}: empty verbatim")
                continue
            page = quote.get("page")
            if page is not None:
                if not source.endswith(".pdf"):
                    problems.append(f"{label}: a page is given but {source} is not a PDF")
                    continue
                pages = pdf_pages(source)
                if not 1 <= page <= len(pages):
                    problems.append(f"{label}: page {page} is outside {source}")
                elif needle not in pages[page - 1]:
                    found = [n + 1 for n, text in enumerate(pages) if needle in text]
                    problems.append(
                        f"{label}: not on page {page} of {source}"
                        + (f" (found on page {found})" if found else " (not in the document)"))
            elif needle not in document_text(source):
                problems.append(f"{label}: not found in {source}")
    return problems


def shape_findings(entries: list[dict]) -> list[str]:
    from lismore_da_mcp.data.interpretations import DIRECTIONS, REVIEW_STATES

    problems = []
    seen = set()
    for entry in entries:
        key = entry.get("key", "(no key)")
        if key in seen:
            problems.append(f"{key}: duplicate key")
        seen.add(key)
        for field in REQUIRED_FIELDS:
            if not entry.get(field):
                problems.append(f"{key}: missing {field}")
        if "duty_planner_question" not in entry:
            problems.append(f"{key}: missing duty_planner_question (None where there is none)")
        if entry.get("if_wrong_this_tool") not in DIRECTIONS:
            problems.append(f"{key}: if_wrong_this_tool must be one of {DIRECTIONS}")
        if entry.get("planner_review") not in REVIEW_STATES:
            problems.append(f"{key}: planner_review must be one of {REVIEW_STATES}")
        for i, quote in enumerate(entry.get("provision") or []):
            for field in ("source", "where", "verbatim"):
                if not quote.get(field):
                    problems.append(f"{key}.provision[{i}]: missing {field}")
    return problems


def link_findings(entries: list[dict]) -> list[str]:
    from lismore_da_mcp.data.readiness import DUTY_PLANNER_QUESTIONS
    import lismore_da_mcp.server  # noqa: F401 — registers every tool
    from lismore_da_mcp.registry import registered

    questions = {q["key"] for q in DUTY_PLANNER_QUESTIONS}
    tools = set(registered())
    problems = []
    for entry in entries:
        question = entry.get("duty_planner_question")
        if question is not None and question not in questions:
            problems.append(f"{entry['key']}: duty_planner_question {question!r} does not exist")
        for name in entry.get("relied_on_by") or []:
            if name not in tools:
                problems.append(f"{entry['key']}: relied_on_by names unknown tool {name!r}")
    return problems


def main() -> int:
    from lismore_da_mcp.data.interpretations import INTERPRETATIONS

    quotes = sum(len(e.get("provision") or []) for e in INTERPRETATIONS)
    groups = [
        ("QUOTES NOT FOUND WHERE THE REGISTER SAYS", quote_findings(INTERPRETATIONS)),
        ("ENTRIES MISSING WHAT THE PLANNER REVIEW NEEDS", shape_findings(INTERPRETATIONS)),
        ("LINKS TO NOTHING", link_findings(INTERPRETATIONS)),
    ]

    print(f"{len(INTERPRETATIONS)} interpretation(s), {quotes} quoted provision(s) checked")
    for entry in INTERPRETATIONS:
        print(f"  {entry['planner_review']:<11} {entry['if_wrong_this_tool']:<12} {entry['key']}")

    total = 0
    for heading, problems in groups:
        if not problems:
            continue
        total += len(problems)
        print(f"\n{heading} — {len(problems)}")
        for problem in problems:
            print(f"  {problem}")

    print(f"\n{total} problem(s)." if total else "\nAll checks pass.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
