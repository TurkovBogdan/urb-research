---
title: Port core_mcp module (MCP-server introspection page)
date: 2026-07-04
status: completed
description: "Port the core_mcp module (backend + frontend) 1:1 from semaphore-core into this project: read-only «MCP-серверы» introspection page over app.state.mcp_servers."
tags: [core_mcp, mcp, frontend]
---

## Task

«перенеси его 1 к 1 в текущий проект» — port the `core_mcp` module (backend `src/modules/core_mcp` + frontend feature) from `AGENTS/semaphore-core` into `src/` + `web/`.

## Context

`core_mcp` is a read-only introspection surface over the core MCP mount (`src/core/router/mcp.py::mount_mcp_servers` puts live FastMCP instances into `app.state.mcp_servers`). It lists mounted MCP servers (`/mcp/<code>`), their tools, and a ready-to-paste remote connection config (Claude desktop via `npx mcp-remote`, Claude Code via Streamable HTTP). It was removed in the 2026-06-24 module strip; now re-ported into the no-auth fork.

The shared frontend deps (`web/src/components/McpInfoPanel.vue`, `web/src/shared/mcp_tool_icons.ts`) were already present and identical — only the feature folder + wiring were missing.

## What was done

Backend (`src/modules/core_mcp/`, 1:1 except auth):
- `__init__.py`, `module.py`, `api.py` copied verbatim; dropped `@guard("ability","manager:read")` decorators + the `guard` import (internal zone default = `allow_all` in this no-auth fork, same as core_monitoring).
- Registered `CoreMcpModule()` in `src/apps/app/modules.py` (after core_monitoring) + docstring note.

Frontend (`web/src/features/core_mcp/`):
- `api.ts`, `views/McpServersView.vue` copied verbatim; `routes.ts` without `action`/`subject` meta; `locales/ru.json` from source (en dropped — this project loads only `ru.json` per feature).
- No `nav.ts` (project has no nav-aggregation) — added a nav item to the central `nav` array in `layout/components/AppSidebar.vue` (section «Мониторинг», `IconServerBolt`).
- Registered `coreMcpRoutes` in `web/src/router/index.ts`.

Verification: backend `build_modules()` lists `core_mcp` with routes `/servers`, `/servers/{code}`; `vue-tsc --noEmit` clean (0 errors). No tests added (module has no DB/logic — pure introspection over live state).

## Result

Created: `src/modules/core_mcp/{__init__,module,api}.py`, `web/src/features/core_mcp/{api.ts,routes.ts,views/McpServersView.vue,locales/ru.json}`.
Changed: `src/apps/app/modules.py`, `web/src/router/index.ts`, `web/src/layout/components/AppSidebar.vue`.
Reused as-is (already present): `web/src/components/McpInfoPanel.vue`, `web/src/shared/mcp_tool_icons.ts`.
Note: `web/dist` not rebuilt (no pnpm on PATH; vite build not run) — rebuild before deploy.
