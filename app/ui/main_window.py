<<<<<<< HEAD
"""HP main window — transcript panel, response panel, and status indicator."""
=======
"""HP main window — state display with dark theme and menu bar."""
>>>>>>> e82e590 (All of sprint 2)

from __future__ import annotations

import logging

<<<<<<< HEAD
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QMainWindow, QTextEdit, QVBoxLayout, QWidget

from app.assistant.state import AssistantState

logger = logging.getLogger(__name__)

# Maps each state to a (display label, color hex) pair.
_STATE_DISPLAY: dict[AssistantState, tuple[str, str]] = {
    AssistantState.IDLE: ("● IDLE", "#888888"),
    AssistantState.WAKE_DETECTED: ("● WAKE DETECTED", "#F5A623"),
    AssistantState.LISTENING: ("● LISTENING", "#7ED321"),
    AssistantState.PROCESSING: ("● PROCESSING", "#4A90E2"),
    AssistantState.SPEAKING: ("● SPEAKING", "#9B59B6"),
    AssistantState.FOLLOW_UP: ("● FOLLOW-UP", "#7ED321"),
}

_STYLESHEET = """
QMainWindow, QWidget#central {
    background-color: #1E1E2E;
}
QLabel#section {
    color: #666688;
    font-size: 10px;
    letter-spacing: 1px;
    padding: 4px 0px 2px 0px;
}
QTextEdit {
    background-color: #2A2A3E;
    color: #E0E0E0;
    border: 1px solid #3A3A5C;
    border-radius: 4px;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
    padding: 8px;
}
"""


def _make_window_icon() -> QIcon:
    """Draw a simple 'H' badge — no external asset required at bootstrap."""
    px = QPixmap(32, 32)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#4A90D9"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(1, 1, 30, 30)
    p.setPen(QColor("#FFFFFF"))
    f = QFont("Arial", 14)
    f.setBold(True)
    p.setFont(f)
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "H")
    p.end()
    return QIcon(px)


class HPMainWindow(QMainWindow):
    def __init__(self, app_name: str = "HP") -> None:
        super().__init__()
        self.setWindowTitle(app_name)
        self.setWindowIcon(_make_window_icon())
        self.setMinimumSize(500, 420)
        self.setStyleSheet(_STYLESHEET)
        self._build_ui()
        logger.debug("Main window initialised")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(6)

        self._status = _StatusBar()
        layout.addWidget(self._status)

        layout.addWidget(_section_label("YOU"))
        self._transcript = QTextEdit()
        self._transcript.setReadOnly(True)
        self._transcript.setPlaceholderText('Say "Hey HP" to start…')
        self._transcript.setFixedHeight(90)
        layout.addWidget(self._transcript)

        layout.addWidget(_section_label("HP"))
        self._response = QTextEdit()
        self._response.setReadOnly(True)
        self._response.setPlaceholderText("HP's response appears here.")
        layout.addWidget(self._response)

    # ------------------------------------------------------------------
    # Public API — called by the assistant runtime
    # ------------------------------------------------------------------

    def set_state(self, state: AssistantState) -> None:
        self._status.update_state(state)
        logger.debug("UI state → %s", state.name)

    def set_transcript(self, text: str) -> None:
        self._transcript.setPlainText(text)

    def set_response(self, text: str) -> None:
        self._response.setPlainText(text)

    def clear(self) -> None:
        self._transcript.clear()
        self._response.clear()


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


class _StatusBar(QLabel):
    def __init__(self) -> None:
        super().__init__("● IDLE")
        self.setObjectName("status")
        self._apply_style("#888888")

    def update_state(self, state: AssistantState) -> None:
        text, color = _STATE_DISPLAY[state]
        self.setText(text)
        self._apply_style(color)

    def _apply_style(self, color: str) -> None:
        self.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: bold; "
            "padding: 6px 8px; background-color: #2A2A3E; border-radius: 4px;"
        )


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("section")
    return lbl
=======
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
>>>>>>> e82e590 (All of sprint 2)
