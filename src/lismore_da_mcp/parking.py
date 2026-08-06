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

from lismore_da_mcp.data.parking import CBD_CASH_IN_LIEU_RATE
from lismore_da_mcp.data.parking import CBD_EXPANSION_ALLOWANCE
from lismore_da_mcp.data.parking import CBD_FIXED_RATE
from lismore_da_mcp.data.parking import CBD_OUTDOOR_DINING
from lismore_da_mcp.data.parking import CBD_PARKING_CREDIT
from lismore_da_mcp.data.parking import CBD_REDUCTIONS
from lismore_da_mcp.data.parking import COMBINED_USES
from lismore_da_mcp.data.parking import COUNTABLE
from lismore_da_mcp.data.parking import MERIT_CRITERIA
from lismore_da_mcp.data.parking import ON_STREET_LOSS


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


# Map 1 of the chapter defines the CBD and is a bitmap — nothing here can read
# it. So the caller says, or neither rate is presented as the answer.
_CBD_VALUES = {"cbd", "in_cbd", "lismore_cbd", "city_centre", "yes", "true"}
_OUTSIDE_VALUES = {"outside_cbd", "outside", "not_cbd", "no", "false"}


def cbd_location(raw: str | None) -> bool | None:
    """True = in the CBD, False = outside it, None = not stated.

    None is a real answer here and never a default to "outside": the whole
    reason `location` is an argument is that the two rates differ several-fold
    and neither is presented as the answer until the site is placed.
    """
    if not raw:
        return None
    value = str(raw).strip().lower().replace(" ", "_").replace("-", "_")
    if value in _CBD_VALUES:
        return True
    if value in _OUTSIDE_VALUES:
        return False
    return None


def uses_schedule_1_in_cbd(dev_type: str) -> bool:
    """True where §7.7.3.1 exception (i) keeps a use on Schedule 1 inside the CBD.

    Residential and tourist/visitor accommodation are carved out of the fixed
    rate. Applying 3.3/100m2 to a motel would understate it badly.
    """
    return dev_type in CBD_FIXED_RATE["excluded_uses"]


def cbd_spaces(floor_area_sqm: float | None, existing_gfa_sqm: float | None = None,
               existing_spaces_on_site: int = 0) -> dict | None:
    """The CBD requirement under §7.7.3.1, net of any §7.7.3.4 parking credit.

    Returns None when the floor area is unknown, since the fixed rate has no
    other basis to work from.

    The credit is deliberately not rounded before it is subtracted. §7.7.2
    rounds the *requirement* up to the next whole number and the DCP says
    nothing about rounding the credit, so rounding the net figure once at the
    end is the reading that neither invents a space nor gives one away.
    """
    if not floor_area_sqm:
        return None

    gross = CBD_FIXED_RATE["rate"] * (floor_area_sqm / CBD_FIXED_RATE["per_area"])
    basis = [
        f"{floor_area_sqm:g}m² GFA at {CBD_FIXED_RATE['rate']:g} spaces per "
        f"{CBD_FIXED_RATE['per_area']:g}m² (the fixed CBD rate) = {gross:.2f}"
    ]

    result = {
        "rate_applied": "CBD fixed rate",
        "gross_requirement": math.ceil(gross),
        "source": CBD_FIXED_RATE["source"],
        "rate": CBD_FIXED_RATE["verbatim"],
    }

    credit = 0.0
    if existing_gfa_sqm:
        deemed = CBD_PARKING_CREDIT["rate"] * (existing_gfa_sqm / CBD_PARKING_CREDIT["per_area"])
        credit = max(0.0, deemed - (existing_spaces_on_site or 0))
        basis.append(
            f"less a deemed parking credit: {existing_gfa_sqm:g}m² of existing GFA at "
            f"{CBD_PARKING_CREDIT['rate']:g} per {CBD_PARKING_CREDIT['per_area']:g}m² "
            f"= {deemed:.2f}, less {existing_spaces_on_site or 0} space(s) already on the "
            f"site = {credit:.2f}"
        )
        result["parking_credit"] = {
            "credit_spaces": round(credit, 2),
            "formula": CBD_PARKING_CREDIT["verbatim"],
            "source": CBD_PARKING_CREDIT["source"],
            "if_previously_paid": CBD_PARKING_CREDIT["evidenced_alternative"],
        }

    net = max(0, math.ceil(gross - credit))
    basis.append(f"net requirement {net} space(s)")

    result["spaces_required"] = net
    result["basis"] = basis
    if not existing_gfa_sqm:
        result["credit_not_applied"] = (
            "No existing floor area was given, so no §7.7.3.4 parking credit has been "
            "deducted. If this is a change of use or redevelopment of an existing CBD "
            "building, supply existing_gfa_sqm — the credit is often most of the "
            "requirement and is not applied automatically."
        )
    return result


def shortfall_options(gap: int, in_cbd: bool, dev_type: str = "") -> dict:
    """What the DCP actually offers a business that cannot provide the spaces.

    This is the point of the tool. A space count and a shortfall are only the
    setup; Chapter 7 contains named mechanisms for closing the gap, and a
    business that does not know they exist argues the wrong case in its SEE.
    """
    options: list[dict] = []

    if in_cbd:
        consolidated = CBD_REDUCTIONS["consolidated"]
        options.append({
            "option": consolidated["name"],
            "effect": "The requirement for each space paid out rather than built is reduced "
                      "by 25%, and the remainder is met by the payment instead of by "
                      "construction.",
            "provision": consolidated["verbatim"],
            "source": consolidated["source"],
            "rate": CBD_CASH_IN_LIEU_RATE,
        })

        shared = CBD_REDUCTIONS["shared"]
        options.append({
            "option": shared["name"],
            "effect": "Reduces the requirement for the shared component by 25%. Only worth "
                      "considering if there are spaces on the site to open up — it does not "
                      "help a tenancy with no parking at all.",
            "provision": shared["verbatim"],
            "conditions_all_of_which_apply": shared["conditions"],
            "ordering": shared["ordering"],
            "source": shared["source"],
        })

        options.append({
            "option": "Deemed parking credit for the existing building",
            "effect": "An existing CBD site is deemed to have already provided parking to the "
                      "CBD, and that amount comes off the requirement. Supply existing_gfa_sqm "
                      "to have it calculated.",
            "provision": CBD_PARKING_CREDIT["verbatim"],
            "source": CBD_PARKING_CREDIT["source"],
        })

        options.append({
            "option": "One-off floor space allowance for an existing commercial premises",
            "effect": f"Up to {CBD_EXPANSION_ALLOWANCE['percent']:.0%} of existing GFA, capped "
                      f"at {CBD_EXPANSION_ALLOWANCE['cap_sqm']}m², added without a parking "
                      "charge — once per premises, ever.",
            "provision": CBD_EXPANSION_ALLOWANCE["verbatim"],
            "note": CBD_EXPANSION_ALLOWANCE["note"],
            "source": CBD_EXPANSION_ALLOWANCE["source"],
        })

        if dev_type in ("cafe", "restaurant", "take_away"):
            options.append({
                "option": "Keep outdoor dining unenclosed",
                "effect": "An unenclosed area is not gross floor area, so it generates no "
                          "parking requirement at all. This is usually the cheapest lever a "
                          "café has.",
                "rules": CBD_OUTDOOR_DINING["rules"],
                "note": CBD_OUTDOOR_DINING["note"],
                "source": CBD_OUTDOOR_DINING["source"],
            })

    options.append({
        "option": "Argue the shortfall on the merits",
        "effect": "Council is directed to consider the criteria below in setting the "
                  "requirement, so a variation is argued against them rather than by asserting "
                  "that nearby parking is sufficient. Nearby on-street or public parking is an "
                  "argument for a variation, not evidence of compliance.",
        "what_council_must_consider": MERIT_CRITERIA["criteria"],
        "source": MERIT_CRITERIA["source"],
    })

    options.append({
        "option": "Separate the hours of the uses",
        "effect": "Two uses in one development are normally added together, but where one "
                  "operates entirely outside the other's hours only the higher rate applies.",
        "provision": COMBINED_USES["verbatim"],
        "source": COMBINED_USES["source"],
    })

    return {
        "shortfall": gap,
        "location_assumed": "Lismore CBD" if in_cbd else "outside the Lismore CBD",
        "options": options,
        "watch_out_for": {
            "losing_on-street_spaces": ON_STREET_LOSS["in_cbd"] if in_cbd
                                       else ON_STREET_LOSS["outside_cbd"],
            "source": ON_STREET_LOSS["source"],
        },
        "before_you_lodge": "Take the shortfall and the option you intend to rely on to the "
                            "free Duty Planner (Tuesdays and Thursdays, 8:30–10:30am) before "
                            "lodging. Parking is the most common thing a CBD business argues "
                            "with Council about, and it is far cheaper to settle the approach "
                            "before the DA is assessed than after it is conditioned.",
    }
