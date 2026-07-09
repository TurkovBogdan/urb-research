---
title: Tasks UI — clickable cards, localStorage list, fresh skeleton detail, server-sorted runs table
date: 2026-05-31
status: completed
description: "Update web/src/features/tasks: make task cards clickable into logs; persist the task LIST in localStorage (stale-while-revalidate, no card jitter); detail (runs) view shows a skeleton on open instead of stale data and never caches; detail filter panel brought to the standard table layout with full backend sorting."
tags: [frontend, tasks, core-api]
---

## Task

1. Make task cards clickable — click drills into the runs/logs page.
2. Store the task LIST in localStorage (list only), still auto-refreshing and on click — so cards don't visually jitter on revisit.
3. Detail (runs) view: show a skeleton loader on open, not the previous logs' stale data. No caching / localStorage in the detail — open = fresh data.
4. Detail top filter panel brought to the standard used on other tables; the runs data table gets full backend sorting (server-side, not just current page).

## Context

- `TasksView.vue` already has a `.filter-panel` + skeleton + grouped cards; cards have an explicit "logs" button. Store `tasks.store.ts` keeps the list in memory only.
- `TaskRunsView.vue` is KeepAlive-cached (App.vue wraps RouterView in `<KeepAlive>`), so navigating between two tasks' logs reuses the instance and shows the previous task's runs until the fetch resolves (`loading` never goes back to true). The filter is a bespoke `filters-bar`, not the standard `.filter-panel` VCard. Sorting is client-side only (data table over the current page).
- Standard table reference: `intercom/views/ConversationsView.vue` + `conversations.store.ts` + backend `_SORTABLE` map in `crud/conversation.py`.

## What was done

**Backend — server-side sorting for runs**
- `src/core/crud/tasks.py` → `list_runs` gained `sort_by`/`sort_dir`; new `_SORTABLE` map (`id`, `status`, `started_at`, `finished_at`, `duration = finished_at - started_at`), `nullslast()`/`nullsfirst()` for null finish/duration, tie-break on `id desc`. Default unchanged (`started_at desc`).
- `src/core/api.py` → `GET /tasks/{module}/{code}/runs` gained `sort_by` (Query default `started_at`) + `sort_dir` (`^(asc|desc)$`), passed through.

**Frontend — `web/src/features/tasks`**
- `api.ts` → `fetchTaskRuns` opts gained `sortBy`/`sortDir` → `sort_by`/`sort_dir` params.
- `tasks.store.ts` → task LIST persisted in `localStorage` (`core.tasks.list`, stale-while-revalidate): store hydrates from cache on creation (`loading=false` when cached so the skeleton shows only on the first-ever visit), `load()` writes the cache. Cards render instantly from cache on revisit and update in-place (stable `module.code` key → no remount, no jitter). Auto-refresh on activate + refresh button unchanged.
- `views/TasksView.vue` → whole card clickable (`role/tabindex/@click/@keydown.enter → openRuns`), hover/focus affordance, run button now `@click.stop`; dropped the standalone "logs" button for a right-aligned `.task-card__open` "→ logs" hint (`IconChevronRight`).
- `views/TaskRunsView.vue` (detail) → **no caching**; new `reload()` clears state and shows a skeleton (`VSkeletonLoader table-row-divider@8`) on every entry, wired to `onActivated` + a `watch` on `(module, code)` so the previous task's runs never linger. Bespoke `filters-bar` replaced by the standard `.filter-panel` VCard (clearable status `VSelect`), refresh moved into `PageHeader #actions`. `VDataTable` switched to **server-side sort** (`must-sort`, `:sort-by="tableSortBy"`, `@update:sort-by`, sortable headers id/status/started/finished/duration, `:loading="refreshing"`). Pagination moved inside the card under a `VDivider` as the standard `.pagination-bar`. Filter/page/page-size are explicit handlers (no `watch`) to avoid double-loads.

**Follow-up — header divider color (DS violation), fixed globally**
- Root cause: with `fixed-header` Vuetify zeroes the header `border-bottom` and draws the divider as `box-shadow: inset 0 -1px 0 rgba(var(--v-border-color), var(--v-border-opacity))` (near-black on-surface). The global `.v-data-table` section in `main.scss` only styled the non-fixed `border-bottom` (`--border`), so it never covered the sticky-header case → dark line.
- Made it a **standard**, not a per-page hack: added `&.v-table--fixed-header .v-data-table__th { box-shadow: inset 0 -1px 0 var(--border) !important }` to the global `.v-data-table` section (`web/src/styles/main.scss`), matching the token used for the ordinary header `border-bottom`. Every `fixed-header` table now gets the same soft divider automatically.
- Removed the bespoke `:deep(.v-data-table__th)` block from `TaskRunsView.vue` entirely (it had been re-styling bg/size/color + the divider workaround); the runs header now inherits the global standard look. `fixed-header` is used in only two views (TaskRunsView + design-system LayoutView) and no view has a per-page `__th` override, so the global rule is conflict-free.

Tests: no new tests (UI + thin query passthrough); existing core suite covers the endpoint. `vue-tsc --noEmit` clean; `uv run pytest --core` → 161 passed.

## Result

Changed: `src/core/crud/tasks.py`, `src/core/api.py`, `web/src/features/tasks/{api.ts,tasks.store.ts,views/TasksView.vue,views/TaskRunsView.vue}`. Leftover unused locale key `tasks.runs.status_all` (status filter is now clearable = "all"); harmless.
