# 🧭 Source Scout

An AI-powered research assistant that scouts the web for information sources on any topic, then lets **you** decide which sources to keep — powered by LangChain, LangGraph, Tavily, and a Gradio UI.

---

## ✨ Features

- 🤖 **AI Agent** — uses Google Gemini (`gemini-flash-lite-latest`, free tier) to orchestrate tool calls
- 🌐 **Web Search** — powered by [Tavily](https://tavily.com/) for real-time, reliable results
- 🧠 **Memory & Checkpointing** — `MemorySaver` persists graph state across the pause/resume cycle
- 🛑 **Human-in-the-Loop (HITL)** — the agent pauses after collecting sources; you approve or reject before anything continues
- ✅ **Approve & Filter** — select specific sources; the agent returns only what you approved
- 🔄 **Reject & Re-search** — provide feedback and the agent performs a new, improved search
- 🔑 **Lazy key resolution** — keys are read the first time they're needed via a `require_key()` helper (fallback chain of env-var names + a single friendly `RuntimeError` pointing you to where to get a key), following the approach in [Weather--MCP](https://github.com/Ayala679/Weather--MCP)
- 🖥️ **Two interfaces** — terminal CLI (`agent.py`) and Gradio web UI (`app.py`)
- 🗂️ **Modular architecture** — logic is split across `config/`, `agents/`, `tools/`, `services/`, and `ui/`

---

## 🗂️ Project Structure

```
LangChain/
├── config/
│   └── settings.py           # Loads .env; require_key() + insecure_http_clients() helpers
├── agents/
│   └── research_agent.py     # create_agent + system prompt + Gemini LLM + GEMINI_API_KEY
├── tools/
│   └── search_tool.py        # Tavily search tool initialization
├── services/
│   ├── graph_service.py      # StateGraph: search → human_review → finalize (+ reject loop)
│   ├── approval_service.py   # Source parsing, checkbox label building, approve/reject helpers
│   └── chat_service.py       # start_run / resume_run — bridges UI ↔ graph
├── ui/
│   ├── components.py         # All Gradio components declared as module-level objects
│   └── handlers.py           # handle_search, handle_approve, handle_reject generators
├── agent.py                  # CLI entry point
├── app.py                    # Gradio web UI entry point (theme + CSS live here)
├── .env.example              # Template — copy to .env and add your keys
├── .env                      # Your keys (not committed — see .gitignore)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Architecture

The agent is a **3-node LangGraph `StateGraph`** with a reject-and-re-search loop:

```
[START]
   │
   ▼
┌─────────┐     Tavily web search + Gemini reasoning
│ search  │  ──────────────────────────────────────▶  numbered list of sources
└─────────┘  ◀──────────────────── (re-search with feedback)
   │                                                  │
   ▼                                                  │  reject
┌──────────────┐   interrupt() pauses here            │
│ human_review │  ────────────────────────────────────┘
└──────────────┘   Command(resume=...) resumes here
   │  approve
   ▼
┌──────────┐     Gemini filters down to selected sources only
│ finalize │  ──────────────────────────────────────▶  final approved list
└──────────┘
   │
   ▼
 [END]
```

### State fields

| Field | Type | Description |
|---|---|---|
| `topic` | `str` | Research topic entered by the user |
| `sources` | `str` | Numbered list of sources produced by the search agent |
| `feedback` | `str` | Rejection message — fed back into `search` for a refined re-search |
| `selected_sources` | `str` | Approval selection: comma-separated numbers or `"all"` |
| `final_answer` | `str` | Final filtered and formatted list of approved sources |

### Human-in-the-Loop mechanism

1. After `search` completes, the graph enters `human_review`
2. `interrupt(payload)` **pauses** the graph and returns the sources to the caller
3. The user either **approves** (with an optional source selection) or **rejects** (with feedback text)
4. `graph.invoke(Command(resume=payload), config)` **resumes** the graph
5. On **approve** → `finalize` filters and returns results
6. On **reject** → the graph routes back to `search` with the feedback, which the agent uses to improve its query
7. The `thread_id` in the config allows `MemorySaver` to restore the frozen state across multiple `invoke()` calls

### Why the HITL interrupt is safe

The research sub-agent runs to completion *inside* the `search` node and returns
plain text. The `interrupt()` lives in a separate `human_review` node that only
runs afterwards — so no matter how many tool calls the sub-agent makes, the graph
always pauses for your review before anything is finalized.

---

## 🖥️ Interfaces

### 1. Terminal CLI — `agent.py`

```bash
# Default topic
python agent.py

# Custom topic
python agent.py "quantum computing"
```

**Example session:**
```
Searching for sources on: "quantum computing"
------------------------------------------------------------
 SOURCES FOUND:

1. IBM Quantum — https://quantum.ibm.com/
   Summary: Official IBM platform for quantum computing...

2. Nature: Quantum Information — https://www.nature.com/npjqi/
   Summary: Peer-reviewed journal covering quantum science...

------------------------------------------------------------
Options:
  [1] Approve selected sources
  [2] Reject and re-search with feedback

Choose (1/2): 1

Enter source numbers to keep (e.g. 1,3,5) or press Enter for all: 1,3

------------------------------------------------------------
✅ Selected sources for topic: "quantum computing"

1. IBM Quantum — ...
3. Nature: Quantum Information — ...
```

---

### 2. Gradio Web UI — `app.py`

```bash
python app.py
# Opens at http://127.0.0.1:7860
```

**UI flow:**

| Step | What happens |
|---|---|
| 1 | User types a research topic and clicks **🔍 Search** |
| 2 | Agent searches the web; chat shows a loading message |
| 3 | Sources appear in the chat; all sources are pre-checked in a **CheckboxGroup** |
| 4a — Approve | Uncheck unwanted sources → click **✅ Approve Selected** → final list displayed |
| 4b — Reject | Type feedback → click **🔄 Reject & Re-search** → agent searches again → back to step 3 |

---

## 🚀 Setup

### 1. Prerequisites

- Python 3.10 – 3.13 *(Python 3.14 has Pydantic v1 incompatibilities)*
- A [Google Gemini API key](https://aistudio.google.com/apikey) — free
- A [Tavily API key](https://app.tavily.com/) — free

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API keys

Copy the template and fill in your own keys:

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

```env
GEMINI_API_KEY=...       # Free key: https://aistudio.google.com/apikey
TAVILY_API_KEY=tvly-...  # Free key: https://app.tavily.com/

# Optional overrides
# GEMINI_MODEL=gemini-flash-lite-latest
# TAVILY_MAX_RESULTS=5
# INSECURE_SSL=1          # 1 = skip TLS verification (useful behind Netfree); 0 = verify
```

Keys are resolved by `require_key()` in [`config/settings.py`](config/settings.py) the
first time the agent or the search tool is imported. If a key is missing you get a
single line telling you which one and where to get it — no stack trace at import time.

### 4. Run

```bash
# Web UI (recommended)
python app.py

# Terminal CLI
python agent.py "your topic here"
```

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `langchain` | Agent orchestration (`create_agent`) |
| `langchain-google-genai` | Google Gemini model integration |
| `langchain-tavily` | Tavily web search tool |
| `langgraph` | `StateGraph`, `interrupt`, `Command`, `MemorySaver` |
| `gradio` ≥6.0 | Web UI — chat, checkboxes, buttons, Soft theme + custom CSS |
| `python-dotenv` | Load API keys from `.env` |

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | ✅ | — | Google Gemini API key (`GOOGLE_API_KEY` also accepted) |
| `TAVILY_API_KEY` | ✅ | — | Tavily search API key (`TAVILY_KEY` also accepted) |
| `GEMINI_MODEL` | ✗ | `gemini-flash-lite-latest` | Gemini model to use |
| `TAVILY_MAX_RESULTS` | ✗ | `5` | Max search results per query |
| `INSECURE_SSL` | ✗ | `1` | `1` skips TLS verification for Gemini calls (Netfree-friendly); `0` verifies |

