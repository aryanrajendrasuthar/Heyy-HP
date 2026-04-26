"""Persistent conversation history backed by SQLite."""

from __future__ import annotations

import sqlite3


class ConversationHistory:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, role: str, text: str) -> None:
        self._conn.execute(
            "INSERT INTO conversation_history (role, text) VALUES (?, ?)",
            (role, text),
        )
        self._conn.commit()

    def recent(self, n: int = 20) -> list[dict[str, str]]:
        cur = self._conn.execute(
            "SELECT role, text, timestamp FROM conversation_history ORDER BY id DESC LIMIT ?",
            (n,),
        )
        return [dict(row) for row in reversed(cur.fetchall())]

    def clear(self) -> None:
        self._conn.execute("DELETE FROM conversation_history")
        self._conn.commit()

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM conversation_history")
        return cur.fetchone()[0]
