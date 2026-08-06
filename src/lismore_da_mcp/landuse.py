"""Matching a proposed use against a zone land use table.

Used by check_permissibility and by the SEE generator.
"""

import re

from lismore_da_mcp.data.definitions import (
    CATCHALL_TERM,
    LAND_USE_HIERARCHY,
)

# Words that describe *what you are doing* rather than *what will operate on
# the land*. The LEP land use table answers only the second question, so these
# fall through to the "any other development not specified" catch-all and come
# back as likely_permitted_with_consent — a confident answer to a question that
# was never asked. See PLAN.md 1.3.
#
# Lives here rather than in the handler that first needed it because
# check_permissibility is no longer the only caller: a readiness check given
# "fitout" as the proposed use has the same problem, and a second copy of this
# set would drift from the first.
NOT_A_LAND_USE = {
    "change of use", "change use", "use change", "changing use",
    "fitout", "fit out", "shop fitout", "refurbishment", "refit",
    "development", "new development", "alteration", "alterations",
    "alterations and additions", "addition", "additions", "renovation",
    "extension", "extensions", "demolition", "construction", "building work",
}


def canonical_use(term: str) -> str:
    """Normalise a land use term for comparison, including naive singularisation.

    Applied to both sides of every comparison, so "Restaurants or cafes" and
    "restaurant or cafe" meet in the middle.
    """
    text = term.lower().replace("-", " ").replace("_", " ")
    text = " ".join(text.split())
    return re.sub(r"\b(\w{3,}?)s\b", r"\1", text)

def match_land_use(term: str, uses: list[str], strength: str) -> str | None:
    """Find `term` in a zone's use list at one matching strength.

    "exact" compares whole terms, "hierarchy" looks for the broader categories the
    term sits under, "approximate" falls back to a word-boundary containment search.
    Keeping these separate is what stops 'shop' latching onto 'Shop top housing'
    before the hierarchy has had a chance to resolve it to 'Commercial premises'.
    """
    target = canonical_use(term)
    if not target:
        return None

    if strength == "exact":
        return next((use for use in uses if canonical_use(use) == target), None)

    if strength == "hierarchy":
        for parent in LAND_USE_HIERARCHY.get(target, []):
            parent_canonical = canonical_use(parent)
            for use in uses:
                if canonical_use(use) == parent_canonical:
                    return use
        return None

    return next(
        (use for use in uses if re.search(rf"\b{re.escape(target)}\b", canonical_use(use))),
        None,
    )

def classify_land_use(proposed_use: str, zone_info: dict, zone_code: str = "") -> dict | None:
    """Classify a use against a zone's land use table.

    Returns None when there is nothing to go on. `permissible` is left None when the
    answer is genuinely unclear, so the form's tick stays blank rather than recording
    a guess. An express listing beats a broader group term, which is why matching
    strength is the outer loop: 'Restaurants or cafes' is expressly permitted in R1
    even though its parent 'Commercial premises' is prohibited there.
    """
    if not proposed_use or not zone_info:
        return None

    zone_label = f"Zone {zone_code}".strip() if zone_code else "the zone"
    categories = (
        ("permitted_without_consent", zone_info.get("permitted_without_consent", []), True, "permitted without consent in"),
        ("permitted_with_consent", zone_info.get("permitted_with_consent", []), True, "permitted with consent in"),
        ("prohibited", zone_info.get("prohibited", []), False, "prohibited in"),
    )

    for strength in ("exact", "hierarchy", "approximate"):
        for category, uses, permissible, phrase in categories:
            matched = match_land_use(proposed_use, uses, strength)
            if not matched or CATCHALL_TERM in canonical_use(matched):
                continue
            if strength == "hierarchy":
                statement = (
                    f"'{proposed_use}' falls under '{matched}', which is {phrase} {zone_label} "
                    "under the LEP 2012 land use table."
                )
            elif strength == "exact":
                statement = f"'{matched}' is {phrase} {zone_label} under the LEP 2012 land use table."
            else:
                statement = (
                    f"'{proposed_use}' appears to correspond to '{matched}', which is {phrase} {zone_label}. "
                    "Confirm the exact land use term with Council."
                )
            return {
                "permissible": permissible if strength != "approximate" else None,
                "matched_use": matched,
                "match_type": strength,
                "category": category,
                "statement": statement,
                "basis": f"LEP 2012 land use table for {zone_label} — matched '{matched}' ({strength})",
            }

    with_consent = zone_info.get("permitted_with_consent", [])
    prohibited = zone_info.get("prohibited", [])

    if any(CATCHALL_TERM in canonical_use(u) for u in with_consent):
        return {
            "permissible": None,
            "matched_use": None,
            "match_type": "catchall",
            "category": "catchall",
            "statement": (
                f"'{proposed_use}' is not listed in the {zone_label} land use table, which permits "
                "'any other development not specified in item 2 or 4' with consent. Confirm with the Duty Planner."
            ),
            "basis": f"not listed in the {zone_label} land use table; catch-all applies",
        }
    if any(CATCHALL_TERM in canonical_use(u) for u in prohibited):
        return {
            "permissible": False,
            "matched_use": None,
            "match_type": "catchall",
            "category": "catchall",
            "statement": (
                f"'{proposed_use}' is not listed in the {zone_label} land use table, which prohibits "
                "'any other development not specified'. This use is likely prohibited."
            ),
            "basis": f"not listed in the {zone_label} land use table; prohibited catch-all applies",
        }

    return {
        "permissible": None,
        "matched_use": None,
        "match_type": "none",
        "category": None,
        "statement": f"'{proposed_use}' could not be located in the {zone_label} land use table. Confirm with Council.",
        "basis": f"no match in the {zone_label} land use table",
    }
