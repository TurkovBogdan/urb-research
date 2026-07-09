---
title: Migrate the app from a desktop binary to a server deployment
date: 2026-06-01
status: in-work
description: "The app currently ships as a Qt-shelled PyInstaller binary (status window + embedded browser) that runs an in-process FastAPI server against a remote DB. Goal: run it headless on a server. Scope/topology under discussion."
tags: [deploy, server, ops, infra]
---

## Task

User wants to migrate the currently self-contained desktop application (Qt status window + embedded FastAPI + remote PostgreSQL) onto a server. Collaborative scoping ("помогай сообразить").

## Context

Current run model (`app_run.py` → `run_gui_app`):
- Qt `QApplication` (needs a display; forces `QT_QPA_PLATFORM=xcb` on Linux) boots a status window + embedded browser pointing at `http://SERVER_HOST:SERVER_PORT`.
- FastAPI app (`src/apps/app/server.py:app`) runs in a daemon `ServerThread` (uvicorn) inside the same process.
- The ASGI app is already server-ready on its own: `mount_spa` serves the built SPA (`_MEIPASS/web` frozen, else `dist/build/web`), `create_app` lifespan runs Alembic (`DB_AUTO_MIGRATE`) + scheduler + module startup; remote DB + verify-full TLS already hardened (see [[db_tls_strict_contract]], remote-database task).
- `semaphore-core-mcp` is a separate binary; MCP servers are stdio (`app_run_mcp.py <name>`).

Findings:
- Only Qt couples the app to a desktop. Headless = run `src.apps.app.server:app` under uvicorn without `run_gui_app`.
- **No HTTP auth anywhere** — it was a LAN/desktop tool. Critical gap before any network exposure.
- `SERVER_HOST` defaults `127.0.0.1`; CORS only allows the Vite ports (single-origin prod needs no CORS).
- Scheduler runs in-process → must stay single web worker (`--workers 1`) or the scheduler doubles (CoreLock guards correctness but not waste).

## Decisions (2026-06-01)

- **Run form:** Docker container (run from source — uvicorn; NO PyInstaller/Qt needed, since `pnpm build` → `dist/build/web` is exactly where non-frozen `mount_spa` looks).
- **Exposure:** public internet.
- **HTTPS:** reverse-proxy (nginx/Caddy) terminates TLS; app listens inside the container network.
- **Auth:** built-in app-level auth (login + sessions/JWT + users table + middleware on `/api`). Mandatory — public + zero existing auth.

## Plan (phased)

- **P1 — `core_auth` module (the real work):** users table + password hashing + login/logout/me endpoints + middleware gating all `/api/*` (except `/api/health`, `/api/auth/*`); bootstrap admin from env; frontend login view + route guard + 401 interceptor + auth store.
- **P2 — Containerization:** multi-stage Dockerfile (node→pnpm build, python→uv, copy web to `dist/build/web`, run `uvicorn ... --workers 1`); docker-compose (app + Caddy/nginx; external DB; env_file secrets; mount `cert/` for DB TLS); `.dockerignore`; reverse-proxy config (auto-HTTPS + security headers).
- **P3 — Ops hardening:** single web replica only (scheduler is in-process; `--workers 1`); log to stdout in container; compose healthcheck on `/api/health`; CORS can be dropped for single-origin prod; consider an optional dep-group to drop PySide6 from the server image.

## What was done

- (pending plan approval) — analysis + decisions captured; plan drafted.

## Result

(in progress)
