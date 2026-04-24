"""Unit tests for VoiceActivityDetector."""

from __future__ import annotations

import struct

import pytest

from app.voice.vad import VoiceActivityDetector, _rms


def _chunk(amplitude: int, n: int = 1024) -> bytes:
    return struct.pack(f"{n}h", *([amplitude] * n))


def test_rms_silent() -> None:
    assert _rms(_chunk(0)) == pytest.approx(0.0)


def test_rms_nonzero() -> None:
    assert _rms(_chunk(1000)) > 0


def test_silent_chunk_no_utterance() -> None:
    vad = VoiceActivityDetector(16000, silence_threshold=500.0, silence_duration_s=0.5)
    fired: list[bytes] = []
    vad.add_utterance_callback(fired.append)
    vad.process_chunk(_chunk(0))
    assert not fired


def test_utterance_fires_after_silence() -> None:
    vad = VoiceActivityDetector(16000, silence_threshold=500.0, silence_duration_s=0.0)
    fired: list[bytes] = []
    vad.add_utterance_callback(fired.append)
    vad.process_chunk(_chunk(1000))
    vad.process_chunk(_chunk(0))
    assert len(fired) == 1


def test_reset_clears_buffer() -> None:
    vad = VoiceActivityDetector(16000, silence_threshold=500.0, silence_duration_s=10.0)
    fired: list[bytes] = []
    vad.add_utterance_callback(fired.append)
    vad.process_chunk(_chunk(1000))
    vad.reset()
    vad.process_chunk(_chunk(0))
    assert not fired
