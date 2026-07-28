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
        return Tool(name=self.name, description=self.description, inputSchema=self.schema)


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


def validate_arguments(name: str, arguments: dict) -> dict | None:
    """Check arguments against the tool's own schema. Returns an error payload, or None if valid.

    Handlers read arguments with .get() and sensible-looking defaults, which means a
    misspelt or omitted argument used to produce a confident wrong answer rather than
    an error — an empty land_use reported 'permitted without consent'. Refuse instead.
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

    return None
