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
    local_only: bool = False

    def as_mcp_tool(self) -> Tool:
        return Tool(name=self.name, description=self.description, input_schema=self.schema)


_REGISTRY: dict[str, RegisteredTool] = {}


def tool(
    *,
    name: str,
    description: str,
    properties: dict | None = None,
    required: list[str] | None = None,
    local_only: bool = False,
):
    """Register a handler along with the schema that describes it.

    `local_only` keeps a tool off the public HTTP transport: it is not listed
    there, and a call to it is refused with `local_only_refusal`. It is for the
    tools that take an applicant's name — ROADMAP.md A4 decided an open,
    unauthenticated endpoint with no terms and no privacy policy should not be
    a place applicant PII can enter at all.
    """

    def decorator(handler: Callable) -> Callable:
        if name in _REGISTRY:
            raise ValueError(f"tool {name!r} is already registered")
        schema: dict = {"type": "object", "properties": properties or {}}
        if required:
            missing = [r for r in required if r not in schema["properties"]]
            if missing:
                raise ValueError(f"{name}: required argument(s) not declared: {missing}")
            schema["required"] = required
        _REGISTRY[name] = RegisteredTool(name, description, schema, handler, local_only)
        return handler

    return decorator


def registered() -> dict[str, RegisteredTool]:
    return dict(_REGISTRY)


def mcp_tools(public: bool = False) -> list[Tool]:
    """The tools to list. `public` drops the local-only ones."""
    return [t.as_mcp_tool() for t in _REGISTRY.values() if not (public and t.local_only)]


def local_only_refusal(name: str) -> dict:
    """What a caller gets for calling a local-only tool on the public server.

    Unlisted there already, so a call means a client cached an old tool list or
    read the name somewhere else. Say plainly that it exists and where it runs,
    rather than "unknown tool", which would read as a typo.
    """
    return {
        "error": "not_available_on_the_public_server",
        "tool": name,
        "detail": (
            f"{name} takes an applicant's name and address, so it is switched off on this "
            "open, unauthenticated public server. It is available when the server is run "
            "locally over stdio — see the repository README. Everything else here, including "
            "prepare_prelodgement_brief and get_see_template, works without it."
        ),
    }


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


# The names callers actually use for the same few concepts, and where each lands.
#
# ROADMAP.md A1. The server spells floor area three ways, cost two, zone two and
# parking provided two, depending on the tool — and the most complex tool in the
# business path was the odd one out on the two commonest. Run 2 of SCENARIOS.md
# sent five natural spellings and all five were refused; every refusal is a
# round trip on the first call a session ever makes.
#
# **Rewrite what we know, refuse what we do not, never default.** An alias here
# is a known-correct rename, not a guess: each concept names the arguments it may
# land on, in order, and a tool takes the first it declares. Nothing else
# changes — an unknown name is still refused by `validate_arguments`, with the
# same message, and a tool's own argument is never rewritten, so an alias cannot
# shadow a real one.
#
# Deliberately left out, because the same word means different things in
# different tools:
#   * `area_sqm` — in signage it is the *sign's* area, not a floor area;
#   * `existing_spaces_on_site` / `existing_parking_spaces` — the first feeds the
#     CBD parking credit, which is not the same fact as the spaces provided;
#   * `development_type` as a general target — it is the land use in the parking
#     and fees tools, and "what you are doing" (fitout, change of use) in the
#     readiness and SEE tools. The use concept reaches it only in those two.
ARGUMENT_CONCEPTS = {
    "floor area": {
        "targets": ("floor_area_sqm", "gross_floor_area_m2"),
        "aliases": {"floor_area", "floor_area_m2", "floor_area_sqm", "gross_floor_area",
                    "gross_floor_area_m2", "gross_floor_area_sqm", "gfa", "gfa_m2", "gfa_sqm"},
    },
    "cost of works": {
        "targets": ("development_cost", "estimated_cost"),
        "aliases": {"cost", "cost_of_works", "cost_of_development", "development_cost",
                    "estimated_cost", "estimated_development_cost", "construction_cost",
                    "project_cost"},
    },
    "zone": {
        "targets": ("zone_code", "zone"),
        "aliases": {"zone", "zone_code", "zoning", "land_zone"},
    },
    "parking spaces provided": {
        "targets": ("spaces_provided", "parking_spaces_provided"),
        "aliases": {"spaces_provided", "parking_spaces_provided", "parking_spaces",
                    "parking_provided", "car_spaces", "car_parking_spaces"},
    },
    "address": {
        "targets": ("property_address", "address"),
        "aliases": {"address", "property_address", "site_address", "street_address"},
    },
    "the proposed use": {
        "targets": ("land_use", "proposed_use"),
        # Only where development_type *is* the use.
        "development_type_in": ("get_parking_rates", "calculate_da_fees"),
        "aliases": {"use", "land_use", "proposed_use", "intended_use", "business_type"},
    },
}


def _alias_target(tool: str, properties: dict, concept: dict) -> str | None:
    """The argument this tool declares for a concept, or None if it has none."""
    for target in concept["targets"]:
        if target in properties:
            return target
    if tool in concept.get("development_type_in", ()) and "development_type" in properties:
        return "development_type"
    return None


def resolve_aliases(name: str, arguments: dict) -> tuple[dict, dict | None]:
    """Rename known aliases to the tool's own argument names.

    Returns (arguments, error). Runs before `validate_arguments`, which then sees
    only the tool's own names and checks them exactly as before. An argument the
    tool itself declares is never rewritten. Two names for one argument with
    different values is refused rather than resolved — which one the caller meant
    is not something to guess.
    """
    registration = _REGISTRY.get(name)
    if registration is None:
        return arguments, None
    properties = registration.schema.get("properties", {})

    resolved, sources = {}, {}
    for key, value in arguments.items():
        target = key
        if key not in properties:
            for concept in ARGUMENT_CONCEPTS.values():
                if key in concept["aliases"]:
                    target = _alias_target(name, properties, concept) or key
                    break
        if target in resolved and resolved[target] != value:
            return arguments, {
                "error": f"'{sources[target]}' and '{key}' both give {target}, with different "
                         "values.",
                "note": "Send one of them. Two values for the same argument are not reconciled "
                        "here, because which one was meant is not something to guess.",
            }
        resolved[target] = value
        sources.setdefault(target, key)
    return resolved, None


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
