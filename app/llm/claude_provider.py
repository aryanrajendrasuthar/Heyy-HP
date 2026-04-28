"""Anthropic Claude LLM provider."""

from __future__ import annotations

import logging

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are HP, a smart Windows desktop voice assistant. "
    "Responses are spoken aloud — keep them SHORT, two sentences max. "
    "Be direct, friendly and conversational. "
    "Never use markdown, bullet points, emojis or special characters. "
    "For factual questions give a brief clear answer. "
    "For things outside your abilities, say so in one sentence. "
    "SPECIAL RULE — when the topic genuinely benefits from watching a video "
    "(cooking a recipe, exercise form, dance moves, DIY repair, art techniques, "
    "any step-by-step physical skill or craft), append this tag at the very end "
    "of your response: [VIDEO:concise youtube search query] "
    "Use [VIDEO:] ONLY for visual how-to content. "
    "Do NOT use it for facts, weather, math, definitions, news, or conversation."
)


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001") -> None:
        import anthropic  # lazy import so missing package doesn't break startup
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def chat(self, prompt: str, history: list | None = None) -> str:
        try:
            if history:
                messages = [{"role": t["role"], "content": t["text"]} for t in history]
            else:
                messages = [{"role": "user", "content": prompt}]
            msg = self._client.messages.create(
                model=self._model,
                max_tokens=160,
                system=_SYSTEM,
                messages=messages,
            )
            return msg.content[0].text.strip()
        except Exception:
            logger.exception("Claude API call failed")
            return "Sorry, I could not reach the AI service right now."
