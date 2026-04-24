"""QApplication factory — ensures a single instance per process."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config.settings import AppSettings


def create_app(settings: AppSettings) -> QApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing  # type: ignore[return-value]
    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    app.setQuitOnLastWindowClosed(False)
    return app
