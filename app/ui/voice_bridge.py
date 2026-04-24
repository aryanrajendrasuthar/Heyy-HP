"""Qt signal bridge — routes voice-thread events to the main-thread UI."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class VoiceBridge(QObject):
    state_changed: Signal = Signal(object)  # AssistantState
    transcript_ready: Signal = Signal(str)
    response_ready: Signal = Signal(str)

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
