"""Groq LLM provider — ultra-fast inference for voice responses."""

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


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant") -> None:
        from groq import Groq  # lazy import
        self._client = Groq(api_key=api_key)
        self._model = model

    def chat(self, prompt: str, history: list | None = None) -> str:
        try:
            messages: list[dict] = [{"role": "system", "content": _SYSTEM}]
            if history:
                for turn in history:
                    messages.append({"role": turn["role"], "content": turn["text"]})
            else:
                messages.append({"role": "user", "content": prompt})
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=160,
                temperature=0.7,
            )
            return completion.choices[0].message.content.strip()
        except Exception:
            logger.exception("Groq API call failed")
            return "Sorry, I could not reach the AI service right now."
