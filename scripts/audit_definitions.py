#!/usr/bin/env python3
"""Check data/definitions.py against the Lismore LEP 2012 Dictionary.

Seven checks, and only the first is the one the other audit scripts run:

1.  every stored `definition` and `additional_controls.control` still appears
    in documents/lep/lep-2012-nsw-full.txt verbatim;
2.  every `definition` opens with its own term — verbatim LEP text lifted from
    the *wrong* Dictionary entry passes check 1 unharmed;
3.  every `land_use_table_term` is really how data/zones.py spells that use,
    since check_permissibility matches the table and not the Dictionary;
4.  every first link in LAND_USE_HIERARCHY agrees with the LEP's own
    "X are a type of Y" notes, read off the document rather than a list here;
5.  every `related_terms` entry is a key that exists;
6.  every definition is in exactly one DEFINITION_CATEGORIES group, so a new
    term cannot be added without appearing in list_definitions;
7.  the figures in FIGURES_NOT_IN_THE_DEFINITION really are **absent** from the
    definitions they were once attached to.

Check 7 is the point. A presence check only ever looks at what is stored, so it
is structurally blind to a sentence somebody invented — which is the failure
this file actually had, in common with data/standards.py before item 0.6. An
audit that can only confirm what is there manufactures confidence about what is
not.

Its first version was itself blind, and that is the more useful warning: it
searched each definition for the *old wording* of the invented figure, so
reinventing the same 80m² cap as "80 square metres" passed. Each record now
names the **kind** of figure the definition does not set, and the check asserts
none of that kind appears — a reinvention is written in fresh words by
definition.

Usage:  .venv/bin/python scripts/audit_definitions.py
Exit status is non-zero if anything fails, so CI can run it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lismore_da_mcp.data.definitions import (  # noqa: E402
    DEFINITION_CATEGORIES,
    FIGURES_NOT_IN_THE_DEFINITION,
    LAND_USE_DEFINITIONS,
    LAND_USE_HIERARCHY,
)
from lismore_da_mcp.data.zones import ZONES  # noqa: E402

LEP_PATH = Path(__file__).resolve().parent.parent / "documents" / "lep" / "lep-2012-nsw-full.txt"


def normalise(text: str) -> str:
    """Collapse whitespace so line wrapping cannot fail a comparison.

    The LEP text separates a paragraph letter from its text with non-breaking
    spaces; the stored quotes use ordinary ones. Both sides come through here.
    """
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def lep_text() -> str:
    if not LEP_PATH.exists():
        sys.exit(f"missing {LEP_PATH} — run scripts/fetch_lep_full.py")
    return normalise(LEP_PATH.read_text(encoding="utf-8"))


def dictionary_parents(raw: str) -> dict[str, str]:
    """Read the LEP's own 'X are a type of Y' notes off the document."""
    return {
        m.group(1).strip(): m.group(2).strip()
        for m in re.finditer(
            r"([A-Z][A-Za-z '()\-]+?) (?:are|is) a type of ([a-z][a-z '()\-]+?)"
            r"—see the definition of that term in this Dictionary",
            raw,
        )
    }


def check_quotes(lep: str) -> list[str]:
    failures = []
    for key, entry in LAND_USE_DEFINITIONS.items():
        if normalise(entry["definition"]) not in lep:
            failures.append(
                f"{key}: `definition` is no longer in the LEP Dictionary verbatim. "
                "Read the Dictionary before changing it — this file was paraphrased once."
            )
        control = entry.get("additional_controls")
        if control and normalise(control["control"]) not in lep:
            failures.append(
                f"{key}: `additional_controls.control` ({control['source']}) is not in the "
                "LEP verbatim. A clause 5.4 sub-clause may have been renumbered or amended."
            )
    return failures


def check_definition_opens_with_its_term() -> list[str]:
    """A quote lifted from the wrong Dictionary entry still passes check 1."""
    failures = []
    for key, entry in LAND_USE_DEFINITIONS.items():
        term = entry["term"]
        if not normalise(entry["definition"]).startswith(f"{term} means"):
            failures.append(
                f"{key}: `definition` does not open with '{term} means' — the quote is "
                "verbatim LEP text but may be a different term's definition."
            )
    return failures


def check_table_terms() -> list[str]:
    failures = []
    listed = {
        re.sub(r"\s+", " ", use).strip()
        for zone in ZONES.values()
        for category in ("permitted_without_consent", "permitted_with_consent", "prohibited")
        for use in (zone.get(category) or [])
    }
    for key, entry in LAND_USE_DEFINITIONS.items():
        table_term = entry.get("land_use_table_term")
        if table_term and table_term not in listed:
            failures.append(
                f"{key}: land_use_table_term {table_term!r} appears in no zone land use "
                "table. check_permissibility matches the table, so this would never resolve."
            )
    return failures


def check_hierarchy(lep: str) -> list[str]:
    parents = dictionary_parents(lep)
    if not parents:
        return ["the 'is a type of' scan matched nothing in the LEP — the regex has rotted"]
    failures = []
    lowered = {k.lower(): v for k, v in parents.items()}
    for term, chain in LAND_USE_HIERARCHY.items():
        parent = lowered.get(term.lower())
        if parent and chain and chain[0] != parent:
            failures.append(
                f"LAND_USE_HIERARCHY[{term!r}] starts at {chain[0]!r}, but the LEP Dictionary "
                f"says {term} is a type of {parent!r}."
            )
    return failures


def check_related_terms() -> list[str]:
    return [
        f"{key}: related_terms points at {related!r}, which is not a key in this file"
        for key, entry in LAND_USE_DEFINITIONS.items()
        for related in entry.get("related_terms", [])
        if related not in LAND_USE_DEFINITIONS
    ]


def check_categories() -> list[str]:
    """Every definition is listed exactly once, so list_definitions shows them all."""
    failures = []
    seen: dict[str, str] = {}
    for category, keys in DEFINITION_CATEGORIES.items():
        for key in keys:
            if key not in LAND_USE_DEFINITIONS:
                failures.append(f"DEFINITION_CATEGORIES[{category!r}] names {key!r}, which does not exist")
            elif key in seen:
                failures.append(f"{key!r} is in both {seen[key]!r} and {category!r}")
            else:
                seen[key] = category
    for key in LAND_USE_DEFINITIONS:
        if key not in seen:
            failures.append(
                f"{key!r} is in no category, so list_definitions will not show it under one"
            )
    return failures


def check_absences() -> list[str]:
    """The check the other audits cannot run: that an invention stayed removed."""
    failures = []
    for key, record in FIGURES_NOT_IN_THE_DEFINITION.items():
        entry = LAND_USE_DEFINITIONS.get(key)
        if entry is None:
            failures.append(f"FIGURES_NOT_IN_THE_DEFINITION names {key!r}, which no longer exists")
            continue
        definition = normalise(entry["definition"])
        for pattern, label in record["must_not_contain"]:
            found = re.search(pattern, definition, re.I)
            if found:
                failures.append(
                    f"{key}: the definition now states {label} ({found.group(0)!r}). The "
                    f"Dictionary sets none — that control is {record['source']}. This is how "
                    f"{record['was_claimed']!r} got into this file the first time."
                )
        if record["real_control"] and not entry.get("additional_controls"):
            failures.append(
                f"{key}: FIGURES_NOT_IN_THE_DEFINITION gives a real control "
                f"({record['source']}) but the entry carries no additional_controls, so the "
                "tool answers with no figure at all."
            )
    return failures


def main() -> int:
    lep = lep_text()
    groups = [
        ("definitions and clause 5.4 controls quoted verbatim", check_quotes(lep)),
        ("each definition opens with its own term", check_definition_opens_with_its_term()),
        ("land use table spellings exist in data/zones.py", check_table_terms()),
        ("hierarchy agrees with the LEP's 'is a type of' notes", check_hierarchy(lep)),
        ("related_terms resolve", check_related_terms()),
        ("every definition is in exactly one category", check_categories()),
        ("recorded inventions are still absent", check_absences()),
    ]

    total = 0
    for label, failures in groups:
        mark = "ok  " if not failures else "FAIL"
        print(f"[{mark}] {label}")
        for failure in failures:
            print(f"       - {failure}")
        total += len(failures)

    controls = sum(1 for e in LAND_USE_DEFINITIONS.values() if e.get("additional_controls"))
    print(
        f"\n{len(LAND_USE_DEFINITIONS)} definitions checked, {controls} with clause 5.4 controls, "
        f"{len(FIGURES_NOT_IN_THE_DEFINITION)} absences asserted."
    )
    if total:
        print(f"{total} problem(s).")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
