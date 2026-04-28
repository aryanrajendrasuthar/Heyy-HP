"""Memory repository — stores user-instructed facts ("remember that …")."""

from __future__ import annotations

import sqlite3


class MemoryRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def remember(self, content: str) -> None:
        self._conn.execute("INSERT INTO memories (content) VALUES (?)", (content,))
        self._conn.commit()

    def list_recent(self, limit: int = 10) -> list[str]:
        rows = self._conn.execute(
            "SELECT content FROM memories ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [r[0] for r in rows]
