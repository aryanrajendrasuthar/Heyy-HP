# ADR-003 — Wake-Word Detection

**Status:** Accepted  
**Date:** 2026-04-23

---

## Context

HP needs always-on, low-CPU wake-word detection for "Hey HP": local, no cloud,
low false-positives on a laptop mic, free and open-source.

---

## Options Considered

| Option | Notes |
|---|---|
| **openWakeWord** | Apache-2.0, Python-native, supports custom wake words, low CPU |
| Porcupine (Picovoice) | High accuracy but API key + usage limits in free tier |
| Precise (Mozilla) | Abandoned |
| Snowboy | Deprecated and archived |

---

## Decision

**openWakeWord.**

Only maintained, fully local, Apache-licensed option. Custom training lets us tune
"Hey HP" specifically rather than relying on a generic pre-trained phrase.

---

## Consequences

- `openwakeword>=0.6.0` in `requirements/prod.txt`
- Wake-word listener: `app/voice/wakeword.py` (Sprint 2)
- Training script: `scripts/train_wakeword.py` (Sprint 2)
