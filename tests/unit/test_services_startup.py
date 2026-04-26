"""Unit tests for Windows startup registration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.services.startup as startup_mod


@pytest.fixture()
def winreg_mock() -> MagicMock:
    mock = MagicMock()
    mock.HKEY_CURRENT_USER = "HKCU"
    mock.KEY_SET_VALUE = 0x0002
    mock.REG_SZ = 1
    with (
        patch.object(startup_mod, "_WINREG_AVAILABLE", True),
        patch.object(startup_mod, "_winreg", mock),
    ):
        yield mock


def test_is_registered_returns_false_when_winreg_unavailable() -> None:
    with patch.object(startup_mod, "_WINREG_AVAILABLE", False):
        assert startup_mod.is_registered() is False


def test_register_returns_false_when_winreg_unavailable() -> None:
    with patch.object(startup_mod, "_WINREG_AVAILABLE", False):
        assert startup_mod.register("hp.exe") is False


def test_unregister_returns_false_when_winreg_unavailable() -> None:
    with patch.object(startup_mod, "_WINREG_AVAILABLE", False):
        assert startup_mod.unregister() is False


def test_is_registered_true_when_key_exists(winreg_mock: MagicMock) -> None:
    winreg_mock.QueryValueEx.return_value = ("hp.exe", 1)
    assert startup_mod.is_registered() is True
    winreg_mock.OpenKey.assert_called_once()


def test_is_registered_false_when_key_missing(winreg_mock: MagicMock) -> None:
    winreg_mock.OpenKey.side_effect = OSError("key not found")
    assert startup_mod.is_registered() is False


def test_register_calls_set_value(winreg_mock: MagicMock) -> None:
    result = startup_mod.register("C:\\HP\\HP.exe")
    assert result is True
    winreg_mock.SetValueEx.assert_called_once()
    call_args = winreg_mock.SetValueEx.call_args[0]
    assert "HP-Assistant" in call_args
    assert "C:\\HP\\HP.exe" in call_args


def test_register_returns_false_on_os_error(winreg_mock: MagicMock) -> None:
    winreg_mock.OpenKey.side_effect = OSError("access denied")
    assert startup_mod.register("hp.exe") is False


def test_unregister_calls_delete_value(winreg_mock: MagicMock) -> None:
    result = startup_mod.unregister()
    assert result is True
    winreg_mock.DeleteValue.assert_called_once()


def test_unregister_returns_false_on_os_error(winreg_mock: MagicMock) -> None:
    winreg_mock.OpenKey.side_effect = OSError("not found")
    assert startup_mod.unregister() is False


def test_version_is_1_0_0() -> None:
    from app.__version__ import __version__

    assert __version__ == "1.0.0"
