"""Unit tests for HPMainWindow. Skipped when PySide6 not installed."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")
from app.assistant.state import AssistantState  # noqa: E402
from app.config.settings import AppSettings  # noqa: E402
from app.ui.main_window import HPMainWindow  # noqa: E402


@pytest.fixture
def window(qtbot):
    w = HPMainWindow(AppSettings())
    qtbot.addWidget(w)
    return w


def test_window_title(window):
    assert window.windowTitle() == "HP"


def test_initial_status_shows_idle(window):
    assert "IDLE" in window._status.text()


def test_set_state_listening(window):
    window.set_state(AssistantState.LISTENING)
    assert "LISTENING" in window._status.text()


def test_set_state_speaking(window):
    window.set_state(AssistantState.SPEAKING)
    assert "SPEAKING" in window._status.text()


def test_set_transcript(window):
    window.set_transcript("Hey HP, open Chrome")
    assert "Chrome" in window._transcript.toPlainText()


def test_set_response(window):
    window.set_response("Opening Chrome now.")
    assert "Opening Chrome" in window._response.toPlainText()


def test_clear_wipes_both_panels(window):
    window.set_transcript("something")
    window.set_response("something")
    window.clear()
    assert window._transcript.toPlainText() == ""
    assert window._response.toPlainText() == ""


def test_all_states_renderable(window):
    for state in AssistantState:
        window.set_state(state)


def test_menu_bar_has_file_and_help(window):
    titles = [window.menuBar().actions()[i].text() for i in range(len(window.menuBar().actions()))]
    assert "File" in titles
    assert "Help" in titles
