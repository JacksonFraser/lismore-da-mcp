#!/usr/bin/env python3
"""Print the interpretation register as a review packet, in Markdown.

ROADMAP.md B2. The register is the document to hand a planner: a couple of
dozen readings, each with the provision quoted, the reading taken, the
alternative, and what it costs if Council disagrees — not 15,000 lines of
source. This renders it for printing, with a line per entry for the planner to
mark confirmed, disputed or unresolved. Those marks go back into
`planner_review` in `data/interpretations.py`; a disputed entry becomes either a
correction or a `DUTY_PLANNER_QUESTIONS` item.

    .venv/bin/python scripts/render_interpretations.py > review-packet.md
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def render() -> str:
    from lismore_da_mcp.data.interpretations import INTERPRETATIONS

    lines = [
        "# Lismore DA assistant — interpretation register",
        "",
        "Readings this tool takes where a planning document admits more than one. "
        "Every quoted provision is checked verbatim against the source document "
        "(`scripts/audit_interpretations.py`); the readings themselves have not been "
        "reviewed by anyone with standing to review them. That is what this packet is for.",
        "",
        "For each entry, please mark one: **confirmed** (Council reads it this way), "
        "**disputed** (Council reads it the other way, or another way), or **unresolved** "
        "(it depends, or Council has no settled view).",
        "",
        "| # | Topic | Reading | If Council disagrees, the tool |",
        "|---|---|---|---|",
    ]
    for n, entry in enumerate(INTERPRETATIONS, 1):
        lines.append(f"| {n} | {entry['topic']} | {entry['in_one_line']} | "
                     f"{entry['if_wrong_this_tool']} |")

    topic = None
    for n, entry in enumerate(INTERPRETATIONS, 1):
        if entry["topic"] != topic:
            topic = entry["topic"]
            lines += ["", f"## {topic.capitalize()}"]
        lines += ["", f"### {n}. {entry['in_one_line']}", "", f"`{entry['key']}`", ""]
        for quote in entry["provision"]:
            page = f", p{quote['page']}" if quote.get("page") else ""
            lines.append(f"> **{quote['where']}** ({quote['source'].split('/')[-1]}{page}): "
                         f"\"{quote['verbatim']}\"")
            lines.append(">")
        if lines[-1] == ">":
            lines.pop()
        lines += [
            "",
            f"- **Reading taken:** {entry['reading']}",
            f"- **Alternative:** {entry['alternative']}",
            f"- **Why this one:** {entry['why_this_one']}",
            f"- **Cost to the applicant if Council disagrees:** "
            f"{entry['cost_if_council_disagrees']} (the tool {entry['if_wrong_this_tool']})",
            f"- **Relied on by:** {', '.join(entry['relied_on_by'])}",
        ]
        if entry.get("duty_planner_question"):
            lines.append(f"- **Duty Planner question:** `{entry['duty_planner_question']}`")
        lines += [
            f"- **Current status:** {entry['planner_review']}",
            "",
            "Planner's mark: ☐ confirmed ☐ disputed ☐ unresolved — note:",
        ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.write(render())
