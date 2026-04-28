"""Anthropic Claude LLM provider."""

from __future__ import annotations

import logging

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are HP, a smart Windows desktop voice assistant. "
    "Your responses are spoken aloud, so keep them SHORT — two sentences maximum. "
    "Be direct, friendly and conversational. "
    "Never use markdown, bullet points, emojis or special characters. "
    "For factual questions give a brief clear answer. "
    "For things outside your abilities, say so in one sentence."
)


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001") -> None:
        import anthropic  # lazy import so missing package doesn't break startup
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def chat(self, prompt: str) -> str:
        try:
            msg = self._client.messages.create(
                model=self._model,
                max_tokens=120,
                system=_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception:
            logger.exception("Claude API call failed")
            return "Sorry, I could not reach the AI service right now."
