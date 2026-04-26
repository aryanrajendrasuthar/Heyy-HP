"""HP main window — conversation history, state display, dark theme."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.__version__ import __version__
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
QLabel#state      { font-size: 16px; font-weight: bold; }
QLabel#transcript { font-size: 12px; color: #a6e3a1; }
QLabel#response   { font-size: 12px; color: #cdd6f4; }
QTextEdit#history {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    font-size: 12px;
    font-family: Segoe UI, sans-serif;
}
QMenuBar { background-color: #181825; color: #cdd6f4; }
QMenuBar::item:selected { background-color: #313244; }
QMenu { background-color: #181825; color: #cdd6f4; }
QMenu::item:selected  { background-color: #313244; }
"""

_STATE_COLORS: dict[AssistantState, str] = {
    AssistantState.IDLE: "#6c7086",
    AssistantState.WAKE_DETECTED: "#f9e2af",
    AssistantState.LISTENING: "#a6e3a1",
    AssistantState.PROCESSING: "#89dceb",
    AssistantState.SPEAKING: "#89b4fa",
    AssistantState.FOLLOW_UP: "#cba6f7",
}


class HPMainWindow(QMainWindow):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle(settings.app_name)
        self.setMinimumSize(480, 260)
        self.setStyleSheet(_DARK_STYLE)
        self._build_menu()
        self._build_body()
        self.set_state(AssistantState.IDLE)

    def _build_menu(self) -> None:
        bar = QMenuBar(self)
        self.setMenuBar(bar)

        file_menu = QMenu("&File", self)
        file_menu.addAction("Settings", self._open_settings)
        file_menu.addAction("Clear History", self._clear_history)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close)
        bar.addMenu(file_menu)

        help_menu = QMenu("&Help", self)
        help_menu.addAction("About", self._show_about)
        bar.addMenu(help_menu)

    def _build_body(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(8)

        self._state_label = QLabel("IDLE")
        self._state_label.setObjectName("state")

        self._transcript_label = QLabel("")
        self._transcript_label.setObjectName("transcript")
        self._transcript_label.setWordWrap(True)

        self._response_label = QLabel("")
        self._response_label.setObjectName("response")
        self._response_label.setWordWrap(True)

        self._history_edit = QTextEdit()
        self._history_edit.setObjectName("history")
        self._history_edit.setReadOnly(True)
        self._history_edit.setMinimumHeight(100)

        layout.addWidget(self._state_label)
        layout.addWidget(self._transcript_label)
        layout.addWidget(self._response_label)
        layout.addWidget(self._history_edit, stretch=1)

        self.setCentralWidget(container)

    # ── Public API ────────────────────────────────────────────────────────

    def set_state(self, state: AssistantState) -> None:
        self._state_label.setText(state.name)
        color = _STATE_COLORS.get(state, "#cdd6f4")
        self._state_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")

    def set_transcript(self, text: str) -> None:
        self._transcript_label.setText(f"You: {text}")

    def set_response(self, text: str) -> None:
        self._response_label.setText(f"HP: {text}")
        transcript = self._transcript_label.text()
        if transcript:
            self._append_history(transcript, f"HP: {text}")

    def clear(self) -> None:
        self._transcript_label.setText("")
        self._response_label.setText("")

    # ── Private helpers ───────────────────────────────────────────────────

    def _append_history(self, transcript: str, response: str) -> None:
        you_color = "#a6e3a1"
        hp_color = "#89b4fa"
        html = (
            f'<p style="margin:4px 0">'
            f'<span style="color:{you_color}">{transcript}</span><br>'
            f'<span style="color:{hp_color}">{response}</span>'
            f"</p>"
        )
        self._history_edit.append(html)

    def _clear_history(self) -> None:
        self._history_edit.clear()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._settings, self)
        dialog.exec()

    def _show_about(self) -> None:
        from PySide6.QtWidgets import QMessageBox  # noqa: PLC0415

        QMessageBox.about(
            self,
            "About HP",
            f"{self._settings.app_name} — local desktop voice assistant\nVersion {__version__}",
        )
