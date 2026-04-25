"""System tray icon — show/hide the main window, quit HP."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon

logger = logging.getLogger(__name__)


def _build_tray_icon() -> QIcon:
    px = QPixmap(64, 64)
    px.fill(Qt.GlobalColor.transparent)
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

    def _show_window(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _hide_window(self) -> None:
        self._window.hide()

    def _quit(self) -> None:

        QApplication.quit()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self._window.isVisible():
                self._hide_window()
            else:
                self._show_window()
