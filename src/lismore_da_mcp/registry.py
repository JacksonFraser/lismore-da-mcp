"""Tool registration and argument validation.

A tool is one decorated function that carries its own schema:

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
from collections.abc import Callable
from dataclasses import dataclass

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


# JSON Schema type names → the Python types that satisfy them. `bool` is kept out
# of the numeric types because it subclasses int, so `True` would pass as a cost.
_JSON_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "number": (int, float),
    "integer": (int,),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


# The schema keywords `validate_arguments` enforces. Nothing else validates
# arguments, so a schema keyword not listed here would document a constraint that
# is never checked; tests/test_registry.py fails if a tool declares one.
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

    The SDK does not validate against the schema, and handlers read arguments with
    `.get()` and defaults, so without this a misspelt or out-of-range argument
    produces a confident wrong answer rather than an error. Values are refused,
    never coerced or clamped.
    """
    registration = _REGISTRY.get(name)
    if registration is None:
        return {"error": f"Unknown tool: {name}", "available_tools": sorted(_REGISTRY)}

    schema = registration.schema
    for check in (_unknown, _missing, _wrong_type, _non_finite, _out_of_range):
        error = check(schema, arguments)
        if error:
            return error
    return None


def _unknown(schema: dict, arguments: dict) -> dict | None:
    properties = schema.get("properties", {})
    unknown = sorted(k for k in arguments if k not in properties)
    if not unknown:
        return None
    return {
        "error": "Unrecognised argument(s): " + ", ".join(unknown),
        "accepted_arguments": sorted(properties),
        "note": "Unrecognised arguments are not guessed at. Re-send the call using the names above.",
    }


def _missing(schema: dict, arguments: dict) -> dict | None:
    required = schema.get("required", [])
    missing = [
        key for key in required
        if arguments.get(key) is None
        or (isinstance(arguments[key], str) and not arguments[key].strip())
    ]
    if not missing:
        return None
    return {
        "error": "Missing or empty required argument(s): " + ", ".join(missing),
        "required_arguments": required,
    }


def _wrong_type(schema: dict, arguments: dict) -> dict | None:
    properties = schema.get("properties", {})
    wrong_type = []
    for key, value in arguments.items():
        spec = properties.get(key, {})
        expected = spec.get("type")
        if value is None or not isinstance(expected, str):
            continue
        received = _type_error(key, expected, value)
        if received:
            wrong_type.append(f"{key} expects {expected}, received {received}")
            continue
        # Array elements too: every array argument is a list of phrases the
        # handler calls string methods on.
        element_type = (spec.get("items") or {}).get("type")
        if expected == "array" and isinstance(element_type, str):
            for position, element in enumerate(value):
                bad = _type_error(key, element_type, element)
                if bad:
                    wrong_type.append(f"{key}[{position}] expects {element_type}, received {bad}")
    if not wrong_type:
        return None
    return {
        "error": "Argument(s) of the wrong type: " + "; ".join(wrong_type),
        "note": (
            "Values are not coerced. Send the argument in the type the schema "
            "declares — a number must be a number, not a string containing one."
        ),
    }


def _non_finite(schema: dict, arguments: dict) -> dict | None:
    # Infinity and NaN parse as JSON numbers and pass the type check, then break
    # the fee arithmetic (every comparison against NaN is false).
    properties = schema.get("properties", {})
    non_finite = sorted(
        key for key, value in arguments.items()
        if isinstance(value, float) and not math.isfinite(value)
        and properties.get(key, {}).get("type") in ("number", "integer")
    )
    if not non_finite:
        return None
    return {
        "error": "Argument(s) that are not a finite number: " + ", ".join(non_finite),
        "note": (
            "Infinity and NaN parse as JSON numbers but cannot be costed, measured "
            "or compared. Send a real figure, or omit the argument."
        ),
    }


def _out_of_range(schema: dict, arguments: dict) -> dict | None:
    # A negative area or cost yields a smaller number, not a visible error, so
    # it is refused loudly rather than clamped.
    properties = schema.get("properties", {})
    out_of_range = []
    for key, value in arguments.items():
        spec = properties.get(key, {})
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        if spec.get("type") not in ("number", "integer"):
            continue
        minimum = spec.get("minimum")
        if minimum is not None and value < minimum:
            out_of_range.append(f"{key} must be at least {minimum}, received {value}")
        maximum = spec.get("maximum")
        if maximum is not None and value > maximum:
            out_of_range.append(f"{key} must be at most {maximum}, received {value}")
    if not out_of_range:
        return None
    return {
        "error": "Argument(s) outside the allowed range: " + "; ".join(out_of_range),
        "note": (
            "Out-of-range values are refused rather than clamped or ignored. A "
            "negative floor area or cost produces an answer that looks like an "
            "answer — it is a smaller number, not a visible error."
        ),
    }
