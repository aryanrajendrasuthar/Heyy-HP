"""Voice pipeline runtime — ties together VAD, wake word, STT, and TTS."""

from __future__ import annotations

import logging
import queue
import struct
import threading
from collections.abc import Callable
from typing import Any

from app.assistant.machine import AssistantStateMachine
from app.assistant.state import AssistantState
from app.config.settings import AppSettings

logger = logging.getLogger(__name__)

# ── Optional dependency guards ────────────────────────────────────────────
try:
    import pyaudio as _pyaudio

    _PYAUDIO_AVAILABLE = True
except ImportError:
    _PYAUDIO_AVAILABLE = False

try:
    from openwakeword.model import Model as _WakeModel  # type: ignore[import-untyped]

    _OWW_AVAILABLE = True
except ImportError:
    _OWW_AVAILABLE = False

try:
    from faster_whisper import WhisperModel as _WhisperModel  # type: ignore[import-untyped]

    _WHISPER_AVAILABLE = True
except ImportError:
    _WHISPER_AVAILABLE = False

try:
    import pyttsx3 as _pyttsx3  # type: ignore[import-untyped]

    _TTS_AVAILABLE = True
except ImportError:
    _TTS_AVAILABLE = False

# ── Constants ─────────────────────────────────────────────────────────────
_SAMPLE_RATE = 16_000
_CHUNK = 512
_FORMAT = 0x8  # paInt16


def _rms(data: bytes) -> float:
    n = len(data) // 2
    if n == 0:
        return 0.0
    samples = struct.unpack_from(f"{n}h", data)
    return (sum(s * s for s in samples) / n) ** 0.5


class VoiceRuntime:
    def __init__(
        self,
        settings: AppSettings,
        state_machine: AssistantStateMachine,
        *,
        on_transcript: Callable[[str], None] | None = None,
        on_response: Callable[[str], None] | None = None,
        on_command: Callable[[str], str | None] | None = None,
    ) -> None:
        self._settings = settings
        self._sm = state_machine
        self._on_transcript = on_transcript
        self._on_response = on_response
        self._on_command = on_command

        self._audio_q: queue.Queue[bytes] = queue.Queue()
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

        self._pa: Any = None
        self._stream: Any = None
        self._wake_model: Any = None
        self._stt_model: Any = None
        self._tts_engine: Any = None

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> None:
        self._stop_event.clear()
        self._init_audio()
        self._init_wake()
        self._init_stt()
        self._init_tts()
        t = threading.Thread(target=self._pipeline_loop, daemon=True, name="voice-pipeline")
        self._threads.append(t)
        t.start()
        logger.info("VoiceRuntime started")

    def stop(self) -> None:
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=3)
        self._threads.clear()
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
        if self._pa is not None:
            try:
                self._pa.terminate()
            except Exception:
                pass
        logger.info("VoiceRuntime stopped")

    # ── Init helpers ──────────────────────────────────────────────────────

    def _init_audio(self) -> None:
        if not _PYAUDIO_AVAILABLE:
            logger.warning("pyaudio not available — mic capture disabled")
            return
        try:
            self._pa = _pyaudio.PyAudio()
            self._stream = self._pa.open(
                format=_FORMAT,
                channels=1,
                rate=_SAMPLE_RATE,
                input=True,
                frames_per_buffer=_CHUNK,
                stream_callback=self._audio_callback,
            )
        except Exception:
            logger.exception("Failed to open audio stream")

    def _init_wake(self) -> None:
        if not _OWW_AVAILABLE:
            logger.warning("openwakeword not available — wake-word detection disabled")
            return
        try:
            self._wake_model = _WakeModel(
                wakeword_models=[self._settings.wake_word_model],
                inference_framework="onnx",
            )
        except Exception:
            logger.exception("Failed to load wake-word model")

    def _init_stt(self) -> None:
        if not _WHISPER_AVAILABLE:
            logger.warning("faster-whisper not available — STT disabled")
            return
        try:
            self._stt_model = _WhisperModel(
                self._settings.whisper_model,
                device="cpu",
                compute_type="int8",
            )
        except Exception:
            logger.exception("Failed to load Whisper model")

    def _init_tts(self) -> None:
        if not _TTS_AVAILABLE:
            logger.warning("pyttsx3 not available — TTS disabled")
            return
        try:
            self._tts_engine = _pyttsx3.init()
            self._tts_engine.setProperty("rate", self._settings.tts_rate)
        except Exception:
            logger.exception("Failed to init TTS engine")

    # ── Audio callback ────────────────────────────────────────────────────

    def _audio_callback(
        self,
        in_data: bytes | None,
        _frame_count: int,
        _time_info: dict[str, float],
        _status: int,
    ) -> tuple[None, int]:
        if in_data:
            self._audio_q.put(in_data)
        return None, 0  # paContinue

    # ── Pipeline loop ─────────────────────────────────────────────────────

    def _pipeline_loop(self) -> None:
        logger.debug("Pipeline loop started")
        while not self._stop_event.is_set():
            if self._stream is None:
                self._stop_event.wait(timeout=0.1)
                continue
            try:
                chunk = self._audio_q.get(timeout=0.1)
            except queue.Empty:
                continue
            self._process_chunk(chunk)

    def _process_chunk(self, chunk: bytes) -> None:
        current = self._sm.state
        if current == AssistantState.IDLE:
            self._check_wake(chunk)
        elif current == AssistantState.LISTENING:
            self._accumulate(chunk)

    def _check_wake(self, chunk: bytes) -> None:
        if self._wake_model is None:
            return
        try:
            import numpy as np  # type: ignore[import-untyped]

            audio = np.frombuffer(chunk, dtype=np.int16)
            scores = self._wake_model.predict(audio)
            threshold = self._settings.wake_word_threshold
            if any(v >= threshold for v in scores.values()):
                logger.info("Wake word detected")
                self._sm.trigger("wake")
        except Exception:
            logger.exception("Wake word check failed")

    _listen_buf: list[bytes] = []
    _silence_count: int = 0

    def _accumulate(self, chunk: bytes) -> None:
        self._listen_buf.append(chunk)
        rms = _rms(chunk)
        if rms < self._settings.vad_energy_threshold:
            self._silence_count += 1
        else:
            self._silence_count = 0
        silence_chunks = int(self._settings.silence_timeout_s * _SAMPLE_RATE / _CHUNK)
        if self._silence_count >= silence_chunks:
            audio = b"".join(self._listen_buf)
            self._listen_buf = []
            self._silence_count = 0
            self._transcribe(audio)

    def _transcribe(self, audio: bytes) -> None:
        if self._stt_model is None:
            self._sm.trigger("no_speech")
            return
        try:
            import numpy as np  # type: ignore[import-untyped]

            self._sm.trigger("processing")
            arr = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = self._stt_model.transcribe(arr, language="en")
            text = " ".join(s.text for s in segments).strip()
            if not text:
                self._sm.trigger("no_speech")
                return
            logger.info("Transcript: %s", text)
            if self._on_transcript:
                self._on_transcript(text)
            self._respond(text)
        except Exception:
            logger.exception("Transcription failed")
            self._sm.trigger("error")

    def _respond(self, text: str) -> None:
        response: str | None = None
        if self._on_command:
            response = self._on_command(text)
        if response is None:
            response = f"I heard you say: {text}"
        logger.info("Response: %s", response)
        if self._on_response:
            self._on_response(response)
        self._speak(response)
        self._sm.trigger("done")

    def _speak(self, text: str) -> None:
        if self._tts_engine is None:
            return
        try:
            self._sm.trigger("speak")
            self._tts_engine.say(text)
            self._tts_engine.runAndWait()
        except Exception:
            logger.exception("TTS failed")
