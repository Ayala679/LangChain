"""
agents/research_agent.py
─────────────────────────
Builds the ReAct sub-agent that uses Tavily to search the web.
Runs on Google Gemini (free tier). The sub-agent runs to completion inside
the `search` node, so the human-review interrupt in the outer graph is
unaffected by how many tool calls it makes.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langchain.agents import create_agent

from config.settings import require_key, gemini_client_args, GEMINI_MODEL
from tools.search_tool import tavily_tool

# ── API key ───────────────────────────────────────────────────────────────────
# Resolved here, on first import of the agent - not when config/ is imported.
GEMINI_API_KEY = require_key(
    "GEMINI_API_KEY", "GOOGLE_API_KEY",
    hint="get a free key at https://aistudio.google.com/apikey",
)

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    temperature=0,
    google_api_key=GEMINI_API_KEY,
    **gemini_client_args(),
)

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = SystemMessage(content=(
    "You are a research assistant specialized in collecting and summarizing "
    "information sources on any given topic.\n\n"
    "Your responsibilities:\n"
    "1. Search for reliable and relevant sources about the requested topic using "
    "the available search tools.\n"
    "2. Gather a diverse set of sources: news articles, academic references, "
    "official websites, and expert opinions.\n"
    "3. Present results as a NUMBERED LIST. For each source provide: title, URL, "
    "a brief summary, and its relevance to the topic.\n"
    "4. Organize the results clearly, grouping sources by sub-topic when possible.\n"
    "5. Always cite your sources and avoid presenting unverified information as fact.\n\n"
    "Your goal is to give the user a comprehensive numbered list of sources "
    "so they can review and decide which ones to keep.\n\n"
    "If you receive feedback that the sources were rejected, carefully read the "
    "feedback and perform a new, improved search addressing the user's concerns."
))

# ── Agent ─────────────────────────────────────────────────────────────────────
research_agent = create_agent(
    model=llm,
    tools=[tavily_tool],
    system_prompt=SYSTEM_PROMPT,
)
