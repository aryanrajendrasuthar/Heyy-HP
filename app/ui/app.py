<<<<<<< HEAD
"""QApplication factory.

Returns the existing instance if one was already created (e.g., inside pytest-qt),
so callers never accidentally create a second QApplication.
"""
=======
"""QApplication factory — ensures a single instance per process."""
>>>>>>> e82e590 (All of sprint 2)

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config.settings import AppSettings


def create_app(settings: AppSettings) -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing  # type: ignore[return-value]
<<<<<<< HEAD

    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    app.setApplicationVersion("0.1.0")
    # Keep the process alive when the main window is hidden to the tray.
=======
    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
>>>>>>> e82e590 (All of sprint 2)
    app.setQuitOnLastWindowClosed(False)
    return app
