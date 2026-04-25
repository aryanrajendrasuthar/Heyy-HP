"""Abstract LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, prompt: str) -> str:
        """Send a prompt and return the text response."""
