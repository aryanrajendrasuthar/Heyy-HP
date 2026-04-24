"""Unit tests for HPMainWindow.

Skipped automatically when PySide6 is not installed (e.g., bare dev environment).
Run with QT_QPA_PLATFORM=offscreen for headless / CI execution.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from app.assistant.state import AssistantState  # noqa: E402
from app.ui.main_window import HPMainWindow  # noqa: E402


@pytest.fixture
def window(qtbot):
    w = HPMainWindow("HP")
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


def test_all_states_can_be_set_without_error(window):
    for state in AssistantState:
        window.set_state(state)  # must not raise
