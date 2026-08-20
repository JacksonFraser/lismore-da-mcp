"""Matching a proposed use against a zone land use table.

Used by check_permissibility and by the SEE generator.
"""

import re

from lismore_da_mcp.data.definitions import (
    LAND_USE_DEFINITIONS,
    LAND_USE_HIERARCHY,
    LAND_USE_TABLE_SPELLINGS,
)

# Words that describe *what you are doing* rather than *what will operate on
# the land*. The LEP land use table answers only the second question, so these
# fall through to the "any other development not specified" catch-all — which
# used to come back as likely_permitted_with_consent, a confident answer to a
# question that was never asked. The catch-all no longer reports as a verdict
# (ROADMAP.md S1), but these still deserve the specific error below rather than
# a generic "not found": the term is not a near miss, it is the wrong question.
# See PLAN.md 1.3.
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


def _flatten(term: str) -> str:
    """Lowercase and settle the punctuation, without touching word endings.

    Separate from `canonical_use` because the spelling table below has to be
    looked up on a form that still has its plural — flattening and singularising
    in one step is what made the table unreachable in the first place.
    """
    text = term.lower().replace("-", " ").replace("_", " ")
    text = text.replace("’", "'").replace("‘", "'")
    return " ".join(text.split())


# The LEP writes its catch-all row two ways, and only one of them was matched.
#
# `data.definitions.CATCHALL_TERM` is the literal "any other development not
# specified", and this module tested for it as a substring. But RU2, RU3, SP2 and
# C1 word their row "Any development not specified in item 2 or 3", without the
# "other" — so in those four zones the prohibiting catch-all was invisible, and a
# use they do not list came back "not found" instead of prohibited.
#
# Found while fixing ROADMAP.md S1 item 3, which is the same defect from the
# other side: there the catch-all answered when it should not have; here it
# stayed silent when it should have answered.
_CATCHALL_ROW = re.compile(r"\bany (?:other )?development not specified\b")


def _is_catchall(use: str) -> bool:
    return bool(_CATCHALL_ROW.search(_flatten(use)))


# Every spelling of a land use -> the one form comparisons happen on.
#
# Built from `LAND_USE_TABLE_SPELLINGS`, which is the LEP's own singular/plural
# pairing read off the Dictionary, plus the `land_use_table_term` already
# carried by individual definitions. Both sides of each pair land on the same
# key, so "Centre-based child care facilities" off the zone table and
# "centre-based child care facility" from an applicant meet without either being
# inflected by rule. ROADMAP.md S1.
#
# The two sources overlap and must not disagree; `audit_landuse_matching.py`
# checks they do not, rather than letting whichever is built second win.
_SPELLING_PAIRS: dict[str, str] = dict(LAND_USE_TABLE_SPELLINGS)
_SPELLING_PAIRS.update({
    entry["term"]: entry["land_use_table_term"]
    for entry in LAND_USE_DEFINITIONS.values()
    if entry.get("land_use_table_term")
})

_CANONICAL_SPELLING: dict[str, str] = {}
for _dictionary_form, _table_form in _SPELLING_PAIRS.items():
    _key = _flatten(_dictionary_form)
    _CANONICAL_SPELLING[_key] = _key
    _CANONICAL_SPELLING[_flatten(_table_form)] = _key


def canonical_use(term: str) -> str:
    """Normalise a land use term for comparison.

    Applied to both sides of every comparison, so "Restaurants or cafes" and
    "restaurant or cafe" meet in the middle.

    The LEP's own pairing decides that meeting point wherever it has one. The
    suffix rule below is the fallback for everything else — words an applicant
    uses that the LEP never defines ("cafes", "offices"), where there is no
    document to consult and both sides get the same treatment anyway. It stays
    naive on purpose: it is no longer load-bearing for any term the tables name,
    and making it cleverer would put guessed inflections back in the path the
    spelling table exists to keep them out of.
    """
    text = _flatten(term)
    if text in _CANONICAL_SPELLING:
        return _CANONICAL_SPELLING[text]
    return re.sub(r"\b(\w{3,}?)s\b", r"\1", text)


# `LAND_USE_HIERARCHY` keyed the way lookups actually arrive.
#
# The dict is written in the LEP's spelling, and `match_land_use` looks it up
# with a canonicalised term — so "business premises" became "busines premise"
# and missed, taking the entire `premises` family with it. That is the second
# half of the S1 defect: E4 prohibits 'Commercial premises' and answered
# "permitted" for every kind of premises that resolves to it.
_HIERARCHY_BY_CANONICAL = {
    canonical_use(term): parents for term, parents in LAND_USE_HIERARCHY.items()
}


# Every land use this server can put a name to, canonicalised.
#
# Drawn from the tables themselves, the Dictionary/table spelling pairs and the
# hierarchy's everyday aliases — so it covers both "Industries" and "industry",
# and the colloquial "cafe" and "gym" that resolve through a parent.
#
# What it buys is the distinction the catch-all turns on: a term in here that is
# absent from a particular zone's table is *genuinely unlisted there*, which is
# a fact about the LEP, whereas a term not in here at all is one this server
# failed to identify. Those two were indistinguishable before, and answering
# both from the catch-all is what produced 120 wrong "yes" answers and 91 wrong
# "no" ones out of the same bug. ROADMAP.md S1.
def _known_land_uses() -> set[str]:
    from lismore_da_mcp.data.zones import ZONES

    known = set()
    for zone in ZONES.values():
        for section in ("permitted_without_consent", "permitted_with_consent", "prohibited"):
            for use in zone.get(section) or []:
                if not _is_catchall(use):
                    known.add(canonical_use(use))
    for dictionary_form, table_form in _SPELLING_PAIRS.items():
        known.add(canonical_use(dictionary_form))
        known.add(canonical_use(table_form))
    for entry in LAND_USE_DEFINITIONS.values():
        known.add(canonical_use(entry["term"]))
    known.update(_HIERARCHY_BY_CANONICAL)
    known.discard("")
    return known


KNOWN_LAND_USES = _known_land_uses()


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
        for parent in _HIERARCHY_BY_CANONICAL.get(target, []):
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

    # A term the LEP names somewhere is never guessed at by containment.
    #
    # "approximate" is a word-boundary search, so once the spelling table let
    # 'Home industries' canonicalise properly, a proposal for 'industry' in R2
    # started matching it — "appears to correspond to Home industries", which it
    # does not. For a use the LEP defines there is nothing to approximate
    # towards: it either appears in this table under its own name, or reaches it
    # through the hierarchy, or it is absent and the catch-all decides. Fuzzy
    # matching is for the words this server cannot place at all.
    recognised = canonical_use(proposed_use) in KNOWN_LAND_USES
    strengths = ("exact", "hierarchy") if recognised else ("exact", "hierarchy", "approximate")

    for strength in strengths:
        for category, uses, permissible, phrase in categories:
            matched = match_land_use(proposed_use, uses, strength)
            if not matched or _is_catchall(matched):
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

    # Nothing in the table matched. The catch-all row decides what happens to
    # development the table does not name, so it is tempting to answer from it —
    # and that is the mistake. Reaching here means *this tool did not recognise
    # the term*, which is not the same fact as the use being absent from the
    # table, and the two have opposite consequences. Every one of the 287
    # disagreements in ROADMAP.md S1 arrived this way, splitting into 120
    # confident "permitted" and 91 confident "prohibited" purely by which
    # catch-all the zone happened to carry.
    #
    # So `permissible` stays None in both branches below. It is the field
    # `readiness.py` raises a "stop" on and `see.py` writes "Prohibited" from,
    # and neither should fire on a term nobody identified. The catch-all itself
    # is not lost — it is reported as what it is, the provision that *would*
    # apply once the right term is established.
    # `recognised` is what separates the two readings of this fall-through.
    #
    # A term the LEP names, absent from *this* table, really is unlisted here,
    # and the catch-all is then the LEP's own answer — 'industry' in R2 is
    # prohibited by item 4 and saying so is correct. A term nothing here can
    # place is a failure to identify the proposal, and answering that from the
    # catch-all is asserting a fact about the LEP on the strength of this
    # server's vocabulary.
    if any(_is_catchall(u) for u in with_consent):
        return {
            # Stays None for a recognised term too. The catch-all does permit an
            # unlisted use with consent, but "permissible" here ticks a box on a
            # SEE, and the whole weight of S1 is that a permitted-shaped answer
            # derived from a fall-through should not be stated as confidently as
            # one read off an express listing.
            "permissible": None,
            "matched_use": None,
            "match_type": "catchall" if recognised else "unrecognised",
            "category": "catchall",
            "statement": (
                f"'{proposed_use}' is not listed in the {zone_label} land use table, which permits "
                "'any other development not specified in item 2 or 4' with consent. Confirm with the Duty Planner."
            ) if recognised else (
                f"'{proposed_use}' could not be matched to any land use the LEP names, so "
                f"permissibility in {zone_label} has not been established. This is a term this "
                "tool did not recognise — not a use it found to be unlisted. Settle which "
                "defined term the proposal falls under (get_definition, or the Duty Planner) "
                "and ask again with that term."
            ),
            "basis": (
                f"not listed in the {zone_label} land use table; catch-all applies"
                if recognised else
                f"{proposed_use!r} is not a land use term this server recognises; no answer derived"
            ),
        }
    if any(_is_catchall(u) for u in prohibited):
        return {
            "permissible": False if recognised else None,
            "matched_use": None,
            "match_type": "catchall" if recognised else "unrecognised",
            "category": "catchall",
            "statement": (
                f"'{proposed_use}' is not listed in the {zone_label} land use table, which prohibits "
                "'any other development not specified'. This use is likely prohibited."
            ) if recognised else (
                f"'{proposed_use}' could not be matched to any land use the LEP names, so "
                f"permissibility in {zone_label} has not been established. This is a term this "
                "tool did not recognise — not a use it found to be unlisted. Settle which "
                "defined term the proposal falls under (get_definition, or the Duty Planner) "
                "and ask again with that term."
            ),
            "basis": (
                f"not listed in the {zone_label} land use table; prohibited catch-all applies"
                if recognised else
                f"{proposed_use!r} is not a land use term this server recognises; no answer derived"
            ),
        }

    return {
        "permissible": None,
        "matched_use": None,
        "match_type": "none",
        "category": None,
        "statement": f"'{proposed_use}' could not be located in the {zone_label} land use table. Confirm with Council.",
        "basis": f"no match in the {zone_label} land use table",
    }
