"""Unit tests for AssistantStateMachine."""

from __future__ import annotations

import threading

import pytest

from app.assistant.machine import AssistantStateMachine
from app.assistant.state import AssistantState
from app.config.settings import AppSettings


@pytest.fixture()
def sm() -> AssistantStateMachine:
    return AssistantStateMachine(AppSettings())


def test_initial_state_is_idle(sm: AssistantStateMachine) -> None:
    assert sm.state is AssistantState.IDLE


def test_wake_transitions_to_listening(sm: AssistantStateMachine) -> None:
    sm.on_wake()
    assert sm.state is AssistantState.LISTENING


def test_full_cycle(sm: AssistantStateMachine) -> None:
    sm.on_wake()
    assert sm.state is AssistantState.LISTENING
    sm.on_utterance_end("hello")
    assert sm.state is AssistantState.PROCESSING
    sm.on_response_ready()
    assert sm.state is AssistantState.SPEAKING
    sm.on_speaking_done()
    sm._timer.cancel()
    assert sm.state is AssistantState.FOLLOW_UP


def test_interrupted_returns_to_listening(sm: AssistantStateMachine) -> None:
    sm.on_wake()
    sm.on_utterance_end("test")
    sm.on_response_ready()
    sm.on_interrupted()
    assert sm.state is AssistantState.LISTENING


def test_invalid_event_ignored(sm: AssistantStateMachine) -> None:
    sm.on_utterance_end("noop")
    assert sm.state is AssistantState.IDLE


def test_timer_expiry_returns_to_idle(sm: AssistantStateMachine) -> None:
    sm.on_wake()
    sm.on_utterance_end("hello")
    sm.on_response_ready()
    sm._timer.cancel()
    sm._state = AssistantState.FOLLOW_UP
    sm._on_timer_expired()
    assert sm.state is AssistantState.IDLE


def test_callbacks_called_on_transition(sm: AssistantStateMachine) -> None:
    received: list[AssistantState] = []
    sm.add_state_callback(received.append)
    sm.on_wake()
    assert AssistantState.LISTENING in received


def test_concurrent_transitions_safe() -> None:
    machine = AssistantStateMachine(AppSettings())
    errors: list[Exception] = []

    def worker() -> None:
        try:
            for _ in range(50):
                machine.on_wake()
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
