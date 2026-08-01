---
description: Drive the server with a real MCP client over stdio and HTTP
allowed-tools: Bash(.venv/bin/python scripts/smoke_test.py:*), Read
---

```
!.venv/bin/python scripts/smoke_test.py $ARGUMENTS
```

(`--stdio` or `--http` to run one transport only.)

## Why this exists

The unit tests call handlers directly and CI only imports `build_http_app()`. Neither opens an MCP
session, and this repo has shipped two bugs that were invisible to everything except a real client:

- `minor_development_type` carried a schema enum, so the SDK rejected "shed" *before* the handler
  ran. Every direct-call test passed; it was found by trying the tool with curl.
- a `NameError` in the HTTP app during the Phase 2 split, which no test reached.

Run it after touching the registry, either transport, the `mcp` version, or any tool schema.

If something fails, the transport it failed on narrows it: stdio-only points at the server or a
handler; HTTP-only points at `transport.py`, the session manager or the rate limiter; both point at
the registry or the tool itself.
