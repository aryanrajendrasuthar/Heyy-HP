"""Unit tests for STTService."""

from __future__ import annotations

import io
import struct
import wave
from unittest.mock import MagicMock

from app.voice.stt import STTService, TranscriptResult


def _pcm(n: int = 16000) -> bytes:
    return struct.pack(f"{n}h", *([0] * n))


def test_unavailable_returns_empty() -> None:
    stt = STTService.__new__(STTService)
    stt._available = False
    stt._model = None
    result = stt.transcribe(b"", 16000)
    assert result.text == ""
    assert isinstance(result, TranscriptResult)


def test_pcm_to_wav_roundtrip() -> None:
    wav = STTService._pcm_to_wav(_pcm(1600), 16000)
    with wave.open(io.BytesIO(wav), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 16000


def test_transcribe_uses_model() -> None:
    stt = STTService.__new__(STTService)
    stt._available = True
    stt._model_size = "small"
    stt._device = "cpu"

    seg = MagicMock()
    seg.text = " hello world"
    info = MagicMock()
    info.language = "en"

    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([seg], info)
    stt._model = mock_model

    result = stt.transcribe(_pcm(), 16000)
    assert result.text == "hello world"
    assert result.language == "en"
