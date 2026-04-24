"""HP Assistant — application entrypoint.

Boots configuration and logging, then hands off to the application runtime.
UI and service wiring are added in subsequent Sprint 1 branches.
"""

from __future__ import annotations

import logging
import sys

from app.config.settings import AppSettings
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    settings = AppSettings()
    setup_logging(settings)

    logger.info("HP assistant starting (version 0.1.0, debug=%s)", settings.debug)
    logger.debug("Full config: %s", settings.model_dump())

    # Voice runtime, UI shell, and action engine boot here in later branches.
    logger.info("HP ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
