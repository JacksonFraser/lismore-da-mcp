"""The MCP Server instance.

Kept in its own module so that transports and tool registration can both reach
it without importing each other — server.py imports transport.py for run_http(),
and transport.py needs the same Server object to serve.
"""

from mcp.server import Server

server = Server("lismore-da-mcp")
