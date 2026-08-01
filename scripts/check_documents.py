#!/usr/bin/env python3
"""Validate the documents/ tree.

Everything here is committed and published, and the document tools search PDF
text — so a file that is secretly an error page surfaces as an *answer to a
planning question*. Fifteen such files were committed once (see
documents/DOCUMENT_INDEX.md); this is the check that would have caught them.

Checks, per file:
  * it is a real PDF or a readable .txt
  * it contains text (looking past a graphical cover page)
  * it is not an "Access Denied" / "Page Not Found" body
  * a DCP chapter is not the superseded LEP 2000 edition filed as if current
  * it has an entry in documents/DOCUMENT_INDEX.md
  * it sits in a category the tools actually search (config.DOC_CATEGORIES)

Usage:
    .venv/bin/python scripts/check_documents.py            # everything
    .venv/bin/python scripts/check_documents.py --new      # only files git sees as new
Exit code is non-zero if anything failed, so CI can gate on it.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "documents"
INDEX = DOCS / "DOCUMENT_INDEX.md"

ERROR_MARKERS = ("access denied", "page not found", "just a moment",
                 "enable javascript", "checking your browser", "403 forbidden")

# A chapter whose own text says LEP 2000 but whose filename does not admit it.
# Getting this backwards publishes superseded controls as current — see
# SCRAPER.md §6, where both editions sit on the council page under identical
# link text.
SUPERSEDED_RE = re.compile(r"\bLEP\s*2000\b|Local Environmental Plan\s*2000", re.I)


def opening_text(path: Path, pages: int = 5) -> str:
    if path.suffix.lower() == ".txt":
        return path.read_text(errors="replace")[:20000]
    import fitz
    with fitz.open(path) as doc:
        return "\n".join(doc[i].get_text() for i in range(min(pages, doc.page_count)))


def check(path: Path, index_text: str, categories: set[str]) -> list[str]:
    rel = path.relative_to(DOCS).as_posix()
    problems = []

    category = rel.split("/")[0]
    if "/" in rel and category not in categories:
        problems.append(
            f"lives in '{category}/', which is not in DOC_CATEGORIES — no tool can reach it")

    # .txt extracts are legitimately short — several are a single LEP clause.
    size = path.stat().st_size
    floor = 400 if path.suffix.lower() == ".txt" else 2000
    if size < floor:
        problems.append(f"suspiciously small ({size} bytes)")

    if path.suffix.lower() == ".pdf" and path.read_bytes()[:5] != b"%PDF-":
        problems.append("not a PDF despite the extension")
        return problems

    try:
        text = opening_text(path)
    except Exception as exc:                                  # noqa: BLE001
        problems.append(f"unreadable ({type(exc).__name__})")
        return problems

    stripped = " ".join(text.split())
    if len(stripped) < 200:
        problems.append("almost no text in the opening pages — scan, stub or error page")
    lowered = stripped.lower()
    for marker in ERROR_MARKERS:
        if marker in lowered[:4000]:
            problems.append(f"opening text contains {marker!r} — this looks like an error page")
            break

    if category == "dcp" and not re.search(r"lep[-_]?2000", path.name, re.I):
        if SUPERSEDED_RE.search(stripped[:3000]):
            problems.append(
                "text refers to LEP 2000 but the filename does not — a superseded chapter "
                "filed as if current (SCRAPER.md §6)")

    if path.name not in index_text:
        problems.append("no entry in documents/DOCUMENT_INDEX.md")

    return problems


def ignored(path: Path) -> bool:
    """Skip anything git ignores — documents/output/ holds generated SEEs with
    applicant details, which are deliberately never committed."""
    return subprocess.run(
        ["git", "check-ignore", "-q", str(path)], cwd=ROOT,
    ).returncode == 0


def changed_files() -> set[Path]:
    out = subprocess.run(
        ["git", "status", "--porcelain", "--", "documents"],
        capture_output=True, text=True, cwd=ROOT,
    ).stdout
    paths = set()
    for line in out.splitlines():
        name = line[3:].strip().strip('"')
        p = ROOT / name
        if p.is_dir():
            paths.update(q for q in p.rglob("*") if q.is_file())
        elif p.exists():
            paths.add(p)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new", action="store_true",
                        help="only files git reports as added or modified")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT / "src"))
    from lismore_da_mcp.config import DOC_CATEGORIES

    index_text = INDEX.read_text() if INDEX.exists() else ""
    targets = sorted(
        p for p in DOCS.rglob("*")
        if p.is_file() and p.suffix.lower() in {".pdf", ".txt"} and p.name != "DOCUMENT_INDEX.md"
        and not ignored(p)
    )
    if args.new:
        new = changed_files()
        targets = [p for p in targets if p in new]
        if not targets:
            print("No new or modified documents.")
            return 0

    failed = 0
    for path in targets:
        problems = check(path, index_text, set(DOC_CATEGORIES))
        if problems:
            failed += 1
            print(f"\n✗ {path.relative_to(DOCS)}")
            for problem in problems:
                print(f"    - {problem}")

    print(f"\n{len(targets)} document(s) checked, {failed} with problems.")
    if failed:
        print(
            "\nA failing file is not automatically junk — check it by hand before deleting.\n"
            "But do not commit one until you know which it is.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
