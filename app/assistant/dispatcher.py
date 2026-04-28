"""Route transcribed commands to the correct action handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.actions.browser import BrowserRouter
from app.actions.files import FileActions
from app.actions.launcher import AppLauncher

if TYPE_CHECKING:
    from app.memory.memories import MemoryRepository
    from app.memory.reminders import ReminderRepository
    from app.memory.tasks import TaskRepository

# Patterns ordered specific-to-general.
# Vision and no-argument intents use no capture group (m.lastindex is None).
_INTENTS: list[tuple[str, re.Pattern[str]]] = [
    # ── High-priority control commands ────────────────────────────────────
    ("go_idle", re.compile(
        r"shut\s+up|be\s+quiet|stop(?:\s+talking)?|silence",
        re.IGNORECASE,
    )),
    ("quit_app", re.compile(
        r"bye(?:\s+bye)?|goodbye|good\s+night|pew\s+pew|see\s+you(?:\s+later)?|quit\s+hp|exit\s+hp",
        re.IGNORECASE,
    )),
    # ── Memory & tasks ─────────────────────────────────────────────────────
    ("remember", re.compile(
        r"remember\s+(?:that\s+|this[:\s]+)?(.+)",
        re.IGNORECASE,
    )),
    ("remind_me", re.compile(
        r"remind\s+me\s+(?:to\s+)?(.+)",
        re.IGNORECASE,
    )),
    ("add_goal", re.compile(
        r"(?:add|set)\s+(.+?)\s+as\s+(?:a\s+|my\s+)?goal",
        re.IGNORECASE,
    )),
    ("add_task", re.compile(
        r"(?:add|create|put)\s+(.+?)\s+(?:to|in(?:to)?)\s+(?:my\s+)?(?:tasks?|to.?do(?:\s+list)?)",
        re.IGNORECASE,
    )),
    ("complete_task", re.compile(
        r"(?:complete|done|finish|mark(?:\s+as)?\s+done)\s+(.+?)(?:\s+task)?",
        re.IGNORECASE,
    )),
    ("show_tasks", re.compile(
        r"(?:show|what(?:\s+are)?(?:\s+my)?|list)\s+(?:my\s+)?(?:tasks?|to.?do(?:\s+list)?)",
        re.IGNORECASE,
    )),
    ("show_goals", re.compile(
        r"(?:show|what(?:\s+are)?(?:\s+my)?|list)\s+(?:my\s+)?goals?",
        re.IGNORECASE,
    )),
    ("show_memories", re.compile(
        r"what(?:\s+do)?(?:\s+you)?\s+remember|show\s+(?:my\s+)?memories",
        re.IGNORECASE,
    )),
    # ─────────────────────────────────────────────────────────────────────
    (
        "vision_identify",
        re.compile(
            r"(?:"
            r"what(?:'s|\s+is)\s+in\s+my\s+hand"
            r"|what\s+am\s+i\s+holding"
            r"|identify\s+this"
            r"|what\s+is\s+this"
            r"|look\s+at\s+(?:my\s+)?hand"
            r"|scan\s+(?:my\s+)?hand"
            r")",
            re.IGNORECASE,
        ),
    ),
    ("open_folder", re.compile(r"open\s+(?:folder|directory)\s+(.+)", re.IGNORECASE)),
    # Bare domain / full URL — must come before open_file so "github.com" isn't treated as a file
    ("open_url", re.compile(
        r"(?:open|go\s+to)\s+((?:https?://\S+|(?:[a-zA-Z0-9-]+\.)+(?:com|org|net|io|gov|edu|co|uk|dev|app|ai|me|in|ca|au|de|fr|jp|tv|ly)(?:/\S*)?))",
        re.IGNORECASE,
    )),
    ("open_file", re.compile(r"open\s+(?:file\s+)?([^\s].+\.\w+)", re.IGNORECASE)),
    # "search X on youtube" / "play X on youtube" — must come before the generic google pattern
    ("youtube", re.compile(r"(?:search(?:\s+for)?)\s+(.+?)\s+on\s+(?:youtube|yt)", re.IGNORECASE)),
    ("youtube", re.compile(r"play\s+(.+?)\s+on\s+(?:youtube|yt)", re.IGNORECASE)),
    ("google", re.compile(r"(?:google|search(?:\s+for)?)\s+(.+)", re.IGNORECASE)),
    ("youtube", re.compile(r"(?:youtube|play(?:\s+on\s+youtube)?)\s+(.+)", re.IGNORECASE)),
    # ── Volume — precise percentage control ───────────────────────────────
    ("volume_set",      re.compile(r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)\s*(?:percent|%)?",           re.IGNORECASE)),
    ("volume_to",       re.compile(r"volume\s+(?:up|down)\s+to\s+(\d+)\s*(?:percent|%)?",             re.IGNORECASE)),
    ("volume_up_pct",   re.compile(r"volume\s+up\s+by\s+(\d+)\s*(?:percent|%)?",                      re.IGNORECASE)),
    ("volume_down_pct", re.compile(r"volume\s+down\s+by\s+(\d+)\s*(?:percent|%)?",                    re.IGNORECASE)),
    ("volume_max",      re.compile(r"(?:full|max(?:imum)?)\s+volume|volume\s+(?:full|max(?:imum)?|100(?:\s*(?:percent|%))?)", re.IGNORECASE)),
    ("volume_low",      re.compile(r"(?:low|min(?:imum)?|quiet)\s+volume|volume\s+(?:low|min(?:imum)?|quiet)",               re.IGNORECASE)),
    ("volume_mid",      re.compile(r"(?:medium|mid(?:dle)?|half)\s+volume|volume\s+(?:medium|mid(?:dle)?|half)",             re.IGNORECASE)),
    # ── Brightness — precise percentage control ────────────────────────────
    ("brightness_set",      re.compile(r"(?:set\s+)?brightness\s+(?:to\s+)?(\d+)\s*(?:percent|%)?",       re.IGNORECASE)),
    ("brightness_to",       re.compile(r"brightness\s+(?:up|down)\s+to\s+(\d+)\s*(?:percent|%)?",         re.IGNORECASE)),
    ("brightness_up_pct",   re.compile(r"brightness\s+up\s+by\s+(\d+)\s*(?:percent|%)?",                  re.IGNORECASE)),
    ("brightness_down_pct", re.compile(r"brightness\s+down\s+by\s+(\d+)\s*(?:percent|%)?",                re.IGNORECASE)),
    ("brightness_max",      re.compile(r"(?:full|max(?:imum)?)\s+brightness|brightness\s+(?:full|max(?:imum)?|100)", re.IGNORECASE)),
    ("brightness_low",      re.compile(r"(?:low|dim(?:med)?|min(?:imum)?)\s+brightness|brightness\s+(?:low|dim(?:med)?|min(?:imum)?)", re.IGNORECASE)),
    ("brightness_mid",      re.compile(r"(?:medium|mid(?:dle)?|half)\s+brightness|brightness\s+(?:medium|mid(?:dle)?|half)", re.IGNORECASE)),
    # ─────────────────────────────────────────────────────────────────────
    ("close_app", re.compile(r"(?:close|quit|kill|exit)\s+(.+)", re.IGNORECASE)),
    ("launch",    re.compile(r"(?:open|launch|start|run)\s+(.+)",  re.IGNORECASE)),
    ("system", re.compile(
        r"(shutdown(?: now)?|shut down(?: now)?|restart(?: now)?|reboot"
        r"|cancel shutdown|sleep|hibernate|lock(?: screen)?"
        r"|sign out|log out|mute|unmute|volume up|volume down"
        r"|(?:empty )?recycle bin|(?:take\s+(?:a\s+)?)?screen\s*shot)",
        re.IGNORECASE,
    )),
]


class CommandDispatcher:
    def __init__(
        self,
        vision: Any | None = None,
        routines: Any | None = None,
        on_idle: Any | None = None,
        on_quit: Any | None = None,
        tasks: TaskRepository | None = None,
        memories: MemoryRepository | None = None,
        reminders: ReminderRepository | None = None,
    ) -> None:
        self._launcher = AppLauncher()
        self._browser = BrowserRouter()
        self._files = FileActions()
        self._vision = vision
        self._routines = routines
        self._on_idle = on_idle
        self._on_quit = on_quit
        self._tasks = tasks
        self._memories = memories
        self._reminders = reminders

    # Conversational filler stripped before pattern matching
    _FILLER = re.compile(
        r"^(?:(?:can|could|would|will)\s+you\s+|please\s+|hey\s+(?:hp|jarvis)[,\s]*|(?:hp|jarvis)[,\s]+)",
        re.IGNORECASE,
    )

    def dispatch(self, text: str) -> str | None:
        cleaned = self._FILLER.sub("", text.strip()).rstrip("?. ").strip()

        # 1. Check built-in intents
        for intent, pattern in _INTENTS:
            m = pattern.fullmatch(cleaned)
            if m:
                arg = m.group(1).strip() if m.lastindex else ""
                return self._handle(intent, arg)

        # 2. Check user-defined routines
        if self._routines is not None:
            routine = self._routines.find(cleaned.lower())
            if routine is not None:
                return self._run_routine(routine)

        return None

    def _handle(self, intent: str, arg: str) -> str | None:  # noqa: PLR0912
        if intent == "go_idle":
            if self._on_idle:
                self._on_idle()
            return ""  # empty → no TTS, state already reset to IDLE

        if intent == "quit_app":
            if self._on_quit:
                import threading
                threading.Timer(3.0, self._on_quit).start()
            return "Goodbye! See you later."

        # ── Memory / task / reminder ───────────────────────────────────────
        if intent == "remember":
            if self._memories is not None:
                self._memories.remember(arg)
                return f"Got it, I'll remember that {arg}"
            return "Memory storage is not available."

        if intent == "remind_me":
            if self._reminders is not None:
                parsed = self._reminders.parse_reminder(arg)
                if parsed:
                    content, remind_at = parsed
                    ok = self._reminders.schedule(content, remind_at)
                    if ok:
                        time_str = remind_at.strftime("%I:%M %p")
                        return f"Sure, I'll remind you to {content} at {time_str}"
                    return "That time has already passed."
                return "I couldn't understand when to remind you. Try saying 'in 5 minutes' or 'at 3:00 pm'."
            return "Reminder system is not available."

        if intent == "add_task":
            if self._tasks is not None:
                self._tasks.add(arg, "task")
                return f"Added to your to-do list: {arg}"
            return "Task storage is not available."

        if intent == "add_goal":
            if self._tasks is not None:
                self._tasks.add(arg, "goal")
                return f"Goal added: {arg}"
            return "Task storage is not available."

        if intent == "complete_task":
            if self._tasks is not None:
                done = self._tasks.complete(arg)
                return f"Marked as done: {arg}" if done else f"Could not find task matching '{arg}'"
            return "Task storage is not available."

        if intent == "show_tasks":
            if self._tasks is not None:
                items = self._tasks.list_open("task")
                if items:
                    return "Your tasks: " + ", ".join(items)
                return "You have no open tasks."
            return "Task storage is not available."

        if intent == "show_goals":
            if self._tasks is not None:
                items = self._tasks.list_open("goal")
                if items:
                    return "Your goals: " + ", ".join(items)
                return "You have no goals set."
            return "Task storage is not available."

        if intent == "show_memories":
            if self._memories is not None:
                items = self._memories.list_recent(5)
                if items:
                    return "I remember: " + "; ".join(items)
                return "I don't have any stored memories yet."
            return "Memory storage is not available."

        # ── Vision ─────────────────────────────────────────────────────────
        if intent == "vision_identify":
            if self._vision is None:
                return "Vision is not available. Please install opencv-python and mediapipe."
            return self._vision.identify_hand_object()

        # ── System ─────────────────────────────────────────────────────────
        if intent == "system":
            result = self._launcher.system_command(arg)
            return result or "Unknown system command"

        if intent == "close_app":
            return self._launcher.close_app(arg)

        if intent == "launch":
            ok = self._launcher.launch(arg)
            return f"Launching {arg}" if ok else f"Could not launch {arg}"

        if intent == "google":
            self._browser.google(arg)
            return f"Searching Google for {arg}"

        if intent == "youtube":
            self._browser.youtube(arg)
            return f"Searching YouTube for {arg}"

        if intent == "open_url":
            url = arg if arg.startswith(("http://", "https://")) else f"https://{arg}"
            self._browser.open_url(url)
            return f"Opening {arg}"

        if intent == "open_folder":
            self._files.open_folder(arg)
            return f"Opening folder {arg}"

        if intent == "open_file":
            self._files.open_file(arg)
            return f"Opening file {arg}"

        # ── Volume precise control ─────────────────────────────────────────
        if intent in ("volume_set", "volume_to"):
            return self._launcher.set_volume(int(arg))
        if intent == "volume_up_pct":
            return self._launcher.change_volume(+int(arg))
        if intent == "volume_down_pct":
            return self._launcher.change_volume(-int(arg))
        if intent == "volume_max":
            return self._launcher.set_volume(100)
        if intent == "volume_low":
            return self._launcher.set_volume(5)
        if intent == "volume_mid":
            return self._launcher.set_volume(50)

        # ── Brightness precise control ─────────────────────────────────────
        if intent in ("brightness_set", "brightness_to"):
            return self._launcher.set_brightness(int(arg))
        if intent == "brightness_up_pct":
            return self._launcher.change_brightness(+int(arg))
        if intent == "brightness_down_pct":
            return self._launcher.change_brightness(-int(arg))
        if intent == "brightness_max":
            return self._launcher.set_brightness(100)
        if intent == "brightness_low":
            return self._launcher.set_brightness(10)
        if intent == "brightness_mid":
            return self._launcher.set_brightness(50)

        return None

    def _run_routine(self, routine: Any) -> str:
        results: list[str] = []
        for cmd in routine.commands:
            result = self.dispatch(cmd)
            if result:
                results.append(result)
        return "; ".join(results) if results else f"Ran routine: {routine.trigger_phrase}"
