"""Unit tests for AppLauncher."""

from __future__ import annotations

from unittest.mock import patch

from app.actions.launcher import AppLauncher


def test_launch_known_app_returns_true() -> None:
    launcher = AppLauncher()
    with patch("app.actions.launcher.subprocess.Popen") as mock_popen:
        mock_popen.return_value = None
        result = launcher.launch("notepad")
    assert result is True


def test_launch_unknown_app_attempts_direct_command() -> None:
    launcher = AppLauncher()
    with patch("app.actions.launcher.subprocess.Popen") as mock_popen:
        mock_popen.return_value = None
        result = launcher.launch("somecustomapp")
    assert result is True
    call_args = mock_popen.call_args
    assert "somecustomapp" in call_args[0][0]


def test_launch_returns_false_on_exception() -> None:
    launcher = AppLauncher()
    with patch("app.actions.launcher.subprocess.Popen", side_effect=OSError("not found")):
        result = launcher.launch("nonexistent_app_xyz")
    assert result is False


def test_launch_chrome_alias() -> None:
    launcher = AppLauncher()
    with patch("app.actions.launcher.subprocess.Popen") as mock_popen:
        mock_popen.return_value = None
        result = launcher.launch("google chrome")
    assert result is True
    call_args = mock_popen.call_args
    assert "chrome" in call_args[0][0]
