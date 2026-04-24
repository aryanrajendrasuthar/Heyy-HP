# HP Assistant — System Overview

## Purpose

HP is a local-first, always-on Windows desktop voice assistant. All audio processing
runs on-device. Cloud components are optional and opt-in.

---

## Layer Diagram

```
┌────────────────────────────────────────────────────┐
│                   Desktop Shell                    │
│           PySide6 window · tray icon               │
│         transcript panel · status indicator        │
└───────────────────┬────────────────────────────────┘
                    │ state events / display commands
┌───────────────────▼────────────────────────────────┐
│               Assistant Runtime                    │
│   state machine · follow-up timer · dispatcher    │
└──────┬──────────────────────────┬──────────────────┘
       │                          │
┌──────▼──────┐          ┌────────▼───────┐
│ Voice       │          │ Action Engine  │
│ Runtime     │          │                │
│             │          │ app launcher   │
│ wake-word   │          │ Google routing │
│ mic capture │          │ YouTube routing│
│ VAD         │          │ folder open    │
│ STT         │          │ routines       │
│ TTS         │          └────────┬───────┘
│ interruption│                   │
└──────┬──────┘          ┌────────▼───────┐
       │                 │  LLM Engine    │
       │                 │                │
       │                 │ provider iface │
       │                 │ local stub     │
       │                 │ cloud adapter  │
       │                 └────────┬───────┘
       │                          │
┌──────▼──────────────────────────▼───────────────────┐
│                    Persistence                      │
│         SQLite · settings · history · routines     │
└─────────────────────────────────────────────────────┘
```

---

## Module Map

| Module | Path | Responsibility |
|---|---|---|
| Desktop Shell | `app/ui/` | PySide6 main window, tray icon, transcript/response panels |
| Assistant Runtime | `app/assistant/` | State machine, follow-up timer, command dispatch |
| Voice Runtime | `app/voice/` | Mic capture, wake-word, VAD, STT, TTS, interruption |
| Action Engine | `app/actions/` | App launcher, URL builders, folder/file operations |
| LLM Engine | `app/llm/` | Provider interface + local stub + optional cloud adapter |
| Persistence | `app/memory/` | SQLite repositories; all DB access is isolated here |
| Config | `app/config/` | `AppSettings` (Pydantic v2) — one load at startup |
| Utils | `app/utils/` | Logging factory, path helpers |
| Services | `app/services/` | Health endpoint, internal event bus |

---

## Assistant State Machine

```
[IDLE] ──── wake phrase detected ──── [WAKE_DETECTED]
                                              │
                                       confirmed silence
                                              │
                                        [LISTENING]
                                              │
                                      utterance complete
                                              │
                                       [PROCESSING]
                                              │
                                        [SPEAKING] ──── interrupted ──── [LISTENING]
                                              │
                                    response delivered
                                              │
                                      [FOLLOW_UP]  (10 s window)
                                       /          \
                              new speech           timeout
                                 │                    │
                           [LISTENING]             [IDLE]
```

Full state machine documentation: [state-machine.md](state-machine.md) _(added in Sprint 2)_

---

## Key Design Decisions

| Decision | Choice | ADR |
|---|---|---|
| Desktop UI framework | PySide6 | [adr-001](../decisions/adr-001-desktop-framework.md) |
| Speech-to-text | faster-whisper (local) | _(Sprint 2)_ |
| Wake-word detection | openWakeWord (local) | _(Sprint 2)_ |
| Persistence | SQLite | _(Sprint 5)_ |

---

## Data Flow — Voice Command

```
mic audio stream
    → wake-word detector  (openWakeWord)
    → VAD silence detection
    → STT transcription   (faster-whisper)
    → command dispatcher  (assistant/dispatcher.py)
    → action engine  OR  LLM engine
    → TTS response        (pyttsx3 / Windows SAPI)
    → UI display
    → follow-up timer start
```

---

## Dependency Rules

- `app/ui/` may import from `app/assistant/` but **never** from `app/voice/` directly
- `app/assistant/` orchestrates; it imports interfaces, not concrete implementations
- `app/memory/` is the only module that touches SQLite
- `app/config/` is imported by everything; it imports nothing from `app/`
- `app/utils/` imports only from stdlib and `app/config/`
