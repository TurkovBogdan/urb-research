---
title: Strip auth/permissions from the bare-core shell (AGENTS docs + web/src)
date: 2026-06-27
status: in-work
description: "After the core was stripped to bare src/core (all modules removed), purge leftover descriptions of old-module functionality from AGENTS, and remove all authentication/authorization/users/permissions code from the web/src frontend — it is now a local site with no auth."
tags: [frontend, docs, cleanup]
---

## Task

После зачистки ядра от всех старых модулей:
1. Убедиться, что в `AGENTS/` не осталось описания функционала старых модулей.
2. В `web/src/` оставить только общие наработки и убрать всё, что относится к авторизации и правам (это локальный сайт).

## Context

`build_modules()` returns `[]` — bare `src/core`. Module dirs, doc hubs, and module memory files were already deleted in task `2026-06-24-remove-non-core-modules`. This task finishes the sweep: dangling doc links / stale module prose in AGENTS, and the still-present auth stack in the frontend (auth store, CASL permissions, login/forbidden views, /me bootstrap, 401/403 redirects).

## What was done

**Part 1 — AGENTS docs (reference tier).** Doc hubs + module memory files were already gone (task `2026-06-24`). Remaining stale prose was the *frontend* auth that this task deletes:
- `docs/frontend/route-meta.md` — rewrote: dropped the whole access-control section (`public`/`guestOnly`/`action`/`subject`, guard flow, `/login`, `/403`); kept only layout meta.
- `docs/frontend/api-client.md` — removed the auth-redirect bullet, the `on401`/`on403` opt-outs, reframed security posture (no session cookie).
- `docs/frontend/validators.md` — dropped the password-policy rows (helpers removed from code).
- `docs/frontend/i18n.md` — dropped the `auth` root-lifted namespace; replaced the non-existent `common.error.*`/`tError` section with the real `common.errors.*` bucket.
- `docs/INDEX.md` — frontend api-client + route-meta rows de-authed.
- `docs/platform/database.md` — fixed a pre-existing broken link → `plans/archive/2026-05-30-remote-database.md`.
- Verified: platform/backend docs describing a *future auth module* (api-zones, router, module-system, mcp/INDEX) are the correct bare-core design — left intact. `backend.md` `User` actor-split example is a generic archetype — left intact. Indexes carry no dangling hub links; full `docs/` markdown link-scan = 0 broken.

**Part 2 — web/src (remove auth/permissions).**
- Deleted: `stores/auth.ts`, `api/auth.ts`, `plugins/casl.ts`, `types/casl.d.ts` (+ empty `types/`), `views/auth/LoginView.vue` (+ dir), `views/errors/ForbiddenView.vue`, `locales/auth/{en,ru}.json` (+ dir).
- `router/guards.ts` — stripped to progress-bar + tooltip-dismiss + nav-history (no `/me`, no CASL, no redirects).
- `router/index.ts` — dropped `/login` + `/403` routes. `router/meta.ts` — dropped access-control meta. `router/design-system.ts` — dropped `action/subject` from all 47 routes. `shared/nav.ts` — dropped `action/subject`.
- `App.vue` — removed auth store, top-bar avatar/profile button + its CSS. `layout/components/AppSidebar.vue` — removed CASL permission filtering (nav now shown unconditionally; kept orphan-section filter). `main.ts` — removed `casl` plugin. `index.html` — boot-splash comment de-authed.
- `api/client/internal.ts` — removed 401→/login & 403→/403 redirects, `on401`/`on403` options, `FORBIDDEN_CODE`, session-cookie prose.
- `features/settings/views/SettingsView.vue` — removed `$can('manage','admin')` gates (settings now always editable).
- `plugins/i18n.ts` — dropped the `auth` namespace. Relocated the still-used error keys (`notFound`, `action.back/home`) into `common.errors.*` (`locales/{en,ru}.json`); repointed `ErrorState.vue` + `NotFoundView.vue`.
- `shared/utils/validators.ts` — removed the dead password-policy helpers (kept generic `isSlug`).
- `package.json` + `pnpm-lock.yaml` — removed `@casl/ability` + `@casl/vue` (lock diff = 54 deletions, casl-only).

## Problems

`vue-tsc`/`pnpm` could not run a real type-check here: the local pnpm store (`web/node_modules/.pnpm`) is a pre-existing sparse/broken install (Jun 24) — many packages' bin files (`vue-tsc`, `vite`, `tsc`, …) were never extracted. Static verification done instead: all imports resolve, no dangling references in edited files, locale JSON valid, full grep sweep for auth terms clean. User should run `pnpm install && pnpm --dir web type-check` after a network-capable install.

## Result

Frontend is auth-free; AGENTS reference docs no longer describe removed-module or removed-auth functionality. **Open (deferred by task `2026-06-24`):** archive-vs-delete decision for `AGENTS/plans/`, `AGENTS/research/`, `AGENTS/education/` entries of deleted modules (and the stale "In work" rows in `plans/INDEX.md`) — pending user direction.
