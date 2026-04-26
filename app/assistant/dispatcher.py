"""Route transcribed commands to the correct action handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.actions.browser import BrowserRouter
from app.actions.files import FileActions
from app.actions.launcher import AppLauncher

if TYPE_CHECKING:
    pass

# Patterns ordered specific-to-general.
# Vision and no-argument intents use no capture group (m.lastindex is None).
_INTENTS: list[tuple[str, re.Pattern[str]]] = [
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
    ("open_url", re.compile(r"(?:open|go\s+to)\s+(https?://\S+)", re.IGNORECASE)),
    ("open_file", re.compile(r"open\s+(?:file\s+)?([^\s].+\.\w+)", re.IGNORECASE)),
    ("google", re.compile(r"(?:google|search(?:\s+for)?)\s+(.+)", re.IGNORECASE)),
    ("youtube", re.compile(r"(?:youtube|play(?:\s+on\s+youtube)?)\s+(.+)", re.IGNORECASE)),
    ("launch", re.compile(r"(?:open|launch|start|run)\s+(.+)", re.IGNORECASE)),
]


class CommandDispatcher:
    def __init__(
        self,
        vision: Any | None = None,
        routines: Any | None = None,
    ) -> None:
        self._launcher = AppLauncher()
        self._browser = BrowserRouter()
        self._files = FileActions()
        self._vision = vision
        self._routines = routines

    def dispatch(self, text: str) -> str | None:
        cleaned = text.strip()

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

    def _handle(self, intent: str, arg: str) -> str | None:
        if intent == "vision_identify":
            if self._vision is None:
                return "Vision is not available. Please install opencv-python and mediapipe."
            return self._vision.identify_hand_object()
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
            self._browser.open_url(arg)
            return f"Opening {arg}"
        if intent == "open_folder":
            self._files.open_folder(arg)
            return f"Opening folder {arg}"
        if intent == "open_file":
            self._files.open_file(arg)
            return f"Opening file {arg}"
        return None

    def _run_routine(self, routine: Any) -> str:
        results: list[str] = []
        for cmd in routine.commands:
            result = self.dispatch(cmd)
            if result:
                results.append(result)
        return "; ".join(results) if results else f"Ran routine: {routine.trigger_phrase}"
