"""Unit tests for VoiceRuntime interruption logic."""

from __future__ import annotations

import struct
from unittest.mock import MagicMock

from app.assistant.machine import AssistantStateMachine
from app.assistant.state import AssistantState
from app.config.settings import AppSettings
from app.voice.runtime import VoiceRuntime, _rms


def _make_chunk(rms_value: float, n_samples: int = 512) -> bytes:
    """Build a chunk of int16 samples that produce approximately the given RMS."""

    amplitude = int(rms_value)
    amplitude = max(0, min(32767, amplitude))
    samples = [amplitude] * n_samples
    return struct.pack(f"{n_samples}h", *samples)


def _make_runtime(
    settings: AppSettings | None = None,
) -> tuple[VoiceRuntime, AssistantStateMachine]:
    s = settings or AppSettings()
    sm = AssistantStateMachine(s)
    rt = VoiceRuntime(s, sm)
    return rt, sm


def test_rms_zero_for_silence() -> None:
    chunk = bytes(1024)  # all zeros
    assert _rms(chunk) == 0.0


def test_rms_positive_for_signal() -> None:
    chunk = _make_chunk(1000)
    assert _rms(chunk) > 0


def test_check_interrupt_fires_when_loud() -> None:
    settings = AppSettings(vad_energy_threshold=300.0)
    rt, sm = _make_runtime(settings)
    # Force state to SPEAKING
    sm.on_wake()
    sm.on_utterance_end("test")
    sm.on_response_ready()
    assert sm.state is AssistantState.SPEAKING

    loud_chunk = _make_chunk(1000.0)  # well above 300 * 1.5 = 450
    rt._check_interrupt(loud_chunk)
    assert sm.state is AssistantState.LISTENING


def test_check_interrupt_does_not_fire_when_quiet() -> None:
    settings = AppSettings(vad_energy_threshold=300.0)
    rt, sm = _make_runtime(settings)
    sm.on_wake()
    sm.on_utterance_end("test")
    sm.on_response_ready()
    assert sm.state is AssistantState.SPEAKING

    quiet_chunk = _make_chunk(100.0)  # below 300 * 1.5 = 450
    rt._check_interrupt(quiet_chunk)
    assert sm.state is AssistantState.SPEAKING


def test_do_interrupt_calls_tts_stop() -> None:
    rt, sm = _make_runtime()
    mock_tts = MagicMock()
    rt._tts_engine = mock_tts
    sm.on_wake()
    sm.on_utterance_end("test")
    sm.on_response_ready()

    rt._do_interrupt()
    mock_tts.stop.assert_called_once()
    assert sm.state is AssistantState.LISTENING


def test_llm_fallback_used_when_command_returns_none() -> None:
    rt, sm = _make_runtime()
    rt._on_command = lambda t: None  # dispatcher returns None
    mock_llm = MagicMock()
    mock_llm.chat.return_value = "LLM response"
    rt._llm = mock_llm
    sm.on_wake()
    sm.on_utterance_end("what is the weather")
    # _respond runs synchronously here
    rt._respond("what is the weather")
    mock_llm.chat.assert_called_once_with("what is the weather")


def test_llm_not_called_when_command_matches() -> None:
    rt, sm = _make_runtime()
    rt._on_command = lambda t: "Launching notepad"
    mock_llm = MagicMock()
    rt._llm = mock_llm
    sm.on_wake()
    sm.on_utterance_end("open notepad")
    rt._respond("open notepad")
    mock_llm.chat.assert_not_called()


def test_conversation_buffer_populated_on_llm_response() -> None:
    rt, sm = _make_runtime()
    rt._on_command = lambda t: None
    mock_llm = MagicMock()
    mock_llm.chat.return_value = "The capital is Paris"
    rt._llm = mock_llm
    sm.on_wake()
    sm.on_utterance_end("capital of France")
    rt._respond("capital of France")
    history = rt._conv.history()
    assert any(t["role"] == "user" and "France" in t["text"] for t in history)
    assert any(t["role"] == "assistant" and "Paris" in t["text"] for t in history)
