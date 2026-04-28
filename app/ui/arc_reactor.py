"""Arc reactor logo widget — animated based on assistant state."""

from __future__ import annotations

import math
import random

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

from app.assistant.state import AssistantState


class ArcReactorWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(180, 180)
        self._state = AssistantState.IDLE
        self._angle = 0.0
        self._spikes = [0.0] * 24
        self._pulse = 0.0
        self._pulse_dir = 1.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_state(self, state: AssistantState) -> None:
        self._state = state

    def _tick(self) -> None:
        if self._state in (
            AssistantState.LISTENING,
            AssistantState.FOLLOW_UP,
            AssistantState.WAKE_DETECTED,
        ):
            self._angle = (self._angle + 3.0) % 360.0
            self._pulse += 0.04 * self._pulse_dir
            if self._pulse >= 1.0:
                self._pulse_dir = -1.0
            elif self._pulse <= 0.0:
                self._pulse_dir = 1.0

        elif self._state == AssistantState.PROCESSING:
            self._angle = (self._angle + 5.0) % 360.0
            self._pulse += 0.06 * self._pulse_dir
            if self._pulse >= 1.0:
                self._pulse_dir = -1.0
            elif self._pulse <= 0.0:
                self._pulse_dir = 1.0

        elif self._state == AssistantState.SPEAKING:
            for i in range(len(self._spikes)):
                self._spikes[i] = self._spikes[i] * 0.6 + random.random() * 0.4
                if random.random() < 0.12:
                    self._spikes[i] = random.uniform(0.6, 1.0)

        else:  # IDLE
            self._pulse += 0.008 * self._pulse_dir
            if self._pulse >= 0.25:
                self._pulse_dir = -1.0
            elif self._pulse <= 0.0:
                self._pulse_dir = 1.0

        self.update()

    def paintEvent(self, _event: object) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        R = min(w, h) * 0.46

        if self._state == AssistantState.IDLE:
            self._draw_idle(p, cx, cy, R)
        elif self._state in (
            AssistantState.LISTENING,
            AssistantState.FOLLOW_UP,
            AssistantState.WAKE_DETECTED,
        ):
            self._draw_listening(p, cx, cy, R)
        elif self._state == AssistantState.PROCESSING:
            self._draw_processing(p, cx, cy, R)
        elif self._state == AssistantState.SPEAKING:
            self._draw_speaking(p, cx, cy, R)

        p.end()

    # ── State draw methods ─────────────────────────────────────────────────

    def _draw_idle(self, p: QPainter, cx: float, cy: float, R: float) -> None:
        gray = QColor(60, 70, 85, 160)
        dim = QColor(40, 50, 65, 100)

        # Outer ring
        p.setPen(QPen(gray, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(cx - R, cy - R, R * 2, R * 2))

        # Tick marks
        for i in range(24):
            a = math.radians(i * 15)
            x1 = cx + math.cos(a) * R * 0.88
            y1 = cy + math.sin(a) * R * 0.88
            x2 = cx + math.cos(a) * R
            y2 = cy + math.sin(a) * R
            p.setPen(QPen(gray, 1.0))
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Middle ring
        r2 = R * 0.65
        p.setPen(QPen(dim, 1.0))
        p.drawEllipse(QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2))

        # Inner ring
        r3 = R * 0.38
        p.setPen(QPen(QColor(35, 45, 60, 100), 1.0))
        p.drawEllipse(QRectF(cx - r3, cy - r3, r3 * 2, r3 * 2))

        # Center glow (dim)
        rc = R * 0.18 * (1.0 + self._pulse * 0.15)
        grad = QRadialGradient(cx, cy, rc)
        grad.setColorAt(0.0, QColor(80, 100, 130, 100))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - rc, cy - rc, rc * 2, rc * 2))

        # "HP" text
        p.setPen(QPen(QColor(90, 105, 130, 180)))
        font = p.font()
        font.setPointSize(max(8, int(R * 0.30)))
        font.setBold(True)
        font.setFamily("Consolas")
        p.setFont(font)
        p.drawText(
            QRectF(cx - R * 0.35, cy - R * 0.22, R * 0.70, R * 0.44),
            Qt.AlignmentFlag.AlignCenter,
            "HP",
        )

    def _draw_listening(self, p: QPainter, cx: float, cy: float, R: float) -> None:
        cyan = QColor(0, 212, 255)
        blue = QColor(0, 130, 255)
        cyan_dim = QColor(0, 212, 255, 60)

        # Outer ring (dim base)
        p.setPen(QPen(cyan_dim, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(cx - R, cy - R, R * 2, R * 2))

        # Spinning outer arc
        arc_pen = QPen(cyan, 3.0)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(arc_pen)
        p.drawArc(
            QRectF(cx - R, cy - R, R * 2, R * 2),
            int(self._angle * 16),
            int(240 * 16),
        )

        # Tick marks (rotating)
        for i in range(36):
            a = math.radians(i * 10 + self._angle * 0.5)
            thick = i % 6 == 0
            x1 = cx + math.cos(a) * R * (0.88 if thick else 0.92)
            y1 = cy + math.sin(a) * R * (0.88 if thick else 0.92)
            x2 = cx + math.cos(a) * R
            y2 = cy + math.sin(a) * R
            p.setPen(QPen(cyan if thick else cyan_dim, 1.0))
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Counter-rotating inner arc
        r2 = R * 0.68
        inner_pen = QPen(blue, 2.0)
        inner_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(inner_pen)
        p.drawArc(
            QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2),
            int(-self._angle * 1.5 * 16),
            int(180 * 16),
        )

        # Dashed inner circle
        r3 = R * 0.40
        dash_pen = QPen(QColor(0, 212, 255, 80), 1.0, Qt.PenStyle.DashLine)
        p.setPen(dash_pen)
        p.drawEllipse(QRectF(cx - r3, cy - r3, r3 * 2, r3 * 2))

        # Pulsing center glow
        rc = R * 0.22 * (1.0 + self._pulse * 0.35)
        grad = QRadialGradient(cx, cy, rc)
        grad.setColorAt(0.0, QColor(0, 212, 255, int(200 + self._pulse * 55)))
        grad.setColorAt(0.5, QColor(0, 130, 255, 100))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - rc, cy - rc, rc * 2, rc * 2))

        # "HP" text
        p.setPen(QPen(QColor(0, 212, 255, 230)))
        font = p.font()
        font.setPointSize(max(8, int(R * 0.30)))
        font.setBold(True)
        font.setFamily("Consolas")
        p.setFont(font)
        p.drawText(
            QRectF(cx - R * 0.35, cy - R * 0.22, R * 0.70, R * 0.44),
            Qt.AlignmentFlag.AlignCenter,
            "HP",
        )

    def _draw_processing(self, p: QPainter, cx: float, cy: float, R: float) -> None:
        orange = QColor(255, 160, 0)
        orange_dim = QColor(255, 160, 0, 60)

        # Outer ring
        p.setPen(QPen(orange_dim, 1.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(cx - R, cy - R, R * 2, R * 2))

        # Fast spinning arc
        arc_pen = QPen(orange, 3.0)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(arc_pen)
        p.drawArc(
            QRectF(cx - R, cy - R, R * 2, R * 2),
            int(self._angle * 2 * 16),
            int(120 * 16),
        )

        # Inner spinning arc (opposite)
        r2 = R * 0.62
        inner_pen = QPen(QColor(255, 100, 0), 2.0)
        inner_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(inner_pen)
        p.drawArc(
            QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2),
            int(-self._angle * 3 * 16),
            int(90 * 16),
        )

        # Center glow
        rc = R * 0.20 * (1.0 + self._pulse * 0.30)
        grad = QRadialGradient(cx, cy, rc)
        grad.setColorAt(0.0, QColor(255, 180, 0, 230))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - rc, cy - rc, rc * 2, rc * 2))

        # "HP" text
        p.setPen(QPen(QColor(255, 180, 0, 230)))
        font = p.font()
        font.setPointSize(max(8, int(R * 0.30)))
        font.setBold(True)
        font.setFamily("Consolas")
        p.setFont(font)
        p.drawText(
            QRectF(cx - R * 0.35, cy - R * 0.22, R * 0.70, R * 0.44),
            Qt.AlignmentFlag.AlignCenter,
            "HP",
        )

    def _draw_speaking(self, p: QPainter, cx: float, cy: float, R: float) -> None:
        gold = QColor(255, 215, 0)
        gold_dim = QColor(255, 215, 0, 60)

        # Frequency spikes
        n = len(self._spikes)
        for i, h in enumerate(self._spikes):
            a = math.radians(i * (360.0 / n))
            r_inner = R * 0.40
            r_outer = r_inner + R * 0.48 * h
            x1 = cx + math.cos(a) * r_inner
            y1 = cy + math.sin(a) * r_inner
            x2 = cx + math.cos(a) * r_outer
            y2 = cy + math.sin(a) * r_outer

            if h > 0.7:
                color = QColor(255, 255, 200, int(255 * h))
            elif h > 0.4:
                color = QColor(255, 215, 0, int(255 * h))
            else:
                color = QColor(200, 120, 0, int(220 * h))

            p.setPen(QPen(color, 2.0))
            p.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Outer ring
        p.setPen(QPen(gold, 2.0))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(cx - R, cy - R, R * 2, R * 2))

        # Inner ring
        r3 = R * 0.40
        p.setPen(QPen(gold_dim, 1.5))
        p.drawEllipse(QRectF(cx - r3, cy - r3, r3 * 2, r3 * 2))

        # Center glow
        rc = R * 0.22
        grad = QRadialGradient(cx, cy, rc)
        grad.setColorAt(0.0, QColor(255, 245, 180, 255))
        grad.setColorAt(0.5, QColor(255, 180, 0, 160))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(cx - rc, cy - rc, rc * 2, rc * 2))

        # "HP" text
        p.setPen(QPen(QColor(255, 240, 150, 255)))
        font = p.font()
        font.setPointSize(max(8, int(R * 0.30)))
        font.setBold(True)
        font.setFamily("Consolas")
        p.setFont(font)
        p.drawText(
            QRectF(cx - R * 0.35, cy - R * 0.22, R * 0.70, R * 0.44),
            Qt.AlignmentFlag.AlignCenter,
            "HP",
        )
