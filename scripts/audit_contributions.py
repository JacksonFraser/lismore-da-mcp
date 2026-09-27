#!/usr/bin/env python3
"""Check the developer contribution rates against their source documents.

PLAN.md item 2.1, and the third of the transcription audits after
`audit_zone_tables.py` and `audit_parking_rates.py`.

Two checks, because either alone would be weak:

  1. **Presence.** Every dollar figure in `data/contributions.py` still appears
     in the page of the source PDF it was taken from. This catches a reissued
     plan and an indexation amendment.

  2. **Derivation.** Table E2 is re-derived from Table E1 — occupancy times the
     per-head rates, plus PVTs times the traffic rate, plus the 4.5%
     administration loading — and compared cell by cell against the stored
     figure. A presence check cannot catch a transposed digit that happens to
     appear elsewhere on the page; this can, and it is what found the tourist
     accommodation discrepancy in the published table.

  3. **Completeness.** Every row of Table E2 is read off the PDF — the label
     column, isolated by x-position — and must be carried in
     `DEVELOPMENT_TYPE_RATES` (matched on `plan_name`) or named in
     `UNCARRIED_TABLE_E2_ROWS`. The first two checks only look at what is
     stored, so neither could see a development type the next plan review adds.

Discrepancies listed in `KNOWN_TABLE_DISCREPANCIES` are expected and reported
separately. Anything else is a failure.

    .venv/bin/python scripts/audit_contributions.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lismore_da_mcp.data.contributions import (  # noqa: E402
    ADMIN_LOADING,
    CATCHMENTS,
    DEMAND_COMPONENTS,
    DEVELOPMENT_TYPE_RATES,
    INFRASTRUCTURE_RATES,
    KNOWN_TABLE_DISCREPANCIES,
    SECTION_64_CHARGES,
    UNCARRIED_TABLE_E2_ROWS,
)

PLAN_PDF = ROOT / "documents" / "fees" / "section-7.11-contributions-plan-2024-2041.pdf"
DSP_PDF = ROOT / "documents" / "fees" / "development-servicing-plans-water-wastewater.pdf"

TABLE_E1_PAGE = 5                 # zero-based; "Summary of Contributions" p6
TABLE_E2_PAGE = 6                 # p7
DSP_TABLE_1_PAGE = 2              # p3

# The published occupancy and PVT figures are rounded to two decimals (Table E2
# note B), so a derivation can only ever land within a few cents of the printed
# total. 50c is comfortably above that and far below any real transcription error.
DERIVATION_TOLERANCE = 0.50


def page_text(pdf: Path, page: int) -> str:
    import fitz

    with fitz.open(pdf) as doc:
        return " ".join(doc[page].get_text().split())


def money_on_page(text: str) -> set[str]:
    """Every dollar figure printed on the page, normalised without separators."""
    return {m.replace(",", "") for m in re.findall(r"\$([\d,]+\.?\d*)", text)}


def formats(amount: float) -> list[str]:
    """The ways a figure might legitimately be printed, e.g. 3000 as 3000 or 3000.00."""
    return [f"{amount:.2f}", f"{amount:g}", f"{amount:.3f}"]


def check_presence(pdf: Path, page: int, label: str, amounts: dict[str, float]) -> list[str]:
    printed = money_on_page(page_text(pdf, page))
    return [
        f"{label}: {name} = {amount} not found on {pdf.name} p{page + 1}"
        for name, amount in amounts.items()
        if amount is not None and not any(f in printed for f in formats(amount))
    ]


def row_label(text: str) -> str:
    """Compare labels on wording, not typography."""
    return " ".join(text.replace("’", "'").split()).lower()


def table_e2_rows(pdf: Path = PLAN_PDF, page: int = TABLE_E2_PAGE) -> list[str]:
    """The development type labels of Table E2, read off the PDF.

    The label column is right-aligned against the Base column, so a label line is
    one that ends left of where the "Base" header starts — every cell of the Base
    column itself overhangs that point. Consecutive label lines are one wrapped
    label. Superscript note letters (the C in "Residential AccommodationC") are
    printed smaller and dropped. Only the table body is read: from the last
    header ("Rural South") to "Notes:".
    """
    import fitz

    with fitz.open(pdf) as doc:
        blocks = doc[page].get_text("dict")["blocks"]
    lines = [line for block in blocks for line in block.get("lines", [])]

    def text(line, body_size=None):
        return "".join(span["text"] for span in line["spans"]
                       if body_size is None or span["size"] >= body_size * 0.8)

    header = next((line for line in lines if text(line).strip() == "Base"), None)
    if header is None:
        return []
    boundary = header["bbox"][0]
    body_size = header["spans"][0]["size"]

    rows: list[str] = []
    current: list[str] = []
    in_body = False
    for line in lines:
        words = text(line).strip()
        if not in_body:
            in_body = words == "Rural South"
            continue
        if words.startswith("Notes:"):
            break
        if line["bbox"][2] < boundary:
            current.append(text(line, body_size))
        elif current:
            rows.append(" ".join(" ".join(current).split()))
            current = []
    if current:
        rows.append(" ".join(" ".join(current).split()))
    return rows


def completeness_problems(rows: list[str], carried: dict, uncarried: dict) -> list[str]:
    """Rows of Table E2 neither carried nor explained, and explanations for no row."""
    if not rows:
        return ["Table E2's row labels could not be read — the page layout changed"]
    in_table = {row_label(r): r for r in rows}
    stored = {row_label(entry["plan_name"]): key for key, entry in carried.items()}
    named = {row_label(r): r for r in uncarried}

    problems = [
        f"Table E2 row {in_table[label]!r} is neither in DEVELOPMENT_TYPE_RATES nor "
        f"named in UNCARRIED_TABLE_E2_ROWS"
        for label in in_table if label not in stored and label not in named
    ]
    problems += [
        f"DEVELOPMENT_TYPE_RATES[{key!r}] plan_name is not a row of Table E2"
        for label, key in stored.items() if label not in in_table
    ]
    problems += [
        f"UNCARRIED_TABLE_E2_ROWS names {named[label]!r}, which is not a row of Table E2"
        for label in named if label not in in_table
    ]
    problems += [
        f"{named[label]!r} is both carried and named in UNCARRIED_TABLE_E2_ROWS"
        for label in named if label in stored
    ]
    return problems


def derive(entry: dict, catchment: str) -> float:
    """Rebuild a Table E2 cell from Table E1."""
    components = DEMAND_COMPONENTS[entry["demand"]]
    per_head = sum(
        row["rates"][catchment]
        for row in INFRASTRUCTURE_RATES
        if row["category"] in components["per_head"] and row["basis"] == components["basis"]
    )
    traffic = next(
        row["rates"][catchment]
        for row in INFRASTRUCTURE_RATES
        if row["basis"] == components["traffic"]
    )
    subtotal = entry["occupancy"] * per_head + entry["pvts"] * traffic
    return subtotal * (1 + ADMIN_LOADING)


def known_discrepancy(dev_type: str, catchment: str) -> dict | None:
    return next(
        (
            d for d in KNOWN_TABLE_DISCREPANCIES
            if d["development_type"] == dev_type and catchment in d["catchments"]
        ),
        None,
    )


def main() -> int:
    problems: list[str] = []

    for pdf in (PLAN_PDF, DSP_PDF):
        if not pdf.exists():
            print(f"MISSING: {pdf}")
            return 1

    # 1. Presence — Table E1, Table E2 and the DSP charges.
    print("Checking every stored figure still appears in its source page...")
    e1 = {
        f"{row['category']} ({row['basis']}, {catchment})": row["rates"][catchment]
        for row in INFRASTRUCTURE_RATES
        for catchment in CATCHMENTS
    }
    problems += check_presence(PLAN_PDF, TABLE_E1_PAGE, "Table E1", e1)

    e2 = {
        f"{key} ({catchment})": entry["rates"][catchment]
        for key, entry in DEVELOPMENT_TYPE_RATES.items()
        for catchment in CATCHMENTS
    }
    problems += check_presence(PLAN_PDF, TABLE_E2_PAGE, "Table E2", e2)

    s64 = {
        f"{area} {service}": amount
        for area, services in SECTION_64_CHARGES.items()
        for service, amount in services.items()
        if amount
    }
    problems += check_presence(DSP_PDF, DSP_TABLE_1_PAGE, "DSP Table 1", s64)

    print(f"  {len(e1)} Table E1 rates, {len(e2)} Table E2 rates, {len(s64)} DSP charges")

    # 2. Derivation — Table E2 against Table E1.
    print("\nRe-deriving Table E2 from Table E1...")
    expected = {(d["development_type"], c) for d in KNOWN_TABLE_DISCREPANCIES for c in d["catchments"]}
    seen: set[tuple[str, str]] = set()
    matched = 0

    for key, entry in DEVELOPMENT_TYPE_RATES.items():
        for catchment in CATCHMENTS:
            published = entry["rates"][catchment]
            derived = derive(entry, catchment)
            gap = abs(derived - published)
            known = known_discrepancy(key, catchment)
            if gap <= DERIVATION_TOLERANCE:
                if known:
                    problems.append(
                        f"{key} ({catchment}): listed in KNOWN_TABLE_DISCREPANCIES but now "
                        f"reproduces exactly. Remove the entry — a stale exception hides the "
                        f"next real one."
                    )
                matched += 1
            elif known:
                seen.add((key, catchment))
                if abs(gap - known["difference"]) > DERIVATION_TOLERANCE:
                    problems.append(
                        f"{key} ({catchment}): known discrepancy has changed size — "
                        f"recorded {known['difference']:.2f}, now {gap:.2f}"
                    )
            else:
                problems.append(
                    f"{key} ({catchment}): published {published:.2f} but Table E1 derives "
                    f"{derived:.2f} (out by {gap:.2f})"
                )

    print(f"  {matched} of {len(e2)} cells reproduce within ${DERIVATION_TOLERANCE:.2f}")
    for dev_type, catchment in sorted(expected):
        entry = known_discrepancy(dev_type, catchment)
        print(f"  known discrepancy: {dev_type} ({catchment}) — "
              f"published ${entry['published']:,.2f}, derives ${entry['derived']:,.2f}")

    for stale in sorted(expected - seen):
        problems.append(
            f"{stale[0]} ({stale[1]}): listed in KNOWN_TABLE_DISCREPANCIES but was not "
            f"reached by the audit — the entry no longer describes anything."
        )

    # 3. Completeness — every row of Table E2 is carried or explained.
    print("\nChecking every development type in Table E2 is carried...")
    rows = table_e2_rows()
    found = completeness_problems(rows, DEVELOPMENT_TYPE_RATES, UNCARRIED_TABLE_E2_ROWS)
    problems += found
    if not found:
        print(f"  {len(rows)} rows: {len(DEVELOPMENT_TYPE_RATES)} carried, "
              f"{len(UNCARRIED_TABLE_E2_ROWS)} named with a reason")

    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print("\nAll contribution rates verify against their source documents.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
