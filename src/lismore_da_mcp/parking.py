"""Turn a DCP Chapter 7 rate into a number of spaces — or decline to.

The rates in Schedule 1 are not all one shape. Some are a simple area rate, some
add several components, some take the greater of two entirely different bases,
some tier by floor area, and several are "assessed on merits". The previous
estimator read the rate out of a prose string with a regex, so it could only ever
see one area-based component: the café rule — *1 per 3 seats, plus 1 per 2
employees or 15 per 100m2 GFA, whichever is greater* — was unreadable to it.

There are two kinds of "whichever is greater" here, and conflating them is what
made the café rule wrong even after it became structured. `or_` and `or_alt`
alternate against the **whole** requirement: the boarding house rule offers two
complete formulas and takes the larger. A `greater_of` component alternates
**within** the sum: the café takes staff spaces plus the larger of two measures
of customer capacity. Both are in Schedule 1 and they are not interchangeable —
see the note above `_RESTAURANT` in `data/parking.py` for what settled which
applies where.

This evaluates the structured `spec` on each entry instead, and returns None
when it cannot honestly produce a figure. Declining is the right answer more
often than it looks: parking is what a Council assessment argues about, and a
confident wrong space count is what sends a DA back.
"""

import math

from lismore_da_mcp.data.parking import COUNTABLE


def _component(part: dict, floor_area_sqm: float | None, counts: dict) -> float | None:
    """One term of a requirement. None means it cannot be evaluated."""
    if "greater_of" in part:
        # A component that is itself an alternation — two measures of the same
        # thing, of which the rate takes the larger. Distinct from the spec-level
        # `or_`, which alternates against the *whole* sum. The café rule needs
        # this one: staff spaces are added, and the greater is taken between the
        # two measures of customer capacity. See the note in data/parking.py.
        values = [_component(p, floor_area_sqm, counts) for p in part["greater_of"]]
        usable = [v for v in values if v is not None]
        return max(usable) if usable else None
    if "per_area" in part:
        if not floor_area_sqm:
            return None
        return part["rate"] * (floor_area_sqm / part["per_area"])
    if "one_per" in part:
        value = counts.get(part["of"])
        return None if not value else value / part["one_per"]
    if "per" in part:
        value = counts.get(part["per"])
        return None if not value else part["rate"] * value
    return None


def _describe(part: dict, floor_area_sqm: float | None, counts: dict) -> str:
    """How a component was arrived at, for the `basis` shown to the applicant."""
    if "greater_of" in part:
        best, description = None, ""
        for alternative in part["greater_of"]:
            value = _component(alternative, floor_area_sqm, counts)
            if value is not None and (best is None or value > best):
                best, description = value, _describe(alternative, floor_area_sqm, counts)
        others = len([p for p in part["greater_of"]
                      if _component(p, floor_area_sqm, counts) is not None]) - 1
        return description + (" (the greater of the two bases)" if others > 0 else "")
    if "per_area" in part:
        return f"{floor_area_sqm:g}m² at {part['rate']:g} per {part['per_area']:g}m²"
    if "one_per" in part:
        return f"{counts[part['of']]:g} {part['of']} at 1 per {part['one_per']:g}"
    return f"{counts[part['per']]:g} {part['per']} at {part['rate']:g} each"


def _needs(part: dict) -> list[str]:
    """The inputs a component could not be evaluated without."""
    if "greater_of" in part:
        return [name for alternative in part["greater_of"] for name in _needs(alternative)]
    if "per_area" in part:
        return ["floor area"]
    return [part.get("of") or part.get("per")]


def _evaluate(parts: list, floor_area_sqm: float | None, counts: dict):
    """Sum a component list. Returns (total, [descriptions], [unmet inputs])."""
    total = 0.0
    described, missing = [], []
    for part in parts:
        value = _component(part, floor_area_sqm, counts)
        if value is None:
            missing.extend(_needs(part))
            continue
        total += value
        described.append(_describe(part, floor_area_sqm, counts))
    return total, described, missing


def estimate_spaces(entry: dict, floor_area_sqm: float | None = None,
                    counts: dict | None = None) -> dict | None:
    """Spaces required by this entry, or None if the rule cannot be applied.

    `counts` holds whatever the caller could supply — seats, employees, children
    and so on, keyed as in `data.parking.COUNTABLE`.
    """
    spec = entry.get("spec")
    if not spec:
        return None
    counts = {k: v for k, v in (counts or {}).items() if v}
    for key, value in (spec.get("defaults") or {}).items():
        counts.setdefault(key, value)

    if "tiers" in spec:
        if not floor_area_sqm:
            return None
        for tier in spec["tiers"]:
            limit = tier.get("up_to_area")
            if limit is None or floor_area_sqm <= limit:
                total = tier["rate"] * (floor_area_sqm / tier["per_area"])
                basis = [f"{floor_area_sqm:g}m² at {tier['rate']:g} per {tier['per_area']:g}m²"
                         + (f" (the ≤{limit:g}m² tier)" if limit else " (the larger-area tier)")]
                break
    else:
        total, basis, missing = _evaluate(spec.get("sum", []), floor_area_sqm, counts)

        # "whichever is greater" — an alternative area rate, or an alternative
        # set of components. Only meaningful if the alternative can be evaluated.
        alternative = None
        if spec.get("or_"):
            alternative = _component(spec["or_"], floor_area_sqm, counts)
            alt_basis = (f"{floor_area_sqm:g}m² at {spec['or_']['rate']:g} per "
                         f"{spec['or_']['per_area']:g}m²") if alternative is not None else None
        elif spec.get("or_alt"):
            alt_total, alt_described, alt_missing = _evaluate(
                spec["or_alt"], floor_area_sqm, counts)
            alternative = alt_total if not alt_missing else None
            alt_basis = " plus ".join(alt_described) if alternative is not None else None

        if alternative is not None and (not basis or alternative > total):
            if basis and alternative > total:
                basis = [alt_basis, "(the greater of the two bases in the DCP rule)"]
            else:
                basis = [alt_basis]
            total = alternative
            missing = []
        elif alternative is not None and basis:
            basis.append("(greater than the alternative basis in the DCP rule)")

        if not basis:
            return None
        if missing:
            basis.append("not counted: " + ", ".join(sorted(set(m for m in missing if m))))

    spaces = math.ceil(total)
    minimum = spec.get("minimum")
    if minimum and spaces < minimum:
        spaces = minimum
        basis.append(f"raised to the DCP minimum of {minimum}")

    result = {
        "spaces_required": spaces,
        "basis": basis,
        "rate": entry["rate"],
        "source": entry.get("source"),
    }
    if entry.get("note"):
        result["caveat"] = entry["note"]
    return result


def shortfall(required: int, provided) -> dict | None:
    if provided is None:
        return None
    gap = required - provided
    return {
        "spaces_provided": provided,
        "shortfall": max(0, gap),
        "surplus": max(0, -gap),
        "meets_requirement": gap <= 0,
    }
