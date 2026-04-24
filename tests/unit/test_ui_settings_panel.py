"""Unit tests for SettingsDialog."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QComboBox, QLabel  # noqa: E402

from app.config.settings import AppSettings  # noqa: E402
from app.ui.settings_panel import SettingsDialog  # noqa: E402


@pytest.fixture()
def dialog(qtbot):  # type: ignore[no-untyped-def]
    d = SettingsDialog(AppSettings())
    qtbot.addWidget(d)
    return d


def test_dialog_creates(dialog: SettingsDialog) -> None:
    assert dialog is not None


def test_dialog_title(dialog: SettingsDialog) -> None:
    assert dialog.windowTitle() == "Settings"


def test_settings_values_reflected(dialog: SettingsDialog) -> None:
    texts = [lb.text() for lb in dialog.findChildren(QLabel)]
    assert "HP" in texts
    assert "Hey HP" in texts


def test_log_level_combo_present(dialog: SettingsDialog) -> None:
    combos = dialog.findChildren(QComboBox)
    assert len(combos) >= 1


def test_log_level_options(dialog: SettingsDialog) -> None:
    combos = dialog.findChildren(QComboBox)
    items = [combos[0].itemText(i) for i in range(combos[0].count())]
    assert "DEBUG" in items
    assert "INFO" in items
