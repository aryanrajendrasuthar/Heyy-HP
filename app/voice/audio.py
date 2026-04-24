"""Microphone capture — background thread streaming 16-bit PCM chunks."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)

AudioCallback = Callable[[bytes], None]

_CHUNK = 1024


class MicCapture:
    def __init__(self, sample_rate: int, device_index: int | None = None) -> None:
        self._sample_rate = sample_rate
        self._device_index = device_index
        self._callbacks: list[AudioCallback] = []
        self._stream = None
        self._pa = None
        self._thread: threading.Thread | None = None
        self._running = False

    def add_callback(self, cb: AudioCallback) -> None:
        self._callbacks.append(cb)

    def start(self) -> None:
        try:
            import pyaudio  # noqa: PLC0415
        except ImportError:
            logger.warning("pyaudio not available — mic capture disabled")
            return

        self._pa = pyaudio.PyAudio()
        try:
            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self._sample_rate,
                input=True,
                input_device_index=self._device_index,
                frames_per_buffer=_CHUNK,
            )
        except Exception:
            logger.exception("Failed to open microphone stream")
            self._pa.terminate()
            self._pa = None
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Mic capture started (rate=%d)", self._sample_rate)

    def stop(self) -> None:
        self._running = False
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._pa:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _loop(self) -> None:
        while self._running and self._stream:
            try:
                data = self._stream.read(_CHUNK, exception_on_overflow=False)
            except Exception:
                logger.exception("Mic read error")
                break
            for cb in self._callbacks:
                try:
                    cb(data)
                except Exception:
                    logger.exception("Audio callback raised")
