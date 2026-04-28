"""HP main window — JARVIS-style HUD interface."""

from __future__ import annotations

import logging
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.__version__ import __version__
from app.assistant.state import AssistantState
from app.config.settings import AppSettings
from app.ui.arc_reactor import ArcReactorWidget
from app.ui.settings_panel import SettingsDialog

if TYPE_CHECKING:
    from app.memory.memories import MemoryRepository
    from app.memory.reminders import ReminderRepository
    from app.memory.tasks import TaskRepository

logger = logging.getLogger(__name__)

# ── HUD color tokens ───────────────────────────────────────────────────────
_BG = "#03080F"
_PANEL_BG = "#060D1A"
_TOPBAR_BG = "#040A14"
_CYAN = "#00D4FF"
_BLUE = "#0096FF"
_GOLD = "#FFD700"
_ORANGE = "#FFA500"
_TEXT = "#A0C8D8"
_DIM = "#2A4A5A"
_BORDER_DIM = "rgba(0,212,255,0.18)"

_STATE_COLORS: dict[AssistantState, str] = {
    AssistantState.IDLE:          "#2A5060",
    AssistantState.WAKE_DETECTED: _GOLD,
    AssistantState.LISTENING:     "#00FF8A",
    AssistantState.PROCESSING:    _ORANGE,
    AssistantState.SPEAKING:      _GOLD,
    AssistantState.FOLLOW_UP:     _CYAN,
}

_HUD_STYLE = f"""
QMainWindow, QWidget {{
    background-color: {_BG};
    color: {_CYAN};
    font-family: 'Consolas', 'Courier New', monospace;
}}
QMenuBar {{
    background-color: {_TOPBAR_BG};
    color: {_CYAN};
    border-bottom: 1px solid {_BORDER_DIM};
    font-size: 11px;
    padding: 2px;
}}
QMenuBar::item:selected {{ background-color: #0A1A2A; }}
QMenu {{
    background-color: {_TOPBAR_BG};
    color: {_CYAN};
    border: 1px solid {_BORDER_DIM};
}}
QMenu::item:selected {{ background-color: #0A1A2A; }}
QTextEdit#history {{
    background-color: {_TOPBAR_BG};
    color: {_TEXT};
    border: 1px solid {_BORDER_DIM};
    font-size: 11px;
    selection-background-color: #0A2A3A;
}}
QScrollBar:vertical {{
    background: {_TOPBAR_BG};
    width: 4px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {_DIM};
    border-radius: 2px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {_TOPBAR_BG};
    height: 4px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {_DIM};
    border-radius: 2px;
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
"""


def _app_icon() -> QIcon | None:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent.parent))
    ico = base / "hp.ico"
    return QIcon(str(ico)) if ico.exists() else None


class HPMainWindow(QMainWindow):
    def __init__(
        self,
        settings: AppSettings,
        tasks: TaskRepository | None = None,
        memories: MemoryRepository | None = None,
        reminders: ReminderRepository | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._tasks = tasks
        self._memories = memories
        self._reminders = reminders
        self._manual_trigger: object = None

        self.setWindowTitle(settings.app_name)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(_HUD_STYLE)
        icon = _app_icon()
        if icon:
            self.setWindowIcon(icon)

        self._build_menu()
        self._build_body()
        self.set_state(AssistantState.IDLE)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

        # Refresh panels every 5 s
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_panels)
        self._refresh_timer.start(5000)

    # ── Menu ──────────────────────────────────────────────────────────────

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

    # ── Body layout ───────────────────────────────────────────────────────

    def _build_body(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_top_bar())
        root.addWidget(self._hline())

        hud = QWidget()
        hud_row = QHBoxLayout(hud)
        hud_row.setContentsMargins(0, 0, 0, 0)
        hud_row.setSpacing(0)

        hud_row.addWidget(self._build_left_panel())
        hud_row.addWidget(self._vline())
        hud_row.addWidget(self._build_center_panel(), stretch=1)
        hud_row.addWidget(self._vline())
        hud_row.addWidget(self._build_right_panel())

        root.addWidget(hud, stretch=1)
        self.setCentralWidget(central)

    # ── Top bar ───────────────────────────────────────────────────────────

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(46)
        bar.setStyleSheet(f"background: {_TOPBAR_BG};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 4, 20, 4)

        title = QLabel("H P   A S S I S T A N T")
        title.setStyleSheet(
            f"font-size: 18px; font-weight: bold; letter-spacing: 5px; color: {_CYAN}; background: transparent;"
        )

        self._state_label = QLabel(f"◆  IDLE  ◆")
        self._state_label.setStyleSheet(
            f"font-size: 10px; letter-spacing: 3px; color: {_DIM}; background: transparent;"
        )

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self._state_label)
        return bar

    # ── Left panel ────────────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(270)
        panel.setStyleSheet(f"background: {_TOPBAR_BG};")

        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        content = QWidget()
        content.setStyleSheet(f"background: {_TOPBAR_BG};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Clock
        clock_frame = self._panel_frame("CLOCK")
        self._clock_label = QLabel("--:--:--")
        self._clock_label.setStyleSheet(
            f"font-size: 26px; font-weight: bold; color: {_CYAN}; letter-spacing: 2px; background: transparent;"
        )
        self._clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._date_label = QLabel("--- ---, ----")
        self._date_label.setStyleSheet(
            f"font-size: 11px; color: {_TEXT}; letter-spacing: 1px; background: transparent;"
        )
        self._date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clock_frame.layout().addWidget(self._clock_label)
        clock_frame.layout().addWidget(self._date_label)
        layout.addWidget(clock_frame)

        # Reminders
        remind_frame = self._panel_frame("REMINDERS")
        self._reminders_label = QLabel("No upcoming reminders")
        self._reminders_label.setStyleSheet(
            f"font-size: 11px; color: {_TEXT}; background: transparent;"
        )
        self._reminders_label.setWordWrap(True)
        remind_frame.layout().addWidget(self._reminders_label)
        layout.addWidget(remind_frame)

        # To-Do
        todo_frame = self._panel_frame("TO-DO")
        self._todo_label = QLabel("No tasks\nSay: 'add X to my tasks'")
        self._todo_label.setStyleSheet(
            f"font-size: 11px; color: {_TEXT}; background: transparent;"
        )
        self._todo_label.setWordWrap(True)
        todo_frame.layout().addWidget(self._todo_label)
        layout.addWidget(todo_frame)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return panel

    # ── Center panel ──────────────────────────────────────────────────────

    def _build_center_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"background: {_BG};")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # Arc reactor
        arc_row = QHBoxLayout()
        arc_row.addStretch()
        self._arc = ArcReactorWidget()
        self._arc.setFixedSize(220, 220)
        arc_row.addWidget(self._arc)
        arc_row.addStretch()
        layout.addLayout(arc_row)

        # Conversation history
        self._history_edit = QTextEdit()
        self._history_edit.setObjectName("history")
        self._history_edit.setReadOnly(True)
        self._history_edit.setMinimumHeight(100)
        layout.addWidget(self._history_edit, stretch=1)

        # Current transcript
        self._transcript_label = QLabel("")
        self._transcript_label.setStyleSheet(
            f"font-size: 12px; color: {_ORANGE}; border-left: 3px solid {_ORANGE};"
            f" padding-left: 8px; min-height: 18px; background: transparent;"
        )
        self._transcript_label.setWordWrap(True)
        layout.addWidget(self._transcript_label)

        # Current response
        self._response_label = QLabel("")
        self._response_label.setStyleSheet(
            f"font-size: 12px; color: {_CYAN}; border-left: 3px solid {_CYAN};"
            f" padding-left: 8px; min-height: 18px; background: transparent;"
        )
        self._response_label.setWordWrap(True)
        layout.addWidget(self._response_label)

        # Mic button
        self._mic_btn = QPushButton("🎙")
        self._mic_btn.setObjectName("mic")
        self._mic_btn.setToolTip("Click to speak  (or say 'Hey HP')")
        self._mic_btn.clicked.connect(self._on_mic_clicked)
        self._mic_btn.setStyleSheet(f"""
            QPushButton#mic {{
                background-color: #080E18;
                color: {_CYAN};
                border: 2px solid {_CYAN};
                border-radius: 32px;
                font-size: 22px;
                min-width: 64px; max-width: 64px;
                min-height: 64px; max-height: 64px;
            }}
            QPushButton#mic:hover   {{ background-color: #0F2030; border-color: #00FFFF; }}
            QPushButton#mic:pressed {{ background-color: #0A2840; }}
            QPushButton#mic:disabled {{
                background-color: #050810;
                color: #1A3040;
                border-color: #1A3040;
            }}
        """)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._mic_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return panel

    # ── Right panel ───────────────────────────────────────────────────────

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(270)
        panel.setStyleSheet(f"background: {_TOPBAR_BG};")

        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        content = QWidget()
        content.setStyleSheet(f"background: {_TOPBAR_BG};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # App shortcuts
        apps_frame = self._panel_frame("APP SHORTCUTS")
        grid = QGridLayout()
        grid.setSpacing(5)

        _SHORTCUT_APPS = [
            ("VSCode",    "🖥",  "code",                  False),
            ("Chrome",    "🌐",  "start chrome",           False),
            ("WhatsApp",  "💬",  "whatsapp",               False),
            ("Zoom",      "📹",  "zoom",                   False),
            ("Settings",  "⚙",   "ms-settings:",           False),
            ("Calc",      "🔢",  "calc",                   False),
            ("ChatGPT",   "🤖",  "https://chatgpt.com",    True),
            ("Claude",    "✨",   "https://claude.ai",      True),
            ("Terminal",  "⬛",  "wt",                     False),
            ("Explorer",  "📁",  "explorer",               False),
            ("Spotify",   "🎵",  "spotify",                False),
            ("Notepad",   "📝",  "notepad",                False),
        ]

        for i, (name, icon, cmd, is_url) in enumerate(_SHORTCUT_APPS):
            btn = QPushButton(f"{icon}\n{name}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {_PANEL_BG};
                    color: {_TEXT};
                    border: 1px solid {_BORDER_DIM};
                    border-radius: 4px;
                    font-size: 10px;
                    padding: 4px 2px;
                }}
                QPushButton:hover {{
                    background: #0A1A2A;
                    border-color: {_CYAN};
                    color: {_CYAN};
                }}
                QPushButton:pressed {{ background: #0F2030; }}
            """)
            btn.setFixedHeight(50)
            if is_url:
                url = cmd
                btn.clicked.connect(lambda _=False, u=url: webbrowser.open(u))
            else:
                c = cmd
                btn.clicked.connect(
                    lambda _=False, s=c: subprocess.Popen(  # noqa: S602
                        s, shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                )
            grid.addWidget(btn, i // 2, i % 2)

        apps_frame.layout().addLayout(grid)
        layout.addWidget(apps_frame)

        # SoundCloud
        music_frame = self._panel_frame("MUSIC")
        sc_btn = QPushButton("♪   S O U N D C L O U D")
        sc_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_PANEL_BG};
                color: #FF7700;
                border: 1px solid rgba(255,119,0,0.35);
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 2px;
                padding: 10px;
            }}
            QPushButton:hover {{ background: #150500; border-color: #FF7700; }}
        """)
        sc_btn.clicked.connect(lambda: webbrowser.open("https://soundcloud.com"))
        music_frame.layout().addWidget(sc_btn)
        layout.addWidget(music_frame)

        # Goals
        goals_frame = self._panel_frame("GOALS")
        self._goals_label = QLabel("No goals set\nSay: 'add X as a goal'")
        self._goals_label.setStyleSheet(
            f"font-size: 11px; color: {_TEXT}; background: transparent;"
        )
        self._goals_label.setWordWrap(True)
        goals_frame.layout().addWidget(self._goals_label)
        layout.addWidget(goals_frame)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return panel

    # ── Helpers ───────────────────────────────────────────────────────────

    def _panel_frame(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {_PANEL_BG};
                border: 1px solid {_BORDER_DIM};
                border-radius: 4px;
            }}
            QLabel {{ border: none; }}
        """)
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(8, 6, 8, 8)
        vbox.setSpacing(5)
        header = QLabel(f"◆  {title}")
        header.setStyleSheet(
            f"font-size: 9px; font-weight: bold; letter-spacing: 3px; color: {_CYAN};"
            f" padding-bottom: 3px; border-bottom: 1px solid {_BORDER_DIM};"
        )
        vbox.addWidget(header)
        return frame

    def _hline(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.HLine)
        f.setFixedHeight(1)
        f.setStyleSheet(f"background: {_BORDER_DIM}; border: none;")
        return f

    def _vline(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.VLine)
        f.setFixedWidth(1)
        f.setStyleSheet(f"background: {_BORDER_DIM}; border: none;")
        return f

    # ── Clock ─────────────────────────────────────────────────────────────

    def _update_clock(self) -> None:
        now = datetime.now()
        self._clock_label.setText(now.strftime("%I:%M:%S %p").lstrip("0") or "12:00:00 AM")
        self._date_label.setText(now.strftime("%a  %b %d,  %Y").upper())

    # ── Panel refresh ─────────────────────────────────────────────────────

    def _refresh_panels(self) -> None:
        self.refresh_tasks()
        self.refresh_reminders()

    def refresh_tasks(self) -> None:
        if self._tasks is None:
            return
        tasks = self._tasks.list_open("task")
        self._todo_label.setText(
            "\n".join(f"• {t}" for t in tasks) if tasks else "No tasks\nSay: 'add X to my tasks'"
        )
        goals = self._tasks.list_open("goal")
        self._goals_label.setText(
            "\n".join(f"• {g}" for g in goals) if goals else "No goals set\nSay: 'add X as a goal'"
        )

    def refresh_reminders(self) -> None:
        if self._reminders is None:
            return
        upcoming = self._reminders.list_upcoming()
        if upcoming:
            lines = []
            for content, remind_at in upcoming[:4]:
                try:
                    dt = datetime.fromisoformat(remind_at)
                    lines.append(f"• {content} @ {dt.strftime('%I:%M %p')}")
                except Exception:
                    lines.append(f"• {content}")
            self._reminders_label.setText("\n".join(lines))
        else:
            self._reminders_label.setText("No upcoming reminders")

    def show_notification(self, text: str) -> None:
        """Display a reminder or notification in the response area and history."""
        self._response_label.setText(f"  HP:  {text}")
        self._append_history("SYSTEM", text)
        self.refresh_reminders()

    # ── Public API ────────────────────────────────────────────────────────

    def set_manual_trigger_callback(self, fn: object) -> None:
        self._manual_trigger = fn

    def set_state(self, state: AssistantState) -> None:
        self._arc.set_state(state)
        color = _STATE_COLORS.get(state, _CYAN)
        self._state_label.setText(f"◆  {state.name}  ◆")
        self._state_label.setStyleSheet(
            f"font-size: 10px; letter-spacing: 3px; color: {color}; background: transparent;"
        )
        active = state in (AssistantState.IDLE, AssistantState.FOLLOW_UP)
        self._mic_btn.setEnabled(active)

    def set_transcript(self, text: str) -> None:
        self._transcript_label.setText(f"  YOU  »  {text}")

    def set_response(self, text: str) -> None:
        self._response_label.setText(f"  HP   »  {text}")
        transcript = self._transcript_label.text()
        if transcript:
            self._append_history(
                transcript.replace("  YOU  »  ", ""),
                text,
            )

    def clear(self) -> None:
        self._transcript_label.setText("")
        self._response_label.setText("")

    # ── Private helpers ───────────────────────────────────────────────────

    def _append_history(self, transcript: str, response: str) -> None:
        html = (
            f'<p style="margin:3px 0; font-family: Consolas, monospace; font-size: 11px;">'
            f'<span style="color:{_ORANGE}">&gt; {transcript}</span><br>'
            f'<span style="color:{_CYAN}">&lt; {response}</span>'
            f"</p>"
        )
        self._history_edit.append(html)

    def _on_mic_clicked(self) -> None:
        if callable(self._manual_trigger):
            self._manual_trigger()

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
