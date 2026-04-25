"""Stub LLM provider used in tests and offline mode."""

from __future__ import annotations

from app.llm.base import LLMProvider


class StubLLM(LLMProvider):
    def chat(self, prompt: str) -> str:
        return f"I heard you say: {prompt}"
