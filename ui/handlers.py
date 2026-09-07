"""
ui/handlers.py
───────────────
Gradio event handler functions.
Each generator yields incremental UI state updates.
All graph/approval logic is delegated to the service layer.
"""

import gradio as gr

from services.chat_service import start_run, resume_run, new_thread_id
from services.approval_service import parse_sources, build_checkbox_choices, build_selection_text


# ── Helpers ───────────────────────────────────────────────────────────────────
def _show_hitl_panel(choices: list[str]):
    """Return gr.update() calls that reveal the HITL panel."""
    return (
        gr.update(choices=choices, value=choices, visible=True),  # checkboxes (all pre-checked)
        gr.update(visible=True),                                   # feedback input
        gr.update(visible=True),                                   # approve btn
        gr.update(visible=True),                                   # reject btn
    )


def _hide_hitl_panel():
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def _apply_interrupt(raw_sources: str, history: list, session: dict):
    """Update history + session when a HITL interrupt occurs."""
    parsed = parse_sources(raw_sources)
    choices = build_checkbox_choices(parsed)

    session["raw_sources"] = raw_sources
    session["parsed"] = parsed
    session["stage"] = "review"

    history = history[:-1] + [(
        None,
        "📋 Here are the sources I found. **Select the ones you want to keep**, "
        "or provide feedback and click *Reject & Re-search*."
    )]
    return history, session, choices


# ── Handler 1: initial search ─────────────────────────────────────────────────
def handle_search(topic: str, session: dict, history: list):
    if not topic.strip():
        yield (history, session, gr.update(), gr.update(interactive=True)) + _hide_hitl_panel()
        return

    thread_id = new_thread_id()
    session = {"thread_id": thread_id, "raw_sources": "", "parsed": [], "stage": "searching"}

    history = history + [
        (f"🔍 Research topic: **{topic}**", None),
        (None, "⏳ Searching for sources, please wait…"),
    ]
    yield (history, session,
           gr.update(value="", interactive=False),
           gr.update(interactive=False)) + _hide_hitl_panel()

    run = start_run(topic, thread_id)

    if run["interrupted"]:
        history, session, choices = _apply_interrupt(run["sources"], history, session)
        yield (history, session,
               gr.update(interactive=False),
               gr.update(interactive=True)) + _show_hitl_panel(choices)
    else:
        history = history[:-1] + [(None, run["final_answer"])]
        session["stage"] = "done"
        yield (history, session,
               gr.update(interactive=True),
               gr.update(interactive=True)) + _hide_hitl_panel()


# ── Handler 2: approve selected sources ──────────────────────────────────────
def handle_approve(chosen: list, session: dict, history: list):
    if session.get("stage") != "review":
        yield (history, session) + _hide_hitl_panel()
        return

    selection = build_selection_text(chosen)
    display   = "all sources" if selection == "all" else f"sources {selection}"

    history = history + [
        (f"✅ I approved: {display}", None),
        (None, "⏳ Preparing your final list…"),
    ]
    yield (history, session) + _hide_hitl_panel()

    run = resume_run(
        {"action": "approve", "selection": selection},
        session["thread_id"],
    )

    if run["interrupted"]:
        # Rare edge case — the graph went back for another search cycle
        history, session, choices = _apply_interrupt(run["sources"], history, session)
        yield (history, session) + _show_hitl_panel(choices)
    else:
        history = history[:-1] + [(None, run["final_answer"])]
        session["stage"] = "done"
        yield (history, session) + _hide_hitl_panel()


# ── Handler 3: reject and re-search ──────────────────────────────────────────
def handle_reject(feedback: str, session: dict, history: list):
    if session.get("stage") != "review":
        yield (history, session) + _hide_hitl_panel()
        return

    fb = feedback.strip() or "Please find better, more relevant sources."

    history = history + [
        (f"🔄 Re-search requested: *{fb}*", None),
        (None, "⏳ Searching again with your feedback…"),
    ]
    yield (history, session) + _hide_hitl_panel()

    run = resume_run(
        {"action": "reject", "feedback": fb},
        session["thread_id"],
    )

    if run["interrupted"]:
        history, session, choices = _apply_interrupt(run["sources"], history, session)
        yield (history, session) + _show_hitl_panel(choices)
    else:
        history = history[:-1] + [(None, run["final_answer"])]
        session["stage"] = "done"
        yield (history, session) + _hide_hitl_panel()
