"""Shared pytest fixtures for all test suites."""

from __future__ import annotations

import logging

import pytest


@pytest.fixture(autouse=True)
def reset_root_logger():
    """Restore root logger state after each test.

    Prevents handler accumulation when tests call setup_logging() directly.
    """
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    yield
    root.handlers = original_handlers
    root.level = original_level
