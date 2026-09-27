"""Matching a proposed use against a zone land use table.

Used by check_permissibility and by the SEE generator.
"""

import re

from lismore_da_mcp.data.definitions import (
    LAND_USE_DEFINITIONS,
    LAND_USE_HIERARCHY,
    LAND_USE_TABLE_SPELLINGS,
    LEP_TYPE_OF,
)

# Words that describe *what you are doing* rather than *what will operate on
# the land*. The LEP land use table answers only the second question, so these
# get a specific "wrong question" error rather than a generic "not found".
# Shared by check_permissibility and the readiness check.
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


# The LEP writes its catch-all row two ways: "any other development not
# specified", and in RU2, RU3, SP2 and C1 "Any development not specified in
# item 2 or 3", without the "other".
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
# inflected by rule. The two sources overlap; `audit_landuse_matching.py` checks
# they agree.
_SPELLING_PAIRS: dict[str, str] = dict(LAND_USE_TABLE_SPELLINGS)
_SPELLING_PAIRS.update({
    entry["term"]: entry["land_use_table_term"]
    for entry in LAND_USE_DEFINITIONS.values()
    if entry.get("land_use_table_term")
})
# The Dictionary's "is a type of" notes spell each use too, usually in the plural,
# and 40 of those uses appear in no table — so this is the only pairing that
# reaches their singular. Where a table pairing exists it wins; the audit checks
# the two agree.
for _dictionary_form, (_note_form, _parent) in LEP_TYPE_OF.items():
    _SPELLING_PAIRS.setdefault(_dictionary_form, _note_form)

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

# The LEP Dictionary's own "X is a type of Y" notes, one link each.
_LEP_PARENT = {canonical_use(term): parent for term, (_, parent) in LEP_TYPE_OF.items()}


def ancestors(term: str) -> list[str]:
    """The broader terms that may carry `term` in a land use table, nearest first.

    Where the LEP Dictionary places the term itself, its notes are the chain, walked
    as far as they go — medical centre -> health services facility, garden centre ->
    retail premises -> commercial premises. Where it does not (the everyday words in
    `LAND_USE_HIERARCHY`: cafe, gym, takeaway), the hand-written chain comes first and
    the notes continue it from its last link.
    """
    target = canonical_use(term)
    if not target:
        return []
    chain = [] if target in _LEP_PARENT else list(_HIERARCHY_BY_CANONICAL.get(target, []))
    seen = {target} | {canonical_use(link) for link in chain}
    current = canonical_use(chain[-1]) if chain else target
    while current in _LEP_PARENT:
        parent = _LEP_PARENT[current]
        current = canonical_use(parent)
        if current in seen:
            break
        chain.append(parent)
        seen.add(current)
    return chain


# Every land use this server can put a name to, canonicalised.
#
# Drawn from the tables themselves, the Dictionary/table spelling pairs and the
# hierarchy's everyday aliases — so it covers both "Industries" and "industry",
# and the colloquial "cafe" and "gym" that resolve through a parent.
#
# What it buys is the distinction the catch-all turns on: a term in here that is
# absent from a particular zone's table is *genuinely unlisted there*, which is
# a fact about the LEP, whereas a term not in here at all is one this server
# failed to identify, and must not be answered from the catch-all.
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
    for term, (note_spelling, parent) in LEP_TYPE_OF.items():
        known.add(canonical_use(term))
        known.add(canonical_use(note_spelling))
        known.add(canonical_use(parent))
    known.discard("")
    return known


KNOWN_LAND_USES = _known_land_uses()


def _named_in(word: str, definition: str) -> bool:
    """Whether the LEP's own definition text names this word (or its plural)."""
    stem = re.escape(_flatten(word))
    return bool(re.search(rf"\b{stem}(?:s|es)?\b", _flatten(definition)))


def lep_term_for(word: str) -> dict | None:
    """The LEP defined term an everyday word stands for, or None.

    ROADMAP.md A2. `get_definition` read "hairdresser" as business premises from
    `DEFINITION_SYNONYMS`, while `check_permissibility` refused the same word and
    `get_parking_rates` refused it too — the same word, adjacent questions,
    opposite outcomes, which reads to a caller as an unreliable tool rather than
    a coverage boundary. This is the one path they now share.

    Only a confident mapping is taken — the word itself, or its synonym-table
    entry. Never a fuzzy one: a near-spelling is a guess, and a guessed land use
    category is the wrong "yes" this repository has spent two phases removing.
    `named_in_definition` says whether the LEP's own words back the reading
    ("hairdressers" is in the business premises definition) or only this
    server's vocabulary does ("barber" is not), and callers say which.
    """
    from lismore_da_mcp.vocabulary import DEFINITION_SYNONYMS, resolve  # noqa: PLC0415

    if not str(word).strip() or canonical_use(word) in KNOWN_LAND_USES:
        return None
    match = resolve(word, LAND_USE_DEFINITIONS, DEFINITION_SYNONYMS)
    if not match.key or match.how not in ("exact", "squashed", "synonym"):
        return None
    entry = LAND_USE_DEFINITIONS[match.key]
    return {
        "word": str(word),
        "term": entry["term"],
        "named_in_definition": _named_in(word, entry.get("definition", "")),
    }


def interpretation(mapped: dict) -> str:
    """The sentence a caller is shown when a word was read as an LEP term."""
    if mapped["named_in_definition"]:
        return (f"Read '{mapped['word']}' as '{mapped['term']}': the LEP Dictionary's "
                f"definition of {mapped['term']} names it.")
    return (f"Read '{mapped['word']}' as '{mapped['term']}'. That is this server's reading, "
            f"not the LEP's words — the definition of {mapped['term']} does not name "
            f"'{mapped['word']}'. Confirm the category with Council before relying on it.")


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
        for parent in ancestors(term):
            parent_canonical = canonical_use(parent)
            for use in uses:
                if canonical_use(use) == parent_canonical:
                    return use
        return None

    return next(
        (use for use in uses if re.search(rf"\b{re.escape(target)}\b", canonical_use(use))),
        None,
    )

def _candidates(proposed_use: str, categories, strength: str):
    """The (category, uses, ...) rows to try, in the order that decides the answer.

    For exact and approximate matching the table's own order is right: a term is
    listed in at most one section. For the hierarchy it is not. LEP cl 2.3(3)(b)
    says a type the table names separately is not caught by its parent's entry, so
    the *nearest* ancestor the table lists decides — and walking the sections
    first let a distant ancestor in "permitted" beat a nearer one in "prohibited"
    just because permitted is checked first. Each row is narrowed to the one
    ancestor being tried, nearest first, so `match_land_use` sees it alone.
    """
    if strength != "hierarchy":
        yield from categories
        return
    for link in ancestors(proposed_use):
        key = canonical_use(link)
        for category, uses, permissible, phrase in categories:
            listed = [use for use in uses if canonical_use(use) == key]
            if listed:
                yield category, listed, permissible, phrase


def classify_land_use(proposed_use: str, zone_info: dict, zone_code: str = "",
                      _already_mapped: bool = False) -> dict | None:
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
    if not recognised and not _already_mapped:
        # A word the LEP does not name, but that stands for one it does. Answered
        # as that term, with the reading stated — see lep_term_for. Mapped once
        # only: a term that somehow fails recognition must not map back to itself.
        mapped = lep_term_for(proposed_use)
        if mapped:
            result = classify_land_use(mapped["term"], zone_info, zone_code, _already_mapped=True)
            if result and result["match_type"] != "unrecognised":
                result["interpreted_as"] = interpretation(mapped)
                return result
    strengths = ("exact", "hierarchy") if recognised else ("exact", "hierarchy", "approximate")

    for strength in strengths:
        for category, uses, permissible, phrase in _candidates(proposed_use, categories, strength):
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
            basis = f"LEP 2012 land use table for {zone_label} — matched '{matched}' ({strength})"
            if strength == "hierarchy":
                path = [proposed_use]
                for link in ancestors(proposed_use):
                    path.append(link)
                    if canonical_use(link) == canonical_use(matched):
                        break
                basis += " via " + " -> ".join(path) + " (LEP Dictionary; cl 2.3(3)(b))"
            return {
                "permissible": permissible if strength != "approximate" else None,
                "matched_use": matched,
                "match_type": strength,
                "category": category,
                "statement": statement,
                "basis": basis,
            }

    with_consent = zone_info.get("permitted_with_consent", [])
    prohibited = zone_info.get("prohibited", [])

    # Nothing in the table matched, so the catch-all row applies — but only if
    # the term is one the LEP names (`recognised`). An unrecognised term is a
    # failure to identify the proposal, not evidence that the use is unlisted.
    #
    # `permissible` stays None in both branches: readiness.py raises a "stop"
    # on it and the SEE writes "Prohibited" from it, and neither should fire on
    # a fall-through. The catch-all is still reported as the provision that
    # would apply.
    if any(_is_catchall(u) for u in with_consent):
        return {
            # None even for a recognised term: a fall-through should not tick
            # the SEE's "permissible" box as confidently as an express listing.
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
