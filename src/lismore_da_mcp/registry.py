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

    Type checking is done here because mcp 2.0 stopped doing it. Under mcp 1.x the
    SDK ran the tool's schema through jsonschema before dispatching, so a string
    where a number belonged never reached a handler; 2.0 removed server-side
    validation entirely (only mcp.client.session still carries jsonschema). Without
    this, `development_cost: "lots"` reached `float()` and surfaced to the caller as
    a raw MCPError reading "could not convert string to float" — an internal
    traceback string standing in for an answer.
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
        expected = properties.get(key, {}).get("type")
        if not isinstance(expected, str):
            continue
        received = _type_error(key, expected, value)
        if received:
            wrong_type.append(
                f"{key} expects {expected}, received {received}"
            )
    if wrong_type:
        return {
            "error": "Argument(s) of the wrong type: " + "; ".join(wrong_type),
            "note": (
                "Values are not coerced. Send the argument in the type the schema "
                "declares — a number must be a number, not a string containing one."
            ),
        }

    return None
