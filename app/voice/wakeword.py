"""Wake-word detection — wraps openWakeWord with graceful degradation."""

from __future__ import annotations

import logging
import struct
from collections.abc import Callable

logger = logging.getLogger(__name__)

WakeCallback = Callable[[], None]


class WakeWordListener:
    def __init__(self, model_name: str, sensitivity: float) -> None:
        self._model_name = model_name
        self._sensitivity = sensitivity
        self._callbacks: list[WakeCallback] = []
        self._model = None
        self._available = False
        self._init_model()

    def _init_model(self) -> None:
        try:
            from openwakeword.model import Model  # noqa: PLC0415

            self._model = Model(wakeword_models=[self._model_name])
            self._available = True
            logger.info("Wake-word model loaded: %s", self._model_name)
        except Exception:
            logger.warning(
                "openWakeWord not available or model '%s' not found — wake-word disabled",
                self._model_name,
            )

    def add_wake_callback(self, cb: WakeCallback) -> None:
        self._callbacks.append(cb)

    def process_chunk(self, data: bytes) -> None:
        if not self._available or self._model is None:
            return
        try:
            n = len(data) // 2
            samples = list(struct.unpack_from(f"{n}h", data))
            prediction = self._model.predict(samples)
            for score in prediction.values():
                if score >= self._sensitivity:
                    for cb in self._callbacks:
                        try:
                            cb()
                        except Exception:
                            logger.exception("Wake callback raised")
                    break
        except Exception:
            logger.exception("Wake-word processing error")
