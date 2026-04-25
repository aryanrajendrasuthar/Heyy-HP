"""Launch desktop applications by name."""

from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)

_WINDOWS_APPS: dict[str, str] = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "explorer": "explorer",
    "file explorer": "explorer",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "teams": "teams",
    "microsoft teams": "teams",
    "spotify": "spotify",
    "discord": "discord",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "terminal": "wt",
    "windows terminal": "wt",
    "cmd": "cmd",
    "powershell": "powershell",
    "paint": "mspaint",
    "task manager": "taskmgr",
    "control panel": "control",
}


class AppLauncher:
    def launch(self, app_name: str) -> bool:
        key = app_name.lower().strip()
        cmd = _WINDOWS_APPS.get(key)
        if cmd is None:
            # Try as a direct command
            cmd = key
        try:
            subprocess.Popen(  # noqa: S603
                cmd,
                shell=True,  # noqa: S602
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Launched: %s (%s)", app_name, cmd)
            return True
        except Exception:
            logger.exception("Failed to launch %s", app_name)
            return False
