"""Vision pipeline: open webcam, detect hand, identify object, return description."""

from __future__ import annotations

import logging
from typing import Any

from app.config.settings import AppSettings
from app.vision.capture import _CV2_AVAILABLE
from app.vision.capture import capture_frames as _capture_frames
from app.vision.hands import BBox
from app.vision.hands import detect_hand_roi as _detect_hand_roi
from app.vision.identifier import identify_objects as _identify_objects

logger = logging.getLogger(__name__)


class VisionPipeline:
    def __init__(self, settings: AppSettings) -> None:
        self._device = settings.webcam_index
        self._max_frames = settings.vision_max_frames
        self._confidence = settings.vision_confidence

    def identify_hand_object(self) -> str:
        if not _CV2_AVAILABLE:
            return (
                "Vision is not available. "
                "Please install opencv-python and mediapipe to use this feature."
            )
        logger.info("Starting vision capture on device %d", self._device)
        frames = _capture_frames(self._device, self._max_frames)
        if not frames:
            return "I couldn't access the webcam. Please check your camera connection."

        best_frame, hand_roi = self._find_best_frame(frames)
        if best_frame is None:
            return (
                "I couldn't detect a hand in the camera view. "
                "Please hold your hand in front of the camera."
            )
        objects = _identify_objects(best_frame, hand_roi, self._confidence)
        if not objects:
            return (
                "I can see your hand but I couldn't identify what you're holding. "
                "Make sure the object is clearly visible."
            )
        return self._describe(objects, hand_detected=hand_roi is not None)

    def _find_best_frame(self, frames: list[Any]) -> tuple[Any, BBox | None]:
        for frame in frames:
            roi = _detect_hand_roi(frame)
            if roi is not None:
                return frame, roi
        return (frames[-1], None) if frames else (None, None)

    def _describe(self, objects: list[str], *, hand_detected: bool) -> str:
        prefix = "In your hand, I can see" if hand_detected else "I can see"
        if len(objects) == 1:
            return f"{prefix} what appears to be a {objects[0]}."
        main = objects[0]
        rest = " and ".join(objects[1:3])
        return f"{prefix} what appears to be a {main}, along with {rest}."
