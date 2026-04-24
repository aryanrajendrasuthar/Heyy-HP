"""System tray icon — show/hide the main window, quit HP."""


from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon

logger = logging.getLogger(__name__)


def _build_tray_icon() -> QIcon:
    px = QPixmap(32, 32)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#4A90D9"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(1, 1, 30, 30)
    p.setPen(QColor("#FFFFFF"))
    f = QFont("Arial", 14)
    f.setBold(True)
    p.setFont(f)
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "H")
    p.end()
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#89b4fa"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
    painter.setPen(QColor("#1e1e2e"))
    font = painter.font()
    font.setPixelSize(32)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "H")
    painter.end()
    return QIcon(px)


class HPTray(QSystemTrayIcon):
    def __init__(self, window: QMainWindow) -> None:
        super().__init__(_build_tray_icon())
        self._window = window
        self.setToolTip("HP Assistant")
        self._build_menu()
        self.activated.connect(self._on_activated)
        logger.debug("Tray icon initialised")

    def _build_menu(self) -> None:
        menu = QMenu()
        menu.addAction("Show", self._show_window)
        menu.addAction("Hide", self._hide_window)
        menu.addSeparator()
        menu.addAction("Quit", self._quit)
        self.setContextMenu(menu)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self._window.isVisible():
                self._window.hide()
            else:
                self._show_window()

    def _show_window(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _quit(self) -> None:
        from PySide6.QtWidgets import QApplication  # noqa: PLC0415

        QApplication.quit()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self._window.isVisible():
                self._hide_window()
            else:
                self._show_window()
