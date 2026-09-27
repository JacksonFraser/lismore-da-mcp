#!/usr/bin/env python3
"""Check `data/heritage.py` against LEP 2012 and DCP Chapter 12.

ROADMAP.md S4 wrote this for the LEP clause 5.10 quotes; ROADMAP.md C1 extended
it to the chapter itself. It runs checks in both directions, because each
direction is blind to what the other catches.

**Presence.** Each LEP quote must still appear verbatim in
`documents/lep/lep-2012-nsw-full.txt`. That text is a fetched snapshot of
legislation.nsw.gov.au, so a mismatch means the clause was amended rather than
that a transcription slipped — the same reading `audit_timing.py` applies. Each
Chapter 12 quote must appear verbatim in the chapter PDF, and each conservation
area's LEP name and Heritage Map label must appear as a row of Schedule 5 Part 2.

**Completeness.** Counted off the document, never off a hardcoded expectation:
every bullet in the chapter must open a stored quote; every PREFERRED and NOT
ENCOURAGED heading must belong to a stored guideline; every numbered objective,
every conservation area heading and every Schedule 5 Part 2 row must be carried;
and every figure with a unit in the chapter must appear in a stored quote. The
last one is the check a figure nobody transcribed cannot slip past — the
failure `audit_flood.py` found three requirements short of.

**Absence.** `WHAT_CHAPTER_12_DOES_NOT_SAY` records that DCP Chapter 12 requires
no heritage document, and a presence check cannot verify a negative. So this
reads the chapter and fails if a requirement appears in it — if Council reissues
Chapter 12 with a real requirement, the correction this file exists for becomes
wrong and has to be revisited. `audit_standards.py` asserts absences for the
same reason: a checker that only looks at what is stored is structurally blind
to the claim that something is not there.

**Modality.** The point of S4 is one word. cl 5.10(5) must still say the consent
authority *may* require a document, and cl 5.10(10) must still say consent may
be granted *even though* the development would otherwise not be allowed. If
either becomes mandatory or is repealed, everything this repo now says about
heritage documents is wrong in the other direction. The phrases the selector
reports as a flat refusal must also still occur in the chapter.

    .venv/bin/python scripts/audit_heritage.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lismore_da_mcp.data.heritage import (  # noqa: E402
    CHAPTER_12_SCOPE,
    CONSENT_NOT_REQUIRED,
    CONSENT_REQUIRED,
    CONSERVATION_AREAS,
    CONSERVATION_INCENTIVES,
    CONSERVATION_MANAGEMENT_PLAN,
    CONSIDERATION_IS_MANDATORY,
    DESIGN_GUIDELINES,
    HERITAGE_ASSESSMENT,
    HERITAGE_IMPACT_STATEMENT_DEFINITION,
    HERITAGE_MANAGEMENT_DOCUMENT,
    HOW_THE_CHAPTER_APPLIES,
    OBJECTIVES,
    PRECINCT_POLICIES_INTRO,
    PRINCIPLES,
    REFUSAL_PHRASES,
    WHAT_CHAPTER_12_DOES_ASK_FOR,
    WHAT_CHAPTER_12_DOES_NOT_SAY,
)

LEP_PATH = ROOT / "documents" / "lep" / "lep-2012-nsw-full.txt"
CHAPTER_12 = ROOT / "documents" / "dcp" / "chapter-12-heritage-conservation.pdf"

QUOTED = {
    "heritage management document (Dictionary)": HERITAGE_MANAGEMENT_DOCUMENT,
    "cl 5.10(2) requirement for consent": CONSENT_REQUIRED,
    "cl 5.10(3) when consent not required": CONSENT_NOT_REQUIRED,
    "cl 5.10(3)(d) exempt development": {
        "clause": "cl 5.10(3)(d)",
        "quote": CONSENT_NOT_REQUIRED["exempt_development_quote"],
    },
    "cl 5.10(4) consideration is mandatory": CONSIDERATION_IS_MANDATORY,
    "cl 5.10(5) heritage assessment": HERITAGE_ASSESSMENT,
    "cl 5.10(6) conservation management plans": CONSERVATION_MANAGEMENT_PLAN,
    "cl 5.10(10) conservation incentives": CONSERVATION_INCENTIVES,
}

# Phrases that would mean Chapter 12 had started requiring a heritage document.
# Deliberately broader than the exact sentence this repo used to assert: the
# check is "has the chapter gained a requirement", not "has this typo returned".
CHAPTER_12_MUST_NOT_REQUIRE = [
    r"heritage impact statement (?:is|shall be|must be) (?:required|submitted|provided)",
    r"(?:must|shall) (?:be accompanied by|submit|provide|prepare) a heritage impact statement",
    r"a heritage impact statement (?:must|shall) accompany",
]

# Every page carries this running header. It is not part of any quote, and
# leaving it in would break every quote that spans a page break — Spinks Park's
# statement of significance and two bullets among them.
RUNNING_HEADER = re.compile(
    r"Lismore Development Control Plan\s*[-–—]\s*Part A\s*Chapter 12\s*[-–—]\s*Page \d+")

# Page 9 carries a photograph whose extracted text is scanner noise containing
# four "•" glyphs ("--••·", "~. Y, •.", and a lone one before the page 10
# "PREFERRED" heading). None opens a policy. Pinned as a count so a real bullet
# cannot be waved through as noise: if extraction changes, this number changes
# and the test says so.
KNOWN_NON_TEXT_BULLETS = 4


def normalise(text: str) -> str:
    """Collapse whitespace and settle the dashes the LEP mixes."""
    text = text.replace("\xa0", " ").replace("—", "—").replace("–", "—")
    text = text.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip()


def fold(text: str) -> str:
    """Compare Chapter 12 on wording, not typography or case.

    The chapter uses curly quotes around ‘colorbond’ and ‘good neighbours’, an
    en dash in "1891 – 94", and "m2" for square metres. None changes a policy.
    """
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-").replace("m²", "m2")
    return " ".join(text.lower().split())


def lep_text() -> str:
    if not LEP_PATH.exists():
        sys.exit(f"missing {LEP_PATH} — run scripts/fetch_lep_full.py")
    return normalise(LEP_PATH.read_text(encoding="utf-8"))


def _chapter_pages() -> list[str]:
    if not CHAPTER_12.exists():
        sys.exit(f"missing {CHAPTER_12}")
    import fitz

    with fitz.open(CHAPTER_12) as doc:
        return [page.get_text() for page in doc]


def chapter_12_text() -> str:
    return normalise("\n".join(_chapter_pages()))


def chapter_12_body() -> str:
    """The chapter with running headers removed, case and whitespace kept."""
    return " ".join(" ".join(RUNNING_HEADER.sub(" ", p).split()) for p in _chapter_pages())


# --- the LEP ----------------------------------------------------------------

def quote_findings(raw: str) -> list[str]:
    problems = []
    for label, entry in QUOTED.items():
        if normalise(entry["quote"]) not in raw:
            problems.append(
                f"{label} ({entry['clause']}): the stored quote is not in the LEP text. "
                "Either the clause was amended or the transcription drifted."
            )
    return problems


def modality_findings(raw: str) -> list[str]:
    """The one word S4 turns on, plus the one 5.10(10) turns on."""
    problems = []
    if "The consent authority may, before granting consent to any development" not in raw:
        problems.append(
            "cl 5.10(5) no longer reads 'The consent authority may' — the heritage "
            "assessment power may have become mandatory, and every 'may' this repo now "
            "says about heritage documents would be wrong."
        )
    if "within the vicinity of land referred to in paragraph (a) or (b)" not in raw:
        problems.append(
            "cl 5.10(5)(c) no longer reaches land in the vicinity of a heritage item. "
            "Neighbouring sites would no longer be caught, and this repo says they are."
        )
    if "even though development for that purpose would otherwise not be allowed by this Plan" not in raw:
        problems.append(
            "cl 5.10(10) no longer permits a use the Plan would otherwise disallow. "
            "check_permissibility offers this as a pathway past a prohibited result."
        )
    return problems


SCHEDULE_5_PART_2_ROW = re.compile(r"([^\n\t]+?)\s*\t\s*Shown by red hatching and labelled “(C\d+)”\s*\t\s*(\w+)")


def schedule_5_part_2_rows(lep_raw: str) -> list[tuple[str, str, str]]:
    """(name, map label, significance) for every conservation area the LEP lists.

    Read off the unnormalised text, where the table's tab separators survive.
    """
    return [(n.strip(), label, sig) for n, label, sig in SCHEDULE_5_PART_2_ROW.findall(lep_raw)]


def conservation_area_findings(lep_raw: str) -> list[str]:
    """Both directions against Schedule 5 Part 2: every stored area is a row with
    the stored label and significance, and every row is a stored area."""
    rows = {name.replace("’", "'"): (label, sig) for name, label, sig in schedule_5_part_2_rows(lep_raw)}
    problems = []
    stored = {}
    for key, area in CONSERVATION_AREAS.items():
        name = area["lep_name"].replace("’", "'")
        stored[name] = key
        if name not in rows:
            problems.append(f"{key}: '{area['lep_name']}' is not a row of LEP Schedule 5 Part 2.")
            continue
        label, sig = rows[name]
        if label != area["heritage_map_label"]:
            problems.append(f"{key}: Heritage Map label is {label} in the LEP, "
                            f"{area['heritage_map_label']} here.")
        if sig != area["lep_significance"]:
            problems.append(f"{key}: significance is {sig} in the LEP, "
                            f"{area['lep_significance']} here.")
    for name in rows:
        if name not in stored:
            problems.append(f"LEP Schedule 5 Part 2 lists '{name}', which data/heritage.py "
                            "does not carry.")
    if not rows:
        problems.append("No Schedule 5 Part 2 rows were found in the LEP text — the table "
                        "layout changed and this check is reading nothing.")
    return problems


# --- the chapter --------------------------------------------------------------

def chapter_quotes() -> list[tuple[str, str]]:
    """Every Chapter 12 string carried, labelled for the report."""
    quotes: list[tuple[str, str]] = []
    for key in ("applies_to", "non_listed_properties", "read_with", "trigger",
                "external_changes_note"):
        quotes.append((f"scope.{key}", CHAPTER_12_SCOPE[key]))
    quotes += [(f"objective {i}", q) for i, q in enumerate(OBJECTIVES, 1)]
    quotes += [("12.3 must comply", HOW_THE_CHAPTER_APPLIES["must_comply"]),
               ("12.3 variation", HOW_THE_CHAPTER_APPLIES["variation"]),
               ("12.2 heritage impact statement", HERITAGE_IMPACT_STATEMENT_DEFINITION["quote"]),
               ("12.6 intro", PRECINCT_POLICIES_INTRO["quote"])]
    quotes += [(f"asks for: {a['section']}", a["quote"]) for a in WHAT_CHAPTER_12_DOES_ASK_FOR]
    for key in ("burra_charter_approach", "burra_charter_intro", "understanding_heritage_value",
                "original_fabric_intro"):
        quotes.append((f"12.4 {key}", PRINCIPLES[key]))
    for key in ("why_conserve", "burra_charter_principles", "original_fabric"):
        quotes += [(f"12.4 {key}[{i}]", q) for i, q in enumerate(PRINCIPLES[key], 1)]
    for key, element in DESIGN_GUIDELINES.items():
        quotes.append((f"12.5 {key}.heading", element["heading"]))
        for field in ("intro", "guidance_label"):
            if field in element:
                quotes.append((f"12.5 {key}.{field}", element[field]))
        for field in ("guidance", "preferred", "not_encouraged"):
            quotes += [(f"12.5 {key}.{field}[{i}]", q)
                       for i, q in enumerate(element.get(field, []), 1)]
    for key, area in CONSERVATION_AREAS.items():
        quotes.append((f"12.6 {key}.heading", area["dcp_heading"]))
        if "also_applies" in area:
            quotes.append((f"12.6 {key}.also_applies", area["also_applies"]))
        for field in ("statement_of_significance", "characteristics", "policies"):
            quotes += [(f"12.6 {key}.{field}[{i}]", q) for i, q in enumerate(area[field], 1)]
    return quotes


def chapter_quote_findings(body: str) -> list[str]:
    haystack = fold(body)
    return [
        f"{label}: not in DCP Chapter 12 — {quote[:100]!r}"
        for label, quote in chapter_quotes()
        if fold(quote) not in haystack
    ]


def _opening(text: str) -> str:
    """The first sentence or clause of a bullet, capped at 50 characters.

    Enough to tell whether a bullet was transcribed, and short enough that the
    last bullet of a list is not judged on the heading that follows it.
    """
    text = fold(text)
    cut = len(text)
    for mark in (". ", ";"):
        at = text.find(mark)
        if 0 < at < cut:
            cut = at
    if text.endswith(".") and len(text) - 1 < cut:
        cut = len(text) - 1
    return text[:min(cut, 50)]


def bullet_segments(body: str) -> tuple[list[str], int]:
    """(text of every real bullet, count of bullet glyphs that open no text)."""
    real, noise = [], 0
    for segment in body.split("•")[1:]:
        segment = segment.strip()
        if len(segment) < 20 or not segment[:1].isalpha():
            noise += 1
            continue
        real.append(segment)
    return real, noise


def uncarried_bullets(body: str) -> tuple[list[str], int]:
    carried = [fold(q) for _, q in chapter_quotes()]
    real, noise = bullet_segments(body)
    missed = [s[:120] for s in real if not any(_opening(s) in c for c in carried)]
    return missed, noise


def structure_findings(body: str) -> list[str]:
    """Headings and numbered items counted off the document."""
    problems = []
    preferred = len(re.findall(r"(?<!NOT )\bPREFERRED\b", body))
    discouraged = body.count("NOT ENCOURAGED")
    stored_pref = sum(1 for e in DESIGN_GUIDELINES.values() if "preferred" in e)
    stored_disc = sum(1 for e in DESIGN_GUIDELINES.values() if "not_encouraged" in e)
    if preferred != stored_pref:
        problems.append(f"The chapter has {preferred} PREFERRED lists; {stored_pref} are carried.")
    if discouraged != stored_disc:
        problems.append(f"The chapter has {discouraged} NOT ENCOURAGED lists; "
                        f"{stored_disc} are carried.")

    lowered = body.lower()
    start = lowered.find("objectives of this chapter")
    end = lowered.find("12.2 definitions")
    objectives = len(re.findall(r"\b\d\. to ", lowered[start:end])) if start != -1 else 0
    if objectives != len(OBJECTIVES):
        problems.append(f"§12.1 has {objectives} numbered objectives; {len(OBJECTIVES)} carried.")

    areas = len(re.findall(r"characteristics that define this heritage conservation area", lowered))
    statements = len(re.findall(r"statement of significance", lowered))
    for label, count in (("'Characteristics that define' headings", areas),
                         ("'Statement of significance' headings", statements)):
        if count != len(CONSERVATION_AREAS):
            problems.append(f"§12.6 has {count} {label}; {len(CONSERVATION_AREAS)} "
                            "conservation areas are carried.")
    return problems


FIGURE = re.compile(r"\b\d+(?:\.\d+)?\s?(?:metres?|m2|m²|mm|hectares?|ha)\b", re.I)


def uncarried_figures(body: str) -> list[str]:
    """Every figure with a unit in the chapter must be in a stored quote.

    Chapter 12 has five. A figure nobody transcribed is the one kind of gap a
    presence check cannot report, and the kind this repo has paid for most.
    """
    carried = " ".join(fold(q) for _, q in chapter_quotes())
    return sorted({m.group(0) for m in FIGURE.finditer(body) if fold(m.group(0)) not in carried})


def refusal_findings(body: str) -> list[str]:
    haystack = fold(body)
    return [f"'{p}' is reported as a refusal but no longer occurs in DCP Chapter 12."
            for p in REFUSAL_PHRASES if p not in haystack]


def chapter_12_findings(chapter: str) -> list[str]:
    """The absence check. A presence check cannot verify a negative."""
    problems = []
    for pattern in CHAPTER_12_MUST_NOT_REQUIRE:
        match = re.search(pattern, chapter, re.I)
        if match:
            problems.append(
                f"DCP Chapter 12 now contains {match.group(0)!r}. This repo records that the "
                "chapter requires no heritage document (WHAT_CHAPTER_12_DOES_NOT_SAY) and "
                "cites LEP cl 5.10(5) instead. If the chapter was reissued, that correction "
                "needs revisiting."
            )
    mentions = len(re.findall(r"heritage impact statement", chapter, re.I))
    if mentions != 2:
        problems.append(
            f"'heritage impact statement' appears {mentions} times in DCP Chapter 12; both "
            "known occurrences are definitions and there were exactly 2 on 2026-08-20. A "
            "change means the chapter was reissued — read the new text before trusting "
            "WHAT_CHAPTER_12_DOES_NOT_SAY."
        )
    return problems


def main() -> int:
    raw = lep_text()
    lep_raw = LEP_PATH.read_text(encoding="utf-8")
    chapter = chapter_12_text()
    body = chapter_12_body()

    missed_bullets, noise = uncarried_bullets(body)
    bullet_problems = [f"not carried: {b!r}" for b in missed_bullets]
    if noise != KNOWN_NON_TEXT_BULLETS:
        bullet_problems.append(
            f"{noise} bullet glyphs open no text (expected {KNOWN_NON_TEXT_BULLETS}, the page 9 "
            "scanner noise). A real bullet may be being skipped as noise.")

    groups = [
        ("LEP QUOTES NOT FOUND IN THE LEP", quote_findings(raw)),
        ("THE CLAUSE NO LONGER SAYS WHAT THIS REPO SAYS IT SAYS", modality_findings(raw)),
        ("CONSERVATION AREAS DISAGREE WITH LEP SCHEDULE 5 PART 2", conservation_area_findings(lep_raw)),
        ("CHAPTER 12 QUOTES NOT FOUND IN THE CHAPTER", chapter_quote_findings(body)),
        ("CHAPTER 12 BULLETS NOT CARRIED", bullet_problems),
        ("CHAPTER 12 STRUCTURE NOT CARRIED", structure_findings(body)),
        ("CHAPTER 12 FIGURES NOT CARRIED", [f"'{f}'" for f in uncarried_figures(body)]),
        ("REFUSAL PHRASES THE CHAPTER NO LONGER USES", refusal_findings(body)),
        ("DCP CHAPTER 12 HAS CHANGED", chapter_12_findings(chapter)),
    ]

    real, _ = bullet_segments(body)
    print(f"{len(QUOTED)} LEP provisions checked against {LEP_PATH.name}")
    print(f"{len(chapter_quotes())} Chapter 12 quotes checked against {CHAPTER_12.name}")
    print(f"{len(real)} bullets in the chapter, {len(CONSERVATION_AREAS)} conservation areas, "
          f"{len(FIGURE.findall(body))} figures counted off the document")
    print("DCP Chapter 12 checked for a heritage document requirement it must not contain")
    print(f"\nsay instead: {WHAT_CHAPTER_12_DOES_NOT_SAY['say_instead']}")

    total = 0
    for heading, problems in groups:
        if not problems:
            continue
        total += len(problems)
        print(f"\n{heading} — {len(problems)}")
        for problem in problems:
            print(f"  {problem}")

    print(f"\n{total} problem(s)." if total else "\nAll checks pass.")
    if total:
        print("\nRead the chapter before editing — do not adjust the stored text to make this\n"
              "pass. A mismatch means either the source was reissued or the transcription drifted.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
