"""QApplication factory.

Returns the existing instance if one was already created (e.g., inside pytest-qt),
so callers never accidentally create a second QApplication.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config.settings import AppSettings


def create_app(settings: AppSettings) -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing  # type: ignore[return-value]

    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)

    # Set app-wide icon (taskbar + alt-tab)
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent.parent))
    ico = base / "hp.ico"
    if ico.exists():
        app.setWindowIcon(QIcon(str(ico)))

    return app
