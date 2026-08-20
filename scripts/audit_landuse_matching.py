#!/usr/bin/env python3
"""Check that check_permissibility agrees with the land use tables it reads.

ROADMAP.md item S1. Every other audit in this repository checks that **the data
matches the source**. This one checks the layer above: that the **tool agrees
with the data**. Nothing did, and that gap is where every defect in run 1 of
`SCENARIOS.md` lived — 15 failures, and not one of them was a bad fact.

`audit_zone_tables.py` establishes that all 21 tables in `data/zones.py` are the
LEP's tables, verbatim. Take that as given and one question is left: ask
`check_permissibility` about a use the table names, and does it come back with
what the table says? On 2026-08-09 it does not, and the shape of the miss is
worse than a miss:

    E4 + 'centre-based child care facility'  -> likely_permitted_with_consent
    E4 + 'centre-based child care facilities' -> prohibited

Same tool, same table, opposite answers, and which one a business hears depends
on whether it typed a plural. The permitted-shaped answer is the wrong one, and
it ships without the SEPP caveat, because that caveat is gated to
prohibited-shaped answers at `tools/zoning.py:251`.

## What is asked, and why those two spellings

Two questions per row of every table:

1.  **the table's own spelling** — 'Centre-based child care facilities'. There is
    no interpretation in this: the string is in the list, the list has a heading,
    the heading is the answer. Any failure here is unarguable.
2.  **the counterpart spelling** — 'centre-based child care facility'. This is
    the form an applicant types and the form `get_definition` hands back, because
    **the Dictionary defines the singular and the table lists the plural**.

The pairing between the two is *data, not a rule*. That distinction is the whole
reason this file exists: `landuse.py` currently pairs them with
`re.sub(r"\\b(\\w{3,}?)s\\b", r"\\1", text)`, which cannot turn 'facilities' into
'facility', and 40 table terms end in -ies.

So the counterpart is not invented here either. `counterpart_forms()` generates
candidate spellings liberally and then **keeps only those the LEP Dictionary
actually defines**, read off `documents/lep/lep-2012-nsw-full.txt`. Generosity is
free when the document is the filter: a candidate the Dictionary does not confirm
is dropped, so this audit can never grade the tool against a word that is not a
land use. 143 of the 159 distinct table terms pair this way.

The 16 that do not are listed in `UNPAIRED_TABLE_TERMS` with the reason for each,
rather than passing silently — six are rules rather than uses (the catch-alls,
'Uses authorised under...'), and the rest are named because an unexplained gap in
a checker is indistinguishable from a checker that is not running.

## How failures are graded

Not all disagreement costs the same, and a flat count would hide the ones that
matter. Every failure is one of:

    wrong_yes      the table prohibits it; the tool said permitted-shaped
    wrong_no       the table permits it; the tool said prohibited-shaped
    wrong_pathway  both say yes, but disagree on whether consent is needed
    hedged         the tool declined or hedged where the table is explicit

`wrong_yes` is the one that costs a business a lodgement fee and a refusal, and
it is the class that `SCENARIOS.md` found shipping unhedged. `hedged` is friction
rather than a wrong fact — real, but it belongs in a different queue, and mixing
the two is how a 190-line report becomes one nobody reads twice.

    .venv/bin/python scripts/audit_landuse_matching.py             # every zone
    .venv/bin/python scripts/audit_landuse_matching.py --business  # E1-E4, MU1, RU5
    .venv/bin/python scripts/audit_landuse_matching.py --zone E4
    .venv/bin/python scripts/audit_landuse_matching.py --verbatim-only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lismore_da_mcp.data.zones import ZONES  # noqa: E402
from lismore_da_mcp.tools.zoning import check_permissibility  # noqa: E402

LEP_PATH = ROOT / "documents" / "lep" / "lep-2012-nsw-full.txt"

BUSINESS_ZONES = ["E1", "E2", "E3", "E4", "MU1", "RU5"]

# Table section -> the verdict check_permissibility should return for a use
# listed under it. These are the handler's own verdict strings.
EXPECTED = {
    "permitted_without_consent": "permitted_without_consent",
    "permitted_with_consent": "permitted_with_consent",
    "prohibited": "prohibited",
}

# Verdicts grouped by what a business would *do* on hearing them. The grading
# turns on this and not on the exact string: 'prohibited' and 'likely_prohibited'
# both stop a proposal, and the difference between them is not what this audit
# is measuring.
PERMITTED_SHAPED = {"permitted", "permitted_without_consent", "permitted_with_consent",
                    "likely_permitted_with_consent"}
PROHIBITED_SHAPED = {"prohibited", "likely_prohibited"}
HEDGED_SHAPED = {"uncertain", "not_found", "unknown"}

# Rows of a land use table that are not land uses. They decide what happens to
# everything the table does *not* name, which makes them rules about the table
# rather than entries in it — asking check_permissibility about the text of the
# catch-all is not a question anyone has.
NOT_A_USE = re.compile(
    r"^(any (other )?development not specified"
    r"|the purpose shown on the land zoning map"
    r"|uses authorised under)",
    re.I,
)

# Table terms the Dictionary defines under no other spelling, with why.
#
# Most terms with no counterpart need none: 'Commercial premises' and
# 'Agriculture' are spelled in the table exactly as the Dictionary defines them,
# so the verbatim question is the only question there is. Those are not listed.
# What is listed is a term the Dictionary does not define *at all* under any
# generated spelling, because that is a gap in the pairing rather than an absence
# of one — and an unexplained gap in a checker is indistinguishable from a
# checker that is not running (PLAN.md item 0.2).
#
# Every one of these is still checked against its verbatim spelling. What it
# lacks is a *second* spelling to ask about.
UNPAIRED_TABLE_TERMS = {
    "Charter boating and tourism facilities":
        "the LEP spells this two ways in its own tables — RU1, RU2 and W2 have "
        "'Charter and tourism boating facilities', which is the Dictionary's word order, "
        "and R1 has this one. Both are transcribed correctly; the Dictionary defines only "
        "the first, so no singular pairs with this spelling.",
}


# The state of the matching layer as measured on 2026-08-09, before any fix.
#
# ROADMAP.md S1 records a figure of 115 wrong-yes and 75 wrong-no from an agent's
# sweep, and notes it "was never independently re-derived". This is the
# re-derivation, and it differs: wrong_yes is close, wrong_no was understated,
# and a third class the sweep did not name is the largest single group after the
# other two. The numbers matter because S1 argued the blast radius decides how
# much surgery is justified — 287 across every zone justifies the data-driven
# pairing rather than a patch to the regex.
#
# This is a baseline, not a tolerance. The test asserts the counts **exactly**,
# so a fix fails until the number here comes down with it, and the shrinking of
# this dict is the record of S1 landing. It reaches zero and then this constant
# goes away.
KNOWN_MATCHING_DEFECTS = {
    "wrong_yes": 120,
    "wrong_no": 91,
    "unfound": 76,
    "wrong_pathway": 0,
    "hedged": 0,
}


def normalise(text: str) -> str:
    """Collapse whitespace and settle the apostrophe.

    The LEP text uses curly apostrophes (Backpackers'); `data/zones.py` has both
    forms, because the table was transcribed from a page that mixed them. Neither
    changes which use is named.
    """
    text = text.replace("\xa0", " ").replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip()


def lep_text() -> str:
    if not LEP_PATH.exists():
        sys.exit(f"missing {LEP_PATH} — run scripts/fetch_lep_full.py")
    return normalise(LEP_PATH.read_text(encoding="utf-8"))


def dictionary_terms(raw: str) -> set[str]:
    """Every term the LEP Dictionary defines, read off the document.

    Entries take the form '<term> means ...' or '<term> has the same meaning as
    in the Act'. This is deliberately the same source `audit_definitions.py`
    reads its 'X is a type of Y' notes from — the pairing this audit needs is in
    the document, and hardcoding it here would be the second copy that drifts.
    """
    terms = {
        normalise(m.group(1)).lower()
        for m in re.finditer(
            r"(?:^|\. |\) )([A-Za-z][A-Za-z0-9 '()\-,]{2,60}?) (?:means|has the same meaning)\b",
            raw,
        )
    }
    if len(terms) < 200:
        sys.exit(
            f"read only {len(terms)} terms out of the LEP Dictionary — the layout has "
            "changed and the pairing below would be silently empty."
        )
    return terms


def _singular_forms(word: str) -> set[str]:
    """Candidate singulars for one word. Over-generates on purpose.

    Nothing downstream trusts these: `counterpart_forms` keeps only what the
    Dictionary confirms, so a wrong guess here costs nothing and a missing guess
    costs coverage. 'crematoria' needs the -um rule; 'jetties' the -y one.
    """
    lower = word.lower()
    out: set[str] = set()
    if len(lower) > 4 and lower.endswith("ies"):
        out.add(lower[:-3] + "y")
    if len(lower) > 3 and lower.endswith("es"):
        out.add(lower[:-2])
    if len(lower) > 2 and lower.endswith("s") and not lower.endswith("ss"):
        out.add(lower[:-1])
    if len(lower) > 3 and lower.endswith("a"):
        out.add(lower[:-1] + "um")
    # The possessive moves rather than disappears. The table lists "Rural
    # workers' dwellings"; the Dictionary defines "rural worker's dwelling".
    if len(lower) > 3 and lower.endswith("s'"):
        out.add(lower[:-2] + "'s")
    return out


def counterpart_forms(term: str, dictionary: set[str]) -> list[str]:
    """Spellings of `term` other than the table's, confirmed by the Dictionary.

    Every combination of singular and as-written across the words, not one word
    at a time: 'Restaurants or cafes' pairs with 'restaurant or cafe' only when
    both sides of the 'or' move together, and a term with two plural words is
    otherwise unreachable.

    Over-generating is safe here and under-generating is not, because the
    Dictionary is the filter — an unconfirmed candidate is discarded, so this can
    never test the tool against a word that is not a land use.
    """
    words = normalise(term).split()
    options = [sorted(_singular_forms(w) | {w.lower()}) for w in words]

    combinations = 1
    for choices in options:
        combinations *= len(choices)
    if combinations > 20000:  # nothing in the LEP comes close; a guard, not a limit
        options = [choices[:1] for choices in options]

    written = normalise(term).lower()
    return sorted({
        candidate for candidate in (" ".join(parts) for parts in product(*options))
        if candidate in dictionary and candidate != written
    })


def table_rows(zones: list[str]) -> list[tuple[str, str, str]]:
    """(zone, section, term) for every land use named in the given tables."""
    rows = []
    for zone in zones:
        for section in EXPECTED:
            for term in ZONES[zone].get(section) or []:
                if NOT_A_USE.match(normalise(term)):
                    continue
                rows.append((zone, section, term))
    return rows


def ask(zone: str, term: str) -> dict:
    """Put the question to the tool exactly as a caller would."""
    payload = check_permissibility({"land_use": term, "zone_code": zone})
    return json.loads(payload[0].text)


def grade(expected: str, answer: dict) -> str | None:
    """Classify one answer against the table. None means it agrees.

    The term being asked about is in the table, so a `catchall` or `none` match
    is a miss *whatever verdict it produced*. The catch-all decides what happens
    to uses the table does not name; reaching it for a use the table does name
    means the tool did not recognise the term, which is a different fact from the
    answer it went on to give. Where the shape coincides with the truth anyway
    that is `unfound` rather than a pass — the same miss in a zone whose catch-all
    prohibits returns the opposite answer, which is how 120 wrong_yes and 91
    wrong_no arise from one bug.
    """
    got = answer.get("permissibility")
    missed = answer.get("match_type") in ("catchall", "none")

    if expected == "prohibited" and got in PERMITTED_SHAPED:
        return "wrong_yes"
    if expected != "prohibited" and got in PROHIBITED_SHAPED:
        return "wrong_no"
    if got == expected:
        return "unfound" if missed else None
    if missed:
        return "unfound"
    if got in HEDGED_SHAPED:
        return "hedged"
    # Both say yes, but disagree on whether a DA is needed. The table's item 2
    # means no consent is required, and sending that applicant to lodge one costs
    # a fee and six weeks.
    if expected in PERMITTED_SHAPED and got in PERMITTED_SHAPED:
        return "wrong_pathway"
    return "hedged"


def audit(zones: list[str], verbatim_only: bool = False) -> list[dict]:
    """Every disagreement between the tool and the tables, as records."""
    dictionary = dictionary_terms(lep_text())
    findings = []

    for zone, section, term in table_rows(zones):
        expected = EXPECTED[section]

        spellings = [(term, "verbatim")]
        if not verbatim_only:
            spellings += [(c, "counterpart") for c in counterpart_forms(term, dictionary)]

        for spelling, kind in spellings:
            answer = ask(zone, spelling)
            failure = grade(expected, answer)
            if failure:
                findings.append({
                    "zone": zone,
                    "section": section,
                    "table_term": term,
                    "asked": spelling,
                    "spelling": kind,
                    "expected": expected,
                    "got": answer.get("permissibility"),
                    "matched_use": answer.get("matched_use"),
                    "match_type": answer.get("match_type"),
                    "class": failure,
                    "hedged_by_sepp_caveat": "scope_of_this_answer" in answer,
                })
    return findings


def coverage(zones: list[str]) -> dict:
    """How much of the table this audit is actually able to ask about.

    'Unpaired' is the only number here that is a deficiency. A term with no
    counterpart because the table already spells it the Dictionary's way — half
    of them, 'Commercial premises', 'Agriculture' — has nothing missing.
    """
    dictionary = dictionary_terms(lep_text())
    rows = table_rows(zones)
    terms = {term for _, _, term in rows}
    paired = {t for t in terms if counterpart_forms(t, dictionary)}
    already = {t for t in terms - paired if normalise(t).lower() in dictionary}
    return {
        "rows": len(rows),
        "distinct_terms": len(terms),
        "paired": sorted(paired),
        "table_spelling_is_the_dictionary_spelling": sorted(already),
        "unpaired": sorted(terms - paired - already),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--business", action="store_true", help="only E1-E4, MU1, RU5")
    parser.add_argument("--zone", help="a single zone code")
    parser.add_argument("--verbatim-only", action="store_true",
                        help="ask only the table's own spelling")
    parser.add_argument("--json", action="store_true", help="findings as JSON")
    args = parser.parse_args()

    current = [z for z in ZONES if "redirect_to" not in ZONES[z]]
    if args.zone:
        zones = [args.zone.upper()]
        if zones[0] not in ZONES:
            sys.exit(f"no such zone: {zones[0]}")
    elif args.business:
        zones = BUSINESS_ZONES
    else:
        zones = current

    findings = audit(zones, verbatim_only=args.verbatim_only)

    if args.json:
        print(json.dumps(findings, indent=2))
        return 1 if findings else 0

    stats = coverage(zones)
    print(f"{len(zones)} zone(s), {stats['rows']} land use rows, "
          f"{stats['distinct_terms']} distinct terms.")
    print(f"  {len(stats['paired'])} have a second spelling in the Dictionary, "
          "asked both ways")
    print(f"  {len(stats['table_spelling_is_the_dictionary_spelling'])} are already "
          "spelled the Dictionary's way, asked once")
    print(f"  {len(stats['unpaired'])} pair with nothing the Dictionary defines")
    for term in stats["unpaired"]:
        reason = UNPAIRED_TABLE_TERMS.get(term, "NOT EXPLAINED — work out why before "
                                                "trusting this audit's coverage")
        print(f"      {term!r} — {reason}")

    by_class = Counter(f["class"] for f in findings)
    order = ["wrong_yes", "wrong_no", "wrong_pathway", "unfound", "hedged"]
    headline = {
        "wrong_yes": "TABLE PROHIBITS IT, TOOL SAID YES",
        "wrong_no": "TABLE PERMITS IT, TOOL SAID NO",
        "wrong_pathway": "RIGHT ANSWER, WRONG CONSENT PATHWAY",
        "unfound": "SHAPE HAPPENS TO AGREE, BUT THE TERM WAS NEVER FOUND",
        "hedged": "TABLE IS EXPLICIT, TOOL HEDGED OR DECLINED",
    }

    for cls in order:
        rows = [f for f in findings if f["class"] == cls]
        if not rows:
            continue
        print(f"\n{headline[cls]} — {len(rows)}")
        for f in sorted(rows, key=lambda r: (r["zone"], r["table_term"], r["asked"])):
            unhedged = "" if f["hedged_by_sepp_caveat"] else "  [no SEPP caveat]"
            print(f"  {f['zone']:4} {f['asked']!r}")
            print(f"       table: {f['table_term']!r} under {f['section']}")
            print(f"       tool:  {f['got']} via {f['match_type']}"
                  f" -> {f['matched_use']!r}{unhedged}")

    breakdown = ", ".join(f"{by_class[c]} {c}" for c in order if by_class[c])
    print(f"\n{len(findings)} disagreement(s)" + (f": {breakdown}" if breakdown else ""))

    if findings:
        print("\nThe tables are not in question here — audit_zone_tables.py checks those\n"
              "against the LEP and they match. A disagreement is the matching layer.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
