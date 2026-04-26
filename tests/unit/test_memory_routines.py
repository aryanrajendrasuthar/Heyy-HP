"""Unit tests for RoutineRepository."""

from __future__ import annotations

import sqlite3

import pytest

from app.memory.db import init_schema
from app.memory.routines import Routine, RoutineRepository


@pytest.fixture()
def repo() -> RoutineRepository:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return RoutineRepository(conn)


def test_save_and_find(repo: RoutineRepository) -> None:
    r = Routine("good morning", ["open chrome", "google news"])
    repo.save(r)
    found = repo.find("good morning")
    assert found is not None
    assert found.trigger_phrase == "good morning"
    assert found.commands == ["open chrome", "google news"]


def test_find_returns_none_for_missing(repo: RoutineRepository) -> None:
    assert repo.find("nonexistent phrase") is None


def test_all_enabled_returns_only_enabled(repo: RoutineRepository) -> None:
    repo.save(Routine("routine a", ["open notepad"]))
    repo.save(Routine("routine b", ["open calc"], enabled=False))
    enabled = repo.all_enabled()
    assert len(enabled) == 1
    assert enabled[0].trigger_phrase == "routine a"


def test_delete_removes_routine(repo: RoutineRepository) -> None:
    repo.save(Routine("temp routine", ["open notepad"]))
    repo.delete("temp routine")
    assert repo.find("temp routine") is None


def test_save_overwrites_existing(repo: RoutineRepository) -> None:
    repo.save(Routine("update me", ["open notepad"]))
    repo.save(Routine("update me", ["open calc", "open chrome"]))
    found = repo.find("update me")
    assert found is not None
    assert "open calc" in found.commands


def test_find_normalises_case_in_input(repo: RoutineRepository) -> None:
    repo.save(Routine("good morning", ["open chrome"]))
    found = repo.find("Good Morning")
    assert found is not None
