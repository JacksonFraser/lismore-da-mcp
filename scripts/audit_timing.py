#!/usr/bin/env python3
"""Check the assessment-period provisions against the EP&A Regulation 2021.

PLAN.md item 2.5, and the fourth of these. Every quote in `data/timing.py` is
verbatim from `documents/legislation/epa-regulation-2021-assessment-periods.txt`
and must still appear in it.

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

    print(f"\n{checked} quote(s) checked, {problems} not matching the regulation.")
    if problems:
        print("\nThis text is fetched from legislation.nsw.gov.au, so a mismatch most likely\n"
              "means the regulation was amended. Read the current provision before editing —\n"
              "do not adjust the stored text to make this pass.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
