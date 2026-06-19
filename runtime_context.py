"""Per-run runtime context shared by the orchestrator and agents."""

from contextvars import ContextVar
from typing import Optional


gemini_api_key: ContextVar[Optional[str]] = ContextVar("gemini_api_key", default=None)


def get_gemini_api_key() -> Optional[str]:
    """Return the Gemini API key for the current run, if one was supplied."""
    return gemini_api_key.get()
