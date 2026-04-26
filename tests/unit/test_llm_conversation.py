"""Unit tests for ConversationBuffer."""

from __future__ import annotations

import pytest

from app.llm.conversation import ConversationBuffer


def test_empty_buffer_has_zero_len() -> None:
    buf = ConversationBuffer()
    assert len(buf) == 0


def test_add_single_turn() -> None:
    buf = ConversationBuffer()
    buf.add("user", "hello")
    assert len(buf) == 1
    assert buf.history()[0] == {"role": "user", "text": "hello"}


def test_history_returns_copy() -> None:
    buf = ConversationBuffer()
    buf.add("user", "hi")
    h1 = buf.history()
    h1.clear()
    assert len(buf) == 1


def test_max_turns_evicts_oldest() -> None:
    buf = ConversationBuffer(max_turns=3)
    for i in range(5):
        buf.add("user", str(i))
    assert len(buf) == 3
    texts = [t["text"] for t in buf.history()]
    assert texts == ["2", "3", "4"]


def test_clear_empties_buffer() -> None:
    buf = ConversationBuffer()
    buf.add("user", "hello")
    buf.add("assistant", "hi")
    buf.clear()
    assert len(buf) == 0


def test_max_turns_must_be_positive() -> None:
    with pytest.raises(ValueError):
        ConversationBuffer(max_turns=0)


def test_multi_role_history() -> None:
    buf = ConversationBuffer()
    buf.add("user", "what time is it")
    buf.add("assistant", "I don't know")
    h = buf.history()
    assert h[0]["role"] == "user"
    assert h[1]["role"] == "assistant"
