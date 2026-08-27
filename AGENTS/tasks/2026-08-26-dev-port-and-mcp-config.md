---
title: Dev instance port isolation + MCP connection config
date: 2026-08-26
status: completed
description: "Give the in-development checkout its own port, separate from the stable instance, and hand the user a ready stdio MCP connection config for it."
tags: [runtime, mcp, ports]
---

## Task

«Выделить под разрабатываемую версию отдельный порт, обновить конфиг и дать конфиг подключения»
(в формате с `env.MCP_TOKEN` и `"type": "stdio"`).

## Context

Two checkouts now run side by side: the stable one (`…/urb-research-stable`, live backend +
a fleet of `--mcp-stdio` shims) and this development one. They must not share a port or a token,
otherwise a shim started for one would bridge to the other's backend — `mcp_stdio.py` connects to
`http://<SERVER_HOST>:<SERVER_PORT>` and reuses an already-running backend if it answers health.

## What was done

- Checked both `.env` files: stable = `SERVER_PORT=22020`; this checkout = `SERVER_PORT=22040`,
  `SERVER_VITE_PORT=22041` — already a distinct pair, and both ports verified free (`ss -ltn`).
  No `.env` change was needed; the isolation requirement was already satisfied.
- Tokens are separate too: each checkout has its own `MCP_TOKEN` in its own `.env`.
- Booted this checkout live to prove the port and the freshly imported DB work:
  `.venv/bin/python src/app.py --backend --worker` → `:22040`, `/internal/health` 200,
  lifespan brought up all six modules.
- Pulled the connection config from the app itself (`GET /internal/core-mcp/servers/research`,
  built by `core_mcp/api.py::_stdio_config`) rather than hand-writing it — 23 tools reported.
- Handed the user that config renamed to a `urb-research-dev` key (the key is client-side naming;
  `MCP_STDIO_CODE` stays unset because this app mounts exactly one MCP server, `research`).

## Result

- Dev: backend `:22040`, Vite `:22041`, own `MCP_TOKEN`. Stable: `:22020`, untouched.
- The dev backend was left running on `:22040`; a shim spawned by an MCP client will reuse it.

Flagged, not changed: `AGENTS/tools/stop-all.sh` reads the ports from `.env` correctly, but its
`pkill -TERM -f 'app\.py'` line is not scoped to a project root — running it from this checkout
would also kill the stable instance's backend and its `--mcp-stdio` shims.
