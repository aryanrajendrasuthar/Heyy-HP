"""Unit tests for StubLLM."""

from __future__ import annotations

from app.llm.stub import StubLLM


def test_stub_returns_heard_you_say() -> None:
    llm = StubLLM()
    result = llm.chat("hello world")
    assert result == "I heard you say: hello world"


def test_stub_preserves_prompt_verbatim() -> None:
    llm = StubLLM()
    prompt = "What is the capital of France?"
    result = llm.chat(prompt)
    assert prompt in result


def test_stub_empty_prompt() -> None:
    llm = StubLLM()
    result = llm.chat("")
    assert isinstance(result, str)


def test_stub_implements_llm_provider() -> None:
    from app.llm.base import LLMProvider

    assert isinstance(StubLLM(), LLMProvider)
