"""Reminder repository — schedules and fires time-based voice reminders."""

from __future__ import annotations

import re
import sqlite3
import threading
from collections.abc import Callable
from datetime import datetime, timedelta


class ReminderRepository:
    def __init__(
        self,
        conn: sqlite3.Connection,
        on_fire: Callable[[str], None],
    ) -> None:
        self._conn = conn
        self._on_fire = on_fire
        self._timers: list[threading.Timer] = []

    def schedule(self, content: str, remind_at: datetime) -> bool:
        now = datetime.now()
        if remind_at <= now:
            return False
        delay = (remind_at - now).total_seconds()
        self._conn.execute(
            "INSERT INTO reminders (content, remind_at) VALUES (?, ?)",
            (content, remind_at.isoformat()),
        )
        self._conn.commit()
        t = threading.Timer(delay, self._fire, args=[content])
        t.daemon = True
        t.start()
        self._timers.append(t)
        return True

    def _fire(self, content: str) -> None:
        self._on_fire(f"Reminder: {content}")
        self._conn.execute(
            "UPDATE reminders SET fired=1 WHERE content=? AND fired=0", (content,)
        )
        self._conn.commit()

    def list_upcoming(self) -> list[tuple[str, str]]:
        rows = self._conn.execute(
            "SELECT content, remind_at FROM reminders WHERE fired=0 ORDER BY remind_at LIMIT 5"
        ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def parse_reminder(self, text: str) -> tuple[str, datetime] | None:
        """Parse 'X in N minutes/hours' or 'X at HH:MM [am/pm]'."""
        # "in N minutes/hours"
        m = re.search(r"\bin\s+(\d+)\s+(minute|hour)s?\b", text, re.IGNORECASE)
        if m:
            amount = int(m.group(1))
            unit = m.group(2).lower()
            content = re.sub(
                r"\s+in\s+\d+\s+(?:minute|hour)s?.*$", "", text, flags=re.IGNORECASE
            ).strip()
            delta = timedelta(minutes=amount) if unit == "minute" else timedelta(hours=amount)
            return content, datetime.now() + delta

        # "at HH:MM [am/pm]"
        m = re.search(r"\bat\s+(\d{1,2}):(\d{2})\s*(am|pm)?\b", text, re.IGNORECASE)
        if m:
            hour, minute = int(m.group(1)), int(m.group(2))
            ampm = m.group(3)
            if ampm:
                if ampm.lower() == "pm" and hour != 12:
                    hour += 12
                elif ampm.lower() == "am" and hour == 12:
                    hour = 0
            content = re.sub(
                r"\s+at\s+\d{1,2}:\d{2}.*$", "", text, flags=re.IGNORECASE
            ).strip()
            target = datetime.now().replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            if target <= datetime.now():
                target += timedelta(days=1)
            return content, target

        return None
