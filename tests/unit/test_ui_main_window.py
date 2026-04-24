"""Unit tests for HPMainWindow.

Skipped automatically when PySide6 is not installed (e.g., bare dev environment).
Run with QT_QPA_PLATFORM=offscreen for headless / CI execution.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from app.assistant.state import AssistantState  # noqa: E402
from app.config.settings import AppSettings  # noqa: E402
from app.ui.main_window import HPMainWindow  # noqa: E402


@pytest.fixture
def window(qtbot):
    w = HPMainWindow("HP")
=======
@pytest.fixture()
def window(qtbot):  # type: ignore[no-untyped-def]
    w = HPMainWindow(AppSettings())
    qtbot.addWidget(w)
    return w


def test_window_title(window):
    assert window.windowTitle() == "HP"


def test_window_min_size(window: HPMainWindow) -> None:
    assert window.minimumWidth() >= 480
    assert window.minimumHeight() >= 260


def test_set_state_updates_label(window: HPMainWindow) -> None:
    window.set_state(AssistantState.LISTENING)
    texts = [lb.text() for lb in window.findChildren(QLabel)]
    assert "LISTENING" in texts


def test_set_transcript_updates_label(window: HPMainWindow) -> None:
    window.set_transcript("hello world")
    texts = [lb.text() for lb in window.findChildren(QLabel)]
    assert any("hello world" in t for t in texts)


def test_set_response_updates_label(window: HPMainWindow) -> None:
    window.set_response("hi there")
    texts = [lb.text() for lb in window.findChildren(QLabel)]
    assert any("hi there" in t for t in texts)


def test_clear_removes_content(window: HPMainWindow) -> None:
    window.set_transcript("hello")
    window.set_response("hi")
    window.clear()
    texts = [lb.text() for lb in window.findChildren(QLabel)]
    assert "You: hello" not in texts
    assert "HP: hi" not in texts


def test_menu_bar_present(window: HPMainWindow) -> None:
    assert window.menuBar() is not None


def test_all_states_can_be_set_without_error(window):
    for state in AssistantState:
        window.set_state(state)  # must not raise
=======
def test_initial_state_label_idle(window: HPMainWindow) -> None:
    texts = [lb.text() for lb in window.findChildren(QLabel)]
    assert "IDLE" in texts
