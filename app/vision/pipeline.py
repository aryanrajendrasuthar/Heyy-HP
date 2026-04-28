"""Vision pipeline: capture a webcam frame and describe it via Claude vision API."""

from __future__ import annotations

import base64
import logging
import threading

from app.config.settings import AppSettings

logger = logging.getLogger(__name__)


class VisionPipeline:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._device = settings.webcam_index

    def identify_hand_object(self) -> str:
        """Capture one webcam frame and ask Claude to describe what's visible."""
        frame_b64 = self._capture_frame()
        if frame_b64 is None:
            return "I couldn't access the webcam. Please check your camera connection."
        return self._describe_with_llm(frame_b64)

    def _capture_frame(self) -> str | None:
        """Open the webcam, grab one frame, return it as a base64-encoded JPEG string."""
        try:
            import cv2  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("opencv-python not installed — vision disabled")
            return None

        cap = cv2.VideoCapture(self._device)
        if not cap.isOpened():
            logger.warning("Could not open webcam device %d", self._device)
            return None
        try:
            # Discard a couple of frames so auto-exposure can settle
            for _ in range(3):
                cap.read()
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.warning("Webcam read failed")
                return None

            # Resize to ≤640 px wide to keep Claude API payload small
            h, w = frame.shape[:2]
            if w > 640:
                scale = 640.0 / w
                frame = cv2.resize(frame, (640, int(h * scale)))

            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ok:
                return None
            return base64.b64encode(buf.tobytes()).decode()
        finally:
            cap.release()

    def _describe_with_llm(self, frame_b64: str) -> str:
        """Send the frame to Claude Haiku and return a brief description."""
        api_key = self._settings.anthropic_api_key
        if not api_key:
            return (
                "Vision analysis requires an Anthropic API key. "
                "Add HP_ANTHROPIC_API_KEY to your .env file."
            )
        try:
            import anthropic  # type: ignore[import-untyped]

            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=120,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": frame_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Describe what you see in this webcam photo in two sentences max. "
                                    "Focus on what the person is holding if anything. "
                                    "Be direct and conversational — no markdown."
                                ),
                            },
                        ],
                    }
                ],
            )
            return msg.content[0].text.strip()
        except Exception:
            logger.exception("Vision LLM call failed")
            return "I captured a photo but couldn't analyse it right now."
