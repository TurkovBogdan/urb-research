---
title: Audit AGENTS/docs against the post-refactor code
date: 2026-06-07
status: completed
description: "After a large refactor, verify every file in AGENTS/docs reflects the real code; report stale descriptions and fix on go-ahead."
tags: [docs, audit]
---

## Task

User: "проект прошёл большой рефактор, документация могла устареть. Нужно сверить её с реальным кодом @AGENTS/docs".

## Context

Big headless refactor (Qt/MCP-apps removed, `Module` ABC, `src/app.py` entry, router zones + guards, core_users auth, MCP-as-server surface). Docs may describe pre-refactor reality.

## What was done

- Read docs INDEX + tasks INDEX.
- Parallel per-doc audit (5 Explore agents) against current code; key claims re-verified by hand (markdown lib, i18n fallback, module table, guards, migration prefixes, bench dirs).
- Applied fixes to the stale docs (see Result).

## Result

Edited docs:
- `core-module-system.md` — full `Module` attr table (`internal_router`/`guards`/`mcp_servers`/`mcp_token_resolver`), `configure` no longer `include_router` (declare `internal_router`), settings path `/core/settings`, registration via `apps/app/modules.py::build_modules`, **12-module table** with migrations/settings/config columns verified per `module.py`.
- `conversations/schema.md` — `id` str PK `provider-provider_id` (not BigSerial), `synced_at`→`ingested_at`+`processed_at`, added `initiated_member_id`/`parser_version`/`content_hash` (+message `content_hash`), soft-delete note; 4-table set.
- `i18n.md` — fallback mismatch flagged (code `fallbackLocale:'en'` vs "ru primary" intent), language switcher moved to profile «Язык и регион» card, `/tasks` path.
- `benches.md` — `bench/`→`dev/bench/`, `python -m dev.bench.…`, `APP_PROFILE`→`APP_ENV`, real bench list.
- `soft-delete.md` — replaced fake migration IDs (`i6n0t0…`) with entity/table list across 7 modules; deleted_at ships in create-table migrations.
- `router.md` — added `self`/`token_owner` guards; corrected example.
- `frontend-layout.md` — full store fields (mobileOpen + action-sheet), PageHeader `backTo`/`loading` props + `#before` slot, softened PageLayout "обязана".
- `frontend-validators.md` — added password helpers (`PASSWORD_MIN_LENGTH`/`passwordChecks`/`passwordValid`/`passwordPolicy`); noted `minLength`/`required` are illustrative.
- `dates.md` — added `fmtDateUtc`/`fmtRelativeShort`/`fmtDaysAgo`, tz-prefs rendering note, fixed deleted `src/core/api.py` ref → core_monitoring.
- `frontend-route-meta.md` — precise `canNavigate` (leaf-pair vs `matched.every` fallback).
- `migrations.md` — real prefixes (`c` not `cv`), legacy-chain note (llm_providers/team), core date-based scheme.
- `markdown-rendering.md` — server-vs-client class asymmetry (client only `md-pre`/`md-code`/`md-codespan`, rest by tag selector).
- `debugging.md` — `/api/core/tasks`→`/internal/tasks` + auth note, Swagger/OpenAPI disabled.
- `INDEX.md` — router MCP entry (live), conversations/schema entry.

Accurate, untouched: `core-architecture.md`, `permissions.md`, `core-locks.md`, `core-loggers.md`, `database.md`, `twenty.md`, `conversation_insights/INDEX.md`, `intercom/INDEX.md`, `vuetify-css-patterns.md`, `frontend-api-client.md`, `testing.md`.

## Open item for the user

`i18n.md` fallback: code has `fallbackLocale: 'en'` but the stated convention is "ru is source of truth, en falls back to ru". Likely a **code** bug (should be `'ru'`), not a doc error — flagged in the doc, awaiting decision.
