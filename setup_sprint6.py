"""Write all Sprint 6 files to disk."""

from pathlib import Path

BASE = Path(r"d:\My Career\Projects\HP-AI assistant")
files: dict[str, str] = {}

# ── app/__version__.py ────────────────────────────────────────────────────
files["app/__version__.py"] = r'''"""HP Assistant version metadata."""

__version__ = "1.0.0"
__author__ = "Aryan Rajendra Suthar"
__app_name__ = "HP"
'''

# ── app/services/startup.py ───────────────────────────────────────────────
files[
    "app/services/startup.py"
] = r'''"""Windows startup registration via the HKCU Run registry key."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import winreg as _winreg

    _WINREG_AVAILABLE = True
except ImportError:
    _WINREG_AVAILABLE = False

_STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "HP-Assistant"


def _default_exe_path() -> str:
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle — executable is self-contained
        return f'"{sys.executable}"'
    main_py = (Path(__file__).parent.parent.parent / "main.py").resolve()
    return f'"{sys.executable}" "{main_py}"'


def is_registered() -> bool:
    if not _WINREG_AVAILABLE:
        return False
    try:
        with _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, _STARTUP_KEY) as key:
            _winreg.QueryValueEx(key, _APP_NAME)
            return True
    except OSError:
        return False


def register(exe_path: str | None = None) -> bool:
    if not _WINREG_AVAILABLE:
        logger.warning("winreg not available — startup registration skipped")
        return False
    path = exe_path or _default_exe_path()
    try:
        with _winreg.OpenKey(
            _winreg.HKEY_CURRENT_USER, _STARTUP_KEY, 0, _winreg.KEY_SET_VALUE
        ) as key:
            _winreg.SetValueEx(key, _APP_NAME, 0, _winreg.REG_SZ, path)
        logger.info("Registered startup: %s", path)
        return True
    except OSError:
        logger.exception("Failed to register startup")
        return False


def unregister() -> bool:
    if not _WINREG_AVAILABLE:
        return False
    try:
        with _winreg.OpenKey(
            _winreg.HKEY_CURRENT_USER, _STARTUP_KEY, 0, _winreg.KEY_SET_VALUE
        ) as key:
            _winreg.DeleteValue(key, _APP_NAME)
        logger.info("Unregistered startup")
        return True
    except OSError:
        return False
'''

# ── hp.spec ───────────────────────────────────────────────────────────────
files["hp.spec"] = r'''# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for HP Assistant — single-folder distribution."""

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "pydantic",
        "pydantic_settings",
        "pydantic_settings.env_settings",
        "PySide6.QtWidgets",
        "PySide6.QtGui",
        "PySide6.QtCore",
        "app.assistant",
        "app.actions",
        "app.config",
        "app.llm",
        "app.memory",
        "app.services",
        "app.ui",
        "app.utils",
        "app.vision",
        "app.voice",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="HP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="HP",
)
'''

# ── build_windows.py ──────────────────────────────────────────────────────
files[
    "build_windows.py"
] = r'''"""Build HP Assistant into a distributable Windows folder via PyInstaller."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    spec = Path(__file__).parent / "hp.spec"
    if not spec.exists():
        print(f"ERROR: spec file not found at {spec}")
        sys.exit(1)

    print("Building HP Assistant…")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec), "--clean", "--noconfirm"],
        check=True,
    )
    dist = Path(__file__).parent / "dist" / "HP"
    print(f"\nBuild complete → {dist}")
    print("Run: dist\\HP\\HP.exe")


if __name__ == "__main__":
    main()
'''

# ── app/ui/tray.py (updated: Start on boot toggle) ────────────────────────
files[
    "app/ui/tray.py"
] = r'''"""System tray icon — show/hide the main window, startup toggle, quit HP."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon

from app.services import startup as _startup

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
        self._startup_action = menu.addAction("Start on boot")
        self._startup_action.setCheckable(True)
        self._startup_action.setChecked(_startup.is_registered())
        self._startup_action.triggered.connect(self._toggle_startup)
        menu.addSeparator()
        menu.addAction("Quit", self._quit)
        self.setContextMenu(menu)

    def _show_window(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _hide_window(self) -> None:
        self._window.hide()

    def _toggle_startup(self, checked: bool) -> None:
        if checked:
            _startup.register()
        else:
            _startup.unregister()

    def _quit(self) -> None:
        QApplication.quit()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self._window.isVisible():
                self._hide_window()
            else:
                self._show_window()
'''

# ── app/ui/main_window.py (updated: version in About) ────────────────────
files[
    "app/ui/main_window.py"
] = r'''"""HP main window — conversation history, state display, dark theme."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.__version__ import __version__
from app.assistant.state import AssistantState
from app.config.settings import AppSettings
from app.ui.settings_panel import SettingsDialog

logger = logging.getLogger(__name__)

_DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: Segoe UI, sans-serif;
}
QLabel#state      { font-size: 16px; font-weight: bold; }
QLabel#transcript { font-size: 12px; color: #a6e3a1; }
QLabel#response   { font-size: 12px; color: #cdd6f4; }
QTextEdit#history {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    font-size: 12px;
    font-family: Segoe UI, sans-serif;
}
QMenuBar { background-color: #181825; color: #cdd6f4; }
QMenuBar::item:selected { background-color: #313244; }
QMenu { background-color: #181825; color: #cdd6f4; }
QMenu::item:selected  { background-color: #313244; }
"""

_STATE_COLORS: dict[AssistantState, str] = {
    AssistantState.IDLE:          "#6c7086",
    AssistantState.WAKE_DETECTED: "#f9e2af",
    AssistantState.LISTENING:     "#a6e3a1",
    AssistantState.PROCESSING:    "#89dceb",
    AssistantState.SPEAKING:      "#89b4fa",
    AssistantState.FOLLOW_UP:     "#cba6f7",
}


class HPMainWindow(QMainWindow):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle(settings.app_name)
        self.setMinimumSize(480, 260)
        self.setStyleSheet(_DARK_STYLE)
        self._build_menu()
        self._build_body()
        self.set_state(AssistantState.IDLE)

    def _build_menu(self) -> None:
        bar = QMenuBar(self)
        self.setMenuBar(bar)

        file_menu = QMenu("&File", self)
        file_menu.addAction("Settings", self._open_settings)
        file_menu.addAction("Clear History", self._clear_history)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close)
        bar.addMenu(file_menu)

        help_menu = QMenu("&Help", self)
        help_menu.addAction("About", self._show_about)
        bar.addMenu(help_menu)

    def _build_body(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(8)

        self._state_label = QLabel("IDLE")
        self._state_label.setObjectName("state")

        self._transcript_label = QLabel("")
        self._transcript_label.setObjectName("transcript")
        self._transcript_label.setWordWrap(True)

        self._response_label = QLabel("")
        self._response_label.setObjectName("response")
        self._response_label.setWordWrap(True)

        self._history_edit = QTextEdit()
        self._history_edit.setObjectName("history")
        self._history_edit.setReadOnly(True)
        self._history_edit.setMinimumHeight(100)

        layout.addWidget(self._state_label)
        layout.addWidget(self._transcript_label)
        layout.addWidget(self._response_label)
        layout.addWidget(self._history_edit, stretch=1)

        self.setCentralWidget(container)

    # ── Public API ────────────────────────────────────────────────────────

    def set_state(self, state: AssistantState) -> None:
        self._state_label.setText(state.name)
        color = _STATE_COLORS.get(state, "#cdd6f4")
        self._state_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {color};"
        )

    def set_transcript(self, text: str) -> None:
        self._transcript_label.setText(f"You: {text}")

    def set_response(self, text: str) -> None:
        self._response_label.setText(f"HP: {text}")
        transcript = self._transcript_label.text()
        if transcript:
            self._append_history(transcript, f"HP: {text}")

    def clear(self) -> None:
        self._transcript_label.setText("")
        self._response_label.setText("")

    # ── Private helpers ───────────────────────────────────────────────────

    def _append_history(self, transcript: str, response: str) -> None:
        you_color = "#a6e3a1"
        hp_color = "#89b4fa"
        html = (
            f'<p style="margin:4px 0">'
            f'<span style="color:{you_color}">{transcript}</span><br>'
            f'<span style="color:{hp_color}">{response}</span>'
            f"</p>"
        )
        self._history_edit.append(html)

    def _clear_history(self) -> None:
        self._history_edit.clear()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._settings, self)
        dialog.exec()

    def _show_about(self) -> None:
        from PySide6.QtWidgets import QMessageBox  # noqa: PLC0415

        QMessageBox.about(
            self,
            "About HP",
            f"{self._settings.app_name} — local desktop voice assistant\nVersion {__version__}",
        )
'''

# ── app/ui/settings_panel.py (updated: startup checkbox) ─────────────────
files[
    "app/ui/settings_panel.py"
] = r'''"""Settings dialog — read-only view of AppSettings with runtime overrides."""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import AppSettings
from app.services import startup as _startup

_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self._build()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        form = QFormLayout()
        outer.addLayout(form)

        fields = {
            "App name": self._settings.app_name,
            "Debug": str(self._settings.debug),
            "Wake phrase": self._settings.wake_phrase,
            "Follow-up timeout (s)": str(self._settings.follow_up_timeout_s),
            "Audio sample rate": str(self._settings.audio_sample_rate),
            "Audio device index": str(self._settings.audio_device_index),
            "Wake word model": self._settings.wake_word_model,
            "STT model": self._settings.whisper_model,
            "STT device": self._settings.stt_device,
            "TTS rate": str(self._settings.tts_rate),
            "TTS volume": str(self._settings.tts_volume),
            "Log dir": self._settings.log_dir,
            "DB path": self._settings.db_path,
        }

        for label_text, value in fields.items():
            form.addRow(QLabel(label_text), QLabel(value))

        self._level_combo = QComboBox()
        self._level_combo.addItems(_LOG_LEVELS)
        current_name = logging.getLevelName(logging.getLogger().level)
        idx = self._level_combo.findText(current_name)
        self._level_combo.setCurrentIndex(idx if idx >= 0 else _LOG_LEVELS.index("INFO"))
        form.addRow(QLabel("Log level (runtime)"), self._level_combo)
        self._level_combo.currentTextChanged.connect(self._on_level_changed)

        self._startup_cb = QCheckBox("Start HP on Windows boot")
        self._startup_cb.setChecked(_startup.is_registered())
        self._startup_cb.toggled.connect(self._on_startup_toggled)
        outer.addWidget(self._startup_cb)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _on_level_changed(self, level_name: str) -> None:
        logging.getLogger().setLevel(level_name)

    def _on_startup_toggled(self, checked: bool) -> None:
        if checked:
            _startup.register()
        else:
            _startup.unregister()
'''

# ── requirements/prod.txt (updated: Sprint 3-5 optional deps) ────────────
files[
    "requirements/prod.txt"
] = r"""# Production dependencies — install with: pip install -r requirements/prod.txt
-r base.txt

# Desktop UI (Sprint 1)
pyside6>=6.7.0

# Local API / orchestration (Sprint 1)
fastapi>=0.111.0
uvicorn[standard]>=0.30.0

# Speech-to-text (Sprint 2)
faster-whisper>=1.0.0

# Wake-word detection (Sprint 2)
openwakeword>=0.6.0

# Microphone capture (Sprint 2)
pyaudio>=0.2.14

# Text-to-speech (Sprint 2)
pyttsx3>=2.90

# Vision — hand tracking + object recognition (Sprint 5, optional)
# Uncomment to enable "what's in my hand" command:
# opencv-python>=4.9.0
# mediapipe>=0.10.0
# ultralytics>=8.0.0
"""

# ── requirements/dev.txt (updated: add pyinstaller) ───────────────────────
files[
    "requirements/dev.txt"
] = r"""# Development + testing — install with: pip install -r requirements/dev.txt
-r base.txt

ruff>=0.4.0
pytest>=8.0.0
pytest-mock>=3.14.0
pytest-qt>=4.4.0
pytest-cov>=5.0.0

# Packaging (Sprint 6)
pyinstaller>=6.0.0
"""

# ── pyproject.toml patch ─ written separately via Edit below ─────────────

# ── tests/unit/test_services_startup.py ──────────────────────────────────
files[
    "tests/unit/test_services_startup.py"
] = r'''"""Unit tests for Windows startup registration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.services.startup as startup_mod


@pytest.fixture()
def winreg_mock() -> MagicMock:
    mock = MagicMock()
    mock.HKEY_CURRENT_USER = "HKCU"
    mock.KEY_SET_VALUE = 0x0002
    mock.REG_SZ = 1
    with (
        patch.object(startup_mod, "_WINREG_AVAILABLE", True),
        patch.object(startup_mod, "_winreg", mock),
    ):
        yield mock


def test_is_registered_returns_false_when_winreg_unavailable() -> None:
    with patch.object(startup_mod, "_WINREG_AVAILABLE", False):
        assert startup_mod.is_registered() is False


def test_register_returns_false_when_winreg_unavailable() -> None:
    with patch.object(startup_mod, "_WINREG_AVAILABLE", False):
        assert startup_mod.register("hp.exe") is False


def test_unregister_returns_false_when_winreg_unavailable() -> None:
    with patch.object(startup_mod, "_WINREG_AVAILABLE", False):
        assert startup_mod.unregister() is False


def test_is_registered_true_when_key_exists(winreg_mock: MagicMock) -> None:
    winreg_mock.QueryValueEx.return_value = ("hp.exe", 1)
    assert startup_mod.is_registered() is True
    winreg_mock.OpenKey.assert_called_once()


def test_is_registered_false_when_key_missing(winreg_mock: MagicMock) -> None:
    winreg_mock.OpenKey.side_effect = OSError("key not found")
    assert startup_mod.is_registered() is False


def test_register_calls_set_value(winreg_mock: MagicMock) -> None:
    result = startup_mod.register("C:\\HP\\HP.exe")
    assert result is True
    winreg_mock.SetValueEx.assert_called_once()
    call_args = winreg_mock.SetValueEx.call_args[0]
    assert "HP-Assistant" in call_args
    assert "C:\\HP\\HP.exe" in call_args


def test_register_returns_false_on_os_error(winreg_mock: MagicMock) -> None:
    winreg_mock.OpenKey.side_effect = OSError("access denied")
    assert startup_mod.register("hp.exe") is False


def test_unregister_calls_delete_value(winreg_mock: MagicMock) -> None:
    result = startup_mod.unregister()
    assert result is True
    winreg_mock.DeleteValue.assert_called_once()


def test_unregister_returns_false_on_os_error(winreg_mock: MagicMock) -> None:
    winreg_mock.OpenKey.side_effect = OSError("not found")
    assert startup_mod.unregister() is False


def test_version_is_1_0_0() -> None:
    from app.__version__ import __version__

    assert __version__ == "1.0.0"
'''

# ── Write all files ───────────────────────────────────────────────────────
for rel, content in files.items():
    path = BASE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")
    print(f"  wrote {rel}")

print("\nSprint 6 setup complete.")
