"""
services/graph_service.py
──────────────────────────
Defines the LangGraph StateGraph:

  START → search → human_review → finalize → END
                       │
                       └─ (reject) → search  (re-search loop)

MemorySaver checkpointer enables pause/resume across two invoke() calls.
"""

from typing import Optional
from typing_extensions import TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from agents.research_agent import research_agent, GEMINI_API_KEY
from services.approval_service import is_rejection, get_feedback, get_selection
from config.settings import gemini_client_args, GEMINI_MODEL


# ── State ─────────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    topic: str
    sources: Optional[str]
    feedback: Optional[str]       # populated on rejection; used to refine re-search
    selected_sources: Optional[str]
    final_answer: Optional[str]


# ── Filtering LLM (reuses same model, no tools needed) ────────────────────────
_filter_llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    temperature=0,
    google_api_key=GEMINI_API_KEY,
    **gemini_client_args(),
)


def _as_text(content) -> str:
    """
    Flatten a message's content to plain text.

    Gemini returns ``content`` as a list of blocks
    (e.g. ``[{"type": "text", "text": "..."}]``), while OpenAI returns a plain
    string. Downstream code (parsing, the chat UI) expects a string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "\n".join(p for p in parts if p)
    return str(content)


# ── Node 1 — Search ───────────────────────────────────────────────────────────
def search_node(state: AgentState) -> dict:
    feedback = state.get("feedback")

    if feedback:
        prompt = (
            f"The user rejected the previous sources with the following feedback:\n"
            f"\"{feedback}\"\n\n"
            f"Please perform a new, improved search on the topic: {state['topic']}\n"
            f"Address the user's concerns and find better sources."
        )
    else:
        prompt = (
            f"Collect and present as a numbered list the information "
            f"sources on the following topic: {state['topic']}"
        )

    result = research_agent.invoke({
        "messages": [HumanMessage(content=prompt)]
    })

    return {"sources": _as_text(result["messages"][-1].content), "feedback": None}


# ── Node 2 — Human-in-the-Loop ────────────────────────────────────────────────
def human_review_node(state: AgentState) -> dict:
    """
    Pauses execution and surfaces sources to the caller.
    Resumes when Command(resume={"action": "approve"|"reject", ...}) is received.
    """
    resume_value = interrupt({"sources": state["sources"]})

    if is_rejection(resume_value):
        return {
            "selected_sources": None,
            "feedback": get_feedback(resume_value),
        }
    else:
        return {
            "selected_sources": get_selection(resume_value),
            "feedback": None,
        }


# ── Routing: approve → finalize, reject → search ──────────────────────────────
def route_after_review(state: AgentState) -> str:
    if state.get("feedback"):
        return "search"
    return "finalize"


# ── Node 3 — Finalize ─────────────────────────────────────────────────────────
def finalize_node(state: AgentState) -> dict:
    selection = (state.get("selected_sources") or "all").strip().lower()

    if selection == "all":
        final_answer = (
            f"✅ **All sources approved** for topic: *{state['topic']}*\n\n"
            + state["sources"]
        )
    else:
        filter_prompt = (
            f"The user reviewed the following numbered list of sources:\n\n"
            f"{state['sources']}\n\n"
            f"The user kept only these numbered entries: {selection}.\n\n"
            "Output ONLY the selected sources, preserving their original "
            "formatting and numbering."
        )
        filtered = _filter_llm.invoke([HumanMessage(content=filter_prompt)])
        final_answer = (
            f"✅ **Selected sources** for topic: *{state['topic']}*\n\n"
            + _as_text(filtered.content)
        )

    return {"final_answer": final_answer}


# ── Graph ─────────────────────────────────────────────────────────────────────
checkpointer = MemorySaver()

graph = (
    StateGraph(AgentState)
    .add_node("search", search_node)
    .add_node("human_review", human_review_node)
    .add_node("finalize", finalize_node)
    .add_edge(START, "search")
    .add_edge("search", "human_review")
    .add_conditional_edges("human_review", route_after_review, {
        "search": "search",
        "finalize": "finalize",
    })
    .add_edge("finalize", END)
    .compile(checkpointer=checkpointer)
)
