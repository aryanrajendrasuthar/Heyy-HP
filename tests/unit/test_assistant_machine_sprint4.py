"""Sprint 4 additions to state machine tests: recovery methods and reset."""

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
