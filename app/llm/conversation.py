"""Rolling conversation history buffer for multi-turn LLM context."""

from __future__ import annotations

from collections import deque
from typing import TypedDict


class Turn(TypedDict):
    role: str  # "user" or "assistant"
    text: str


class ConversationBuffer:
    """Fixed-capacity FIFO of conversation turns (pairs)."""

    def __init__(self, max_turns: int = 10) -> None:
        if max_turns < 1:
            raise ValueError("max_turns must be >= 1")
        self._max = max_turns
        self._buf: deque[Turn] = deque()

    def add(self, role: str, text: str) -> None:
        self._buf.append(Turn(role=role, text=text))
        while len(self._buf) > self._max:
            self._buf.popleft()

    def history(self) -> list[Turn]:
        return list(self._buf)

    def clear(self) -> None:
        self._buf.clear()

    def __len__(self) -> int:
        return len(self._buf)
