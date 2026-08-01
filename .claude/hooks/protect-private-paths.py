#!/usr/bin/env python3
"""Refuse to stage or commit private material.

Everything under `documents/` is committed and therefore published. Three paths
must never reach a commit:

  documents/output/   generated SEEs carrying a named applicant's address
  my-application/     the repo owner's own real business and address details
  _quarantined/       a third party's real, signed application, committed once
                      by mistake and kept out on purpose (see its README)

`.gitignore` already lists all three, which handles the accident. This handles
the deliberate-but-mistaken case — `git add -f`, a rewritten .gitignore, a path
moved out of an ignored directory — and it handles the case that matters most:
a future session, or a different contributor, who never read CLAUDE.md.

The model knows these rules. Hooks are for the times it doesn't remember, and
the cost of forgetting here is a real person's details published irreversibly.

Blocks with exit code 2; stderr is shown to Claude so it can correct course.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

PROTECTED = ("documents/output/", "my-application/", "_quarantined/")

# Staging or history-writing commands. `git add` is where a path first enters
# the index, `commit` is the last chance, and the others can smuggle a path in.
STAGING = re.compile(r"\bgit\s+(add|commit|stash\s+push|stash\s+save)\b")


def staged_private_paths(cwd: str) -> list[str]:
    """Paths already in the index that must not be committed."""
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=10, cwd=cwd,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [p for p in out.splitlines() if p.startswith(PROTECTED)]


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # never break the session over a malformed event

    if event.get("tool_name") != "Bash":
        return 0
    command = (event.get("tool_input") or {}).get("command", "")
    if not STAGING.search(command):
        return 0

    cwd = event.get("cwd") or str(Path.cwd())
    offenders = sorted(set(
        [p for p in PROTECTED if p in command] + staged_private_paths(cwd)
    ))
    if not offenders:
        return 0

    print(
        "BLOCKED: this would put private material into a published repository.\n\n"
        "Paths involved:\n" + "".join(f"  - {p}\n" for p in offenders) +
        "\nEverything under documents/ is committed and public. These three paths are "
        "excluded on purpose:\n"
        "  documents/output/  generated SEEs contain a named applicant's address\n"
        "  my-application/    the repo owner's real business and address details\n"
        "  _quarantined/      a third party's real signed application\n\n"
        "If a file is genuinely public and belongs in the repo, move it to the right "
        "category under documents/ first (and run /check-documents). Do not use "
        "git add -f to get around this.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
