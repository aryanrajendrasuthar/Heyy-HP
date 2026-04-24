"""Unit tests for logging setup."""

from __future__ import annotations

import logging

from app.config.settings import AppSettings
from app.utils.logging import setup_logging


def test_log_directory_is_created(tmp_path):
    settings = AppSettings(log_dir=str(tmp_path / "logs"))
    setup_logging(settings)
    assert (tmp_path / "logs").is_dir()


def test_log_file_is_created(tmp_path):
    settings = AppSettings(log_dir=str(tmp_path / "logs"))
    setup_logging(settings)
    assert (tmp_path / "logs" / "hp.log").exists()


def test_root_logger_level_info(tmp_path):
    settings = AppSettings(log_dir=str(tmp_path / "logs"), log_level="INFO")
    setup_logging(settings)
    assert logging.getLogger().level == logging.INFO


def test_root_logger_level_warning(tmp_path):
    settings = AppSettings(log_dir=str(tmp_path / "logs"), log_level="WARNING")
    setup_logging(settings)
    assert logging.getLogger().level == logging.WARNING


def test_two_handlers_added(tmp_path):
    root = logging.getLogger()
    initial_count = len(root.handlers)
    settings = AppSettings(log_dir=str(tmp_path / "logs"))
    setup_logging(settings)
    assert len(root.handlers) == initial_count + 2  # console + rotating file
