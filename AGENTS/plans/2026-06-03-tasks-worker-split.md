---
title: Tasks/cron worker split (API ↔ worker process separation)
date: 2026-06-03
status: in-work  # in-work | completed | deferred
description: "Extract the scheduler/cron + task execution out of the headless API process into a dedicated worker process (same codebase, worker mode). API signals on-demand runs via a DB run-request row (+ optional LISTEN/NOTIFY); the worker owns the ticker and runs handlers."
tags: [scheduler, tasks, deploy, architecture]
---

## Goal

Background tasks and cron no longer run inside the API process. A dedicated `worker` process
(same `semaphore-core` image, worker mode, no FastAPI) owns the ticker and executes all task
handlers. The API process serves requests only (`SCHEDULER_ENABLED=false`) and triggers
on-demand runs by **persisting a run-request row** that the worker picks up — never by calling
`run_entry` in-process. Cron needs no cross-process signal (the worker checks schedules off the DB).

## Context

Current state (`src/core/scheduler/`):
- The ticker (`ticker.py`) starts inside `create_app` lifespan → every uvicorn worker spins its own.
- Execution state is entirely in the DB: `core_tasks` (+ partial-unique `(module, code) WHERE
  status='running'`), `core_tasks_logs`, `core_locks`.
- The runner is already **multi-instance safe**: distributed DB lock `task:{module}:{code}` via
  `CoreLock.acquire` + heartbeat zombie-cleanup. Several tickers can coexist; a task still runs once.
- Two coupling points block a clean process split:
  1. **Registry is built from module code** — `entry.handler` is a Python fn registered via each
     module's `register(app, settings)`. A worker must import the same modules to execute tasks.
     → the worker shares the codebase (decided), it is NOT the minimal `new_structure/` mock.
  2. **Manual run executes in the API process** — `src/core/api.py:121`
     `asyncio.create_task(run_entry(entry))`. This is the single line that breaks on split.

Decided with the user (see task `AGENTS/tasks/2026-06-03-server-layout-refactor.md`, RESOLVED DECISION):
shared codebase + worker mode (layout **A+**); manual-run signal = DB run-request row (+ optional
`LISTEN/NOTIFY`); cron needs no signal. This plan is the implementation of that decision.

Relevant memory: `AGENTS/memory/project_architecture.md`, `src/core/scheduler/README.md`.

## Scope

**In scope:**
- Lift task registration out of `create_app` lifespan into a shared bootstrap callable by both API and worker.
- New `app_worker.py` entry point (no FastAPI): boot DB + build registry + run the ticker, graceful shutdown.
- API: gate the ticker off in API mode; rewrite the manual-run endpoint to persist a run-request instead of
  calling `run_entry`.
- Run-request mechanism: a `requested` lifecycle for a task run that the ticker consumes (DB-backed).
- Worker ticker consumes due cron entries **and** pending run-requests each tick.
- Config/env: document `SCHEDULER_ENABLED` per process; deploy wiring note for `backend` + `worker` containers.
- Optional: Postgres `LISTEN/NOTIFY` as a latency optimisation over the run-request row (source of truth stays the row).

**Out of scope:**
- Replacing the scheduler with an external broker (Redis/RabbitMQ) — rejected, see Approach.
- The other server-layout-refactor phases (Qt teardown, storage split, nginx/docker-compose) — tracked separately.
- Per-task argument passing for manual runs (current tasks take none; add later if a handler needs args).

## Approach

Keep the existing DB-centric scheduler — it is already multi-instance safe — and change only **where**
the ticker runs and **how** a manual run is requested. The worker shares the codebase so handlers stay
plain Python (no serialization/registry duplication). On-demand runs become a persisted row consumed by
the worker's ticker; this is idempotent, survives worker restarts, and adds no new infrastructure.

Alternatives rejected:
- **External broker (Redis/RabbitMQ)** — adds infra absent from the project for a job the DB already does
  (persistence, ordering, multi-instance dedup via `core_locks` + partial-unique index).
- **Direct HTTP API → worker** — forces the worker to expose and be addressable over HTTP; breaks the
  "worker is just a process" model and complicates multi-instance.
- **NOTIFY-only (no row)** — non-persistent; a NOTIFY fired while the worker is down is lost. Hence the row
  is the source of truth and NOTIFY is optional sugar.

### Run-request representation — decision needed (see open questions)

Two viable shapes; both keep the source of truth in the DB:
- **(R1) Reuse `core_tasks` with a `requested` status.** Add `requested` to `CoreTaskStatus`; API inserts a
  `requested` row; the ticker, each tick, promotes due `requested` rows to `running` (via the same atomic
  `create_running`-style transition) and runs them. Pro: one table, runs list already shows it. Con: the
  partial-unique index and `last_run_at`/stats queries must learn the new status.
- **(R2) Separate `core_task_requests` table** (`module, code, requested_at, consumed_at`). The ticker reads
  unconsumed requests, marks consumed, then runs via the existing `run_entry`. Pro: zero change to
  `core_tasks` semantics/index. Con: one more table + crud.

Leaning **R2** (smaller blast radius on the proven `core_tasks` index/stats path). Confirm at step 4.

## Steps

Ordered; each lands as its own commit/review unit.

1. **Shared task-registration bootstrap.** Extract the module `register()` fan-out + core task registration
   out of `create_app` lifespan into a reusable function (e.g. `src/core/app_factory.py` →
   `build_registry(config)` or a `bootstrap` module) that does NOT require a FastAPI app. `create_app`
   calls it; the worker will too. — files: `src/core/app_factory.py`, `src/core/module.py` (if registration
   lives there), module `__init__`/`register` call sites as needed.
2. **Gate the ticker to non-API processes.** `scheduler.start(config)` already honours `config.scheduler_enabled`;
   ensure the API deploy sets `SCHEDULER_ENABLED=false` and the ticker no longer starts implicitly for the API.
   Confirm `create_app` lifespan still starts it for local one-shot dev (single process) — keep dev ergonomic.
   — files: `src/core/app_factory.py`, `src/core/scheduler/__init__.py`, `.env.example`.
3. **`app_worker.py` entry point.** Root launcher, no FastAPI: init DB (`init_database`), run Alembic only if
   `DB_AUTO_MIGRATE` (default off in deploy), call the shared bootstrap, `await scheduler.start(config)` with
   `SCHEDULER_ENABLED=true`, block until signal, `await scheduler.stop()` + `close_database` on shutdown.
   Mirror the lifespan ordering in `create_app`. — files: `app_worker.py` (new), `.run/` config (new `worker` run config).
4. **Run-request mechanism (R2 unless reversed).** Model `core_task_requests` + migration (core branch,
   naming per `feedback_migration_naming`) + crud (`create_request`, `claim_pending` → atomically mark
   consumed and return claimable `(module, code)` list). — files: `src/core/models/tasks.py`,
   `src/core/migrations/versions/<next>_core_task_requests.py`, `src/core/crud/tasks_requests.py` (new).
5. **API manual-run rewrite.** `POST /tasks/{module}/{code}/run` no longer does
   `asyncio.create_task(run_entry(entry))`; it validates (`enabled` + `manual_run`) then `create_request(...)`
   and returns `202`. Keep the registry lookup for validation (API still imports modules for its own routes,
   so the registry is present). — files: `src/core/api.py`.
6. **Ticker consumes run-requests.** In `_tick_once`, after the cron sweep, `claim_pending()` and `_spawn`
   each claimed entry (look up the `TaskEntry` from the registry by `(module, code)`; skip unknown/disabled).
   De-dup against already-running via the existing `create_running` atomicity — no extra guard needed.
   — files: `src/core/scheduler/ticker.py`.
7. **(Optional) LISTEN/NOTIFY fast-path.** API `NOTIFY core_task_request, '{module}:{code}'` after inserting
   the row; worker holds a dedicated asyncpg connection LISTENing, and on notify does an early
   `claim_pending()` instead of waiting for the next tick. Boot-time `claim_pending()` covers missed notifies.
   — files: `src/core/scheduler/ticker.py` (or a small `notify.py`), `src/core/crud/tasks_requests.py`.
8. **Docs + memory.** Update `src/core/scheduler/README.md` (worker process, run-request flow, deploy split),
   add a memory entry for the API↔worker split + signalling contract. — files: `src/core/scheduler/README.md`,
   `AGENTS/memory/` (+ `MEMORY.md` pointer).

## Tests

- Unit: `claim_pending` is atomic — two concurrent claims of the same pending request yield it once
  (mirror the `create_running` double-run test). Marker `db`.
- Unit: `create_request` + ticker consumption end-to-end — request a manual run, tick once, assert one
  `core_tasks` run created and the request marked consumed. Marker `db`.
- Unit: ticker still de-dups — a run-request for an already-`running` task is a no-op (atomic
  `create_running` returns `None`). Marker `db`.
- Unit: API endpoint persists a request and returns `202` without executing the handler in-process
  (assert no run row appears until a tick). Marker `db`.
- Regression: cron path unchanged — `is_due` + `last_run_at` sweep still spawns due tasks with the ticker
  in worker mode. Marker `db`.
- Manual: boot `app_worker.py` + API separately against the dev DB; trigger a `manual_run` task from the UI;
  confirm it runs in the worker process (log channel `tasks`) and the run appears in the API's runs list.

## Validation

- With `SCHEDULER_ENABLED=false`, the API process starts no ticker (no `tasks.log` cron activity from it).
- `app_worker.py` alone runs cron tasks on schedule and consumes manual run-requests.
- A manual run triggered via API while the worker is briefly down is **not lost** — it runs once the worker
  boots (boot-time `claim_pending`).
- Two worker instances (if ever) still run each task once (existing `core_locks` + partial-unique index).
- Local one-shot dev (single process, scheduler on) keeps working unchanged.

## Risks / open questions

- Open question (step 4): run-request representation — **R1** (`requested` status on `core_tasks`) vs **R2**
  (separate `core_task_requests` table). Leaning R2; confirm before step 4. Needs answer before step 4.
- Risk: a manual run-request with no matching/enabled registry entry (e.g. task renamed/removed between
  request and consume) — mitigation: ticker skips unknown/disabled `(module, code)` and logs a warning;
  optionally mark the request consumed-with-note so it doesn't loop.
- Risk: registration moved out of lifespan could change import/init ordering for modules relying on
  app-state — mitigation: keep `create_app` calling the same bootstrap in the same lifespan position; diff
  route count (113) before/after.
- Risk: NOTIFY (step 7) adds a long-lived asyncpg LISTEN connection that can drop on DB failover —
  mitigation: it is optional sugar; reconnect-with-backoff + the per-tick `claim_pending` floor guarantees
  progress regardless. Defer step 7 if it adds churn.
- Risk: heavy migration tests for the new table/status must include the core branch only (no cross-module FK).

## References

- Related task: `AGENTS/tasks/2026-06-03-server-layout-refactor.md` (RESOLVED DECISION section)
- Scheduler internals: `src/core/scheduler/README.md`, `src/core/scheduler/{ticker,runner,registry,context}.py`
- Manual-run coupling point: `src/core/api.py:111-121`
- Models: `src/core/models/tasks.py` (`CoreTask`, `CoreTaskStatus`, partial-unique index)
- Deploy skeleton (API only, not the worker): `new_structure/README.md`
- Memory: `AGENTS/memory/project_architecture.md`, `feedback_migration_naming`, `migration_cross_module_depends_on`
