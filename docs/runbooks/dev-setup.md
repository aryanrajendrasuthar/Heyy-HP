# Runbook — Local Development Setup

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | [python.org](https://python.org) — add to PATH during install |
| Git | any recent | [git-scm.com](https://git-scm.com) |
| Windows | 11 | Primary target; Windows 10 likely works |
| Microphone | any | Required for Sprint 2+ voice features |

---

## First-time Setup

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/hp-assistant.git
cd hp-assistant

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dev dependencies (includes base + ruff + pytest)
pip install -r requirements/dev.txt

# 4. Install the package in editable mode so imports resolve
pip install -e .

# 5. Copy environment config
copy .env.example .env
# Edit .env if you need to change log level, audio device, etc.
```

---

## Running HP

```bash
# Ensure venv is active
.venv\Scripts\activate

python main.py
```

Logs are written to `logs/hp.log` (rotated at 5 MB, 3 backups kept).

---

## Running Tests

```bash
pytest
```

Run a specific file:
```bash
pytest tests/unit/test_config.py -v
```

---

## Linting and Formatting

```bash
# Check for lint errors
ruff check .

# Auto-fix safe issues
ruff check . --fix

# Format all files
ruff format .

# Check format without writing (mirrors CI)
ruff format --check .
```

---

## Branch Workflow

```bash
# Start a new feature branch from develop
git checkout develop
git pull origin develop
git checkout -b sprint-1/your-feature

# ... make changes, commit small and often ...

# Push and open a PR into develop
git push -u origin sprint-1/your-feature
```

Merge into `develop` after CI passes. Merge `develop` into `main` only at sprint end.

---

## Environment Variables Reference

See [.env.example](../../.env.example) for the full list with descriptions.
All variables use the `HP_` prefix.

| Variable | Default | Purpose |
|---|---|---|
| `HP_DEBUG` | `false` | Enable debug logging and verbose output |
| `HP_LOG_LEVEL` | `INFO` | Root log level (DEBUG/INFO/WARNING/ERROR) |
| `HP_LOG_DIR` | `logs` | Directory for rotating log files |
| `HP_WAKE_PHRASE` | `Hey HP` | Wake phrase (Sprint 2) |
| `HP_FOLLOW_UP_TIMEOUT_S` | `10` | Seconds to stay in follow-up listen mode |
| `HP_AUDIO_DEVICE_INDEX` | _(unset)_ | Mic device index; omit for system default |
| `HP_DB_PATH` | `data/hp.db` | SQLite database path (Sprint 5) |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'app'`**
Run `pip install -e .` from the repo root to register the package in editable mode.

**`pydantic_settings` not found**
Run `pip install -r requirements/dev.txt` — it is not part of base `pydantic`.

**Ruff not found**
Ensure `.venv\Scripts\activate` is active before running `ruff`.
