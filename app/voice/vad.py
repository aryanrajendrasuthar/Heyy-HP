"""Energy-based voice activity detection (no external dependencies)."""

from __future__ import annotations

import logging
import struct
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)

UtteranceCallback = Callable[[bytes], None]


def _rms(data: bytes) -> float:
    n = len(data) // 2
    if n == 0:
        return 0.0
    samples = struct.unpack_from(f"{n}h", data)
    return (sum(s * s for s in samples) / n) ** 0.5


class VoiceActivityDetector:
    def __init__(
        self,
        sample_rate: int,
        silence_threshold: float,
        silence_duration_s: float,
    ) -> None:
        self._threshold = silence_threshold
        self._callbacks: list[UtteranceCallback] = []
        self._buffer: list[bytes] = []
        self._active = False
        self._silence_frames = 0
        self._lock = threading.Lock()
        frames_per_second = sample_rate / 1024
        self._silence_frame_limit = int(frames_per_second * silence_duration_s)

    def add_utterance_callback(self, cb: UtteranceCallback) -> None:
        self._callbacks.append(cb)

    def reset(self) -> None:
        with self._lock:
            self._buffer.clear()
            self._active = False
            self._silence_frames = 0

    def process_chunk(self, data: bytes) -> None:
        level = _rms(data)
        audio: bytes | None = None
        with self._lock:
            if level >= self._threshold:
                self._active = True
                self._silence_frames = 0
                self._buffer.append(data)
            elif self._active:
                self._buffer.append(data)
                self._silence_frames += 1
                if self._silence_frames >= self._silence_frame_limit:
                    audio = b"".join(self._buffer)
                    self._buffer.clear()
                    self._active = False
                    self._silence_frames = 0

        if audio is not None:
            for cb in self._callbacks:
                try:
                    cb(audio)
                except Exception:
                    logger.exception("VAD utterance callback raised")
