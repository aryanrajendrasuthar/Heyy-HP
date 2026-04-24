"""Assistant state enum — shared by the state machine, UI, and voice runtime."""

from __future__ import annotations

from enum import Enum, auto


class AssistantState(Enum):
    IDLE = auto()  # Listening only for the wake phrase
    WAKE_DETECTED = auto()  # Wake phrase heard; confirming before opening mic
    LISTENING = auto()  # Actively capturing a user utterance
    PROCESSING = auto()  # Transcribing / routing / generating response
    SPEAKING = auto()  # TTS playing back a response
    FOLLOW_UP = auto()  # 10-second window — no wake phrase required
