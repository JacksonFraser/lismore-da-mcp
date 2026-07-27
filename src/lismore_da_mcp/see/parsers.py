"""Parsing free-text address, lot/DP and parking rates into form fields.

A wrong result here is written into a box on a document that goes to Council, so
these refuse rather than guess. See tests/test_parsers.py.
"""

import math
import re

def parse_street_address(
    property_address: str,
    unit: str = "",
    street_number: str = "",
    street: str = "",
    suburb: str = "",
) -> dict:
    """Split an address into the form's boxes, preferring explicitly supplied parts.

    The free-text fallback handles tenancy prefixes ("Shop 3, 88 Keen Street"),
    which the previous first-token-before-the-comma approach shifted one box left.
    """
    parts = {
        "unit": unit.strip(),
        "street_number": street_number.strip(),
        "street": street.strip(),
        "suburb": suburb.strip(),
    }
    if parts["street_number"] and parts["street"]:
        return parts

    text = property_address.strip()
    if not text:
        return parts

    segments = [s.strip() for s in text.split(",") if s.strip()]

    # Suburb: the last segment that isn't just NSW and/or a postcode
    if not parts["suburb"]:
        for segment in reversed(segments[1:] or segments):
            candidate = re.sub(r"\b\d{4}\b", "", segment)
            candidate = re.sub(r"\bNSW\b", "", candidate, flags=re.I)
            candidate = " ".join(candidate.split())
            if candidate:
                parts["suburb"] = candidate
                break

    # Street: work through the leading segments, peeling off any tenancy prefix
    street_text = segments[0] if segments else ""
    prefix = re.match(r"^(shop|unit|suite|tenancy|villa|apartment|apt)\s*([\w/-]+)?\s*$", street_text, re.I)
    if prefix and len(segments) > 1:
        # "Shop 3, 88 Keen Street, ..." — the tenancy is its own segment
        if not parts["unit"]:
            parts["unit"] = " ".join(w for w in prefix.groups() if w).strip()
        street_text = segments[1]
    else:
        inline = re.match(r"^(shop|unit|suite|tenancy|villa|apartment|apt)\s+([\w/-]+)[,\s]+(.*)$", street_text, re.I)
        if inline:
            if not parts["unit"]:
                parts["unit"] = f"{inline.group(1)} {inline.group(2)}".strip()
            street_text = inline.group(3)

    number = re.match(r"^(\d+[A-Za-z]?(?:\s*[-–/]\s*\d+[A-Za-z]?)?)\s+(.*)$", street_text.strip())
    if number:
        parts["street_number"] = parts["street_number"] or number.group(1).replace(" ", "")
        parts["street"] = parts["street"] or number.group(2).strip()
    else:
        parts["street"] = parts["street"] or street_text.strip()

    return parts

def parse_land_identifier(
    lot_dp: str = "",
    lot: str = "",
    plan_type: str = "",
    plan_number: str = "",
    section: str = "",
) -> dict:
    """Resolve the Lot / DP / Section boxes, preferring explicitly supplied parts.

    Recognises "Lot 12 DP 758651", "12/758651", "SP 12345" and comma-separated
    variants. Returns whatever it could resolve — the caller refuses to write a
    blank land identifier rather than printing empty boxes.
    """
    resolved = {
        "lot": lot.strip(),
        "plan_type": (plan_type or "").strip().upper(),
        "plan_number": str(plan_number or "").strip(),
        "section": section.strip(),
    }
    text = " ".join((lot_dp or "").split())
    if not text:
        return resolved

    # Each part is picked up by its own keyword, so "Lot 5 Section 3 DP 1234"
    # doesn't hand the section number to the lot box.
    if not resolved["section"]:
        m = re.search(r"\bsec(?:tion)?\s*[:.]?\s*([\w-]+)", text, re.I)
        if m:
            resolved["section"] = m.group(1).strip(" ,.").upper()

    if not resolved["lot"]:
        m = re.search(r"\blot\s*[:.]?\s*([\w-]+)", text, re.I)
        if m:
            resolved["lot"] = m.group(1).strip(" ,.").upper()

    if not resolved["plan_number"]:
        m = re.search(r"\b(DP|SP|CP)\s*[:.]?\s*(\d+)", text, re.I)
        if m:
            resolved["plan_type"] = m.group(1).upper()
            resolved["plan_number"] = m.group(2)
            # "12 DP 758651" — a bare lot number ahead of the plan, no keyword
            if not resolved["lot"]:
                before = re.search(r"([\w-]+)\s*,?\s*$", text[:m.start()])
                if before and "sec" not in before.group(1).lower():
                    resolved["lot"] = before.group(1).strip(" ,.").upper()
        else:
            # 12/758651 — lot over plan, deposited plan assumed
            m = re.match(r"^(?:lot\s*)?([\w-]+)\s*/\s*(\d+)$", text, re.I)
            if m:
                resolved["lot"] = resolved["lot"] or m.group(1).upper()
                resolved["plan_type"] = "DP"
                resolved["plan_number"] = m.group(2)

    return resolved

def estimate_parking_requirement(rate_text: str, floor_area_sqm: float, num_employees: int) -> dict | None:
    """Turn a DCP Chapter 7 rate string into an indicative number of spaces.

    Returns None when the rate can't be read numerically, rather than guessing.
    """
    total = 0.0
    basis = []

    area_rate = re.search(r"1\s*(?:space)?\s*per\s*(\d+(?:\.\d+)?)\s*m", rate_text, re.I)
    if area_rate and floor_area_sqm:
        per = float(area_rate.group(1))
        total += floor_area_sqm / per
        basis.append(f"{floor_area_sqm:g}m² at 1 space per {per:g}m²")

    staff_rate = re.search(r"1\s*(?:space)?\s*per\s*(\d+)\s*(?:staff|employee)", rate_text, re.I)
    if staff_rate and num_employees:
        per = float(staff_rate.group(1))
        total += num_employees / per
        basis.append(f"{num_employees} staff at 1 space per {per:g}")

    if not basis:
        return None

    return {
        "spaces_required": math.ceil(total),
        "basis": basis,
        "rate": rate_text,
        "caveat": "Indicative only. The DCP rate may apply to a narrower area (e.g. dining area rather than gross floor area) — confirm the area basis with Council.",
    }
