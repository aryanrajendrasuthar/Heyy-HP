"""Open files and folders using the OS default handler."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class FileActions:
    def open_file(self, path: str) -> bool:
        try:
            if hasattr(os, "startfile"):
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path])  # noqa: S603, S607
            logger.info("Opened file: %s", path)
            return True
        except Exception:
            logger.exception("Failed to open file %s", path)
            return False

    def open_folder(self, folder: str) -> bool:
        path = Path(folder).expanduser()
        try:
            if hasattr(os, "startfile"):
                os.startfile(str(path))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(path)])  # noqa: S603, S607
            logger.info("Opened folder: %s", path)
            return True
        except Exception:
            logger.exception("Failed to open folder %s", folder)
            return False
