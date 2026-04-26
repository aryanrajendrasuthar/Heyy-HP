"""Settings dialog — read-only view of AppSettings with runtime overrides."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import AppSettings
from app.services import startup as _startup

_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        form = QFormLayout()
        outer.addLayout(form)

        fields = {
            "App name": self._settings.app_name,
            "Debug": str(self._settings.debug),
            "Wake phrase": self._settings.wake_phrase,
            "Follow-up timeout (s)": str(self._settings.follow_up_timeout_s),
            "Audio sample rate": str(self._settings.audio_sample_rate),
            "Audio device index": str(self._settings.audio_device_index),
            "Wake word model": self._settings.wake_word_model,
            "STT model": self._settings.whisper_model,
            "STT device": self._settings.stt_device,
            "TTS rate": str(self._settings.tts_rate),
            "TTS volume": str(self._settings.tts_volume),
            "Log dir": self._settings.log_dir,
            "DB path": self._settings.db_path,
        }

        for label_text, value in fields.items():
            form.addRow(QLabel(label_text), QLabel(value))

        self._level_combo = QComboBox()
        self._level_combo.addItems(_LOG_LEVELS)
        current_name = logging.getLevelName(logging.getLogger().level)
        idx = self._level_combo.findText(current_name)
        self._level_combo.setCurrentIndex(idx if idx >= 0 else _LOG_LEVELS.index("INFO"))
        form.addRow(QLabel("Log level (runtime)"), self._level_combo)
        self._level_combo.currentTextChanged.connect(self._on_level_changed)

        self._startup_cb = QCheckBox("Start HP on Windows boot")
        self._startup_cb.setChecked(_startup.is_registered())
        self._startup_cb.toggled.connect(self._on_startup_toggled)
        outer.addWidget(self._startup_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _on_level_changed(self, level_name: str) -> None:
        logging.getLogger().setLevel(level_name)

    def _on_startup_toggled(self, checked: bool) -> None:
        if checked:
            _startup.register()
        else:
            _startup.unregister()
