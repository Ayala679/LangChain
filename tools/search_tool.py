"""
tools/search_tool.py
────────────────────
Initializes the Tavily web-search tool used by the research agent.
The Tavily key is resolved lazily via require_key (see config/settings.py).
"""

from langchain_tavily import TavilySearch
from config.settings import require_key, TAVILY_MAX_RESULTS

TAVILY_API_KEY = require_key(
    "TAVILY_API_KEY", "TAVILY_KEY",
    hint="get a free key at https://app.tavily.com/",
)

tavily_tool = TavilySearch(
    max_results=TAVILY_MAX_RESULTS,
    tavily_api_key=TAVILY_API_KEY,
)
