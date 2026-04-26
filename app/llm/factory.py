"""LLM provider factory — returns the configured provider instance."""

from __future__ import annotations

from app.config.settings import AppSettings
from app.llm.base import LLMProvider
from app.llm.stub import StubLLM


def get_provider(settings: AppSettings) -> LLMProvider:
    """Return the LLM provider specified by settings.llm_provider."""
    name = settings.llm_provider.lower().strip()
    if name == "stub":
        return StubLLM()
    raise ValueError(f"Unknown LLM provider: {name!r}")
