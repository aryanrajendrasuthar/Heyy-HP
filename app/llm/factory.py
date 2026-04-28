"""LLM provider factory — returns the configured provider instance."""

from __future__ import annotations

import logging

from app.config.settings import AppSettings
from app.llm.base import LLMProvider
from app.llm.stub import StubLLM

logger = logging.getLogger(__name__)


def get_provider(settings: AppSettings) -> LLMProvider:
    name = settings.llm_provider.lower().strip()

    if name == "claude":
        if not settings.anthropic_api_key:
            logger.warning(
                "HP_LLM_PROVIDER=claude but HP_ANTHROPIC_API_KEY is not set. "
                "Create a .env file next to HP.exe with: HP_ANTHROPIC_API_KEY=sk-ant-..."
            )
            return StubLLM()
        from app.llm.claude_provider import ClaudeProvider
        return ClaudeProvider(api_key=settings.anthropic_api_key, model=settings.llm_model)

    if name == "groq":
        if not settings.groq_api_key:
            logger.warning("HP_LLM_PROVIDER=groq but HP_GROQ_API_KEY is not set.")
            return StubLLM()
        from app.llm.groq_provider import GroqProvider
        return GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)

    if name == "ollama":
        from app.llm.ollama_provider import OllamaProvider
        return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)

    return StubLLM()
