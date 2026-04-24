"""Unit tests for FollowUpTimer."""

from __future__ import annotations

import threading

from app.assistant.timer import FollowUpTimer


def test_fires_on_expire():
    fired = threading.Event()
    timer = FollowUpTimer(timeout_s=0, on_expire=fired.set)
    timer.start()
    assert fired.wait(timeout=1.0), "Timer did not fire within 1 s"


def test_cancel_prevents_fire():
    fired = threading.Event()
    timer = FollowUpTimer(timeout_s=60, on_expire=fired.set)
    timer.start()
    assert timer.running
    timer.cancel()
    assert not timer.running
    assert not fired.is_set()


def test_restart_cancels_previous():
    fired: list[int] = []
    # Long timeout so the first timer cannot fire before we cancel it
    timer = FollowUpTimer(timeout_s=60, on_expire=lambda: fired.append(1))
    timer.start()
    assert timer.running
    timer.start()  # cancels first, starts a new 60-second timer
    assert timer.running
    timer.cancel()  # cancel before it fires
    assert not timer.running
    assert not fired
