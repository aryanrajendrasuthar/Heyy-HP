"""HP main window — state display with dark theme and menu bar."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QVBoxLayout,
    QWidget,
)

from app.assistant.state import AssistantState
from app.config.settings import AppSettings
from app.ui.settings_panel import SettingsDialog

logger = logging.getLogger(__name__)

_DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: Segoe UI, sans-serif;
}
QLabel#state   { font-size: 16px; font-weight: bold; color: #89b4fa; }
QLabel#transcript { font-size: 12px; color: #a6e3a1; }
QLabel#response   { font-size: 12px; color: #cdd6f4; }
QMenuBar { background-color: #181825; color: #cdd6f4; }
QMenuBar::item:selected { background-color: #313244; }
QMenu { background-color: #181825; color: #cdd6f4; }
QMenu::item:selected  { background-color: #313244; }
"""


class HPMainWindow(QMainWindow):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle(settings.app_name)
        self.setMinimumSize(480, 260)
        self.setStyleSheet(_DARK_STYLE)
        self._build_menu()
        self._build_body()

    def _build_menu(self) -> None:
        bar = QMenuBar(self)
        self.setMenuBar(bar)

        file_menu = QMenu("&File", self)
        file_menu.addAction("Settings", self._open_settings)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close)
        bar.addMenu(file_menu)

        help_menu = QMenu("&Help", self)
        help_menu.addAction("About", self._show_about)
        bar.addMenu(help_menu)

    def _build_body(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self._state_label = QLabel("IDLE")
        self._state_label.setObjectName("state")

        self._transcript_label = QLabel("")
        self._transcript_label.setObjectName("transcript")
        self._transcript_label.setWordWrap(True)

        self._response_label = QLabel("")
        self._response_label.setObjectName("response")
        self._response_label.setWordWrap(True)

        layout.addWidget(self._state_label)
        layout.addWidget(self._transcript_label)
        layout.addWidget(self._response_label)
        layout.addStretch()

        self.setCentralWidget(container)

    def set_state(self, state: AssistantState) -> None:
        self._state_label.setText(state.name)

    def set_transcript(self, text: str) -> None:
        self._transcript_label.setText(f"You: {text}")

    def set_response(self, text: str) -> None:
        self._response_label.setText(f"HP: {text}")

    def clear(self) -> None:
        self._transcript_label.setText("")
        self._response_label.setText("")

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._settings, self)
        dialog.exec()

    def _show_about(self) -> None:
        from PySide6.QtWidgets import QMessageBox  # noqa: PLC0415

        QMessageBox.about(
            self,
            "About HP",
            f"{self._settings.app_name} — local desktop voice assistant\nVersion 0.1.0",
        )
