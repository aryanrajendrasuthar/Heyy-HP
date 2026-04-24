"""Speech-to-text — wraps faster-whisper with graceful degradation."""

from __future__ import annotations

import io
import logging
import wave
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TranscriptResult:
    text: str
    language: str
    confidence: float


class STTService:
    def __init__(self, model_size: str = "small", device: str = "cpu") -> None:
        self._model_size = model_size
        self._device = device
        self._model = None
        self._available = False
        self._init_model()

    def _init_model(self) -> None:
        try:
            from faster_whisper import WhisperModel  # noqa: PLC0415

            self._model = WhisperModel(self._model_size, device=self._device)
            self._available = True
            logger.info("STT model loaded: %s on %s", self._model_size, self._device)
        except Exception:
            logger.warning("faster-whisper not available — STT disabled")

    def transcribe(self, audio_bytes: bytes, sample_rate: int) -> TranscriptResult:
        if not self._available or self._model is None:
            return TranscriptResult(text="", language="en", confidence=0.0)
        try:
            wav_bytes = self._pcm_to_wav(audio_bytes, sample_rate)
            audio_file = io.BytesIO(wav_bytes)
            segments, info = self._model.transcribe(audio_file, language="en")
            text = " ".join(seg.text.strip() for seg in segments).strip()
            return TranscriptResult(text=text, language=info.language, confidence=1.0)
        except Exception:
            logger.exception("STT transcription error")
            return TranscriptResult(text="", language="en", confidence=0.0)

    @staticmethod
    def _pcm_to_wav(pcm: bytes, sample_rate: int) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm)
        return buf.getvalue()
