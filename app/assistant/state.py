"""Assistant conversation state enumeration."""

from __future__ import annotations

from enum import Enum, auto


class AssistantState(Enum):
    IDLE = auto()
    WAKE_DETECTED = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    FOLLOW_UP = auto()
