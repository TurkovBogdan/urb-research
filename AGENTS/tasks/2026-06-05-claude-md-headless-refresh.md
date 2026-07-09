---
title: CLAUDE.md / AGENTS.md refresh — headless server migration
date: 2026-06-05
status: completed
description: "Reconcile CLAUDE.md (= AGENTS.md = AGENTS/agent-primary.md) against the actual codebase after the PyInstaller-desktop → headless-server refactor. The earlier docs-refresh task (2026-06-04) flagged this file as out-of-scope-but-stale."
tags: [docs, deploy, agents]
---

## Task

User: "После глобального рефактора нужно обновлять документацию. Твоя задача сверять
описанное в CLAUDE.md с реальным положением дел." Verify every claim in the agent
primary instructions and bring it current.

## Context

`CLAUDE.md` and `AGENTS.md` are both symlinks to `AGENTS/agent-primary.md`. Task
`2026-06-04-docs-refresh-headless` updated README + `dev/docs/` but explicitly left
this file stale (Qt/PyInstaller architecture). The architecture migrated to a headless
server: unified `src/app.py` entry (`--backend`/`--worker`/`migrate`), SPA served by
nginx (prod) / Vite (dev), built front committed to `static/`, deploy = `git pull` +
`uv sync`; `src/gui/` and the MCP apps were deleted.

## Verification (CLAUDE.md vs reality)

- **About** — stale: "Qt status-panel shell", "single PyInstaller binary". → headless.
- **Structure** — `SPEC: ModuleSpec` → `Module` subclass (`src/core/module.py`);
  `src/gui/` deleted; `bench/` → `dev/bench/`; `.run/` → `dev/.run/`; `dist/` gone;
  new dirs missing: `src/app.py`, `static/`, `storage/`, `tools/`, `dev/docs/`;
  `runtime/dev|test` → `runtime/dev|test|prod`.
- **Inventory** — `APP_PROFILE` → `APP_ENV` (verified `tests/conftest.py:121` +
  `src/core/config.py`); prod `dist/release` binary → headless from source +
  `runtime/prod/`; `.gitignore` block rewritten (runtime/* + storage/* kept-but-ignored).
- **Running and building** — entire section was Qt/PyInstaller (`app_run.py`,
  `app_build.py`, `watch-gui`, `dist/release/core-semaphore`, `run_gui_app` boots Qt).
  None exist. Rewrote against `dev/.run/` (`run-server`/`run-worker`/`group-server*`/
  `build-web`/`tool-migrate`) + `dev/docs/DEVELOPMENT.md`/`BUILD.md`.
- **Testing / At the start of work / Working rules** — verified accurate (markers +
  `addopts` match `pyproject.toml`; all index links exist). No edits.

Leftover noted (not in this file): `pyproject.toml` still carries the `PySide6`/`qasync`
build deps though `src/gui/` is gone (flagged TBD in `BUILD.md`).

## What was done

Edited `AGENTS/agent-primary.md` (affects both symlinks): rewrote **About**,
**Structure**, **Inventory**, **Running and building**. No code changes; no tests
(docs only).

## Result

`CLAUDE.md`/`AGENTS.md` now describe the headless architecture, real directory layout,
real entry point (`src/app.py` + `src/apps/app/server.py::app`), and real run configs.

## Follow-up: GUI-mentions sweep

User: "Изучи все упоминания gui в документации и агентах." Grepped every `*.md` for
`gui`/`Qt`/`qasync`/`PySide`/`status-panel`. Split into live docs (fixed) vs historical
logs `AGENTS/tasks/**` (incl. archive) + `AGENTS/plans/**` + `AGENTS/research/**` (left —
they record past work).

Fixed (live docs):
- **Deleted** `AGENTS/memory/qt_rules.md` — whole file described the removed `src/gui/`.
- `MEMORY.md` — dropped the `### Qt & GUI` section (kept Bench under new `### Bench`);
  fixed the Overview hook (Qt GUI → headless) + the Architecture hook (`ModuleSpec` →
  `Module` subclass).
- `AGENTS/docs/debugging.md` — ports `VITE_PORT`→`SERVER_VITE_PORT`; launch table
  `dev-watch`/`web-watch`/`gui-watch` + `DEV=true`/`QDesktopServices` → `group-server`/
  `watch-web`/`run-server-worker`; dropped the Qt-loop troubleshooting row.
- `AGENTS/docs/core-architecture.md` — "основное web+GUI" → one assembled headless app.
- `AGENTS/docs/INDEX.md` — debugging summary "Qt remote debugging" → browser DevTools.
- `AGENTS/memory/project_loggers.md` — global-tee "works for GUI, MCP servers" → "any
  entry point (server/worker)".
- `src/core/database/README.md` — "без сервера/Qt" → "без подъёма сервера".

Left intentionally:
- `dev/docs/BUILD.md` — already correctly notes `PySide6`/`qasync` are still deps (Qt
  legacy), move to optional `gui` group is TBD. Accurate.
- `AGENTS/memory/project_crud_session_ownership.md` — "Qt browser" is an illustrative
  legacy example; the CRUD-grep lesson is still valid.

Separate staleness noticed, NOT GUI (flagged, not fixed): `bench/` → `dev/bench/` path is
wrong in `project_bench_layout.md` body + `dev/bench/**/README.md` run commands
(`python -m bench.…`; no top-level `bench` package anymore). The MEMORY index hook was
corrected to `dev/bench/`.
