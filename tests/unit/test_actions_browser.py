"""Unit tests for BrowserRouter."""

from __future__ import annotations

from unittest.mock import patch

from app.actions.browser import BrowserRouter


def test_open_url_returns_true() -> None:
    router = BrowserRouter()
    with patch("app.actions.browser.webbrowser.open") as mock_open:
        result = router.open_url("https://example.com")
    assert result is True
    mock_open.assert_called_once_with("https://example.com")


def test_open_url_returns_false_on_exception() -> None:
    router = BrowserRouter()
    with patch("app.actions.browser.webbrowser.open", side_effect=OSError):
        result = router.open_url("https://example.com")
    assert result is False


def test_google_builds_correct_url() -> None:
    router = BrowserRouter()
    with patch("app.actions.browser.webbrowser.open") as mock_open:
        router.google("python tutorial")
    url = mock_open.call_args[0][0]
    assert "google.com/search" in url
    assert "python+tutorial" in url or "python%20tutorial" in url


def test_youtube_builds_correct_url() -> None:
    router = BrowserRouter()
    with patch("app.actions.browser.webbrowser.open") as mock_open:
        router.youtube("lo fi music")
    url = mock_open.call_args[0][0]
    assert "youtube.com/results" in url
    assert "lo" in url
