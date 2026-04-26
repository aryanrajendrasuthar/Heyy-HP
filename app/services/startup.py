"""Windows startup registration via the HKCU Run registry key."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import winreg as _winreg

    _WINREG_AVAILABLE = True
except ImportError:
    _WINREG_AVAILABLE = False

_STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "HP-Assistant"


def _default_exe_path() -> str:
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle — executable is self-contained
        return f'"{sys.executable}"'
    main_py = (Path(__file__).parent.parent.parent / "main.py").resolve()
    return f'"{sys.executable}" "{main_py}"'


def is_registered() -> bool:
    if not _WINREG_AVAILABLE:
        return False
    try:
        with _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, _STARTUP_KEY) as key:
            _winreg.QueryValueEx(key, _APP_NAME)
            return True
    except OSError:
        return False


def register(exe_path: str | None = None) -> bool:
    if not _WINREG_AVAILABLE:
        logger.warning("winreg not available — startup registration skipped")
        return False
    path = exe_path or _default_exe_path()
    try:
        with _winreg.OpenKey(
            _winreg.HKEY_CURRENT_USER, _STARTUP_KEY, 0, _winreg.KEY_SET_VALUE
        ) as key:
            _winreg.SetValueEx(key, _APP_NAME, 0, _winreg.REG_SZ, path)
        logger.info("Registered startup: %s", path)
        return True
    except OSError:
        logger.exception("Failed to register startup")
        return False


def unregister() -> bool:
    if not _WINREG_AVAILABLE:
        return False
    try:
        with _winreg.OpenKey(
            _winreg.HKEY_CURRENT_USER, _STARTUP_KEY, 0, _winreg.KEY_SET_VALUE
        ) as key:
            _winreg.DeleteValue(key, _APP_NAME)
        logger.info("Unregistered startup")
        return True
    except OSError:
        return False
