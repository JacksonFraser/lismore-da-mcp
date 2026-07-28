"""Transports.

stdio for local .mcp.json use; Streamable HTTP for the public Render deployment,
which is open and unauthenticated and so carries a best-effort per-IP limiter.
"""

import os

from mcp.server.stdio import stdio_server

from lismore_da_mcp.app import server
from lismore_da_mcp.observability import (
    configure_logging,
    record_index_state,
    record_rate_limited,
    record_startup,
)

async def run():
    """Run the MCP server over stdio (local, single-user — used by .mcp.json)."""
    configure_logging()
    record_startup("stdio")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

class _RateLimitMiddleware:
    """Best-effort in-memory per-IP fixed-window rate limiter.

    This is meant as a cheap abuse guard for an open, unauthenticated public deployment —
    not a substitute for a real edge limiter (e.g. Cloudflare) if traffic grows.
    """

    def __init__(self, app, max_requests: int = 30, window_seconds: float = 60.0):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict = {}

    async def __call__(self, scope, receive, send):
        import time
        from collections import deque

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        ip = client[0] if client else "unknown"
        now = time.monotonic()
        hits = self._hits.setdefault(ip, deque())
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            from starlette.responses import PlainTextResponse
            record_rate_limited(self.window_seconds, self.max_requests)
            response = PlainTextResponse("Rate limit exceeded, try again shortly.", status_code=429)
            await response(scope, receive, send)
            return

        hits.append(now)
        await self.app(scope, receive, send)

def build_http_app():
    """Build the Starlette ASGI app that serves the MCP server over Streamable HTTP."""
    from contextlib import asynccontextmanager

    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Mount, Route
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

    # stateless=True: no tool here needs cross-request session state, and it keeps the
    # deployment simple (no session affinity needed if this is ever scaled beyond one instance).
    session_manager = StreamableHTTPSessionManager(app=server, stateless=True)

    async def handle_mcp(scope, receive, send):
        await session_manager.handle_request(scope, receive, send)

    async def health(_request):
        return PlainTextResponse("ok")

    @asynccontextmanager
    async def lifespan(_app):
        configure_logging()
        record_startup("http")
        # A missing index is invisible from outside — search still answers, just
        # via a full scan at roughly a thousand times the cost. That shipped once.
        from lismore_da_mcp.index import index_status

        state = index_status()
        record_index_state(
            "present" if state.get("present") else "absent",
            state.get("segments"),
        )
        async with session_manager.run():
            yield

    app = Starlette(
        routes=[
            Route("/health", health),
            Mount("/mcp", app=handle_mcp),
        ],
        lifespan=lifespan,
    )
    return _RateLimitMiddleware(app)

def run_http():
    """Run the MCP server over Streamable HTTP (public deployment)."""
    import uvicorn

    app = build_http_app()
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
