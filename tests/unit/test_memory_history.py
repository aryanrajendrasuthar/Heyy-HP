"""Unit tests for ConversationHistory repository."""

from __future__ import annotations

import sqlite3

import pytest

from app.memory.db import init_schema
from app.memory.history import ConversationHistory


@pytest.fixture()
def history() -> ConversationHistory:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return ConversationHistory(conn)


def test_save_and_count(history: ConversationHistory) -> None:
    history.save("user", "hello")
    assert history.count() == 1


def test_recent_returns_ordered_turns(history: ConversationHistory) -> None:
    history.save("user", "first")
    history.save("assistant", "reply")
    turns = history.recent(n=10)
    assert turns[0]["text"] == "first"
    assert turns[1]["text"] == "reply"


def test_recent_respects_limit(history: ConversationHistory) -> None:
    for i in range(10):
        history.save("user", str(i))
    turns = history.recent(n=3)
    assert len(turns) == 3


def test_clear_removes_all(history: ConversationHistory) -> None:
    history.save("user", "hello")
    history.clear()
    assert history.count() == 0


def test_recent_returns_correct_roles(history: ConversationHistory) -> None:
    history.save("user", "ping")
    history.save("assistant", "pong")
    turns = history.recent()
    assert turns[0]["role"] == "user"
    assert turns[1]["role"] == "assistant"
