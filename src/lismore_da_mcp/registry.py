"""Tool registration and dispatch.

Previously a tool lived in three distant places: an entry in a 635-line `TOOLS`
list, a branch in a 1,055-line `if/elif` chain, and a row in the README. Nothing
enforced that they stayed in agreement, and no branch could be exercised without
going through the whole dispatcher.

Here a tool is one decorated function that carries its own schema:

    @tool(
        name="get_zone_info",
        description="Zone objectives, permitted uses and standards.",
        properties={"zone_code": {"type": "string", "description": "e.g. R2"}},
        required=["zone_code"],
    )
    def get_zone_info(arguments: dict):
        ...

Registration order is the order tools are declared, which is the order clients
see them in — so it stays stable and reviewable rather than depending on dict
iteration.
"""

import math
from dataclasses import dataclass
from typing import Callable

from mcp.types import Tool


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    schema: dict
    handler: Callable

    def as_mcp_tool(self) -> Tool:
        return Tool(name=self.name, description=self.description, input_schema=self.schema)


_REGISTRY: dict[str, RegisteredTool] = {}


def tool(
    *,
    name: str,
    description: str,
    properties: dict | None = None,
    required: list[str] | None = None,
):
    """Register a handler along with the schema that describes it."""

    def decorator(handler: Callable) -> Callable:
        if name in _REGISTRY:
            raise ValueError(f"tool {name!r} is already registered")
        schema: dict = {"type": "object", "properties": properties or {}}
        if required:
            missing = [r for r in required if r not in schema["properties"]]
            if missing:
                raise ValueError(f"{name}: required argument(s) not declared: {missing}")
            schema["required"] = required
        _REGISTRY[name] = RegisteredTool(name, description, schema, handler)
        return handler

    return decorator


def registered() -> dict[str, RegisteredTool]:
    return dict(_REGISTRY)


def mcp_tools() -> list[Tool]:
    return [t.as_mcp_tool() for t in _REGISTRY.values()]


def schemas() -> dict[str, dict]:
    return {name: t.schema for name, t in _REGISTRY.items()}


def get(name: str) -> RegisteredTool | None:
    return _REGISTRY.get(name)


# JSON Schema type names → the Python types that satisfy them.
#
# `bool` is excluded from the numeric types deliberately: in Python it is a
# subclass of int, so `True` would otherwise pass as a development cost.
_JSON_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


# The schema keywords `validate_arguments` actually enforces.
#
# `CLAUDE.md` records the rule this exists to keep: **anything the schema can
# express that this gate does not check is unenforced**, because nothing else
# validates arguments. A schema that declares `maxLength` or `enum` or `pattern`
# would read as a constraint, document itself to the caller as a constraint, and
# be worth nothing. `tests/test_registry.py` fails if a property declares a
# keyword absent from this set, in the same shape as the `_JSON_TYPES` test —
# so the way to add a constraint is to enforce it here first.
_ENFORCED_KEYWORDS = frozenset({"type", "description", "minimum", "maximum", "items"})


def _type_error(argument: str, expected: str, value) -> str | None:
    """Return a description of the mismatch, or None if the value fits."""
    allowed = _JSON_TYPES.get(expected)
    if allowed is None:
        return None
    if isinstance(value, bool) and expected in ("number", "integer"):
        return "boolean"
    if isinstance(value, allowed):
        return None
    return type(value).__name__


def validate_arguments(name: str, arguments: dict) -> dict | None:
    """Check arguments against the tool's own schema. Returns an error payload, or None if valid.

    Handlers read arguments with .get() and sensible-looking defaults, which means a
    misspelt or omitted argument used to produce a confident wrong answer rather than
    an error — an empty land_use reported 'permitted without consent'. Refuse instead.

    Checking is done here because nothing else does it — the SDK dispatches
    whatever arrives without checking it against the tool's schema. Without this,
    `development_cost: "lots"` reached `float()` and surfaced to the caller as a
    raw MCPError reading "could not convert string to float" — an internal
    traceback string standing in for an answer.

    Five checks, in order: unknown arguments, missing or empty required ones,
    wrong types (including array element types), non-finite numbers, and
    `minimum`/`maximum`. The last two are ROADMAP.md S2 and exist because a type
    check alone let `gross_floor_area_m2: -80` through, where it deleted a
    $16,081 contribution from a total that still read like a total.

    **The set of checks here is the set of constraints a schema may express.**
    `_ENFORCED_KEYWORDS` pins that both ways and a test fails on a keyword this
    function does not honour, because a declared-but-unchecked constraint is
    worse than an absent one: it documents itself to the caller as enforced.
    """
    registration = _REGISTRY.get(name)
    if registration is None:
        return {"error": f"Unknown tool: {name}", "available_tools": sorted(_REGISTRY)}

    properties = registration.schema.get("properties", {})
    unknown = sorted(k for k in arguments if k not in properties)
    if unknown:
        return {
            "error": "Unrecognised argument(s): " + ", ".join(unknown),
            "accepted_arguments": sorted(properties),
            "note": "Unrecognised arguments are not guessed at. Re-send the call using the names above.",
        }

    missing = [
        key for key in registration.schema.get("required", [])
        if arguments.get(key) is None
        or (isinstance(arguments[key], str) and not arguments[key].strip())
    ]
    if missing:
        return {
            "error": "Missing or empty required argument(s): " + ", ".join(missing),
            "required_arguments": registration.schema.get("required", []),
        }

    wrong_type = []
    for key, value in arguments.items():
        if value is None:
            continue
        spec = properties.get(key, {})
        expected = spec.get("type")
        if not isinstance(expected, str):
            continue
        received = _type_error(key, expected, value)
        if received:
            wrong_type.append(
                f"{key} expects {expected}, received {received}"
            )
            continue
        # `items` was declared on all five array arguments and enforced on none,
        # so an array of the wrong thing read as validated and was not. Every one
        # of them is a list of phrases the handler calls string methods on, and
        # `documents_prepared: ["site plan", 5, None]` surfaced to the caller as
        # an uncaught AttributeError — the same shape as the raw MCPError this
        # gate was built to stop.
        element_type = (spec.get("items") or {}).get("type")
        if expected == "array" and isinstance(element_type, str):
            for position, element in enumerate(value):
                bad = _type_error(key, element_type, element)
                if bad:
                    wrong_type.append(
                        f"{key}[{position}] expects {element_type}, received {bad}"
                    )
    if wrong_type:
        return {
            "error": "Argument(s) of the wrong type: " + "; ".join(wrong_type),
            "note": (
                "Values are not coerced. Send the argument in the type the schema "
                "declares — a number must be a number, not a string containing one."
            ),
        }

    # Infinity and NaN are valid JSON to Python's parser, so they arrive over the
    # wire and pass every check above — `inf` is a float, and a float is what
    # `development_cost` declares. They then reach arithmetic that has no answer
    # for them: `inf` surfaced as an uncaught OverflowError out of `fees.py`, and
    # `nan` as an UnboundLocalError, because every bracket comparison against NaN
    # is false and the loop assigned nothing. ROADMAP.md S2.
    non_finite = sorted(
        key for key, value in arguments.items()
        if isinstance(value, float) and not math.isfinite(value)
        and properties.get(key, {}).get("type") in ("number", "integer")
    )
    if non_finite:
        return {
            "error": "Argument(s) that are not a finite number: " + ", ".join(non_finite),
            "note": (
                "Infinity and NaN parse as JSON numbers but cannot be costed, measured "
                "or compared. Send a real figure, or omit the argument."
            ),
        }

    # `minimum` from the schema, enforced.
    #
    # Without this a sign flip silently deleted the largest charge in an answer:
    # `gross_floor_area_m2: -80` returned a budget of $420 where `+80` returned
    # $16,501, because the contribution is computed per 100m² and a negative area
    # fell out of every bracket into "no figure available". The tool then said so
    # in a field three levels down while the headline total stayed confident.
    #
    # A wrong *number* is worse than a rejected call, which is the whole argument
    # for this gate: the caller cannot see that -80 was refused unless it is
    # refused loudly.
    out_of_range = []
    for key, value in arguments.items():
        spec = properties.get(key, {})
        if isinstance(value, bool) or spec.get("type") not in ("number", "integer"):
            continue
        if not isinstance(value, (int, float)):
            continue
        minimum = spec.get("minimum")
        if minimum is not None and value < minimum:
            out_of_range.append(f"{key} must be at least {minimum}, received {value}")
        maximum = spec.get("maximum")
        if maximum is not None and value > maximum:
            out_of_range.append(f"{key} must be at most {maximum}, received {value}")
    if out_of_range:
        return {
            "error": "Argument(s) outside the allowed range: " + "; ".join(out_of_range),
            "note": (
                "Out-of-range values are refused rather than clamped or ignored. A "
                "negative floor area or cost produces an answer that looks like an "
                "answer — it is a smaller number, not a visible error."
            ),
        }

    return None
