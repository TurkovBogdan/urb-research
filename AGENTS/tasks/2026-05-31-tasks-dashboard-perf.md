---
title: Tasks dashboard — kill N+1 on 24h stats
date: 2026-05-31
status: completed
description: "Dashboard GET /api/core/tasks computed 24h stats with one DB query per task (N+1, sequential, own session each). Replaced with a single GROUP BY across all (module, code)."
tags: [core, tasks, performance, sql]
---

## Task

User: tasks dashboard (`web/src/features/tasks`) feels slow to refresh; speed up the dashboard and its building SQL queries.

## Context

`GET /api/core/tasks` (`src/core/api.py`) built the dashboard via
`[await _to_info(e) for e in entries]` — sequential. Each `_to_info` called
`crud_tasks.stats_24h(module, code)`, which opened its **own** `session_scope()`
and ran a per-pair `GROUP BY status`. With N registered tasks that is N
sequential round-trips (+ connection acquire/release each) — latency × N,
dominating on the remote SSL DB. The SQL itself is trivial; the cost is the
query count and their serialization.

## What was done

- `src/core/crud/tasks.py`: new `stats_24h_all()` — single
  `SELECT module, code, status, count() ... WHERE started_at >= cutoff
  GROUP BY module, code, status` in one session; returns
  `dict[(module, code) -> {total,success,error,running}]`. Pairs with no runs in
  the window are absent (caller fills zeros). Extracted shared `_stats_row()`;
  `stats_24h` kept (still used by single-task `get_task`). Exported in `__all__`.
- `src/core/api.py`: `_to_info` is now sync and takes precomputed `stats`.
  `list_tasks` calls `stats_24h_all()` once and maps with
  `stats.get((module, code), _ZERO_STATS)`. `get_task` still uses the cheap
  single-pair `stats_24h`.
- No new index: `started_at` already indexed (`models/tasks.py`) → 24h window is
  selective, aggregation runs over a small filtered set.
- Test: `tests/core/test_crud_tasks.py::test_stats_24h_all_aggregates_per_pair`
  (per-pair counts, parity with `stats_24h`, no spurious pairs).

## Result

Dashboard build went from N sequential queries/sessions to 1. Frontend
unchanged (same `/api/core/tasks` shape). `tests/core/test_crud_tasks.py` +
`tests/core/test_api.py` → 7 passed.

Changed: `src/core/crud/tasks.py`, `src/core/api.py`,
`tests/core/test_crud_tasks.py`.
