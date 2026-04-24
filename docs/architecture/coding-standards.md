# HP Assistant — Coding Standards

## Tooling

| Concern | Tool |
|---|---|
| Lint + format | Ruff (`pyproject.toml`) |
| Testing | pytest |
| Coverage | pytest-cov (CI only) |
| Type hints | inline annotations |

---

## Module dependency rules

- `app/config/` imports nothing from `app/`. Everything else may import from it.
- `app/utils/` imports only stdlib and `app/config/`.
- `app/ui/` imports from `app/assistant/` and `app/config/`. Never from `app/voice/` directly.
- `app/memory/` is the only module that may touch SQLite.
- No circular imports.

---

## File layout

One class or one logical group per file. Keep files under ~200 lines.
Private helpers live in the same file, prefixed `_`.
Shared helpers go in `app/utils/`.

---

## Naming

| Thing | Convention |
|---|---|
| Modules | `snake_case` |
| Classes | `PascalCase` |
| Functions/methods | `snake_case` |
| Private | `_leading_underscore` |
| Constants | `UPPER_SNAKE` |
| Enum members | `UPPER_SNAKE` |

---

## Comments

Write comments only when the **why** is non-obvious.
Never comment what the code already says.

---

## Logging

`logging.getLogger(__name__)` at module level. Never use `print()`.

| Level | When |
|---|---|
| `INFO` | Normal lifecycle events |
| `DEBUG` | Detailed state/values |
| `WARNING` | Unexpected but recoverable |
| `ERROR` | Unrecoverable failure |

---

## Tests

- Mirror `app/` structure inside `tests/unit/`.
- Use `pytest.importorskip("PySide6")` at top of Qt test files.
- No test depends on state left by another. Use `tmp_path`.
- Prefer `monkeypatch.setenv` over real `.env` manipulation.

---

## Git

- Max 10 branches total in the repo at any time.
- No micro-commits. Each commit is a complete, reviewable unit.
- Branch naming: `sprint-N/short-description`.
- Delete branches after merging.
- `main` receives merges from `develop` only at sprint end, then gets a version tag.
