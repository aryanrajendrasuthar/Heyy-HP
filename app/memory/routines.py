"""Routine storage: user-defined trigger → command sequences."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass


@dataclass
class Routine:
    trigger_phrase: str
    commands: list[str]
    enabled: bool = True


class RoutineRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def save(self, routine: Routine) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO routines (trigger_phrase, commands, enabled) VALUES (?, ?, ?)",
            (routine.trigger_phrase, json.dumps(routine.commands), int(routine.enabled)),
        )
        self._conn.commit()

    def find(self, trigger_phrase: str) -> Routine | None:
        cur = self._conn.execute(
            "SELECT trigger_phrase, commands, enabled FROM routines "
            "WHERE trigger_phrase = ? AND enabled = 1",
            (trigger_phrase.lower().strip(),),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return Routine(row["trigger_phrase"], json.loads(row["commands"]), bool(row["enabled"]))

    def all_enabled(self) -> list[Routine]:
        cur = self._conn.execute(
            "SELECT trigger_phrase, commands, enabled FROM routines WHERE enabled = 1"
        )
        return [
            Routine(r["trigger_phrase"], json.loads(r["commands"]), True) for r in cur.fetchall()
        ]

    def delete(self, trigger_phrase: str) -> None:
        self._conn.execute("DELETE FROM routines WHERE trigger_phrase = ?", (trigger_phrase,))
        self._conn.commit()
