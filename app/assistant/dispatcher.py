"""Route transcribed commands to the correct action handler."""

from __future__ import annotations

import re

from app.actions.browser import BrowserRouter
from app.actions.files import FileActions
from app.actions.launcher import AppLauncher

# Patterns ordered specific-to-general to prevent short patterns capturing
# longer, more specific phrases first.
_INTENTS: list[tuple[str, re.Pattern[str]]] = [
    ("open_folder", re.compile(r"open\s+(?:folder|directory)\s+(.+)", re.IGNORECASE)),
    ("open_url", re.compile(r"(?:open|go\s+to)\s+(https?://\S+)", re.IGNORECASE)),
    ("open_file", re.compile(r"open\s+(?:file\s+)?([^\s].+\.\w+)", re.IGNORECASE)),
    ("google", re.compile(r"(?:google|search(?:\s+for)?)\s+(.+)", re.IGNORECASE)),
    ("youtube", re.compile(r"(?:youtube|play(?:\s+on\s+youtube)?)\s+(.+)", re.IGNORECASE)),
    ("launch", re.compile(r"(?:open|launch|start|run)\s+(.+)", re.IGNORECASE)),
]


class CommandDispatcher:
    def __init__(self) -> None:
        self._launcher = AppLauncher()
        self._browser = BrowserRouter()
        self._files = FileActions()

    def dispatch(self, text: str) -> str | None:
        for intent, pattern in _INTENTS:
            m = pattern.fullmatch(text.strip())
            if m:
                arg = m.group(1).strip()
                return self._handle(intent, arg)
        return None

    def _handle(self, intent: str, arg: str) -> str | None:
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
