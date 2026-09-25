"""Which planning instrument each document belongs to.

Lismore's DCP has parallel chapters for land under LEP 2012 and land still under
LEP 2000. Both sets sit in documents/dcp/ and, until this registry existed,
search returned hits from either with nothing to tell them apart — so a
superseded residential setback could be quoted as current.

LEP 2000 is not repealed. It continues to apply to the areas still under
Ministerial review for the former E2/E3 environmental zones (now C2/C3). For
almost every site LEP 2012 is the applicable instrument, which is why a LEP 2000
hit is flagged rather than hidden: it is usually the wrong control, and
occasionally exactly the right one.

Old fee schedules are registered here too, for the same reason and with one
difference: they are never the right answer, so search ranks them last.

Verified 2026-07-27 by scanning each PDF for its own "applying to land to which
LEP 20xx applies" header. Every document that self-identifies says LEP 2012;
none says LEP 2000, so the LEP 2000 set is identified by the filename convention
used when they were downloaded, corroborated by the pairing (each -lep2000 file
has a LEP 2012 counterpart of the same chapter).
"""

LEP_2012 = "Lismore LEP 2012"
LEP_2000 = "Lismore LEP 2000"
STATE = "NSW state-wide"
NOT_INSTRUMENT_SPECIFIC = "not instrument-specific"

# Documents that apply to land under the superseded LEP 2000.
LEP_2000_DOCUMENTS = {
    "chapter-1-residential-lep2000.pdf",
    "chapter-12-heritage-lep2000.pdf",
    "chapter-14-tree-preservation-lep2000.pdf",
    "part-b-chapter-6-nimbin-village-lep2000.pdf",
    # Found 2026-08-01 by scripts/check_documents.py: this was filed as
    # `part-b-chapter-1-lismore-urban-area.pdf`, with no marker, and so was
    # being reported as current. Its own text zones the area 2(a) Residential,
    # 3(a) Business, 3(b) Neighbourhood Business — LEP 2000 codes. The council
    # publishes no LEP 2012 edition of this chapter, so this is the only
    # version there is; it just has to say so.
    "part-b-chapter-1-lismore-urban-area-lep2000.pdf",
}

# Guidance, forms and handbooks that are not tied to either LEP.
GENERAL_DOCUMENTS = {
    "koala-plan-of-management.pdf",
    "stormwater-drainage-handbook.pdf",
    "onsite-sewage-wastewater-management-strategy.pdf",
    "guidelines-erosion-sedimentation-control.pdf",
    "c211-erosion-sedimentation-spec.pdf",
    "vegetation-management-plan-guidelines-2024.pdf",
    "guide-for-resited-dwellings.pdf",
    "statement-of-environmental-effects-minor-development.pdf",
}

SUPERSEDED_NOTE = (
    "This document applies to land under Lismore LEP 2000, which for most of the LGA has "
    "been superseded by LEP 2012. LEP 2000 still applies only to areas under Ministerial "
    "review for the former E2/E3 environmental zones. Unless the site is in one of those "
    "areas, the LEP 2012 chapter of the same number is the applicable control — check "
    "which instrument applies to the site before relying on this."
)

# Superseded chapters the council never reissued under LEP 2012. The standard
# note above sends the reader to "the LEP 2012 chapter of the same number",
# which for these does not exist — so they get their own wording. Verified
# against the council's DCP page on 2026-08-01: only the LEP 2000 edition of
# Part B Chapter 1 is published.
LEP_2000_WITHOUT_COUNTERPART = {
    "part-b-chapter-1-lismore-urban-area-lep2000.pdf",
}

NO_COUNTERPART_NOTE = (
    "This document applies to land under Lismore LEP 2000, which for most of the LGA has "
    "been superseded by LEP 2012. Council has not reissued this chapter under LEP 2012, so "
    "there is no current equivalent to read instead — this is the only version of these "
    "controls. Treat it as indicative and confirm with Council which controls apply to the "
    "site, because the zone codes it uses (2(a), 3(a) and similar) were replaced in 2012."
)


# The fee schedule every figure in this repository is transcribed from:
# data/fees.py, data/approvals.py and scripts/audit_approvals.py all cite it.
CURRENT_FEE_SCHEDULE = "fees-and-charges-2026-27.pdf"

# Fee schedules a later edition replaces, with the year each one prices.
#
# Found 2026-09-25: a search for "footpath dining fee" ranked the 2025-26
# schedule first, with nothing marking it as old, so the answer to a business
# asking what a fee costs was last year's figure. Unlike a LEP 2000 chapter,
# which is still the right control for some land, an old fee schedule is never
# the one a new application pays — so these are also ranked below every current
# hit in search, not just labelled. Both are kept rather than deleted because
# they are the record of what the figures were.
SUPERSEDED_FEE_SCHEDULES = {
    # Its two columns are 24/25 and 25/26, so even its later column is a year
    # behind — outdoor dining is $81.15/m² there and $85.25/m² in 2026-27.
    "fees-and-charges-2025-26.pdf": "2025-26",
    # The DPHI fact sheet of state planning fees. The statutory fees are indexed
    # every July; Council's schedule carries the current ones.
    "nsw-planning-fees-2024-25.pdf": "2024-25",
}

SUPERSEDED_FEE_NOTE = (
    "This is the {year} fee schedule, which has been replaced. Its figures are out of date "
    f"and are not what an application lodged now pays. Use {CURRENT_FEE_SCHEDULE} for "
    "Council's current fees, or calculate_da_fees for the DA fee itself."
)

# Verified 2026-09-25 on all 52 pages of the current schedule that carry year
# headers: 25/26 sits left of 26/27 on every one, and in all 999 rows printing
# two figures the left figure comes first in the extracted text. A snippet that
# shows "$396.50 $416.50" is therefore last year's fee followed by this year's.
FEE_SCHEDULE_COLUMNS_NOTE = (
    "Rows in this schedule that print two figures give 2025-26 first and 2026-27 second. "
    "The second is the current fee."
)


def superseded_note_for(filename: str) -> str:
    """The warning to attach to a superseded document."""
    name = filename.rsplit("/", 1)[-1]
    if name in SUPERSEDED_FEE_SCHEDULES:
        return SUPERSEDED_FEE_NOTE.format(year=SUPERSEDED_FEE_SCHEDULES[name])
    return NO_COUNTERPART_NOTE if name in LEP_2000_WITHOUT_COUNTERPART else SUPERSEDED_NOTE


def superseded_banner(filename: str) -> str:
    """The line to put above a superseded document's text when it is read directly."""
    name = filename.rsplit("/", 1)[-1]
    heading = (
        "SUPERSEDED FEE SCHEDULE" if name in SUPERSEDED_FEE_SCHEDULES
        else "SUPERSEDED FOR MOST LAND"
    )
    return f"⚠️ {heading} — {superseded_note_for(name)}"


def instrument_for(filename: str, category: str = "") -> str:
    """The planning instrument a document belongs to."""
    if filename in LEP_2000_DOCUMENTS:
        return LEP_2000
    if filename in GENERAL_DOCUMENTS:
        return NOT_INSTRUMENT_SPECIFIC
    if category == "exempt-development":
        return STATE
    if category == "fees":
        return NOT_INSTRUMENT_SPECIFIC
    if category in ("dcp", "lep"):
        return LEP_2012
    return NOT_INSTRUMENT_SPECIFIC


def is_superseded(filename: str) -> bool:
    return filename in LEP_2000_DOCUMENTS or filename in SUPERSEDED_FEE_SCHEDULES
