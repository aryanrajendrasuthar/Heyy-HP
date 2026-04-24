# HP — Local Desktop Voice Assistant

[![CI](https://github.com/YOUR_USERNAME/hp-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/hp-assistant/actions/workflows/ci.yml)

HP is a local-first, always-on Windows desktop voice assistant built for personal daily use.
It runs entirely on-device, wakes on **"Hey HP"**, and handles voice commands for app control,
search, media, and conversational answers — without sending audio to the cloud.

---

## Quick Start

```bash
# 1. Clone and enter the repo
git clone https://github.com/YOUR_USERNAME/hp-assistant.git
cd hp-assistant

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows

# 3. Install dev dependencies
pip install -r requirements/dev.txt

# 4. Copy and configure environment
copy .env.example .env          # Edit .env if needed

# 5. Run
python main.py
```

---

## Architecture

| Layer | Module | Purpose |
|---|---|---|
| Desktop Shell | `app/ui/` | PySide6 window, tray icon, panels |
| Voice Runtime | `app/voice/` | Wake-word, mic, STT, TTS, VAD, interruption |
| Assistant Core | `app/assistant/` | State machine, follow-up timer, command dispatch |
| Action Engine | `app/actions/` | App launcher, browser routing, search routing |
| LLM Engine | `app/llm/` | Pluggable chat provider (local or cloud) |
| Persistence | `app/memory/` | SQLite repositories for settings, history, routines |
| Config | `app/config/` | Pydantic `AppSettings` — single source of truth |
| Utils | `app/utils/` | Logging factory, path helpers |

Full architecture documentation: [docs/architecture/system-overview.md](docs/architecture/system-overview.md)

---

## Development

```bash
# Lint
ruff check .

# Format
ruff format .

# Test
pytest

# Lint + format check (mirrors CI)
ruff check . && ruff format --check . && pytest
```

### Branch strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, releasable only |
| `develop` | Sprint integration |
| `sprint-N/feature` | Short-lived feature work |

---

## Project Status

| Sprint | Goal | Status |
|---|---|---|
| Sprint 1 | Repo foundation, config, logging, CI | In progress |
| Sprint 2 | Voice runtime (wake, STT, TTS, state machine) | Planned |
| Sprint 3 | Action engine and routing | Planned |
| Sprint 4 | Chat mode and interruption | Planned |
| Sprint 5 | Personalization, routines, UI polish | Planned |
| Sprint 6 | Packaging, Windows startup, v1.0.0 release | Planned |

---

## Requirements

- Python 3.11+
- Windows 11
- Microphone

See [docs/runbooks/dev-setup.md](docs/runbooks/dev-setup.md) for full setup instructions.
