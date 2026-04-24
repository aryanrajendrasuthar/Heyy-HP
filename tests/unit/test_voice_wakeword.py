"""Unit tests for WakeWordListener."""

from __future__ import annotations

import struct
from unittest.mock import MagicMock

from app.voice.wakeword import WakeWordListener


def _chunk(n: int = 512) -> bytes:
    return struct.pack(f"{n}h", *([0] * n))


def test_unavailable_process_no_error() -> None:
    ww = WakeWordListener.__new__(WakeWordListener)
    ww._available = False
    ww._model = None
    ww._callbacks = []
    ww.process_chunk(_chunk())


def test_callback_fires_above_threshold() -> None:
    ww = WakeWordListener.__new__(WakeWordListener)
    ww._available = True
    ww._sensitivity = 0.5
    ww._callbacks = []
    ww._model = MagicMock()
    ww._model.predict.return_value = {"hey_jarvis": 0.9}

    fired: list[bool] = []
    ww.add_wake_callback(lambda: fired.append(True))
    ww.process_chunk(_chunk())
    assert fired


def test_callback_silent_below_threshold() -> None:
    ww = WakeWordListener.__new__(WakeWordListener)
    ww._available = True
    ww._sensitivity = 0.5
    ww._callbacks = []
    ww._model = MagicMock()
    ww._model.predict.return_value = {"hey_jarvis": 0.1}

    fired: list[bool] = []
    ww.add_wake_callback(lambda: fired.append(True))
    ww.process_chunk(_chunk())
    assert not fired
