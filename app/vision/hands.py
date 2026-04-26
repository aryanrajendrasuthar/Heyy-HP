"""Hand ROI detection using MediaPipe."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

BBox = tuple[int, int, int, int]  # x, y, w, h

try:
    import mediapipe as _mp

    _MP_AVAILABLE = True
except ImportError:
    _MP_AVAILABLE = False


def detect_hand_roi(frame: Any) -> BBox | None:
    """Return (x, y, w, h) bounding box of the first detected hand, or None."""
    if not _MP_AVAILABLE or frame is None:
        return None
    try:
        h, w = frame.shape[:2]
        rgb = frame[:, :, ::-1].copy()  # BGR → RGB
        with _mp.solutions.hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.6,
        ) as detector:
            result = detector.process(rgb)
        if not result.multi_hand_landmarks:
            return None
        landmarks = result.multi_hand_landmarks[0].landmark
        xs = [lm.x * w for lm in landmarks]
        ys = [lm.y * h for lm in landmarks]
        pad = 30
        x1 = max(0, int(min(xs)) - pad)
        y1 = max(0, int(min(ys)) - pad)
        x2 = min(w, int(max(xs)) + pad)
        y2 = min(h, int(max(ys)) + pad)
        return (x1, y1, x2 - x1, y2 - y1)
    except Exception:
        logger.exception("Hand detection failed")
        return None
