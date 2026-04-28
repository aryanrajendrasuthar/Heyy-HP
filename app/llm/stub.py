"""Stub LLM provider used in tests and offline mode."""

from __future__ import annotations

from app.llm.base import LLMProvider


class StubLLM(LLMProvider):
    def chat(self, prompt: str) -> str:
        return (
            "I can run commands but I am not connected to an AI. "
            "Add HP_ANTHROPIC_API_KEY to a .env file next to HP.exe to enable answers."
        )
