"""
services/chat_service.py
─────────────────────────
Thin orchestration layer between the UI and the LangGraph.
Handles both the initial invoke and the resume invoke, returning
structured results so the UI layer stays logic-free.
"""

import time
from langgraph.types import Command
from services.graph_service import graph


def new_thread_id() -> str:
    return f"thread_{int(time.time())}"


def make_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def start_run(topic: str, thread_id: str) -> dict:
    """
    Phase 1: invoke the graph from START.
    Returns a dict with keys:
      - interrupted (bool)
      - sources (str | None)   — present when interrupted
      - final_answer (str | None) — present when graph ran to completion
    """
    config = make_config(thread_id)
    result = graph.invoke({"topic": topic}, config)
    interrupts = result.get("__interrupt__", [])

    if interrupts:
        return {
            "interrupted": True,
            "sources": interrupts[0].value["sources"],
            "final_answer": None,
        }

    return {
        "interrupted": False,
        "sources": None,
        "final_answer": result.get("final_answer") or result.get("sources", ""),
    }


def resume_run(resume_payload: dict, thread_id: str) -> dict:
    """
    Phase 2 (or N): resume after a HITL interrupt.
    resume_payload must be {"action": "approve", "selection": "..."} or
                           {"action": "reject",  "feedback":  "..."}

    Returns a dict with keys:
      - interrupted (bool)  — True if another HITL interrupt occurred (re-search)
      - sources (str | None)
      - final_answer (str | None)
    """
    config = make_config(thread_id)
    result = graph.invoke(Command(resume=resume_payload), config)
    interrupts = result.get("__interrupt__", [])

    if interrupts:
        return {
            "interrupted": True,
            "sources": interrupts[0].value["sources"],
            "final_answer": None,
        }

    return {
        "interrupted": False,
        "sources": None,
        "final_answer": result.get("final_answer", ""),
    }
