---
title: Docs refresh — headless server migration
date: 2026-06-04
status: completed
description: "User flagged README + dev/docs as stale after the PyInstaller-desktop → headless-server migration. Verify each doc against the actual code and bring them current."
tags: [docs, deploy, build]
---

## Task

User: "вся документация устарела, проверяй" pointing at `README.md` + `dev/docs/`.
Verify all four docs against the current codebase and update.

## Findings (verification)

Architecture migrated: PyInstaller desktop binary (Qt window + embedded FastAPI,
served own SPA on `:13410`) → **headless server**. Unified entry `src/app.py`
(`server`/`worker`/`migrate`); static SPA served by **nginx (prod) / Vite (dev)`;
built front committed to git (`static/`); deploy = `git pull` + `uv sync`. Qt GUI
(`src/gui/`) + all MCP apps (`src/apps/mcp_*`) deleted.

- **README.md** — stale: Qt shell, "single PyInstaller binary", `app_run.py`/
  `app_build.py` entry points, `src/gui/`, root `assets/`, `dist/` as output.
  New dirs missing: `static/`, `storage/`, `tools/`.
- **BUILD.md** — fully stale (whole doc = PyInstaller `app_build.py` + `dist/release/`
  binary). New model in `new_structure/README.md`; prod artifacts (Dockerfile/compose/
  nginx.conf) still TBD (task `2026-06-02-server-docker-migration`, in-work).
- **DEVELOPMENT.md** — mostly current; stale bits: `build-app | app_build.py` table row
  (no such `.run` config / script), "Запуск собранного: `app_run.py` — Qt-окно".
- **ENV.md** — accurate. Env names verified against `src/core/config.py`
  (`SERVER_*`/`WORKER_*`/`APP_*`/`DB_*`). Task-index mention of `app_backend.py`/
  `BACKEND_*` was an abandoned branch; final state is `src/app.py` + `SERVER_ENABLED`.

## Decision

User chose: rewrite BUILD.md into a deploy guide (git pull + uv + nginx + storage-split
per `new_structure/README.md`), noting Dockerfile/compose/nginx.conf are TBD.

## What was done

- **README.md** — rewrote architecture line (headless: Vue + FastAPI + PG, `src/app.py` entry,
  nginx/Vite static, `git pull` deploy) + structure tree (added `src/app.py`, `static/`,
  `storage/` public/protected, `tools/`; dropped `src/gui/`, root `assets/`, `dist/` as output;
  BUILD.md link relabeled «Деплой»).
- **BUILD.md** — rewrote PyInstaller doc → deploy guide: topology (nginx → static/ + proxy →
  backend; worker separate), tools list, front build to `static/`, `uv sync`, storage-split +
  `tools/storage_mount.sh --prod`, `.env.prod` + `app_hash_password.py`, migrate, run
  `--backend`/`--worker`. Flagged Docker/compose/nginx.conf + PySide6-group as TBD.
- **DEVELOPMENT.md** — dropped `build-app`/`app_build.py` table row; removed «Запуск собранного»
  (`app_run.py`/Qt) block; de-Qt'd the dev proxy line; «Сборка дистрибутива» → «Деплой на сервер»;
  stop-all `:13410 (release)` → `(prod-порт)`.
- **ENV.md** — verified accurate vs `src/core/config.py`; no edits needed.

## Result

README + BUILD + DEVELOPMENT updated; ENV verified. Out of scope but still stale (flagged to user):
`CLAUDE.md`/`AGENTS.md` (Qt/PyInstaller architecture description) and some `AGENTS/memory/`
overview entries.
