"""Unit tests for SettingsDialog. Skipped when PySide6 not installed."""

from __future__ import annotations

import logging

import pytest

pytest.importorskip("PySide6")
from app.config.settings import AppSettings  # noqa: E402
from app.ui.settings_panel import SettingsDialog  # noqa: E402


@pytest.fixture
def dialog(qtbot):
    d = SettingsDialog(AppSettings())
    qtbot.addWidget(d)
    return d


def test_dialog_opens_without_error(dialog):
    assert dialog is not None


def test_window_title(dialog):
    assert "Settings" in dialog.windowTitle()


def test_default_log_level_shown(dialog):
    assert dialog.current_log_level() in ("DEBUG", "INFO", "WARNING", "ERROR")


def test_changing_log_level_updates_root_logger(dialog):
    dialog._level_combo.setCurrentText("WARNING")
    assert logging.getLogger().level == logging.WARNING


def test_settings_values_reflected(qtbot):
    from PySide6.QtWidgets import QLabel

    settings = AppSettings(wake_phrase="Hey Test", follow_up_timeout_s=5)
    d = SettingsDialog(settings)
    qtbot.addWidget(d)
    all_label_texts = [w.text() for w in d.findChildren(QLabel)]
    assert "Hey Test" in all_label_texts
    assert "5 s" in all_label_texts
