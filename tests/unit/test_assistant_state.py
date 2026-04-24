"""Unit tests for AssistantState."""

from __future__ import annotations

from app.assistant.state import AssistantState


def test_all_states_present():
    names = {s.name for s in AssistantState}
    assert names == {"IDLE", "WAKE_DETECTED", "LISTENING", "PROCESSING", "SPEAKING", "FOLLOW_UP"}


def test_states_are_unique():
    values = [s.value for s in AssistantState]
    assert len(values) == len(set(values))


def test_states_accessible_by_name():
    assert AssistantState["IDLE"] is AssistantState.IDLE
    assert AssistantState["SPEAKING"] is AssistantState.SPEAKING


def test_states_iterable():
    assert len(list(AssistantState)) == 6
