# ADR-002 — Speech-to-Text Engine

**Status:** Accepted  
**Date:** 2026-04-23

---

## Context

HP needs local, offline speech-to-text that runs on a mid-range Windows laptop,
produces accurate transcriptions in 1-2 seconds, and is free to use.

---

## Options Considered

| Option | Notes |
|---|---|
| **faster-whisper** | CTranslate2 Whisper reimplementation; significantly faster + lower memory; Apache-2.0 |
| openai-whisper | Reference implementation; same accuracy, slower, heavier |
| Vosk | Very fast but lower accuracy for conversational English |
| Cloud STT | Requires internet + API key; excluded by local-first constraint |

---

## Decision

**faster-whisper** with the `small` English model.

Runs in under 1 second on CPU for typical short commands. The `base` model is the
fallback if memory is constrained.

---

## Consequences

- `faster-whisper>=1.0.0` in `requirements/prod.txt`
- STT module: `app/voice/stt.py` (Sprint 2)
- Models downloaded on first run and cached locally
