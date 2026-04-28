"""iCloud Reminders bidirectional sync via CalDAV.

Setup:
  1. Enable iCloud Reminders on your iPhone.
  2. Go to https://appleid.apple.com → Sign-In and Security → App-Specific Passwords.
  3. Generate a password (name it "HP Assistant").
  4. Add to .env:
       HP_ICLOUD_USERNAME=you@icloud.com
       HP_ICLOUD_PASSWORD=xxxx-xxxx-xxxx-xxxx
"""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


def _get_summary(todo: object) -> str | None:
    """Extract SUMMARY from a caldav Todo, handling both caldav 3.x and older APIs."""
    # caldav >= 1.0: icalendar_component
    try:
        val = todo.icalendar_component.get("SUMMARY")  # type: ignore[attr-defined]
        if val:
            return str(val)
    except AttributeError:
        pass
    # Older caldav: vobject_instance
    try:
        return str(todo.vobject_instance.vtodo.summary.value)  # type: ignore[attr-defined]
    except Exception:
        return None


class ICloudReminderSync:
    """Read/write iCloud Reminders over CalDAV — thread-safe, background-polling."""

    ICLOUD_URL = "https://caldav.icloud.com"
    POLL_INTERVAL_S = 60

    def __init__(
        self,
        username: str,
        password: str,
        list_name: str = "Reminders",
    ) -> None:
        self._username = username.strip()
        self._password = password.strip()
        self._list_name = list_name
        self._calendar: object | None = None
        self._cached: list[str] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self.connected = False

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> bool:
        """Connect to iCloud and launch background poll. Returns True if connected."""
        if not self._username or not self._password:
            return False
        if not self._connect():
            return False
        self._refresh_cache()
        t = threading.Thread(target=self._poll_loop, daemon=True, name="icloud-poll")
        t.start()
        return True

    def stop(self) -> None:
        self._stop.set()

    # ── Internal connection ────────────────────────────────────────────────

    def _connect(self) -> bool:
        try:
            import caldav  # noqa: PLC0415 — optional dependency

            client = caldav.DAVClient(
                url=self.ICLOUD_URL,
                username=self._username,
                password=self._password,
            )
            principal = client.principal()
            calendars = principal.calendars()

            # 1. Look for the named list (e.g. "Reminders")
            for cal in calendars:
                name = self._cal_name(cal)
                if name.lower() == self._list_name.lower():
                    self._calendar = cal
                    self.connected = True
                    logger.info("iCloud: connected to '%s'", name)
                    return True

            # 2. Fallback — first calendar that exposes todos
            for cal in calendars:
                try:
                    cal.todos()  # type: ignore[attr-defined]
                    self._calendar = cal
                    self.connected = True
                    name = self._cal_name(cal)
                    logger.info("iCloud: using fallback calendar '%s'", name)
                    return True
                except Exception:
                    continue

            logger.warning("iCloud: no VTODO-capable calendar found")
        except ImportError:
            logger.warning("caldav not installed — iCloud sync disabled")
        except Exception:
            logger.exception("iCloud CalDAV connection failed")
        return False

    @staticmethod
    def _cal_name(cal: object) -> str:
        """Best-effort display-name extraction for a caldav Calendar."""
        try:
            n = getattr(cal, "name", None)
            if n:
                return str(n)
        except Exception:
            pass
        try:
            import caldav.elements.dav as _dav  # noqa: PLC0415
            props = cal.get_properties([_dav.DisplayName()])  # type: ignore[attr-defined]
            return props.get("{DAV:}displayname", "") or ""
        except Exception:
            return ""

    # ── Background polling ────────────────────────────────────────────────

    def _poll_loop(self) -> None:
        while not self._stop.wait(timeout=self.POLL_INTERVAL_S):
            self._refresh_cache()

    def _refresh_cache(self) -> None:
        if not self.connected or self._calendar is None:
            return
        try:
            todos = self._calendar.todos()  # type: ignore[attr-defined]
            titles: list[str] = []
            for todo in todos:
                t = _get_summary(todo)
                if t:
                    titles.append(t)
            with self._lock:
                self._cached = titles
            logger.debug("iCloud cache: %d items", len(titles))
        except Exception:
            logger.exception("iCloud cache refresh failed")

    # ── Public read ───────────────────────────────────────────────────────

    def get_todos(self) -> list[str]:
        """Return cached pending reminder titles (no network call)."""
        with self._lock:
            return list(self._cached)

    # ── Public write (network — call from worker thread) ──────────────────

    def add_reminder(self, title: str) -> bool:
        if not self.connected or self._calendar is None:
            return False
        try:
            uid = str(uuid.uuid4()).upper()
            now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            vcal = (
                "BEGIN:VCALENDAR\r\n"
                "VERSION:2.0\r\n"
                "PRODID:-//HP Assistant//EN\r\n"
                "BEGIN:VTODO\r\n"
                f"UID:{uid}\r\n"
                f"DTSTAMP:{now}\r\n"
                f"CREATED:{now}\r\n"
                f"LAST-MODIFIED:{now}\r\n"
                f"SUMMARY:{title}\r\n"
                "STATUS:NEEDS-ACTION\r\n"
                "END:VTODO\r\n"
                "END:VCALENDAR\r\n"
            )
            self._calendar.add_todo(vcal)  # type: ignore[attr-defined]
            with self._lock:
                if title not in self._cached:
                    self._cached.append(title)
            logger.info("iCloud: added '%s'", title)
            return True
        except Exception:
            logger.exception("iCloud add_reminder failed: %s", title)
            return False

    def complete_reminder(self, partial: str) -> str | None:
        """Complete first matching todo. Returns matched title or None."""
        if not self.connected or self._calendar is None:
            return None
        try:
            todos = self._calendar.todos()  # type: ignore[attr-defined]
            for todo in todos:
                title = _get_summary(todo)
                if title and partial.lower() in title.lower():
                    todo.complete()  # type: ignore[attr-defined]
                    with self._lock:
                        self._cached = [t for t in self._cached if t != title]
                    logger.info("iCloud: completed '%s'", title)
                    return title
        except Exception:
            logger.exception("iCloud complete_reminder failed: %s", partial)
        return None
