# Changelog

All notable changes documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

## [0.1.0] — 2026-04-23

### Added

- Project scaffold: `pyproject.toml`, `.gitignore`, `.env.example`
- `AppSettings` (Pydantic v2) with `HP_` env prefix and field validation
- Rotating log file + console logging factory
- `AssistantState` enum: IDLE, WAKE_DETECTED, LISTENING, PROCESSING, SPEAKING, FOLLOW_UP
- PySide6 main window: dark theme, transcript panel, response panel, status bar
- System tray icon with show/hide/quit and double-click toggle
- Settings dialog: displays config values; runtime log level control
- File/Help menu bar on main window
- GitHub Actions CI: lint + tests + coverage on every push/PR
- PR template and coding standards documentation
- Architecture overview, ADRs 001-003, dev-setup runbook
- pytest markers registered: `unit`, `integration`, `e2e`, `ui`
