"""Unit tests for AppSettings."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import AppSettings


def test_defaults():
    s = AppSettings()
    assert s.app_name == "HP"
    assert s.wake_phrase == "Hey HP"
    assert s.follow_up_timeout_s == 10
    assert s.audio_sample_rate == 16000
    assert s.debug is False
    assert s.audio_device_index is None
    assert s.log_level == "INFO"
    assert s.db_path == "data/hp.db"


def test_env_prefix_overrides(monkeypatch):
    monkeypatch.setenv("HP_DEBUG", "true")
    monkeypatch.setenv("HP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("HP_FOLLOW_UP_TIMEOUT_S", "15")
    s = AppSettings()
    assert s.debug is True
    assert s.log_level == "DEBUG"
    assert s.follow_up_timeout_s == 15


def test_constructor_kwargs_override_env(monkeypatch):
    monkeypatch.setenv("HP_LOG_LEVEL", "ERROR")
    s = AppSettings(log_level="WARNING")
    assert s.log_level == "WARNING"


def test_follow_up_timeout_must_be_positive(monkeypatch):
    monkeypatch.setenv("HP_FOLLOW_UP_TIMEOUT_S", "0")
    with pytest.raises(ValidationError):
        AppSettings()


def test_follow_up_timeout_negative_rejected(monkeypatch):
    monkeypatch.setenv("HP_FOLLOW_UP_TIMEOUT_S", "-5")
    with pytest.raises(ValidationError):
        AppSettings()


def test_audio_sample_rate_must_be_positive(monkeypatch):
    monkeypatch.setenv("HP_AUDIO_SAMPLE_RATE", "0")
    with pytest.raises(ValidationError):
        AppSettings()


def test_audio_device_index_optional_none_by_default():
    s = AppSettings()
    assert s.audio_device_index is None


def test_audio_device_index_can_be_set(monkeypatch):
    monkeypatch.setenv("HP_AUDIO_DEVICE_INDEX", "2")
    s = AppSettings()
    assert s.audio_device_index == 2
