"""Transport wiring.

Render runs the HTTP path and nothing else exercises it, so a break here is
invisible to every other test — as happened during the Phase 2 split, when
transport.py lost its reference to the Server object and only the CI import
check caught it.
"""


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


class TestClientAddress:
    """Behind Render's proxy every connection comes from the proxy, so the
    limiter has to key on the address the proxy forwarded."""

    @staticmethod
    def _request(path="/mcp", forwarded=None, client=("10.0.0.1", 1234)):
        headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded else []
        return {"type": "http", "path": path, "headers": headers, "client": client}

    def _run(self, limiter, scopes):
        import asyncio

        statuses = []

        async def send(message):
            if message["type"] == "http.response.start":
                statuses.append(message["status"])

        async def run():
            for scope in scopes:
                await limiter(scope, None, send)

        asyncio.run(run())
        return statuses

    def _limiter(self, **kw):
        passed = []

        async def app(scope, receive, send):
            passed.append(scope["path"])

        limiter = transport._RateLimitMiddleware(app, **kw)
        return limiter, passed

    def test_callers_behind_one_proxy_get_separate_buckets(self):
        limiter, passed = self._limiter(max_requests=2, proxy_hops=1)
        scopes = [self._request(forwarded=f"203.0.113.{n}") for n in (1, 2, 3) for _ in range(2)]
        assert self._run(limiter, scopes) == []
        assert len(passed) == 6

    def test_one_caller_is_still_limited(self):
        limiter, passed = self._limiter(max_requests=2, proxy_hops=1)
        statuses = self._run(limiter, [self._request(forwarded="203.0.113.1")] * 3)
        assert statuses == [429]
        assert len(passed) == 2

    def test_a_spoofed_entry_does_not_escape_the_limit(self):
        """A client can only prepend to X-Forwarded-For; the entry the proxy
        appended is the right-most one and that is what is keyed on."""
        limiter, passed = self._limiter(max_requests=2, proxy_hops=1)
        scopes = [self._request(forwarded=f"198.51.100.{n}, 203.0.113.1") for n in range(3)]
        assert self._run(limiter, scopes) == [429]

    def test_two_hops_reads_the_second_entry_from_the_right(self):
        limiter, _ = self._limiter(proxy_hops=2)
        scope = self._request(forwarded="198.51.100.9, 203.0.113.1, 172.16.0.5")
        assert limiter._client_ip(scope) == "203.0.113.1"

    def test_without_hops_the_connection_address_is_used(self):
        limiter, _ = self._limiter(proxy_hops=0)
        assert limiter._client_ip(self._request(forwarded="203.0.113.1")) == "10.0.0.1"

    def test_too_few_entries_falls_back_to_the_connection(self):
        limiter, _ = self._limiter(proxy_hops=2)
        assert limiter._client_ip(self._request(forwarded="203.0.113.1")) == "10.0.0.1"

    def test_health_checks_are_not_counted(self):
        limiter, passed = self._limiter(max_requests=1, proxy_hops=1)
        scopes = [self._request(path="/health", forwarded="203.0.113.1")] * 5
        scopes.append(self._request(forwarded="203.0.113.1"))
        assert self._run(limiter, scopes) == []
        assert len(passed) == 6

    def test_the_public_app_trusts_one_hop_by_default(self, monkeypatch):
        monkeypatch.delenv("LISMORE_TRUSTED_PROXY_HOPS", raising=False)
        assert transport.build_http_app().proxy_hops == 1
        monkeypatch.setenv("LISMORE_TRUSTED_PROXY_HOPS", "2")
        assert transport.build_http_app().proxy_hops == 2
