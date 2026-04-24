"""Unit tests for TTSService."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

from app.voice.tts import TTSService


def test_unavailable_speak_no_error() -> None:
    tts = TTSService.__new__(TTSService)
    tts._available = False
    tts._engine = None
    tts._lock = threading.Lock()
    tts.speak("hello")


def test_speak_calls_engine() -> None:
    tts = TTSService.__new__(TTSService)
    tts._available = True
    tts._lock = threading.Lock()
    tts._engine = MagicMock()
    tts.speak("hello")
    tts._engine.say.assert_called_once_with("hello")
    tts._engine.runAndWait.assert_called_once()


def test_speak_async_calls_on_complete() -> None:
    tts = TTSService.__new__(TTSService)
    tts._available = False
    tts._engine = None
    tts._lock = threading.Lock()
    done = threading.Event()
    tts.speak_async("test", on_complete=done.set)
    assert done.wait(timeout=2.0)


def test_stop_calls_engine_stop() -> None:
    tts = TTSService.__new__(TTSService)
    tts._available = True
    tts._lock = threading.Lock()
    tts._engine = MagicMock()
    tts.stop()
    tts._engine.stop.assert_called_once()
