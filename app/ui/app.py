"""QApplication factory."""

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
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)
    return app
