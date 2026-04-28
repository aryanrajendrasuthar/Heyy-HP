"""Groq LLM provider — ultra-fast inference for voice responses."""

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


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant") -> None:
        from groq import Groq  # lazy import
        self._client = Groq(api_key=api_key)
        self._model = model

    def chat(self, prompt: str) -> str:
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=120,
                temperature=0.7,
            )
            return completion.choices[0].message.content.strip()
        except Exception:
            logger.exception("Groq API call failed")
            return "Sorry, I could not reach the AI service right now."
