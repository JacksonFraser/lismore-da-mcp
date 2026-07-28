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
    return filename in LEP_2000_DOCUMENTS
