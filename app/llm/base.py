"""Abstract LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, prompt: str, history: list[Any] | None = None) -> str:
        """Send a prompt with optional prior conversation turns and return the text response."""
