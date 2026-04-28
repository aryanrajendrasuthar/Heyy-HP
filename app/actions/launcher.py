"""Launch desktop applications and run system commands by voice."""

from __future__ import annotations

import ctypes
import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

# ── Precise volume control via pycaw / Windows Core Audio ─────────────────
try:
    from ctypes import cast as _cast
    from ctypes import POINTER as _POINTER
    from comtypes import CLSCTX_ALL as _CLSCTX_ALL  # type: ignore[import-untyped]
    from pycaw.pycaw import AudioUtilities as _AudioUtils  # type: ignore[import-untyped]
    from pycaw.pycaw import IAudioEndpointVolume as _IAudioEndpointVol  # type: ignore[import-untyped]
    _PYCAW_AVAILABLE = True
except ImportError:
    _PYCAW_AVAILABLE = False


def _get_volume_com() -> Any | None:
    if not _PYCAW_AVAILABLE:
        return None
    try:
        devices = _AudioUtils.GetSpeakers()
        interface = devices.Activate(_IAudioEndpointVol._iid_, _CLSCTX_ALL, None)
        return _cast(interface, _POINTER(_IAudioEndpointVol))
    except Exception:
        logger.debug("Could not get volume COM interface", exc_info=True)
        return None

# ── App aliases → shell command / URI ─────────────────────────────────────
_WINDOWS_APPS: dict[str, str] = {
    # Browsers — use 'start' so Windows App Paths registry is used (no PATH needed)
    "chrome": "start chrome",
    "google chrome": "start chrome",
    "firefox": "start firefox",
    "edge": "start msedge",
    "microsoft edge": "start msedge",
    "brave": "start brave",
    "opera": "start opera",
    # Microsoft Office
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "onenote": "onenote",
    "access": "msaccess",
    "publisher": "mspub",
    # Communication
    "teams": "teams",
    "microsoft teams": "teams",
    "zoom": "zoom",
    "slack": "slack",
    "discord": "discord",
    "whatsapp": "whatsapp",
    "telegram": "telegram",
    "skype": "skype",
    # Development
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "visual studio": "devenv",
    "terminal": "wt",
    "windows terminal": "wt",
    "cmd": "cmd",
    "command prompt": "cmd",
    "powershell": "powershell",
    "git bash": "git-bash",
    "github desktop": "github",
    "postman": "postman",
    # Media & entertainment
    "spotify": "spotify",
    "vlc": "vlc",
    "media player": "wmplayer",
    "windows media player": "wmplayer",
    "photos": "ms-photos:",
    "camera": "microsoft.windows.camera:",
    "netflix": "netflix:",
    # Creative
    "paint": "mspaint",
    "paint 3d": "ms-paint:",
    "snip": "snippingtool",
    "snipping tool": "snippingtool",
    "snip and sketch": "ms-screenclip:",
    "screen snip": "ms-screenclip:",
    "photo editor": "ms-photos:",
    # System tools
    "notepad": "notepad",
    "wordpad": "wordpad",
    "calculator": "calc",
    "calc": "calc",
    "explorer": "explorer",
    "file explorer": "explorer",
    "my computer": "explorer",
    "task manager": "taskmgr",
    "control panel": "control",
    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "event viewer": "eventvwr.msc",
    "services": "services.msc",
    "registry editor": "regedit",
    "system information": "msinfo32",
    "resource monitor": "resmon",
    "performance monitor": "perfmon",
    "character map": "charmap",
    "on screen keyboard": "osk",
    "magnifier": "magnify",
    "narrator": "narrator",
    "remote desktop": "mstsc",
    # Settings pages
    "settings": "ms-settings:",
    "windows settings": "ms-settings:",
    "wifi settings": "ms-settings:network-wifi",
    "wifi": "ms-settings:network-wifi",
    "bluetooth": "ms-settings:bluetooth",
    "bluetooth settings": "ms-settings:bluetooth",
    "display settings": "ms-settings:display",
    "sound settings": "ms-settings:sound",
    "notification settings": "ms-settings:notifications",
    "battery settings": "ms-settings:batterysaver",
    "power settings": "ms-settings:powersleep",
    "privacy settings": "ms-settings:privacy",
    "update settings": "ms-settings:windowsupdate",
    "windows update": "ms-settings:windowsupdate",
    "apps settings": "ms-settings:appsfeatures",
    "storage settings": "ms-settings:storagesense",
    "accounts settings": "ms-settings:accounts",
    "personalization": "ms-settings:personalization",
    "taskbar settings": "ms-settings:taskbar",
    "startup apps": "ms-settings:startupapps",
    # Microsoft Store & built-ins
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
    "xbox": "xbox:",
    "mail": "outlookmail:",
    "calendar": "outlookcal:",
    "maps": "bingmaps:",
    "news": "bingnews:",
    "weather": "bingweather:",
    "clock": "ms-clock:",
    "alarms": "ms-clock:",
    "sticky notes": "ms-stickynotes:",
    "to do": "ms-todo:",
    "microsoft to do": "ms-todo:",
    "cortana": "ms-cortana:",
    "feedback hub": "feedback-hub:",
    "get help": "ms-contact-support:",
    "tips": "ms-get-started:",
}

# ── Process names for close/kill ──────────────────────────────────────────
_PROCESS_NAMES: dict[str, str] = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "brave": "brave.exe",
    "opera": "opera.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
    "onenote": "onenote.exe",
    "teams": "teams.exe",
    "microsoft teams": "teams.exe",
    "zoom": "zoom.exe",
    "slack": "slack.exe",
    "discord": "discord.exe",
    "whatsapp": "whatsapp.exe",
    "telegram": "telegram.exe",
    "spotify": "spotify.exe",
    "vlc": "vlc.exe",
    "notepad": "notepad.exe",
    "wordpad": "wordpad.exe",
    "calculator": "calculator.exe",
    "calc": "calculator.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "vscode": "code.exe",
    "vs code": "code.exe",
    "visual studio code": "code.exe",
    "visual studio": "devenv.exe",
    "terminal": "wt.exe",
    "windows terminal": "wt.exe",
    "postman": "postman.exe",
    "github desktop": "github.exe",
    "obs": "obs64.exe",
    "steam": "steam.exe",
}

# ── System commands ────────────────────────────────────────────────────────
_SYSTEM_COMMANDS: dict[str, tuple[str, str]] = {
    # key: (shell_command, display_name)
    "shutdown": ("shutdown /s /t 30", "Shutting down in 30 seconds"),
    "shut down": ("shutdown /s /t 30", "Shutting down in 30 seconds"),
    "shutdown now": ("shutdown /s /t 0", "Shutting down now"),
    "restart": ("shutdown /r /t 30", "Restarting in 30 seconds"),
    "restart now": ("shutdown /r /t 0", "Restarting now"),
    "reboot": ("shutdown /r /t 30", "Restarting in 30 seconds"),
    "cancel shutdown": ("shutdown /a", "Shutdown cancelled"),
    "sleep": ("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", "Going to sleep"),
    "hibernate": ("shutdown /h", "Hibernating"),
    "lock": ("rundll32.exe user32.dll,LockWorkStation", "Locking screen"),
    "lock screen": ("rundll32.exe user32.dll,LockWorkStation", "Locking screen"),
    "sign out": ("logoff", "Signing out"),
    "log out": ("logoff", "Signing out"),
    "mute": (None, "Muted"),
    "unmute": (None, "Unmuted"),
    "toggle mute": (None, "Toggled mute"),
    "volume up": (None, "Volume up"),
    "volume down": (None, "Volume down"),
    "empty recycle bin": ("PowerShell -Command Clear-RecycleBin -Force", "Recycle bin emptied"),
    "take screenshot": ("snippingtool", "Opening snipping tool"),
    "take a screenshot": ("snippingtool", "Opening snipping tool"),
    "screenshot": ("snippingtool", "Opening snipping tool"),
    "screen shot": ("snippingtool", "Opening snipping tool"),
    "take screen shot": ("snippingtool", "Opening snipping tool"),
    "take a screen shot": ("snippingtool", "Opening snipping tool"),
}


# Windows virtual key codes for media keys
_VK_VOLUME_MUTE = 0xAD
_VK_VOLUME_DOWN = 0xAE
_VK_VOLUME_UP = 0xAF


def _press_media_key(vk: int, times: int = 1) -> None:
    for _ in range(times):
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)


class AppLauncher:
    def launch(self, app_name: str) -> bool:
        key = app_name.lower().strip()
        cmd = _WINDOWS_APPS.get(key)
        if cmd is None:
            cmd = key
        try:
            subprocess.Popen(  # noqa: S603
                cmd,
                shell=True,  # noqa: S602
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Launched: %s (%s)", app_name, cmd)
            return True
        except Exception:
            logger.exception("Failed to launch %s", app_name)
            return False

    # ── Close / kill applications ─────────────────────────────────────────

    def close_app(self, app_name: str) -> str:
        key = app_name.lower().strip()
        process = _PROCESS_NAMES.get(key)
        if process is None:
            # Fall back: assume user said the exe name or try appending .exe
            process = key if key.endswith(".exe") else key + ".exe"
        try:
            result = subprocess.run(
                ["taskkill", "/f", "/im", process],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                logger.info("Closed %s (%s)", app_name, process)
                return f"Closed {app_name}"
            return f"{app_name} is not running"
        except Exception:
            logger.exception("Failed to close %s", app_name)
            return f"Could not close {app_name}"

    # ── Precise volume ────────────────────────────────────────────────────

    def set_volume(self, percent: int) -> str:
        """Set master volume to an exact percentage (0–100)."""
        percent = max(0, min(100, percent))
        vc = _get_volume_com()
        if vc is not None:
            try:
                vc.SetMasterVolumeLevelScalar(percent / 100.0, None)
                return f"Volume set to {percent} percent"
            except Exception:
                logger.exception("pycaw SetMasterVolumeLevelScalar failed")
        # Fallback: approximate with keypresses
        return self._volume_keys_set(percent)

    def change_volume(self, delta: int) -> str:
        """Raise or lower volume by delta percent (positive = up, negative = down)."""
        vc = _get_volume_com()
        if vc is not None:
            try:
                current = round(vc.GetMasterVolumeLevelScalar() * 100)
                new_val = max(0, min(100, current + delta))
                vc.SetMasterVolumeLevelScalar(new_val / 100.0, None)
                direction = "up" if delta > 0 else "down"
                return f"Volume {direction} to {new_val} percent"
            except Exception:
                logger.exception("pycaw GetMasterVolumeLevelScalar failed")
        # Fallback: press key ~delta/2 times (each press ≈ 2%)
        vk = _VK_VOLUME_UP if delta > 0 else _VK_VOLUME_DOWN
        _press_media_key(vk, times=max(1, abs(delta) // 2))
        return f"Volume {'up' if delta > 0 else 'down'}"

    def _volume_keys_set(self, percent: int) -> str:
        """Approximate volume set via key presses when pycaw unavailable."""
        vc = _get_volume_com()
        current_pct = 50  # unknown — assume mid
        if vc is not None:
            try:
                current_pct = round(vc.GetMasterVolumeLevelScalar() * 100)
            except Exception:
                pass
        delta = percent - current_pct
        if delta != 0:
            vk = _VK_VOLUME_UP if delta > 0 else _VK_VOLUME_DOWN
            _press_media_key(vk, times=max(1, abs(delta) // 2))
        return f"Volume set to approximately {percent} percent"

    # ── Brightness (laptop built-in display via WMI) ──────────────────────

    def get_brightness(self) -> int | None:
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightness).CurrentBrightness"],
                capture_output=True, text=True, timeout=5,
            )
            return int(result.stdout.strip())
        except Exception:
            return None

    def set_brightness(self, percent: int) -> str:
        percent = max(0, min(100, percent))
        cmd = (
            f"(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods)"
            f".WmiSetBrightness(1, {percent})"
        )
        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return f"Brightness set to {percent} percent"
        except Exception:
            logger.exception("Failed to set brightness")
            return "Failed to set brightness"

    def change_brightness(self, delta: int) -> str:
        current = self.get_brightness()
        if current is None:
            return "Cannot read screen brightness"
        new_val = max(0, min(100, current + delta))
        return self.set_brightness(new_val)

    # ── System commands ───────────────────────────────────────────────────

    def system_command(self, key: str) -> str | None:
        """Run a system command. Returns spoken response or None if not found."""
        normalized = key.lower().strip()

        # Volume / mute — handled via Windows media keys (no external tool needed)
        if normalized in ("volume up",):
            _press_media_key(_VK_VOLUME_UP, times=5)
            return "Volume up"
        if normalized in ("volume down",):
            _press_media_key(_VK_VOLUME_DOWN, times=5)
            return "Volume down"
        if normalized in ("mute", "toggle mute"):
            _press_media_key(_VK_VOLUME_MUTE)
            return "Muted"
        if normalized == "unmute":
            _press_media_key(_VK_VOLUME_MUTE)
            return "Unmuted"

        entry = _SYSTEM_COMMANDS.get(normalized)
        if entry is None:
            return None
        cmd, response = entry
        if cmd is None:
            return response
        try:
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S602,S603
            logger.info("System command: %s", key)
        except Exception:
            logger.exception("System command failed: %s", key)
            return f"Failed to run {key}"
        return response
