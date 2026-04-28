"""Ollama local LLM provider (no API key needed)."""

from __future__ import annotations

import logging

import requests

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are HP, a smart Windows desktop voice assistant. "
    "Keep responses SHORT — two sentences maximum — since they are spoken aloud. "
    "Be direct and conversational. No markdown or special characters."
)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2") -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def chat(self, prompt: str) -> str:
        try:
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
