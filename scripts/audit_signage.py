#!/usr/bin/env python3
"""Check the signage standards against DCP Chapter 9.

PLAN.md item 2.3, and the third of these after `audit_parking_rates.py` and
`audit_zone_tables.py`. Chapter 9's controls are prose scattered under per-sign
headings rather than a table, so there is nothing to diff structurally: each
definition, standard and provision is stored **verbatim** in `data/signage.py`
and this checks the stored string still appears in the document.

That catches a reissued chapter, an amended control, and — the reason this was
written before the tool that uses the data — a transcription that quietly
paraphrases the source. It cannot catch a sign type the chapter defines that we
never carried, so it reports those too.

    .venv/bin/python scripts/audit_signage.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTER = ROOT / "documents" / "dcp" / "chapter-9-signage.pdf"


def chapter_text() -> str:
    import fitz

    with fitz.open(CHAPTER) as doc:
        pages = [doc[i].get_text() for i in range(doc.page_count)]
    return " ".join(" ".join(p.split()) for p in pages)


def normalise(text: str) -> str:
    """Compare on wording, not typography.

    The chapter uses m2 for m², curly apostrophes, and an en dash inside
    "A – frame" with spaces around it. None of those change the control.
    """
    text = text.replace("m²", "m2").replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    return " ".join(text.lower().split())


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.data.signage import (
        APPLICATION_REQUIREMENTS, DESIGN_GUIDELINES, EXISTING_USE_RIGHTS,
        ROAD_RESERVE, SEPP_PROHIBITED_ZONES, SIGNAGE)

    if not CHAPTER.exists():
        print(f"missing {CHAPTER}")
        return 2

    haystack = normalise(chapter_text())
    problems = 0

    print("Sign types (definition and standard, DCP Chapter 9):")
    for key, entry in sorted(SIGNAGE.items()):
        for field in ("definition", "standard"):
            value = entry.get(field)
            if not value:
                continue
            if normalise(value) in haystack:
                print(f"  ✓ {key:24} {field}")
            else:
                problems += 1
                print(f"\n  ✗ {key:24} {field}")
                print(f"      stored: {value[:110]}")
                anchor = normalise(entry["dcp_name"].split("(")[0])
                found = re.search(re.escape(anchor) + r"(.{0,160})", haystack)
                print(f"      near '{anchor}': "
                      f"{found.group(1).strip() if found else 'name not found'}")

    print("\nGeneral provisions:")
    provisions = {
        "9.2 prohibited zones intro": SEPP_PROHIBITED_ZONES["verbatim_intro"],
        "9.2 exceptions": SEPP_PROHIBITED_ZONES["exceptions_verbatim"],
        "9.5 applications": APPLICATION_REQUIREMENTS["verbatim"],
        "9.5 plans": APPLICATION_REQUIREMENTS["plans_verbatim"],
        "9.5 not a separate DA": APPLICATION_REQUIREMENTS["not_a_separate_da"],
        "9.6 existing use rights": EXISTING_USE_RIGHTS["verbatim"],
        "9.7 duration": APPLICATION_REQUIREMENTS["duration_verbatim"],
        "9.8 road reserve": ROAD_RESERVE["verbatim"],
    }
    for label, quote in provisions.items():
        if normalise(quote) in haystack:
            print(f"  ✓ {label}")
        else:
            problems += 1
            print(f"  ✗ {label}")
            print(f"      stored: {quote[:110]}")

    print("\n§9.2 prohibited zones, item by item:")
    for zone in SEPP_PROHIBITED_ZONES["zones"]:
        if normalise(zone) in haystack:
            print(f"  ✓ {zone}")
        else:
            problems += 1
            print(f"  ✗ {zone}")

    print("\n§9.4 design guidelines:")
    for name, text in DESIGN_GUIDELINES["guidelines"].items():
        if normalise(text) in haystack:
            print(f"  ✓ {name}")
        else:
            problems += 1
            print(f"  ✗ {name}")
            print(f"      stored: {text[:110]}")

    # A sign type the chapter defines but we do not carry is a gap, not an
    # error — but it should be visible rather than discovered by a user.
    #
    # Matched on the term §9.3 itself defines rather than on our display name,
    # which differs from the chapter in two places on purpose: the chapter
    # spells it "fascia" in §9.3 and "Facia" in the §9.11 heading, and
    # "free standing" against "Freestanding". Comparing display names reported
    # both as missing when both are carried.
    defined = {d.strip() for d in re.findall(r"([a-z/ ]+?) means a sign", haystack)}
    carried = {normalise(e["definition"]).split(" means ")[0]
               for e in SIGNAGE.values() if e.get("definition")}
    missing = sorted(defined - carried)
    if missing:
        print(f"\n  {len(missing)} sign type(s) defined in §9.3 with no entry here:")
        for name in missing:
            print(f"      {name}")

    print(f"\n{len(SIGNAGE)} sign type(s) checked, {problems} not matching the DCP.")
    if problems:
        print("\nA mismatch means either the chapter was reissued or the transcription drifted.\n"
              "Read the chapter before editing — do not adjust the stored text to make this\n"
              "pass.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
