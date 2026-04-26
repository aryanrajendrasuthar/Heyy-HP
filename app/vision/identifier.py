"""Object identification using YOLOv8."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO as _YOLO  # type: ignore[import-untyped]

    _YOLO_AVAILABLE = True
except ImportError:
    _YOLO_AVAILABLE = False

_MODEL: Any = None


def _get_model() -> Any:
    global _MODEL  # noqa: PLW0603
    if _MODEL is None and _YOLO_AVAILABLE:
        try:
            _MODEL = _YOLO("yolov8n.pt")
            logger.info("YOLOv8n model loaded")
        except Exception:
            logger.exception("Failed to load YOLOv8 model")
    return _MODEL


BBox = tuple[int, int, int, int]  # x, y, w, h


def identify_objects(
    frame: Any,
    roi: BBox | None,
    confidence: float = 0.4,
) -> list[str]:
    """Return detected object class names in/near the hand roi."""
    model = _get_model()
    if model is None or frame is None:
        return []
    try:
        results = model(frame, verbose=False)
        names: list[str] = []
        for result in results:
            for box in result.boxes:
                conf = float(box.conf[0])
                if conf < confidence:
                    continue
                cls_id = int(box.cls[0])
                name: str = result.names[cls_id]
                if roi is not None:
                    bx1, by1, bx2, by2 = (float(v) for v in box.xyxy[0])
                    rx, ry, rw, rh = roi
                    if bx2 < rx or bx1 > rx + rw or by2 < ry or by1 > ry + rh:
                        continue
                if name not in names:
                    names.append(name)
        return names
    except Exception:
        logger.exception("Object identification failed")
        return []
