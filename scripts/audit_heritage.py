#!/usr/bin/env python3
"""Check `data/heritage.py` against LEP 2012 and DCP Chapter 12.

ROADMAP.md S4. Every data module here has an audit; this is the one for the
heritage provisions, and it runs three checks rather than one.

**Presence.** Each quote must still appear verbatim in
`documents/lep/lep-2012-nsw-full.txt`. That text is a fetched snapshot of
legislation.nsw.gov.au, so a mismatch means the clause was amended rather than
that a transcription slipped — the same reading `audit_timing.py` applies.

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
heritage documents is wrong in the other direction.

    .venv/bin/python scripts/audit_heritage.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lismore_da_mcp.data.heritage import (  # noqa: E402
    CONSERVATION_INCENTIVES,
    CONSIDERATION_IS_MANDATORY,
    HERITAGE_ASSESSMENT,
    HERITAGE_MANAGEMENT_DOCUMENT,
    WHAT_CHAPTER_12_DOES_NOT_SAY,
)

LEP_PATH = ROOT / "documents" / "lep" / "lep-2012-nsw-full.txt"
CHAPTER_12 = ROOT / "documents" / "dcp" / "chapter-12-heritage-conservation.pdf"

QUOTED = {
    "heritage management document (Dictionary)": HERITAGE_MANAGEMENT_DOCUMENT,
    "cl 5.10(5) heritage assessment": HERITAGE_ASSESSMENT,
    "cl 5.10(4) consideration is mandatory": CONSIDERATION_IS_MANDATORY,
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


def normalise(text: str) -> str:
    """Collapse whitespace and settle the dashes the LEP mixes."""
    text = text.replace("\xa0", " ").replace("—", "—").replace("–", "—")
    text = text.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip()


def lep_text() -> str:
    if not LEP_PATH.exists():
        sys.exit(f"missing {LEP_PATH} — run scripts/fetch_lep_full.py")
    return normalise(LEP_PATH.read_text(encoding="utf-8"))


def chapter_12_text() -> str:
    if not CHAPTER_12.exists():
        sys.exit(f"missing {CHAPTER_12}")
    import fitz

    with fitz.open(CHAPTER_12) as doc:
        return normalise("\n".join(page.get_text() for page in doc))


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
    chapter = chapter_12_text()

    groups = [
        ("QUOTES NOT FOUND IN THE LEP", quote_findings(raw)),
        ("THE CLAUSE NO LONGER SAYS WHAT THIS REPO SAYS IT SAYS", modality_findings(raw)),
        ("DCP CHAPTER 12 HAS CHANGED", chapter_12_findings(chapter)),
    ]

    print(f"{len(QUOTED)} quoted provisions checked against {LEP_PATH.name}")
    print(f"DCP Chapter 12 checked for a requirement it must not contain")
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
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
