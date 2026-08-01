#!/usr/bin/env python3
"""Drive the server the way a real client does, over both transports.

The unit tests call handlers directly and CI only imports `build_http_app()`.
Neither opens an MCP session, and this repo has already shipped two bugs that
were invisible to everything except a real client:

  * `minor_development_type` carried a schema enum, so "shed" was rejected by
    SDK-side validation before the handler ran. Every direct-call test passed.
    It was found by trying the tool with curl.
  * a NameError in the HTTP app during the Phase 2 split, which no test reached.

Run after touching the registry, the transports, the SDK version, or any tool
schema.

    .venv/bin/python scripts/smoke_test.py            # both transports
    .venv/bin/python scripts/smoke_test.py --stdio    # or --http
"""

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = str(ROOT / ".venv" / "bin" / "python")

# (tool, arguments, predicate on the response text, description)
CHECKS = [
    ("get_zone_info", {"zone_code": "RU1"},
     lambda t: json.loads(t)["name"] == "Primary Production",
     "a plain lookup answers"),
    ("check_permissibility", {"zone_code": "E2", "land_use": "cafe"},
     lambda t: json.loads(t)["permissibility"].startswith("permitted"),
     "permissibility answers for a business use"),
    ("get_zone_info", {"zone": "R2"},
     lambda t: "Unrecognised" in t,
     "an unknown argument is refused, not guessed"),
    ("calculate_da_fees", {"development_cost": "lots"},
     lambda t: "wrong type" in t,
     "a wrong-typed argument is refused (mcp 2.0 dropped SDK-side validation)"),
    ("preview_see_form", {
        "applicant_name": "A Person", "property_address": "12 Keen Street, Lismore NSW 2480",
        "lot_dp": "Lot 12 DP 758651", "zone_code": "R2", "proposed_use": "dwelling house",
        "development_type": "dwelling", "floor_area_sqm": 40,
        "minor_development_type": "shed"},
     lambda t: json.loads(t)["success"] is True,
     "plain wording reaches the handler rather than being rejected by a schema enum"),
]


def free_port() -> int:
    with closing(socket.socket()) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


async def run_checks(session, label: str) -> int:
    failures = 0
    tools = await session.list_tools()
    print(f"  {label}: {len(tools.tools)} tools listed")
    if not tools.tools:
        print(f"  {label}: FAIL — no tools listed")
        return 1
    for name, args, predicate, description in CHECKS:
        try:
            result = await session.call_tool(name, args)
            text = result.content[0].text
            ok = predicate(text)
        except Exception as exc:                              # noqa: BLE001
            ok, text = False, f"{type(exc).__name__}: {exc}"
        print(f"  {label}: {'ok  ' if ok else 'FAIL'} {description}")
        if not ok:
            failures += 1
            print(f"        {str(text)[:200]}")
    return failures


async def over_stdio() -> int:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=PY, args=["-m", "lismore_da_mcp.server"],
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            instructions = getattr(init, "instructions", "") or ""
            print(f"  stdio: initialized, {len(instructions)} chars of instructions")
            failures = 0 if instructions.strip() else 1
            if not instructions.strip():
                print("  stdio: FAIL — no instructions delivered to the client")
            return failures + await run_checks(session, "stdio")


async def over_http() -> int:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    port = free_port()
    proc = subprocess.Popen(
        [PY, "-m", "lismore_da_mcp.server"],
        env={**os.environ, "MCP_TRANSPORT": "http", "PORT": str(port),
             "PYTHONPATH": str(ROOT / "src")},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(40):                                   # wait for the port
            time.sleep(0.25)
            with closing(socket.socket()) as s:
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    break
        else:
            print("  http: FAIL — server never came up")
            return 1
        async with streamable_http_client(f"http://127.0.0.1:{port}/mcp") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print(f"  http: initialized on port {port}")
                return await run_checks(session, "http ")
    finally:
        proc.terminate()
        proc.wait(timeout=10)


async def main(which: str) -> int:
    failures = 0
    if which in ("both", "stdio"):
        print("stdio transport (what .mcp.json uses locally)")
        failures += await over_stdio()
    if which in ("both", "http"):
        print("\nStreamable HTTP transport (what Render serves)")
        failures += await over_http()
    print(f"\n{'PASS' if not failures else str(failures) + ' FAILURE(S)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdio", action="store_const", const="stdio", dest="which")
    parser.add_argument("--http", action="store_const", const="http", dest="which")
    parser.set_defaults(which="both")
    sys.exit(asyncio.run(main(parser.parse_args().which)))
