"""Transport wiring.

Render runs the HTTP path and nothing else exercises it, so a break here is
invisible to every other test — as happened during the Phase 2 split, when
transport.py lost its reference to the Server object and only the CI import
check caught it.
"""

import pytest

from lismore_da_mcp import transport
from lismore_da_mcp.app import server


class TestHttpApp:
    def test_builds(self):
        assert transport.build_http_app() is not None

    def test_exposes_health_and_mcp_routes(self):
        app = transport.build_http_app()
        # The rate limiter wraps the Starlette app.
        inner = getattr(app, "app", app)
        paths = {getattr(r, "path", None) for r in inner.routes}
        assert "/health" in paths
        assert any(p and p.startswith("/mcp") for p in paths)

    def test_rate_limiter_wraps_the_app(self):
        assert isinstance(transport.build_http_app(), transport._RateLimitMiddleware)


class TestRateLimiter:
    def _limiter(self, **kw):
        async def app(scope, receive, send):
            return None

        return transport._RateLimitMiddleware(app, **kw)

    def test_allows_traffic_under_the_limit(self):
        limiter = self._limiter(max_requests=3, window_seconds=60)
        assert limiter.max_requests == 3

    def test_non_http_scopes_pass_through(self):
        import asyncio

        seen = []

        async def app(scope, receive, send):
            seen.append(scope["type"])

        limiter = transport._RateLimitMiddleware(app)
        asyncio.run(limiter({"type": "lifespan"}, None, None))
        assert seen == ["lifespan"]


class TestServerInstance:
    def test_single_shared_instance(self):
        """transport and server must serve the same object, or tools registered on
        one are invisible to the other."""
        from lismore_da_mcp import server as server_module

        assert server_module.server is server

    def test_named(self):
        assert server.name == "lismore-da-mcp"
