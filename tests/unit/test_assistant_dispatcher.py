"""Unit tests for CommandDispatcher."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.assistant.dispatcher import CommandDispatcher


@pytest.fixture()
def dispatcher() -> CommandDispatcher:
    return CommandDispatcher()


def test_launch_chrome(dispatcher: CommandDispatcher) -> None:
    with patch.object(dispatcher._launcher, "launch", return_value=True) as mock_launch:
        result = dispatcher.dispatch("open chrome")
    mock_launch.assert_called_once_with("chrome")
    assert result is not None
    assert "chrome" in result.lower()


def test_google_search(dispatcher: CommandDispatcher) -> None:
    with patch.object(dispatcher._browser, "google", return_value=True) as mock_google:
        result = dispatcher.dispatch("google python tutorial")
    mock_google.assert_called_once_with("python tutorial")
    assert result is not None


def test_youtube_search(dispatcher: CommandDispatcher) -> None:
    with patch.object(dispatcher._browser, "youtube", return_value=True) as mock_yt:
        result = dispatcher.dispatch("youtube lo fi music")
    mock_yt.assert_called_once_with("lo fi music")
    assert result is not None


def test_open_url(dispatcher: CommandDispatcher) -> None:
    with patch.object(dispatcher._browser, "open_url", return_value=True) as mock_url:
        result = dispatcher.dispatch("open https://example.com")
    mock_url.assert_called_once_with("https://example.com")
    assert result is not None


def test_open_folder(dispatcher: CommandDispatcher) -> None:
    with patch.object(dispatcher._files, "open_folder", return_value=True) as mock_folder:
        result = dispatcher.dispatch("open folder Documents")
    mock_folder.assert_called_once_with("Documents")
    assert result is not None


def test_open_file(dispatcher: CommandDispatcher) -> None:
    with patch.object(dispatcher._files, "open_file", return_value=True) as mock_file:
        result = dispatcher.dispatch("open file report.pdf")
    mock_file.assert_called_once_with("report.pdf")
    assert result is not None


def test_unknown_command_returns_none(dispatcher: CommandDispatcher) -> None:
    result = dispatcher.dispatch("this is nonsense blah blah")
    assert result is None


def test_open_folder_not_matched_as_launch(dispatcher: CommandDispatcher) -> None:
    """'open folder X' must route to open_folder, not launch."""
    with (
        patch.object(dispatcher._files, "open_folder", return_value=True) as mock_folder,
        patch.object(dispatcher._launcher, "launch") as mock_launch,
    ):
        dispatcher.dispatch("open folder Documents")
    mock_folder.assert_called_once()
    mock_launch.assert_not_called()


def test_search_alias(dispatcher: CommandDispatcher) -> None:
    with patch.object(dispatcher._browser, "google", return_value=True) as mock_google:
        result = dispatcher.dispatch("search for best pizza")
    mock_google.assert_called_once_with("best pizza")
    assert result is not None
