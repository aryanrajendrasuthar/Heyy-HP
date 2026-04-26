"""Webcam frame capture."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import cv2 as _cv2

    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


def capture_frames(device: int, n: int) -> list[Any]:
    """Capture up to n BGR frames from webcam device index."""
    if not _CV2_AVAILABLE:
        return []
    cap = _cv2.VideoCapture(device)
    if not cap.isOpened():
        logger.warning("Could not open webcam device %d", device)
        return []
    frames: list[Any] = []
    try:
        for _ in range(n):
            ret, frame = cap.read()
            if ret and frame is not None:
                frames.append(frame)
    except Exception:
        logger.exception("Error during frame capture")
    finally:
        cap.release()
    return frames
