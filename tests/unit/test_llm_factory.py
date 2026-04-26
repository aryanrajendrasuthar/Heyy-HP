"""Unit tests for LLM provider factory."""

from __future__ import annotations

import pytest

from app.config.settings import AppSettings
from app.llm.factory import get_provider
from app.llm.stub import StubLLM


def test_stub_provider_returned_by_default() -> None:
    settings = AppSettings()
    provider = get_provider(settings)
    assert isinstance(provider, StubLLM)


def test_stub_provider_explicit() -> None:
    settings = AppSettings(llm_provider="stub")
    provider = get_provider(settings)
    assert isinstance(provider, StubLLM)


def test_unknown_provider_raises() -> None:
    settings = AppSettings(llm_provider="openai")
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_provider(settings)


def test_provider_case_insensitive() -> None:
    settings = AppSettings(llm_provider="STUB")
    provider = get_provider(settings)
    assert isinstance(provider, StubLLM)
