"""Thread-safe assistant state machine."""

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
