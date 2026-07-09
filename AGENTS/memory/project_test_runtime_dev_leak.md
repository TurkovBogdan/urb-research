---
name: Test runtime → runtime/test
description: tests/conftest.py sets APP_ENV=test before src imports — all AppPath-derived artifacts (logs/cache/user) go to runtime/test/.
type: project
---
Since 2026-05-08 `tests/conftest.py` sets `os.environ["APP_ENV"] = "test"` before the first imports from `src`. `AppPath.resolve_runtime_root()` reads `APP_ENV` from env → `runtime/test/`. The DB is configured separately via `DB_PROVIDER=sqlite` + `DB_PATH=:memory:` override (in-memory; no `runtime/test/` DB file). `runtime/test/` is in `.gitignore`.

**Why:** before the fix `_default_factory` via `AppPath.from_root()` wrote to `runtime/dev/logs/` on any `get_logger()` call from tests.

**How to apply:**
- If entries with test module="m" / code="c" appear in `runtime/dev/logs/` — someone is importing `src` before conftest sets `APP_ENV`, or running a script manually with `APP_ENV=dev`.
- Tests must not replace the logger factory with `tmp_path` — the profile already separates the paths.
