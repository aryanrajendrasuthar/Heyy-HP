"""HP Assistant — application entrypoint."""

from __future__ import annotations

import logging
import sys

from app.config.settings import AppSettings
from app.ui import HPMainWindow, HPTray, create_app
from app.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    settings = AppSettings()
    setup_logging(settings)

    logger.info("HP assistant starting (version 0.1.0, debug=%s)", settings.debug)
    logger.debug("Full config: %s", settings.model_dump())

    app = create_app(settings)

    window = HPMainWindow(settings)
    tray = HPTray(window)
    tray.show()
    window.show()

    logger.info("HP ready")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
