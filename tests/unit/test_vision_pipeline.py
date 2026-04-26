"""Unit tests for VisionPipeline."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.config.settings import AppSettings
from app.vision.pipeline import VisionPipeline


@pytest.fixture()
def pipeline() -> VisionPipeline:
    return VisionPipeline(AppSettings())


def test_returns_not_available_when_cv2_missing(pipeline: VisionPipeline) -> None:
    with patch("app.vision.pipeline._CV2_AVAILABLE", False):
        result = pipeline.identify_hand_object()
    assert "not available" in result.lower()


def test_returns_camera_error_when_no_frames(pipeline: VisionPipeline) -> None:
    with (
        patch("app.vision.pipeline._CV2_AVAILABLE", True),
        patch("app.vision.pipeline._capture_frames", return_value=[]),
    ):
        result = pipeline.identify_hand_object()
    assert "webcam" in result.lower() or "camera" in result.lower()


def test_returns_no_hand_when_hand_not_detected(pipeline: VisionPipeline) -> None:
    fake_frame = object()
    with (
        patch("app.vision.pipeline._CV2_AVAILABLE", True),
        patch("app.vision.pipeline._capture_frames", return_value=[fake_frame]),
        patch("app.vision.pipeline._detect_hand_roi", return_value=None),
        patch("app.vision.pipeline._identify_objects", return_value=[]),
    ):
        result = pipeline.identify_hand_object()
    assert "hand" in result.lower()


def test_returns_cannot_identify_when_no_objects(pipeline: VisionPipeline) -> None:
    fake_frame = object()
    with (
        patch("app.vision.pipeline._CV2_AVAILABLE", True),
        patch("app.vision.pipeline._capture_frames", return_value=[fake_frame]),
        patch("app.vision.pipeline._detect_hand_roi", return_value=(0, 0, 100, 100)),
        patch("app.vision.pipeline._identify_objects", return_value=[]),
    ):
        result = pipeline.identify_hand_object()
    assert "identify" in result.lower() or "couldn't" in result.lower()


def test_describes_single_object(pipeline: VisionPipeline) -> None:
    fake_frame = object()
    with (
        patch("app.vision.pipeline._CV2_AVAILABLE", True),
        patch("app.vision.pipeline._capture_frames", return_value=[fake_frame]),
        patch("app.vision.pipeline._detect_hand_roi", return_value=(0, 0, 100, 100)),
        patch("app.vision.pipeline._identify_objects", return_value=["pen"]),
    ):
        result = pipeline.identify_hand_object()
    assert "pen" in result
    assert "hand" in result.lower()


def test_describes_multiple_objects(pipeline: VisionPipeline) -> None:
    fake_frame = object()
    with (
        patch("app.vision.pipeline._CV2_AVAILABLE", True),
        patch("app.vision.pipeline._capture_frames", return_value=[fake_frame]),
        patch("app.vision.pipeline._detect_hand_roi", return_value=(0, 0, 100, 100)),
        patch("app.vision.pipeline._identify_objects", return_value=["phone", "earbuds"]),
    ):
        result = pipeline.identify_hand_object()
    assert "phone" in result
    assert "earbuds" in result


def test_uses_last_frame_when_no_hand_in_any_frame(pipeline: VisionPipeline) -> None:
    frames = [object(), object(), object()]
    with (
        patch("app.vision.pipeline._CV2_AVAILABLE", True),
        patch("app.vision.pipeline._capture_frames", return_value=frames),
        patch("app.vision.pipeline._detect_hand_roi", return_value=None),
        patch("app.vision.pipeline._identify_objects", return_value=["bottle"]) as mock_id,
    ):
        pipeline.identify_hand_object()
    # Last frame passed to identify_objects, no roi
    call_args = mock_id.call_args
    assert call_args[0][0] is frames[-1]
    assert call_args[0][1] is None
