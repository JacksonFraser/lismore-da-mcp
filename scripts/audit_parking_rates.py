#!/usr/bin/env python3
"""Check the parking rates against DCP Chapter 7 Schedule 1.

PLAN.md item 0.3, and the companion to `audit_zone_tables.py`.

Schedule 1 is a three-column table in a PDF, so unlike the LEP's semicolon lists
it cannot be diffed structurally with any confidence — the columns interleave
under text extraction and continuation rows wrap mid-phrase. Rather than pretend
otherwise, `data/parking.py` stores each requirement **verbatim** and this script
checks that each stored string still appears in the document.

That catches what matters: a reissued chapter, an amended rate, or a
transcription that drifts from the source. It does not catch a use we have
never carried, so it also reports Schedule 1 land uses with no entry here.

    .venv/bin/python scripts/audit_parking_rates.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTER = ROOT / "documents" / "dcp" / "chapter-7-off-street-carparking.pdf"
SCHEDULE_FIRST_PAGE = 10          # zero-based; Schedule 1 starts on p11


def schedule_text() -> str:
    import fitz

    with fitz.open(CHAPTER) as doc:
        pages = [doc[i].get_text() for i in range(SCHEDULE_FIRST_PAGE, doc.page_count)]
    return " ".join(" ".join(p.split()) for p in pages)


def normalise(text: str) -> str:
    """Compare on wording, not typography.

    The PDF uses m2 where the transcription may use m², curly apostrophes, and
    en dashes. None of those change the rule.
    """
    text = text.replace("m²", "m2").replace("’", "'").replace("‘", "'")
    text = text.replace("–", "-").replace("—", "-")
    return " ".join(text.lower().split())


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.data.parking import PARKING_RATES

    if not CHAPTER.exists():
        print(f"missing {CHAPTER}")
        return 2

    haystack = normalise(schedule_text())
    problems = 0
    unsourced = []

    for key, entry in sorted(PARKING_RATES.items()):
        if entry.get("dcp_use") is None:
            unsourced.append(key)
            continue
        needle = normalise(entry["rate"])
        if needle in haystack:
            print(f"  ✓ {key:26} {entry['dcp_use']}")
        else:
            problems += 1
            print(f"\n  ✗ {key:26} {entry['dcp_use']}")
            print(f"      stored: {entry['rate'][:110]}")
            # Show what the schedule says near the land use name, to make the
            # difference diagnosable rather than just reported.
            anchor = normalise(entry["dcp_use"].split("—")[0])
            found = re.search(re.escape(anchor) + r"(.{0,140})", haystack)
            print(f"      near '{anchor}': {found.group(1).strip() if found else 'name not found'}")

    if unsourced:
        print(f"\n  {len(unsourced)} entr(ies) with no Schedule 1 land use, by design:")
        for key in unsourced:
            print(f"      {key} — {PARKING_RATES[key]['rate']}")

    print(f"\n{len(PARKING_RATES)} entr(ies) checked, {problems} not matching the DCP.")
    if problems:
        print("\nA mismatch means either the chapter was reissued or the transcription drifted.\n"
              "Read the schedule before editing — do not adjust the stored text to make this\n"
              "pass.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
