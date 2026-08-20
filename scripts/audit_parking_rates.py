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
never carried — so `check_completeness` isolates Schedule 1's land use column
from the PDF by x-position and reports every row with no entry in the data.

**That check did not exist until 2026-08-20, and this docstring claimed it did.**
The audit printed "27 entries checked, 0 not matching" while `Shop top housing`
was absent from `data/parking.py` altogether, so a CBD business was told to use
`Shop (individual)` at 4.4 spaces per 100m² against a Schedule 1 entry reading
"CBD (defined in Map 1) - No carparking requirements". Reading a docstring is not
verifying a claim (SCENARIOS.md D8, and `ROADMAP.md`'s *What is already fine*,
which had credited this file on exactly that basis).

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


def chapter_text() -> str:
    """The whole chapter, for the §7.x provisions that sit before Schedule 1."""
    import fitz

    with fitz.open(CHAPTER) as doc:
        pages = [doc[i].get_text() for i in range(doc.page_count)]
    return " ".join(" ".join(p.split()) for p in pages)


def normalise(text: str) -> str:
    """Compare on wording, not typography.

    The PDF uses m2 where the transcription may use m², curly apostrophes, and
    en dashes. None of those change the rule.
    """
    text = text.replace("m²", "m2").replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    return " ".join(text.lower().split())


# Schedule 1's land use column, read off the document.
#
# The docstring above has claimed since this file was written that it "also
# reports Schedule 1 land uses with no entry here". **It did not** — there was no
# such code, and the audit printed "27 entries checked, 0 not matching" while
# `Shop top housing` was missing from `data/parking.py` entirely. A CBD business
# asking about it was told to use `Shop (individual)` at 4.4 per 100m², against a
# Schedule 1 entry reading "CBD (defined in Map 1) - No carparking requirements".
# SCENARIOS.md D8.
#
# This list is hand-read, but it is not taken on trust: `land_use_column()`
# extracts the table's left column from the PDF by x-position and
# `check_completeness` fails if any name below is absent from it. So the list
# cannot drift into fiction, and a reissued schedule breaks the audit rather than
# passing quietly.
SCHEDULE_1_LAND_USES = [
    "Amusement centre", "Animal boarding or training establishment",
    "Bed and breakfast accommodation", "Boarding house", "Bulky goods premises",
    "Business premises (other than funeral homes)", "Caravan park", "Child care centre", "Community facility",
    "Correctional centre", "Dual occupancy", "Dwelling house", "Eco-tourist facility",
    "Educational establishment", "Electricity generating works", "Entertainment facility",
    "Environmental facility", "Exhibition home", "Extractive industry",
    "Farm stay accommodation", "Freight transport facility", "Function centre",
    "Funeral home", "Home industry", "Hospital", "Hostel", "Hotel or motel accommodation",
    "Information and education facility", "Intensive livestock agriculture",
    "Landscaping material supplies", "Liquid fuel depot", "Livestock processing industry",
    "Marina", "Market", "Medical centre", "Mine", "Mortuary", "Multi dwelling housing",
    "Neighbourhood shop", "Office premises", "Passenger transport facility",
    "Place of public worship", "Pub", "Public administration building", "Recreation area",
    "Recreation facility (indoor)", "Recreation facility (major)",
    "Recreation facility (outdoor)", "Registered club", "Residential flat building",
    "Respite day care centre", "Restaurant or cafe", "Restricted premises",
    "Rural industry", "Rural worker's dwelling", "Sawmill or log processing works",
    "Self-storage units", "Service station", "Sex services premises",
    "Shop (liquor outlet)", "Shop (individual)", "Shop top housing", "Stock and sale yard",
    "Telecommunications facility", "Temporary use of land", "Transport depot",
    "Vehicle body repair workshop", "Vehicle repair station",
    "Vehicle sales or hire premises", "Veterinary hospital",
    "Warehouse or distribution centre", "Waste or resource transfer station",
]

# Schedule 1 entries this server does not carry a rate for, as at 2026-08-20.
#
# A baseline, not a tolerance — `tests/test_parking_rates.py` asserts it exactly,
# so adding a rate means removing its name here in the same commit, and a use
# appearing in a reissued Schedule 1 shows up as an unexplained gap rather than
# silence. Most of these are uses no Lismore business asks this server about
# (mines, correctional centres, livestock processing); the point is not that they
# should all be carried, it is that the number is visible.
UNCARRIED_SCHEDULE_1_USES = {
    "Amusement centre", "Animal boarding or training establishment",
    "Bed and breakfast accommodation", "Community facility",
    "Correctional centre", "Eco-tourist facility", "Educational establishment",
    "Electricity generating works", "Entertainment facility", "Environmental facility",
    "Exhibition home", "Extractive industry", "Farm stay accommodation",
    "Freight transport facility", "Funeral home", "Home industry", "Hospital", "Hostel",
    "Information and education facility", "Intensive livestock agriculture",
    "Landscaping material supplies", "Liquid fuel depot", "Livestock processing industry",
    "Marina", "Market", "Mine", "Mortuary", "Passenger transport facility",
    "Pub", "Public administration building", "Recreation area", "Recreation facility (indoor)",
    "Recreation facility (major)", "Recreation facility (outdoor)", "Registered club",
    "Respite day care centre", "Restricted premises", "Rural industry",
    "Rural worker's dwelling", "Sawmill or log processing works", "Self-storage units",
    "Sex services premises", "Shop (liquor outlet)", "Stock and sale yard",
    "Telecommunications facility", "Temporary use of land", "Transport depot",
    "Vehicle body repair workshop", "Vehicle sales or hire premises",
    "Veterinary hospital", "Waste or resource transfer station",
}


def land_use_column() -> str:
    """Schedule 1's left-hand column, by x-position rather than by reading order.

    The rate text cannot be diffed structurally — that is why the rates are
    stored verbatim and presence-checked — but the *land use* column can be
    isolated geometrically, which is enough to answer "is there a row here with
    no entry in our data".
    """
    import fitz

    lines = []
    with fitz.open(CHAPTER) as doc:
        for index in range(SCHEDULE_FIRST_PAGE, doc.page_count):
            words = [w for w in doc[index].get_text("words") if w[0] < 175]
            rows: dict[int, list] = {}
            for word in words:
                rows.setdefault(round(word[1] / 4), []).append(word)
            for key in sorted(rows):
                lines.append(" ".join(w[4] for w in sorted(rows[key], key=lambda w: w[0])))
    return normalise(" ".join(lines))


def check_completeness(column: str, rates: dict) -> int:
    """Every Schedule 1 land use is either carried or named as not carried."""
    problems = 0

    unverified = [use for use in SCHEDULE_1_LAND_USES if normalise(use) not in column]
    if unverified:
        problems += len(unverified)
        print("\nNot found in Schedule 1's land use column — the list here is wrong, or the "
              "schedule was reissued:")
        for use in unverified:
            print(f"  ✗ {use}")

    carried = {entry["dcp_use"] for entry in rates.values() if entry.get("dcp_use")}
    missing = [use for use in SCHEDULE_1_LAND_USES
               if use not in carried and use not in UNCARRIED_SCHEDULE_1_USES]
    if missing:
        problems += len(missing)
        print("\nIn Schedule 1, no rate in data/parking.py, and not listed as deliberately "
              "uncarried:")
        for use in missing:
            print(f"  ✗ {use}")

    stale = sorted(UNCARRIED_SCHEDULE_1_USES & carried)
    if stale:
        problems += len(stale)
        print("\nListed as uncarried but a rate now exists — remove from "
              "UNCARRIED_SCHEDULE_1_USES:")
        for use in stale:
            print(f"  ✗ {use}")

    print(f"\nSchedule 1 completeness: {len(SCHEDULE_1_LAND_USES)} land uses, "
          f"{len(SCHEDULE_1_LAND_USES) - len(UNCARRIED_SCHEDULE_1_USES)} carried, "
          f"{len(UNCARRIED_SCHEDULE_1_USES)} deliberately not.")
    return problems


def check_provisions(chapter: str) -> int:
    """Presence-check the §7.7.3 CBD provisions, not just Schedule 1.

    Schedule 1 is not the whole chapter, and for the businesses this server is
    for it is not even the operative part: §7.7.3 sets an entirely different
    rate inside the CBD and the mechanisms for dealing with a shortfall. Those
    are transcribed verbatim for the same reason the rates are, so they get the
    same check.
    """
    from lismore_da_mcp.data.parking import CBD_EXPANSION_ALLOWANCE
    from lismore_da_mcp.data.parking import CBD_FIXED_RATE
    from lismore_da_mcp.data.parking import CBD_PARKING_CREDIT
    from lismore_da_mcp.data.parking import CBD_REDUCTIONS
    from lismore_da_mcp.data.parking import COMBINED_USES
    from lismore_da_mcp.data.parking import DISABILITY_PARKING
    from lismore_da_mcp.data.parking import ON_STREET_LOSS

    quotes = {
        "7.7.3.1 fixed CBD rate": CBD_FIXED_RATE["verbatim"],
        "7.7.3.1 residential exception": CBD_FIXED_RATE["exclusion_verbatim"],
        "7.7.3.1(iii) expansion allowance": CBD_EXPANSION_ALLOWANCE["verbatim"],
        "7.7.3.2 shared parking": CBD_REDUCTIONS["shared"]["verbatim"],
        "7.7.3.2 ordering note": CBD_REDUCTIONS["shared"]["ordering"],
        "7.7.3.3 contribution in lieu": CBD_REDUCTIONS["consolidated"]["verbatim"],
        "7.7.3.4 parking credit formula": CBD_PARKING_CREDIT["verbatim"],
        "7.7.3.4 evidenced alternative": CBD_PARKING_CREDIT["evidenced_alternative"],
        "7.7.2 combined uses": COMBINED_USES["verbatim"],
        "7.7.2 on-street loss": ON_STREET_LOSS["outside_cbd"],
        "7.7.3.5 on-street debit": ON_STREET_LOSS["in_cbd"],
        "7.7.1 accessible parking": DISABILITY_PARKING["verbatim"],
    }

    print("\nCBD provisions (§7.7.1–7.7.3.5):")
    problems = 0
    for label, quote in quotes.items():
        if normalise(quote) in chapter:
            print(f"  ✓ {label}")
        else:
            problems += 1
            print(f"  ✗ {label}")
            print(f"      stored: {quote[:110]}")
    return problems


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

    problems += check_provisions(normalise(chapter_text()))
    problems += check_completeness(land_use_column(), PARKING_RATES)

    print(f"\n{len(PARKING_RATES)} entr(ies) checked, {problems} not matching the DCP.")
    if problems:
        print("\nA mismatch means either the chapter was reissued or the transcription drifted.\n"
              "Read the schedule before editing — do not adjust the stored text to make this\n"
              "pass.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
