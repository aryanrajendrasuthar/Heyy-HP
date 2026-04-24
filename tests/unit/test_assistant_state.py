"""Unit tests for AssistantState enum."""

from __future__ import annotations

from app.assistant.state import AssistantState


def test_all_states_present():
    names = {s.name for s in AssistantState}
    assert names == {"IDLE", "WAKE_DETECTED", "LISTENING", "PROCESSING", "SPEAKING", "FOLLOW_UP"}


def test_state_values_are_unique():
    values = [s.value for s in AssistantState]
    assert len(values) == len(set(values))


def test_idle_is_accessible():
    assert AssistantState.IDLE is not None


def test_all_states_iterable():
    assert len(list(AssistantState)) == 6
