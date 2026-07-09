---
title: User-requested task runs (core_task_requests queue + watcher)
date: 2026-06-11
status: completed
description: "Queue table for user-initiated scheduler-task runs, owned end-to-end by core_users: enqueue API (manager+), a permanently-running watcher task that serves the queue by observing core_tasks, manual_run→user_request rename."
tags: [core_users, scheduler, core_monitoring]
---

## Task

Add the ability to run a scheduler task on user request with priority: a queue
table holding code + request time; the worker checks the table with locks etc.
Iterated in discussion to: rename `manual_run`→`user_request`; table named as
*requests* (not queue) with `requested_by`, `status` (mirroring task statuses +
`pending`), nullable `task_id`; API gated at manager level; no duplicate pending
request per task; **core_users owns all the code** (the migration needs the
users table) — so the consumer is a permanently-running watcher task, not the
core ticker.

## Context

The scheduler had only cron scheduling; `manual_run` was a UI label backed by a
fire-and-forget endpoint in core_monitoring (`asyncio.create_task(run_entry)`)
with no queueing, no dedup, no record of who asked. Core cannot reference a
module's table (migrations: core chain can't `depends_on` a module chain;
models: cross-metadata FK breaks `create_all` in tests), so ownership had to
sit in core_users entirely.

## What was done

- **Rename** `manual_run` → `user_request` through the stack: `TaskEntry`,
  `CoreTaskBase.USER_REQUEST`, `scheduler.register()`, all 20 module task
  classes, monitoring `TaskInfo` DTO, FE `api.ts` type + `TasksView` button
  gate (`$can('manage','manager')` now).
- **Table** `core_task_requests` (model `core_users.models.TaskRequest`):
  id / module / code / status(pending|running|success|error) / priority
  (default 500, lower = sooner) / task_id (bare Integer in model; FK→core_tasks
  only in the migration) / requested_by FK→core_users SET NULL / requested_at.
  Partial
  `UNIQUE(module,code) WHERE status='pending'` enforces single pending request
  per task. Migration `cu06_task_requests` (core_users chain,
  `depends_on="c0re00010001"` — the non-head core revision creating
  `core_tasks`).
- **CRUD** `core_users/crud/task_request.py`: `enqueue` (INSERT ... ON CONFLICT
  DO NOTHING → None on duplicate), `list_pending` (priority, requested_at
  order), `list_running`, `attach_run`, `finalize`.
- **Watcher** — "постоянно выполняемая задача" `core_users.watch_task_requests`
  (`SCHEDULE="* * * * *"`, TTL 90, ~55s inner loop polling every 5s → a
  continuous queue consumer; single instance guaranteed by the scheduler's own
  partial-unique + task lock). Logic in
  `core_users/service/task_requests.py::process_once` — requests are served by
  **pure observation of core_tasks** (runner/ticker know nothing about
  requests): pending→running/final when a run of the pair with
  `started_at >= requested_at` appears (whoever started it — watcher or cron,
  which also kills the "request 5s before the cron run → double execution"
  case); running→success/error when the linked run finalizes (zombie-cleanup
  included); pending with no satisfying run → spawn `run_entry`
  (fire-and-forget) unless the pair is currently running; unservable requests
  (unregistered / disabled / not user_request) → error.
- **Core helpers** (generic core_tasks queries, no request knowledge):
  `crud/tasks.py` `get_running_set`, `first_run_since`, `statuses_by_ids`.
- **API** `POST /internal/core-users/task-requests/{module}/{code}`
  (`manager:update`): 404 unregistered, 403 disabled / not user_request,
  409 duplicate pending, 202 + request_id. Old monitoring endpoint
  `/tasks/{m}/{c}/run` removed (its admin-only route contract test restored);
  FE `runTask()` repointed, signature unchanged.
- **Requests monitoring section** (FE, under task monitoring): backend list
  `GET /internal/core-users/task-requests` (`admin:read`; paginated, optional
  `status` filter, newest-first; LEFT JOIN core_users for `requested_by_name`)
  via `crud.list_requests` + DTO `TaskRequestView`/`TaskRequestsPage`. FE page
  `views/TaskRequestsView.vue` at `/tasks/requests` (VDataTable: task /
  status-chip / priority / requester / requested_at / linked run #→runs page;
  status filter + pagination, mirrors `TaskRunsView`); reached via a
  «Запросы»/Requests button in the `TasksView` header. i18n `requests.*` ru/en.
- **Tests**: new `tests/modules/core_users/test_task_requests.py` — 14 cases
  (enqueue dedup + re-enqueue after finalize; watcher serves a request;
  external/cron run satisfies a request without respawn; run started before
  the request is ignored → waits and respawns after; unregistered /
  non-user_request → error; API 403/404/409/202; list admin-gate +
  requester-name + status filter). Monitoring tests updated for the rename.

## Problems

- FK `requested_by → core_users.id` from a core-owned model broke
  `Base.metadata.create_all` in tests without core_users metadata (and
  `use_alter=True` doesn't help — still resolved at create_all). Solved by the
  ownership move itself; the remaining cross-boundary FK (`task_id`) lives
  only in the migration, bare Integer in the model.
- A core-chain migration with `depends_on="cu01_init"` broke
  `test_retired_team_branch_tombstones_collapsed_into_core` (loads the core
  branch alone → unresolvable dependency). Module-chain migrations can depend
  on core revisions, not vice versa — another push toward core_users ownership.
- First watcher design (claim request in ticker before `create_running`) had a
  crash window leaving requests stuck in `running` + a reset race under the
  partial-unique index. Replaced with claim-after-create, then simplified
  further to pure observation (no claim at all) once the watcher moved out of
  core.
- `--core --dbs 1` showed 11 phantom failures (xdist workers sharing one DB);
  core suite must run on the full pool per testing.md. Module runs on 2 slots
  for 2 modules also collided (26 failures) — fine on `--dbs 1-4`.
- `TIMESTAMP(precision=0)` second-rounding makes `started_at >= requested_at`
  comparisons flaky in tests when both land in the same second → tests age
  the request/run rows backwards instead of sleeping.

## Result

Working user-request queue for scheduler tasks, owned by core_users. Changed:
`src/core/scheduler/{registry,task_base,__init__}.py` (rename),
`src/core/crud/tasks.py` (observation helpers),
`src/modules/core_users/{models.py,module.py,api.py}`,
`src/modules/core_users/crud/task_request.py` (new),
`src/modules/core_users/service/task_requests.py` (new),
`src/modules/core_users/tasks/{__init__,watch_task_requests_task}.py` (new),
`src/modules/core_users/migrations/versions/cu06_task_requests.py` (new),
`src/modules/core_monitoring/api/tasks.py` (endpoint removed, DTO renamed),
20 module task files (USER_REQUEST), `web/src/features/core_monitoring/{api.ts,
views/TasksView.vue}`, tests (new file + monitoring updates).
Verified: `--core` 232, `core_users+core_monitoring` 294, heavy 24, vue-tsc —
all green; dev DB migrated (`cu06` applied), `migrate check` clean.
