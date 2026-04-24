"""Text-to-speech — wraps pyttsx3 / Windows SAPI with graceful degradation."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)


class TTSService:
    def __init__(self, rate: int = 175, volume: float = 1.0) -> None:
        self._rate = rate
        self._volume = volume
        self._engine = None
        self._available = False
        self._lock = threading.Lock()
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pyttsx3  # noqa: PLC0415

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self._rate)
            self._engine.setProperty("volume", self._volume)
            self._available = True
            logger.info("TTS engine initialised (rate=%d)", self._rate)
        except Exception:
            logger.warning("pyttsx3 not available — TTS disabled")

    def speak(self, text: str) -> None:
        if not self._available or self._engine is None:
            logger.debug("TTS say (unavailable): %s", text)
            return
        with self._lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception:
                logger.exception("TTS speak error")

    def speak_async(self, text: str, on_complete: Callable[[], None] | None = None) -> None:
        def _run() -> None:
            self.speak(text)
            if on_complete:
                try:
                    on_complete()
                except Exception:
                    logger.exception("TTS on_complete callback raised")

        threading.Thread(target=_run, daemon=True).start()

    def stop(self) -> None:
        if not self._available or self._engine is None:
            return
        try:
            self._engine.stop()
        except Exception:
            logger.exception("TTS stop error")
