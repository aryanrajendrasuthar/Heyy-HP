"""HP main window — transcript panel, response panel, status bar, and menu."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.assistant.state import AssistantState
from app.config.settings import AppSettings

logger = logging.getLogger(__name__)

_STATE_DISPLAY: dict[AssistantState, tuple[str, str]] = {
    AssistantState.IDLE: ("● IDLE", "#888888"),
    AssistantState.WAKE_DETECTED: ("● WAKE DETECTED", "#F5A623"),
    AssistantState.LISTENING: ("● LISTENING", "#7ED321"),
    AssistantState.PROCESSING: ("● PROCESSING", "#4A90E2"),
    AssistantState.SPEAKING: ("● SPEAKING", "#9B59B6"),
    AssistantState.FOLLOW_UP: ("● FOLLOW-UP", "#7ED321"),
}

_STYLESHEET = """
QMainWindow, QWidget#central { background-color: #1E1E2E; }
QMenuBar { background-color: #1E1E2E; color: #AAAACC; font-size: 13px; }
QMenuBar::item:selected { background-color: #2A2A3E; }
QMenu { background-color: #2A2A3E; color: #E0E0E0; border: 1px solid #3A3A5C; }
QMenu::item:selected { background-color: #4A4A6C; }
QLabel#section { color: #666688; font-size: 10px; letter-spacing: 1px; padding: 4px 0px 2px 0px; }
QTextEdit {
    background-color: #2A2A3E; color: #E0E0E0; border: 1px solid #3A3A5C;
    border-radius: 4px; font-family: "Segoe UI", sans-serif; font-size: 13px; padding: 8px;
}
"""


def _make_window_icon() -> QIcon:
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
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self._settings = settings
        self.setWindowTitle(settings.app_name)
        self.setWindowIcon(_make_window_icon())
        self.setMinimumSize(500, 420)
        self.setStyleSheet(_STYLESHEET)
        self._build_menu_bar()
        self._build_ui()
        logger.debug("Main window initialised")

    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        sa = QAction("Settings…", self)
        sa.triggered.connect(self._open_settings)
        file_menu.addAction(sa)
        file_menu.addSeparator()
        qa = QAction("Quit", self)
        qa.triggered.connect(QApplication.quit)
        file_menu.addAction(qa)
        hm = self.menuBar().addMenu("Help")
        aa = QAction("About HP", self)
        aa.triggered.connect(self._open_about)
        hm.addAction(aa)

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
        self._response.setPlaceholderText("HP response appears here.")
        layout.addWidget(self._response)

    def set_state(self, state: AssistantState) -> None:
        self._status.update_state(state)
        logger.debug("UI state -> %s", state.name)

    def set_transcript(self, text: str) -> None:
        self._transcript.setPlainText(text)

    def set_response(self, text: str) -> None:
        self._response.setPlainText(text)

    def clear(self) -> None:
        self._transcript.clear()
        self._response.clear()

    def _open_settings(self) -> None:
        from app.ui.settings_panel import SettingsDialog

        SettingsDialog(self._settings, parent=self).exec()

    def _open_about(self) -> None:
        QMessageBox.about(self, "HP Assistant", "HP — Local Desktop Voice Assistant\nVersion 0.1.0")


class _StatusBar(QLabel):
    def __init__(self) -> None:
        super().__init__("● IDLE")
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
