"""Ollama local LLM provider (no API key needed)."""

from __future__ import annotations

import logging

import requests

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are HP, a smart Windows desktop voice assistant. "
    "Responses are spoken aloud — keep them SHORT, two sentences max. "
    "Be direct and conversational. No markdown or special characters. "
    "SPECIAL RULE — when the topic genuinely benefits from watching a video "
    "(cooking a recipe, exercise form, dance moves, DIY repair, art techniques, "
    "any step-by-step physical skill or craft), append this tag at the very end "
    "of your response: [VIDEO:concise youtube search query] "
    "Use [VIDEO:] ONLY for visual how-to content. "
    "Do NOT use it for facts, weather, math, definitions, news, or conversation."
)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def chat(self, prompt: str, history: list | None = None) -> str:
        try:
            if history:
                messages = [{"role": "system", "content": _SYSTEM}]
                for turn in history:
                    messages.append({"role": turn["role"], "content": turn["text"]})
                resp = requests.post(
                    f"{self._base_url}/api/chat",
                    json={"model": self._model, "messages": messages, "stream": False},
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json().get("message", {}).get("content", "").strip()
            else:
                resp = requests.post(
                    f"{self._base_url}/api/generate",
                    json={"model": self._model, "prompt": prompt, "system": _SYSTEM, "stream": False},
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json().get("response", "").strip()
        except Exception:
            logger.exception("Ollama request failed")
            return "Sorry, I could not reach the local AI model right now."
