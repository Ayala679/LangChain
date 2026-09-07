"""
config/settings.py
──────────────────
Loads the .env file and resolves API keys *lazily* - the first time a key is
actually needed, not at import time.

This mirrors the key-handling style used in Weather--MCP
(https://github.com/Ayala679/Weather--MCP): a small ``require_key`` helper with
a fallback chain of environment-variable names and a single, friendly
``RuntimeError`` that tells you exactly where to get a key. The model provider
here is Google Gemini, which has a free tier - same as Weather--MCP.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def require_key(*names: str, hint: str) -> str:
    """
    Return the first non-empty environment variable from ``names``.

    ``names`` is a fallback chain - e.g. ``require_key("GEMINI_API_KEY",
    "GOOGLE_API_KEY", hint=...)`` accepts either name. Placeholder values left
    over from the template (``your_...``) are treated as "not set".

    Raises ``RuntimeError`` with ``hint`` appended when nothing is found.
    """
    for name in names:
        value = os.environ.get(name)
        if value and not value.startswith("your_"):
            return value

    raise RuntimeError(
        f"Missing {names[0]} in .env - {hint}"
    )


def gemini_client_args() -> dict:
    """
    Extra kwargs for ChatGoogleGenerativeAI.

    Same trick as Weather--MCP: ``client_args={"verify": False}`` disables TLS
    verification so requests pass through a TLS-inspecting proxy such as Netfree
    without a certificate error. Controlled by ``INSECURE_SSL`` in .env
    (default: on). Set ``INSECURE_SSL=0`` to verify certificates normally.
    """
    if os.getenv("INSECURE_SSL", "1") != "1":
        return {}
    return {"client_args": {"verify": False}}


# ── Non-secret configuration (safe to read at import time) ────────────────────
# "-lite" has a much larger free daily quota on Google AI Studio. Pin an
# explicit version (e.g. "gemini-2.5-flash-lite") for reproducible behaviour.
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
TAVILY_MAX_RESULTS: int = int(os.getenv("TAVILY_MAX_RESULTS", "5"))
