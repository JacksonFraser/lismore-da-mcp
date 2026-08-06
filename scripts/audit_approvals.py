#!/usr/bin/env python3
"""Check the non-DA approval fees against Council's fees and charges schedule.

PLAN.md item 2.4. Unlike the parking rates and the signage standards, these are
not verbatim quotes — they are prose describing what a business will be charged,
so there is no sentence to search for. What can still be checked is every dollar
figure: each one must appear in the schedule it is cited against.

That is the check that matters, because these figures go stale on a fixed
annual cycle. Council's schedule is reissued every July, and this repo has
already missed that refresh twice (see PLAN.md 0.1). A fee that has moved will
fail here rather than being quoted at a business a year late.

Figures that are deliberately not Council's — the long service levy, a liquor
licence — carry no dollar amount at all and so have nothing to check, which is
the intended state rather than an omission.

    .venv/bin/python scripts/audit_approvals.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEDULE = ROOT / "documents" / "fees" / "fees-and-charges-2026-27.pdf"
DINING_POLICY = ROOT / "documents" / "business" / "nsw-outdoor-dining-policy-2019.pdf"

MONEY = re.compile(r"\$[\d,]+(?:\.\d{2})?")


def pdf_text(path: Path) -> str:
    import fitz

    with fitz.open(path) as doc:
        return " ".join(" ".join(doc[i].get_text().split()) for i in range(doc.page_count))


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.data.approvals import APPROVALS, BY_ACTIVITY, SEQUENCE

    for path in (SCHEDULE, DINING_POLICY):
        if not path.exists():
            print(f"missing {path}")
            return 2

    haystack = pdf_text(SCHEDULE) + " " + pdf_text(DINING_POLICY)
    problems = 0

    print("Fee figures against the source documents:")
    checked = 0
    for key in sorted(APPROVALS):
        entry = APPROVALS[key]
        fee = entry.get("fee")
        if not fee:
            continue
        amounts = MONEY.findall(fee)
        if not amounts:
            # Prose saying the fee is not quotable from here. Intended.
            print(f"  – {key:34} no figure quoted, by design")
            continue
        missing = [a for a in amounts if a not in haystack]
        checked += len(amounts)
        if missing:
            problems += 1
            print(f"\n  ✗ {key:34} {len(missing)} of {len(amounts)} figures not found")
            print(f"      missing: {', '.join(missing)}")
            print(f"      source cited: {entry.get('fee_source', '(none)')}")
        else:
            print(f"  ✓ {key:34} {len(amounts)} figure(s)")

    print("\nStructure:")
    if set(SEQUENCE) != set(APPROVALS):
        problems += 1
        print(f"  ✗ SEQUENCE and APPROVALS disagree — "
              f"only in SEQUENCE: {sorted(set(SEQUENCE) - set(APPROVALS))}; "
              f"only in APPROVALS: {sorted(set(APPROVALS) - set(SEQUENCE))}")
    else:
        print(f"  ✓ SEQUENCE covers all {len(APPROVALS)} approvals exactly once")

    unknown = {k for keys in BY_ACTIVITY.values() for k in keys} - set(APPROVALS)
    if unknown:
        problems += 1
        print(f"  ✗ BY_ACTIVITY references approvals that do not exist: {sorted(unknown)}")
    else:
        print("  ✓ every BY_ACTIVITY reference resolves")

    for key, entry in sorted(APPROVALS.items()):
        if entry.get("fee") and not entry.get("fee_source") and MONEY.search(entry["fee"]):
            problems += 1
            print(f"  ✗ {key} quotes a figure with no fee_source")

    print(f"\n{checked} fee figure(s) checked across {len(APPROVALS)} approvals, "
          f"{problems} problem(s).")
    if problems:
        print("\nCouncil reissues its schedule every July. A missing figure most likely means\n"
              "the refresh has happened — read the new schedule and update the prose, do not\n"
              "adjust this script.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
