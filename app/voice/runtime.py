"""Voice runtime — orchestrates mic, VAD, wake-word, STT, and TTS."""

from __future__ import annotations

import logging
import struct
from collections.abc import Callable

from app.assistant.machine import AssistantStateMachine
from app.assistant.state import AssistantState
from app.config.settings import AppSettings
from app.voice.audio import MicCapture
from app.voice.stt import STTService
from app.voice.tts import TTSService
from app.voice.vad import VoiceActivityDetector
from app.voice.wakeword import WakeWordListener

logger = logging.getLogger(__name__)

_INTERRUPT_RMS = 1500.0


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
        on_transcript: Callable[[str], None] | None = None,
        on_response: Callable[[str], None] | None = None,
    ) -> None:
        self._settings = settings
        self._sm = state_machine
        self._on_transcript = on_transcript
        self._on_response = on_response

        self._mic = MicCapture(settings.audio_sample_rate, settings.audio_device_index)
        self._vad = VoiceActivityDetector(
            settings.audio_sample_rate,
            settings.vad_silence_threshold,
            settings.vad_silence_duration_s,
        )
        self._wakeword = WakeWordListener(settings.wakeword_model, settings.wakeword_sensitivity)
        self._stt = STTService(settings.stt_model_size, settings.stt_device)
        self._tts = TTSService(settings.tts_rate, settings.tts_volume)

        self._mic.add_callback(self._route_chunk)
        self._wakeword.add_wake_callback(self._sm.on_wake)
        self._vad.add_utterance_callback(self._on_utterance)

    def start(self) -> None:
        self._mic.start()
        logger.info("Voice runtime started")

    def stop(self) -> None:
        self._tts.stop()
        self._mic.stop()
        logger.info("Voice runtime stopped")

    def speak(self, text: str) -> None:
        self._sm.on_response_ready()
        self._tts.speak_async(text, on_complete=self._sm.on_speaking_done)
        if self._on_response:
            self._on_response(text)

    def _route_chunk(self, data: bytes) -> None:
        state = self._sm.state
        if state in (AssistantState.IDLE, AssistantState.WAKE_DETECTED):
            self._wakeword.process_chunk(data)
        elif state in (AssistantState.LISTENING, AssistantState.FOLLOW_UP):
            self._vad.process_chunk(data)
        elif state == AssistantState.SPEAKING:
            if _rms(data) > _INTERRUPT_RMS:
                self._sm.on_interrupted()
                self._tts.stop()
                self._vad.reset()

    def _on_utterance(self, audio: bytes) -> None:
        result = self._stt.transcribe(audio, self._settings.audio_sample_rate)
        if result.text:
            if self._on_transcript:
                self._on_transcript(result.text)
            self._sm.on_utterance_end(result.text)
