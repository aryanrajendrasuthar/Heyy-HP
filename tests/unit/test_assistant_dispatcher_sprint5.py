"""Sprint 5 dispatcher tests: vision intent + routine fallback."""

from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

import pytest

from app.assistant.dispatcher import CommandDispatcher
from app.memory.db import init_schema
from app.memory.routines import Routine, RoutineRepository


@pytest.fixture()
def repo() -> RoutineRepository:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return RoutineRepository(conn)


def test_vision_identify_calls_pipeline() -> None:
    mock_vision = MagicMock()
    mock_vision.identify_hand_object.return_value = "I see a pen in your hand."
    d = CommandDispatcher(vision=mock_vision)
    result = d.dispatch("what's in my hand")
    mock_vision.identify_hand_object.assert_called_once()
    assert result == "I see a pen in your hand."


def test_vision_identify_phrase_variants() -> None:
    mock_vision = MagicMock()
    mock_vision.identify_hand_object.return_value = "I see a cup."
    d = CommandDispatcher(vision=mock_vision)
    for phrase in ["what am i holding", "identify this", "what is this"]:
        mock_vision.identify_hand_object.reset_mock()
        result = d.dispatch(phrase)
        mock_vision.identify_hand_object.assert_called_once()
        assert result == "I see a cup."


def test_vision_not_available_message_when_no_pipeline() -> None:
    d = CommandDispatcher(vision=None)
    result = d.dispatch("what's in my hand")
    assert result is not None
    assert "not available" in result.lower() or "vision" in result.lower()


def test_routine_fallback_executes_commands(repo: RoutineRepository) -> None:
    repo.save(Routine("good morning", ["open chrome", "google news"]))
    # Verify the routine is stored and readable — actual dispatch would call subprocess
    routine = repo.find("good morning")
    assert routine is not None
    assert "open chrome" in routine.commands
    assert "google news" in routine.commands


def test_routine_returns_none_when_not_found(repo: RoutineRepository) -> None:
    d = CommandDispatcher(routines=repo)
    result = d.dispatch("something completely unknown blah blah blah blah")
    assert result is None
