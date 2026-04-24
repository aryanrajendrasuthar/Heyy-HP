"""Follow-up conversation window timer."""

from __future__ import annotations

import threading
from collections.abc import Callable


class FollowUpTimer:
    def __init__(self, timeout_s: int, on_expire: Callable[[], None]) -> None:
        self._timeout_s = timeout_s
        self._on_expire = on_expire
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._timeout_s, self._fire)
            self._timer.daemon = True
            self._timer.start()

    def cancel(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

    @property
    def running(self) -> bool:
        with self._lock:
            return self._timer is not None and self._timer.is_alive()

    def _fire(self) -> None:
        with self._lock:
            self._timer = None
        self._on_expire()
