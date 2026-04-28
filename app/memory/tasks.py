"""Task and goal repository — persistent to-do list via SQLite."""

from __future__ import annotations

import sqlite3


class TaskRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, task: str, category: str = "task") -> None:
        self._conn.execute(
            "INSERT INTO todos (task, category) VALUES (?, ?)", (task, category)
        )
        self._conn.commit()

    def list_open(self, category: str = "task") -> list[str]:
        rows = self._conn.execute(
            "SELECT task FROM todos WHERE done=0 AND category=? ORDER BY id DESC LIMIT 10",
            (category,),
        ).fetchall()
        return [r[0] for r in rows]

    def complete(self, partial: str) -> bool:
        row = self._conn.execute(
            "SELECT id FROM todos WHERE done=0 AND task LIKE ? LIMIT 1",
            (f"%{partial}%",),
        ).fetchone()
        if row:
            self._conn.execute("UPDATE todos SET done=1 WHERE id=?", (row[0],))
            self._conn.commit()
            return True
        return False
