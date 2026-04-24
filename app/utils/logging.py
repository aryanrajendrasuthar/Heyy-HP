"""Logging factory: rotating file handler + stderr console, driven by AppSettings."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from app.config.settings import AppSettings

_FMT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_DATE_FMT = "%Y-%m-%dT%H:%M:%S"


def setup_logging(settings: AppSettings) -> None:
    """Configure the root logger.

    Safe to call once at application startup. Tests should reset root logger
    handlers via the shared fixture in conftest.py.
    """
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    rotating_file = logging.handlers.RotatingFileHandler(
        log_dir / "hp.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB per file
        backupCount=3,
        encoding="utf-8",
    )
    rotating_file.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    root.addHandler(console)
    root.addHandler(rotating_file)
