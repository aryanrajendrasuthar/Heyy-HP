"""Write all Sprint 4 files to disk."""

from pathlib import Path

BASE = Path(r"d:\My Career\Projects\HP-AI assistant")
files: dict[str, str] = {}

# ── app/llm/conversation.py ───────────────────────────────────────────────
files[
    "app/llm/conversation.py"
] = r'''"""Rolling conversation history buffer for multi-turn LLM context."""

from __future__ import annotations

from collections import deque
from typing import TypedDict


class Turn(TypedDict):
    role: str   # "user" or "assistant"
    text: str


class ConversationBuffer:
    """Fixed-capacity FIFO of conversation turns (pairs)."""

    def __init__(self, max_turns: int = 10) -> None:
        if max_turns < 1:
            raise ValueError("max_turns must be >= 1")
        self._max = max_turns
        self._buf: deque[Turn] = deque()

    def add(self, role: str, text: str) -> None:
        self._buf.append(Turn(role=role, text=text))
        while len(self._buf) > self._max:
            self._buf.popleft()

    def history(self) -> list[Turn]:
        return list(self._buf)

    def clear(self) -> None:
        self._buf.clear()

    def __len__(self) -> int:
        return len(self._buf)
'''

# ── app/llm/factory.py ────────────────────────────────────────────────────
files[
    "app/llm/factory.py"
] = r'''"""LLM provider factory — returns the configured provider instance."""

from __future__ import annotations

from app.config.settings import AppSettings
from app.llm.base import LLMProvider
from app.llm.stub import StubLLM


def get_provider(settings: AppSettings) -> LLMProvider:
    """Return the LLM provider specified by settings.llm_provider."""
    name = settings.llm_provider.lower().strip()
    if name == "stub":
        return StubLLM()
    raise ValueError(f"Unknown LLM provider: {name!r}")
'''

# ── app/assistant/machine.py (updated: recovery methods + reset) ──────────
files["app/assistant/machine.py"] = r'''"""Thread-safe assistant state machine."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from app.assistant.state import AssistantState
from app.assistant.timer import FollowUpTimer
from app.config.settings import AppSettings

logger = logging.getLogger(__name__)

StateCallback = Callable[[AssistantState], None]

_S = AssistantState
_TRANSITIONS: dict[tuple[AssistantState, str], AssistantState] = {
    (_S.IDLE, "wake"): _S.LISTENING,
    (_S.WAKE_DETECTED, "wake"): _S.LISTENING,
    (_S.LISTENING, "utterance_end"): _S.PROCESSING,
    (_S.LISTENING, "no_speech"): _S.IDLE,
    (_S.PROCESSING, "response_ready"): _S.SPEAKING,
    (_S.PROCESSING, "no_speech"): _S.IDLE,
    (_S.PROCESSING, "error"): _S.IDLE,
    (_S.SPEAKING, "speaking_done"): _S.FOLLOW_UP,
    (_S.SPEAKING, "interrupted"): _S.LISTENING,
    (_S.SPEAKING, "error"): _S.IDLE,
    (_S.FOLLOW_UP, "utterance_end"): _S.PROCESSING,
    (_S.FOLLOW_UP, "wake"): _S.LISTENING,
    (_S.FOLLOW_UP, "timeout"): _S.IDLE,
}


class AssistantStateMachine:
    def __init__(self, settings: AppSettings) -> None:
        self._state = _S.IDLE
        self._lock = threading.Lock()
        self._callbacks: list[StateCallback] = []
        self._timer = FollowUpTimer(settings.follow_up_timeout_s, self._on_timer_expired)

    @property
    def state(self) -> AssistantState:
        with self._lock:
            return self._state

    def add_state_callback(self, cb: StateCallback) -> None:
        self._callbacks.append(cb)

    def on_wake(self) -> None:
        self._fire("wake")

    def on_utterance_end(self, text: str = "") -> None:
        self._fire("utterance_end")

    def on_response_ready(self) -> None:
        self._fire("response_ready")

    def on_speaking_done(self) -> None:
        self._fire("speaking_done")
        self._timer.start()

    def on_interrupted(self) -> None:
        self._timer.cancel()
        self._fire("interrupted")

    def on_no_speech(self) -> None:
        self._fire("no_speech")

    def on_error(self) -> None:
        self._timer.cancel()
        self.reset()

    def reset(self) -> None:
        """Force state back to IDLE regardless of current state."""
        with self._lock:
            if self._state is _S.IDLE:
                return
            logger.debug("Reset: %s --> IDLE", self._state)
            self._state = _S.IDLE
            callbacks = list(self._callbacks)
        for cb in callbacks:
            try:
                cb(_S.IDLE)
            except Exception:
                logger.exception("State callback raised during reset")

    def _on_timer_expired(self) -> None:
        self._fire("timeout")

    def _fire(self, event: str) -> None:
        with self._lock:
            key = (self._state, event)
            next_state = _TRANSITIONS.get(key)
            if next_state is None:
                logger.debug("No transition from %s on '%s'", self._state, event)
                return
            logger.debug("State %s --[%s]--> %s", self._state, event, next_state)
            self._state = next_state
            callbacks = list(self._callbacks)

        for cb in callbacks:
            try:
                cb(next_state)
            except Exception:
                logger.exception("State callback raised")
'''

# ── app/voice/runtime.py (updated: fix triggers, interruption, LLM) ───────
files[
    "app/voice/runtime.py"
] = r'''"""Voice pipeline runtime — ties together VAD, wake word, STT, and TTS."""

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
from app.llm.conversation import ConversationBuffer

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
_INTERRUPT_RMS_MULTIPLIER = 1.5  # speech during TTS must exceed this × vad threshold


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
        llm: Any | None = None,
        conversation: ConversationBuffer | None = None,
    ) -> None:
        self._settings = settings
        self._sm = state_machine
        self._on_transcript = on_transcript
        self._on_response = on_response
        self._on_command = on_command
        self._llm = llm
        self._conv = conversation or ConversationBuffer(max_turns=10)

        self._audio_q: queue.Queue[bytes] = queue.Queue()
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

        self._pa: Any = None
        self._stream: Any = None
        self._wake_model: Any = None
        self._stt_model: Any = None
        self._tts_engine: Any = None
        self._tts_lock = threading.Lock()

        self._listen_buf: list[bytes] = []
        self._silence_count: int = 0

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
                device=self._settings.stt_device,
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
            self._tts_engine.setProperty("volume", self._settings.tts_volume)
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
        elif current in (AssistantState.LISTENING, AssistantState.FOLLOW_UP):
            self._accumulate(chunk)
        elif current == AssistantState.SPEAKING:
            self._check_interrupt(chunk)

    # ── Wake-word detection ───────────────────────────────────────────────

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
                self._sm.on_wake()
        except Exception:
            logger.exception("Wake word check failed")

    # ── Listening / VAD ───────────────────────────────────────────────────

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

    # ── Transcription ─────────────────────────────────────────────────────

    def _transcribe(self, audio: bytes) -> None:
        if self._stt_model is None:
            self._sm.on_no_speech()
            return
        try:
            import numpy as np  # type: ignore[import-untyped]

            self._sm.on_utterance_end()
            arr = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
            segments, _ = self._stt_model.transcribe(arr, language="en")
            text = " ".join(s.text for s in segments).strip()
            if not text:
                self._sm.on_no_speech()
                return
            logger.info("Transcript: %s", text)
            if self._on_transcript:
                self._on_transcript(text)
            self._respond(text)
        except Exception:
            logger.exception("Transcription failed")
            self._sm.on_error()

    # ── Response ──────────────────────────────────────────────────────────

    def _respond(self, text: str) -> None:
        response: str | None = None

        # 1. Try command dispatcher
        if self._on_command:
            response = self._on_command(text)

        # 2. Fall back to LLM chat
        if response is None and self._llm is not None:
            try:
                self._conv.add("user", text)
                response = self._llm.chat(text)
                self._conv.add("assistant", response)
            except Exception:
                logger.exception("LLM chat failed")

        # 3. Ultimate echo fallback
        if response is None:
            response = f"I heard you say: {text}"

        logger.info("Response: %s", response)
        if self._on_response:
            self._on_response(response)
        self._speak(response)
        self._sm.on_speaking_done()

    # ── TTS + interruption ────────────────────────────────────────────────

    def _speak(self, text: str) -> None:
        if self._tts_engine is None:
            return
        try:
            self._sm.on_response_ready()
            with self._tts_lock:
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
        except Exception:
            logger.exception("TTS failed")

    def _check_interrupt(self, chunk: bytes) -> None:
        threshold = self._settings.vad_energy_threshold * _INTERRUPT_RMS_MULTIPLIER
        if _rms(chunk) > threshold:
            self._do_interrupt()

    def _do_interrupt(self) -> None:
        logger.info("Speech detected during TTS — interrupting")
        if self._tts_engine is not None:
            try:
                self._tts_engine.stop()
            except Exception:
                logger.debug("TTS stop() raised (may be harmless)", exc_info=True)
        self._sm.on_interrupted()
'''

# ── app/config/settings.py (updated: add llm_max_history) ────────────────
files[
    "app/config/settings.py"
] = r'''"""Application settings loaded from environment / .env file."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_name: str = "HP"
    log_level: str = "INFO"
    log_dir: str = "logs"
    debug: bool = False
    db_path: str = "data/hp.db"

    # Wake word
    wake_phrase: str = "Hey HP"
    wake_word_model: str = "hey_jarvis"
    wake_word_threshold: float = Field(default=0.5, ge=0.0, le=1.0)

    # Audio
    audio_sample_rate: int = Field(default=16000, gt=0)
    audio_device_index: int | None = None

    # VAD
    vad_energy_threshold: float = Field(default=300.0, ge=0.0)
    silence_timeout_s: float = Field(default=1.5, ge=0.1)

    # STT
    whisper_model: str = "tiny.en"
    stt_device: str = "cpu"

    # TTS
    tts_rate: int = Field(default=175, ge=50, le=400)
    tts_volume: float = Field(default=1.0, ge=0.0, le=1.0)

    # Follow-up
    follow_up_timeout_s: float = Field(default=10.0, gt=0)

    # LLM
    llm_provider: str = "stub"
    llm_max_history: int = Field(default=10, ge=1)
'''

# ── main.py (updated: wire LLM + conversation) ────────────────────────────
files["main.py"] = r'''"""HP Assistant — application entry point."""

from __future__ import annotations

import sys


def main() -> int:
    from app.assistant.dispatcher import CommandDispatcher
    from app.assistant.machine import AssistantStateMachine
    from app.config.settings import AppSettings
    from app.llm.conversation import ConversationBuffer
    from app.llm.factory import get_provider
    from app.ui.app import create_app
    from app.ui.main_window import HPMainWindow
    from app.ui.tray import HPTray
    from app.ui.voice_bridge import VoiceBridge
    from app.utils.logging import setup_logging
    from app.voice.runtime import VoiceRuntime

    settings = AppSettings()
    setup_logging(settings)

    app = create_app(settings)
    state_machine = AssistantStateMachine(settings)
    bridge = VoiceBridge()
    dispatcher = CommandDispatcher()
    llm = get_provider(settings)
    conv = ConversationBuffer(max_turns=settings.llm_max_history)

    state_machine.add_state_callback(bridge.state_changed.emit)

    window = HPMainWindow(settings)
    tray = HPTray(window)

    bridge.state_changed.connect(window.set_state)
    bridge.transcript_ready.connect(window.set_transcript)
    bridge.response_ready.connect(window.set_response)

    runtime = VoiceRuntime(
        settings,
        state_machine,
        on_transcript=bridge.transcript_ready.emit,
        on_response=bridge.response_ready.emit,
        on_command=dispatcher.dispatch,
        llm=llm,
        conversation=conv,
    )

    tray.show()
    window.show()
    runtime.start()

    result = app.exec()
    runtime.stop()
    return result


if __name__ == "__main__":
    sys.exit(main())
'''

# ── tests/unit/test_llm_conversation.py ──────────────────────────────────
files["tests/unit/test_llm_conversation.py"] = r'''"""Unit tests for ConversationBuffer."""

from __future__ import annotations

import pytest

from app.llm.conversation import ConversationBuffer


def test_empty_buffer_has_zero_len() -> None:
    buf = ConversationBuffer()
    assert len(buf) == 0


def test_add_single_turn() -> None:
    buf = ConversationBuffer()
    buf.add("user", "hello")
    assert len(buf) == 1
    assert buf.history()[0] == {"role": "user", "text": "hello"}


def test_history_returns_copy() -> None:
    buf = ConversationBuffer()
    buf.add("user", "hi")
    h1 = buf.history()
    h1.clear()
    assert len(buf) == 1


def test_max_turns_evicts_oldest() -> None:
    buf = ConversationBuffer(max_turns=3)
    for i in range(5):
        buf.add("user", str(i))
    assert len(buf) == 3
    texts = [t["text"] for t in buf.history()]
    assert texts == ["2", "3", "4"]


def test_clear_empties_buffer() -> None:
    buf = ConversationBuffer()
    buf.add("user", "hello")
    buf.add("assistant", "hi")
    buf.clear()
    assert len(buf) == 0


def test_max_turns_must_be_positive() -> None:
    with pytest.raises(ValueError):
        ConversationBuffer(max_turns=0)


def test_multi_role_history() -> None:
    buf = ConversationBuffer()
    buf.add("user", "what time is it")
    buf.add("assistant", "I don't know")
    h = buf.history()
    assert h[0]["role"] == "user"
    assert h[1]["role"] == "assistant"
'''

# ── tests/unit/test_llm_factory.py ───────────────────────────────────────
files["tests/unit/test_llm_factory.py"] = r'''"""Unit tests for LLM provider factory."""

from __future__ import annotations

import pytest

from app.config.settings import AppSettings
from app.llm.factory import get_provider
from app.llm.stub import StubLLM


def test_stub_provider_returned_by_default() -> None:
    settings = AppSettings()
    provider = get_provider(settings)
    assert isinstance(provider, StubLLM)


def test_stub_provider_explicit() -> None:
    settings = AppSettings(llm_provider="stub")
    provider = get_provider(settings)
    assert isinstance(provider, StubLLM)


def test_unknown_provider_raises() -> None:
    settings = AppSettings(llm_provider="openai")
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_provider(settings)


def test_provider_case_insensitive() -> None:
    settings = AppSettings(llm_provider="STUB")
    provider = get_provider(settings)
    assert isinstance(provider, StubLLM)
'''

# ── tests/unit/test_assistant_machine_sprint4.py ─────────────────────────
files[
    "tests/unit/test_assistant_machine_sprint4.py"
] = r'''"""Sprint 4 additions to state machine tests: recovery methods and reset."""

from __future__ import annotations

from app.assistant.machine import AssistantStateMachine
from app.assistant.state import AssistantState
from app.config.settings import AppSettings


def _sm() -> AssistantStateMachine:
    return AssistantStateMachine(AppSettings())


def test_no_speech_from_listening_goes_idle() -> None:
    sm = _sm()
    sm.on_wake()
    assert sm.state is AssistantState.LISTENING
    sm.on_no_speech()
    assert sm.state is AssistantState.IDLE


def test_no_speech_from_processing_goes_idle() -> None:
    sm = _sm()
    sm.on_wake()
    sm.on_utterance_end("hi")
    assert sm.state is AssistantState.PROCESSING
    sm.on_no_speech()
    assert sm.state is AssistantState.IDLE


def test_error_from_processing_goes_idle() -> None:
    sm = _sm()
    sm.on_wake()
    sm.on_utterance_end("hi")
    sm.on_error()
    assert sm.state is AssistantState.IDLE


def test_error_from_speaking_goes_idle() -> None:
    sm = _sm()
    sm.on_wake()
    sm.on_utterance_end("hi")
    sm.on_response_ready()
    assert sm.state is AssistantState.SPEAKING
    sm._fire("error")
    assert sm.state is AssistantState.IDLE


def test_reset_from_any_state_goes_idle() -> None:
    sm = _sm()
    sm.on_wake()
    assert sm.state is AssistantState.LISTENING
    sm.reset()
    assert sm.state is AssistantState.IDLE


def test_reset_from_idle_is_noop() -> None:
    sm = _sm()
    received: list[AssistantState] = []
    sm.add_state_callback(received.append)
    sm.reset()
    assert sm.state is AssistantState.IDLE
    assert received == []


def test_reset_fires_callbacks() -> None:
    sm = _sm()
    sm.on_wake()
    received: list[AssistantState] = []
    sm.add_state_callback(received.append)
    sm.reset()
    assert AssistantState.IDLE in received
'''

# ── tests/unit/test_voice_interruption.py ────────────────────────────────
files[
    "tests/unit/test_voice_interruption.py"
] = r'''"""Unit tests for VoiceRuntime interruption logic."""

from __future__ import annotations

import struct
from unittest.mock import MagicMock, patch

from app.assistant.machine import AssistantStateMachine
from app.assistant.state import AssistantState
from app.config.settings import AppSettings
from app.voice.runtime import VoiceRuntime, _rms


def _make_chunk(rms_value: float, n_samples: int = 512) -> bytes:
    """Build a chunk of int16 samples that produce approximately the given RMS."""
    import math

    amplitude = int(rms_value)
    amplitude = max(0, min(32767, amplitude))
    samples = [amplitude] * n_samples
    return struct.pack(f"{n_samples}h", *samples)


def _make_runtime(settings: AppSettings | None = None) -> tuple[VoiceRuntime, AssistantStateMachine]:
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
'''

# ── Write all files ───────────────────────────────────────────────────────
for rel, content in files.items():
    path = BASE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"  wrote {rel}")

print("\nSprint 4 setup complete.")
