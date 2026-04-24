# ADR-001 — Desktop UI Framework

**Status:** Accepted
**Date:** 2026-04-23

---

## Context

HP needs a native Windows desktop UI with:
- A persistent main window (transcript + response panels, status indicator)
- A system tray icon for always-on background operation
- A settings/preferences panel
- The ability to package into a standalone `.exe` for deployment without a Python environment

The UI layer will be read-heavy (displaying assistant output) with minimal user-initiated input
(voice is primary; keyboard is fallback).

---

## Options Considered

### Option 1 — PySide6 (Qt for Python)
- Full-featured native desktop UI framework
- System tray, notifications, custom windows, styling all supported
- Packagable with PyInstaller into a standalone `.exe`
- Active maintainance; Python 3.11+ support confirmed
- Large but well-documented API surface
- Licensing: LGPLv3 for PySide6 itself; Qt framework components vary; acceptable for personal use

### Option 2 — Tkinter
- Bundled with CPython; zero extra install
- Adequate for simple forms but limited tray/notification support
- Dated visual style; harder to make look professional
- Less expressive layout system

### Option 3 — PyQt6
- Nearly identical to PySide6 in capability
- GPL license (commercial license required for proprietary use)
- PySide6 is the official Qt Company binding; PyQt6 is third-party
- No material technical advantage over PySide6 for this project

### Option 4 — Electron / web-based (via pywebview)
- Requires Node.js or a bundled Chromium runtime
- Large binary footprint (~150 MB+)
- Adds frontend/backend language split without benefit for a local personal tool
- Overkill for the use case

---

## Decision

**PySide6.**

It is the only option that satisfies all requirements (tray, window, packaging, styling) without
a GPL licensing issue or excessive runtime overhead. For a personal local project it is practical
immediately; if commercialization ever becomes relevant, Qt licensing can be revisited then.

---

## Consequences

- Add `pyside6>=6.7.0` to `requirements/prod.txt`
- UI module lives entirely in `app/ui/`; no Qt imports anywhere else
- PyInstaller is the packaging tool (Sprint 6); confirmed to work with PySide6
- Tests for UI components use `pytest-qt` (added in Sprint 1/ui-shell)
