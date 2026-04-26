# HP — Local Desktop Voice Assistant

[![CI](https://github.com/aryanrajendrasuthar/Heyy-HP/actions/workflows/ci.yml/badge.svg)](https://github.com/aryanrajendrasuthar/Heyy-HP/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%2011-lightgrey)

HP is a local-first, always-on Windows desktop voice assistant built for personal daily use.
It runs entirely on-device, wakes on **"Hey HP"**, and handles voice commands for app control,
web search, file access, conversational answers, and object recognition — without sending audio
to the cloud.

---

## Features

- **Wake word** — always listening for "Hey HP" via openWakeWord (local, no cloud)
- **Speech-to-text** — faster-whisper running fully on CPU
- **App launcher** — "open Chrome", "launch VS Code", "start Spotify" and 20+ aliases
- **Browser routing** — "google Python tutorial", "youtube lo-fi music", "open https://..."
- **File & folder access** — "open folder Documents", "open file report.pdf"
- **Conversational fallback** — unrecognised commands routed to an LLM (stub by default, pluggable)
- **TTS interruption** — speak over HP mid-response to immediately stop and re-listen
- **Vision — hand/object recognition** — "what's in my hand?" opens the webcam, detects your hand with MediaPipe, identifies the object with YOLOv8, and responds by voice
- **Persistent history** — every conversation turn saved to SQLite
- **Routines** — store custom trigger phrases that run sequences of commands
- **System tray** — hide to tray, double-click to show, "Start on boot" toggle
- **Dark UI** — Catppuccin-themed PySide6 window with scrollable conversation history

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/aryanrajendrasuthar/Heyy-HP.git
cd Heyy-HP

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements/prod.txt

# 4. (Optional) configure
copy .env.example .env   # edit HP_* variables as needed

# 5. Run
python main.py
```

---

## Voice Commands

| Say | Action |
|---|---|
| "Hey HP" | Wake the assistant |
| "open Chrome" | Launch Chrome |
| "open VS Code" | Launch VS Code |
| "google [query]" | Google search |
| "youtube [query]" | YouTube search |
| "open https://..." | Open URL in browser |
| "open folder Documents" | Open a folder |
| "open file report.pdf" | Open a file |
| "what's in my hand?" | Identify object via webcam |
| "what am I holding?" | Identify object via webcam |
| "identify this" | Identify object via webcam |
| Anything else | Routed to LLM for a conversational reply |

---

## Vision Setup (optional)

The hand/object recognition feature requires three extra packages:

```bash
pip install opencv-python mediapipe ultralytics
```

YOLOv8n (~6 MB) is downloaded automatically on first use. No GPU required.

---

## Architecture

| Layer | Module | Purpose |
|---|---|---|
| Desktop Shell | `app/ui/` | PySide6 window, tray icon, settings dialog, history panel |
| Voice Runtime | `app/voice/` | Wake-word, mic capture, VAD, STT, TTS, interruption |
| Assistant Core | `app/assistant/` | State machine, follow-up timer, command dispatcher |
| Action Engine | `app/actions/` | App launcher, browser router, file actions |
| Vision | `app/vision/` | Webcam capture, MediaPipe hand detection, YOLOv8 identification |
| LLM Engine | `app/llm/` | Pluggable provider interface + stub + conversation buffer |
| Persistence | `app/memory/` | SQLite — conversation history, routines |
| Services | `app/services/` | Windows startup registry |
| Config | `app/config/` | Pydantic `AppSettings` — single source of truth |
| Utils | `app/utils/` | Logging factory |

Full architecture: [docs/architecture/system-overview.md](docs/architecture/system-overview.md)

---

## Configuration

All settings are controlled via environment variables (prefix `HP_`) or a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `HP_WAKE_PHRASE` | `Hey HP` | Wake phrase label |
| `HP_WAKE_WORD_MODEL` | `hey_jarvis` | openWakeWord model name |
| `HP_WHISPER_MODEL` | `tiny.en` | faster-whisper model size |
| `HP_TTS_RATE` | `175` | Speech rate (words per minute) |
| `HP_TTS_VOLUME` | `1.0` | TTS volume (0.0 – 1.0) |
| `HP_SILENCE_TIMEOUT_S` | `1.5` | Seconds of silence to end utterance |
| `HP_FOLLOW_UP_TIMEOUT_S` | `10.0` | Seconds to wait for follow-up after response |
| `HP_LLM_PROVIDER` | `stub` | LLM provider (`stub` or future cloud keys) |
| `HP_LLM_MAX_HISTORY` | `10` | Conversation turns kept in context |
| `HP_WEBCAM_INDEX` | `0` | Webcam device index for vision |
| `HP_LOG_LEVEL` | `INFO` | Logging level |
| `HP_DB_PATH` | `data/hp.db` | SQLite database path |

---

## Development

```bash
# Lint
ruff check .

# Format
ruff format .

# Test
pytest

# All checks (mirrors CI)
ruff check . && ruff format --check . && pytest
```

### Build executable (Windows)

```bash
pip install pyinstaller
python build_windows.py
# → dist\HP\HP.exe
```

### Branch strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, releasable |
| `develop` | Sprint integration |
| `sprint-N/feature` | Short-lived feature work |

---

## Project Status

| Sprint | Goal | Status |
|---|---|---|
| Sprint 1 | Repo foundation, config, logging, CI | Done |
| Sprint 2 | Voice runtime (wake, STT, TTS, VAD, state machine) | Done |
| Sprint 3 | Action engine and routing | Done |
| Sprint 4 | Chat mode, LLM fallback, TTS interruption | Done |
| Sprint 5 | Vision (hand/object recognition), persistence, routines, UI polish | Done |
| Sprint 6 | Packaging, Windows startup, v1.0.0 release | Done |

---

## Requirements

- Python 3.11+
- Windows 11
- Microphone
- Webcam *(optional — required for vision commands only)*

See [docs/runbooks/dev-setup.md](docs/runbooks/dev-setup.md) for full setup instructions.
