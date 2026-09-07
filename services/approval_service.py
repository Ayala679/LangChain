"""
services/approval_service.py
─────────────────────────────
Handles all HITL decision logic:
  - Parsing numbered source blocks from agent output
  - Building selection text from user-chosen indices
  - Deciding approve vs reject routing
"""

import re
from typing import Optional


def parse_sources(text: str) -> list[str]:
    """
    Split the agent's numbered output into individual source blocks.
    E.g. "1. Title\\n...\\n2. Title\\n..." → ["1. Title\\n...", "2. Title\\n..."]
    """
    parts = re.split(r"\n(?=\d+\.)", text.strip())
    return [p.strip() for p in parts if p.strip()]


def build_selection_text(chosen_labels: list[str]) -> str:
    """
    Convert checkbox labels ("Source 3: …") to a comma-separated index string
    or "all" when nothing was deselected.
    """
    if not chosen_labels:
        return "all"

    indices = []
    for label in chosen_labels:
        m = re.match(r"Source (\d+)", label)
        if m:
            indices.append(int(m.group(1)))

    return ", ".join(str(i) for i in sorted(indices))


def build_checkbox_choices(parsed: list[str]) -> list[str]:
    """Return checkbox labels from parsed source blocks (first line, truncated)."""
    return [
        f"Source {i + 1}: {src.splitlines()[0][:120]}…"
        for i, src in enumerate(parsed)
    ]


def is_rejection(resume_value: dict) -> bool:
    """Return True when the user chose to reject and re-search."""
    return resume_value.get("action") == "reject"


def get_feedback(resume_value: dict) -> Optional[str]:
    return resume_value.get("feedback")


def get_selection(resume_value: dict) -> str:
    return resume_value.get("selection", "all")
