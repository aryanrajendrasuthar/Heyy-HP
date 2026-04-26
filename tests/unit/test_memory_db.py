"""Unit tests for database initialisation."""

from __future__ import annotations

import sqlite3

from app.memory.db import init_schema


def _mem_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def test_schema_creates_conversation_history_table() -> None:
    conn = _mem_conn()
    init_schema(conn)
    tables = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert "conversation_history" in tables


def test_schema_creates_routines_table() -> None:
    conn = _mem_conn()
    init_schema(conn)
    tables = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert "routines" in tables


def test_schema_is_idempotent() -> None:
    conn = _mem_conn()
    init_schema(conn)
    init_schema(conn)  # should not raise
    tables = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert len([t for t in tables if t in {"conversation_history", "routines"}]) == 2
