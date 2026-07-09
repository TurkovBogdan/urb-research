# Task: task-requests → open the requested task

Date: 2026-06-11
Status: completed

## Goal

On `/tasks/requests` (manager-accessible list of user-requested task runs) add a way to
drill into the task itself (its runs/logs detail page `/tasks/:module/:code`).

## Decision

The task detail page + its backend endpoints were **admin-only**, while the requests list
is **manager**. User chose: **open the task detail to manager** (rather than gate the link
behind admin). Only the `/tasks` overview list stays admin-only.

## What was done

- **Backend** `core_monitoring/api/tasks.py`: lowered the guard on the three task-detail
  endpoints from `admin:read` → `manager:read`: `GET /tasks/{module}/{code}`,
  `.../runs`, `.../runs/{run_id}/logs`. `GET /tasks` (overview list) stays `admin:read`.
- **routes.ts**: `/tasks/:module/:code` meta `subject: 'admin'` → `'manager'` (+ comment).
- **TaskRequestsView.vue**: task cell is now a clickable `.task-link` button → `router.push(/tasks/{module}/{code})` (hover reveals a chevron).
- **TaskRunsView.vue**: back-button target computed by ability — `can('manage','admin') ? '/tasks' : '/tasks/requests'` (manager must not be bounced to the admin-only overview).
- **Test contract** `tests/modules/core_monitoring/test_api.py`: rewrote
  `test_every_route_requires_admin` → `test_route_gating_contract` — routes whose path
  contains `{module}/{code}` are manager-gated, the rest admin-gated.

## Follow-up — whole task section at the manager bar

User: "ensure everything related to the task system / task viewing requires manager
and above". Audited every task surface; the only remaining admin-only one was the
**tasks overview** `GET /tasks` + its route/nav. Lowered it to manager so the whole
`/tasks*` section is uniformly manager-gated:

- `core_monitoring/api/tasks.py`: `GET /tasks` `admin:read` → `manager:read`.
- `routes.ts` `/tasks` + `nav.ts` `coreMonitoringNav` subject `admin` → `manager`.
- Reverted the now-pointless ability-based back-button in `TaskRunsView` to a plain
  `back-to="/tasks"` (the overview is reachable by anyone who can open the detail).
- Test contract `_expected_min_level`: `/tasks*` → manager, `/monitor*` (lock status)
  stays admin.

`GET /monitor/locks/{key}` left admin-only — it is lock monitoring, not the task system,
and has no frontend consumer.

## Result

`--module=core_monitoring --dbs 1-4` 6 passed; vue-tsc clean. Every task-related
backend endpoint and FE route/nav is now manager-gated (manager and above).
