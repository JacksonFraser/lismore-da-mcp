"""Transports.

stdio for local .mcp.json use; Streamable HTTP for the public Render deployment,
which is open and unauthenticated and so carries a best-effort per-IP limiter.
"""

import os
import time
from collections import deque

from mcp.server.stdio import stdio_server

from lismore_da_mcp.app import server
from lismore_da_mcp.observability import (
    configure_logging,
    record_index_state,
    record_proxy_chain,
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

    Behind a reverse proxy the connection's address is the proxy's, so every
    caller would share one bucket. `proxy_hops` is how many proxies in front of
    this process append to X-Forwarded-For; the client is the entry the
    outermost of them appended, counted from the right. Entries further left
    are whatever the client sent, and are never trusted. 0 uses the connection.
    """

    # Sweep idle IPs this often, so the map does not grow with every distinct IP.
    SWEEP_EVERY_SECONDS = 300.0

    # Not rate limited: the platform's health checks would otherwise use up a
    # bucket, and the endpoint does no work.
    UNLIMITED_PATHS = frozenset({"/health"})

    def __init__(self, app, max_requests: int = 30, window_seconds: float = 60.0,
                 proxy_hops: int = 0):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.proxy_hops = proxy_hops
        self._hits: dict = {}
        self._last_sweep = 0.0
        self._proxy_chain_logged = False

    def _client_ip(self, scope) -> str:
        if self.proxy_hops:
            forwarded = dict(scope.get("headers") or []).get(b"x-forwarded-for", b"")
            entries = [e.strip() for e in forwarded.decode("latin-1").split(",") if e.strip()]
            if not self._proxy_chain_logged:
                record_proxy_chain(len(entries), self.proxy_hops)
                self._proxy_chain_logged = True
            if len(entries) >= self.proxy_hops:
                return entries[-self.proxy_hops]
        client = scope.get("client")
        return client[0] if client else "unknown"

    def _sweep(self, now: float) -> int:
        """Drop IPs with no request inside the current window. Returns how many."""
        stale = [
            ip for ip, hits in self._hits.items()
            if not hits or now - hits[-1] > self.window_seconds
        ]
        for ip in stale:
            del self._hits[ip]
        self._last_sweep = now
        return len(stale)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") in self.UNLIMITED_PATHS:
            await self.app(scope, receive, send)
            return

        ip = self._client_ip(scope)
        now = time.monotonic()

        # Amortised: a sweep is O(tracked IPs) and runs at most every few minutes,
        # rather than on every request.
        if now - self._last_sweep > self.SWEEP_EVERY_SECONDS:
            self._sweep(now)

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

    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Mount, Route

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
        # A missing index is invisible from outside, so log its state at startup.
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
    return _RateLimitMiddleware(app, proxy_hops=trusted_proxy_hops())


def trusted_proxy_hops() -> int:
    """How many reverse proxies append to X-Forwarded-For in front of the HTTP app.

    Defaults to 1, for Render's load balancer. The first proxied request logs
    `event=proxy_chain` with its entry count; if that is higher than this,
    another proxy (e.g. a CDN) is in front and this should be raised to match.
    """
    try:
        return max(0, int(os.environ.get("LISMORE_TRUSTED_PROXY_HOPS", "1")))
    except ValueError:
        return 1

def run_http():
    """Run the MCP server over Streamable HTTP (public deployment)."""
    import uvicorn

    app = build_http_app()
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
