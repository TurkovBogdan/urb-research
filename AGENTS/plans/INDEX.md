# PLANS INDEX

Implementation plans for the project. Each plan in a separate file. Filename format: `YYYY-MM-DD-slug.md`.

## Rules

- Create `AGENTS/plans/YYYY-MM-DD-slug.md` from `AGENTS/plans/TEMPLATE.md` when the user asks for a plan.
- The slug describes the area, not the action.
- Add an entry to the "In work" table below.
- Set status to `completed` on completion; then move the row to "Completed".

## In work

Plans currently being executed.

| File | Date | Description |
|------|------|-------------|
| [2026-06-14-page-header-smart-back.md](2026-06-14-page-header-smart-back.md) | 2026-06-14 | **Plan (not started).** `PageHeader` back arrow returns to the **actual previous in-app page** instead of a hard-coded parent. Today `PageHeader.vue` does a fixed `router.push(backTo)`; same detail page is reachable from many parents → user expects "back" = where they came from. Fix: track the immediate previous in-app route in `router.afterEach` (real prev = `from.matched.length>0`, START_LOCATION = none) via a small tracker (composable/store) exposing `goBack(fallback)`; back button → `router.back()` when in-app history exists (restores list scroll + KeepAlive), else `router.push(backTo)`. **`backTo` becomes the fallback** → ~50 call sites unchanged. Open (defaults chosen): back() vs push(savedPath). Task: `2026-06-14-page-header-smart-back`. |
| [2026-06-03-api-zones.md](2026-06-03-api-zones.md) | 2026-06-03 | Split HTTP into 3 zones (`internal`/`api`/`webhook`); core owns one zone-router per zone aggregating module sub-routers (`router_internal`/`router_api`/`router_webhook`); routes carry a protection label (`private` default, `@public` opts out); core ships a default-**deny** guard per label + `set_guard(label, fn)` registry so `core_users` plugs the real check (zero auth logic in core). Migration `/api`→`/internal` (backend + 9 frontend BASE + nginx + tests). Decisions: deny-all-by-default (no dev pass-through), `/webhook` singular, guard sig `async(request)->None` raises. |
| [2026-06-03-tasks-worker-split.md](2026-06-03-tasks-worker-split.md) | 2026-06-03 | Extract scheduler/cron + task execution out of the headless API into a dedicated `worker` process (same codebase, worker mode, no FastAPI). API sets `SCHEDULER_ENABLED=false` and triggers on-demand runs by persisting a DB run-request row (+ optional `LISTEN/NOTIFY`) instead of `asyncio.create_task(run_entry)`; the worker owns the ticker (cron + run-request consume). Coupling points: registry built from module code (→ shared bootstrap) + manual-run line `api.py:121`. Run-request shape R1(`requested` status) vs R2(new `core_task_requests` table) open, leaning R2. |

## Completed

Plans the user has confirmed as complete.

| File | Date | Description |
|------|------|-------------|
| [2026-06-10-core-module-state-store.md](2026-06-10-core-module-state-store.md) | 2026-06-10 | **DONE.** Core **generic per-module state store** for arbitrary runtime data (import cursors, counters, markers) — "куда модулю положить состояние задачи". New table `core_modules_state` (PK `(module, code)` — chose `code` over `key`; `value` **JSONB**; `created_at`/`updated_at`), sibling of `core_modules_settings` but for **internal machine state**, not operator config (no schema/registry/API/UI). `CoreModuleState` model + `crud/module_state.py` (dialect-aware upsert: `get_one`/`get_value`/`upsert`/`seed_if_absent`/`delete`/`delete_for_module`/`list_for_module`/`list_all`) + bound accessor `ModuleStore`/`module_store(code)` (`get`/`set`/`seed_if_absent`/`delete`/`all`) + `Module.store` property (= `module_store(self.name)`). Migration `c0re00010005` (`down_revision=c0re00010004`). Doc `platform/module-state.md` + memory router + docs INDEX. Tests: 9 db (CRUD + JSONB nested round-trip + composite-key isolation + accessor + `Module.store`) green; heavy migration table-set assertion extended, green; dev DB migrated, `migrate check` no drift. |

## Deferred

Plans paused at the user's request. Move the row here from "In work" and set status to `deferred` in the plan's frontmatter.

| File | Date | Description |
|------|------|-------------|

## Archive

Archiving runs via the [`agent-tasks-maintenance`](../agent-tasks-maintenance.md) playbook: a `completed` plan whose every related task is completed-or-archived is moved into `AGENTS/plans/archive/`, its row removed from this index and added to [`AGENTS/plans/archive/INDEX.md`](AGENTS/plans/archive/INDEX.md). A manual archive request works as an addition.
