"""Settings dialog — displays current AppSettings and allows runtime log level change."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import AppSettings

logger = logging.getLogger(__name__)
_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]

_STYLESHEET = """
QDialog { background-color: #1E1E2E; }
QLabel { color: #E0E0E0; font-size: 13px; }
QComboBox {
    background-color: #2A2A3E; color: #E0E0E0; border: 1px solid #3A3A5C;
    border-radius: 4px; padding: 4px 8px; font-size: 13px; min-width: 120px;
}
QComboBox QAbstractItemView { background-color: #2A2A3E; color: #E0E0E0; selection-background-color: #4A4A6C; }
QPushButton { background-color: #3A3A5C; color: #E0E0E0; border: none; border-radius: 4px; padding: 6px 16px; font-size: 13px; }
QPushButton:hover { background-color: #4A4A6C; }
"""


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("HP — Settings")
        self.setMinimumWidth(380)
        self.setModal(True)
        self.setStyleSheet(_STYLESHEET)
        self._settings = settings
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(14)
        layout.addLayout(self._build_info_form())
        layout.addLayout(self._build_log_level_row())
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_info_form(self) -> QFormLayout:
        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        rows = [
            ("App name:", self._settings.app_name),
            ("Wake phrase:", self._settings.wake_phrase),
            ("Follow-up timeout:", f"{self._settings.follow_up_timeout_s} s"),
            ("Audio sample rate:", f"{self._settings.audio_sample_rate} Hz"),
            ("Audio device:", str(self._settings.audio_device_index or "system default")),
            ("Database:", self._settings.db_path),
        ]
        for label, value in rows:
            val_label = QLabel(value)
            val_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form.addRow(label, val_label)
        return form

    def _build_log_level_row(self) -> QFormLayout:
        row = QFormLayout()
        self._level_combo = QComboBox()
        self._level_combo.addItems(_LOG_LEVELS)
        current_name = logging.getLevelName(logging.getLogger().level)
        if current_name in _LOG_LEVELS:
            self._level_combo.setCurrentText(current_name)
        self._level_combo.currentTextChanged.connect(self._on_level_changed)
        row.addRow("Log level:", self._level_combo)
        return row

    def current_log_level(self) -> str:
        return self._level_combo.currentText()

    def _on_level_changed(self, level_name: str) -> None:
        logging.getLogger().setLevel(level_name)
        logger.debug("Runtime log level changed to %s", level_name)
