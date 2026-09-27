"""Cite a registered interpretation inside the answer that depends on it.

ROADMAP.md B1. `data/interpretations.py` is the register; this is the one way a
tool refers to it, so every citation has the same shape and an unknown key
fails loudly at the call site rather than shipping an answer that cites nothing.

A citation is deliberately short — the reading in one line and what it costs if
Council reads the provision the other way. The alternative, the reasoning and
the quoted provision stay in the register, which `scripts/render_interpretations.py`
prints as the planner review packet. A wall of text beside every figure is the
standing caveat item 0.1 diagnosed; one line beside the figure it changes is not.
"""

from lismore_da_mcp.data.interpretations import BY_KEY

REGISTER = "Interpretation register (data/interpretations.py)"


def cite(key: str) -> dict:
    """The citation for one registered reading. Raises KeyError on an unknown key."""
    entry = BY_KEY[key]
    return {
        "id": key,
        "reading": entry["in_one_line"],
        "if_council_disagrees": entry["cost_if_council_disagrees"],
        "provision": "; ".join(dict.fromkeys(q["where"] for q in entry["provision"])),
        "planner_review": entry["planner_review"],
    }


def cite_all(keys) -> list[dict]:
    """Citations for several readings, in order, each once."""
    return [cite(key) for key in dict.fromkeys(keys)]
