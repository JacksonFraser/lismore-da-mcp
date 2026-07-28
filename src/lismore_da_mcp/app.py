"""The MCP Server instance.

Kept in its own module so that transports and tool registration can both reach
it without importing each other — server.py imports transport.py for run_http(),
and transport.py needs the same Server object to serve.
"""

from mcp.server import Server

from lismore_da_mcp.instructions import INSTRUCTIONS

# `instructions` is returned in the initialize response and surfaced to the model
# by clients. Without it a remote agent gets 21 tool descriptions and no sense of
# the process or the caveats — all of which previously lived only in this repo's
# CLAUDE.md, which someone connecting to the hosted server never sees.
server = Server("lismore-da-mcp", instructions=INSTRUCTIONS)
