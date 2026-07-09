---
title: Frontend tasks store + brief-status endpoint + DS demo page
date: 2026-06-11
status: completed
description: "Global Pinia tasks store (status map + run requests, core_users domain), backend GET /core-users/tasks-status (manager) returning per-task last-run brief, design-system data page rendering the store. Groundwork for a run-task control on the mail-sync/filters page."
tags: [core_users, frontend, scheduler, design-system]
---

## Task

Build a run-task control (eventually for `/mail-sync/filters`), but first as a
reusable component backed by a global store:
1. A separate frontend store mounted in the global space.
2. It owns: fetching task status, posting run requests, building task status
   (core_users domain).
3. A method that fetches a brief log for all tasks and builds, per registered
   task (from `core/crud/tasks.py`), `{status, last_completed_at}` keyed by
   `module:code` — a short report with codes only.
4. A design-system page (in the **Data** section) that renders the store.

## Context

Run requests already existed end-to-end in core_users
([task-user-requests](2026-06-11-task-user-requests.md)): the enqueue API
(`POST /core-users/task-requests/{m}/{c}`, manager) + the watcher. Missing was
a *brief status* read (managers can't reach the admin-only monitoring list) and
a frontend store to drive a run button from any page.

## What was done

- **Backend brief-status query** `core/crud/tasks.py::brief_status_all()` —
  one pass over `core_tasks`: a window-function subquery (`row_number()` over
  `partition_by (module, code) order_by started_at desc`, take rank 1) gives the
  latest run's status; a `max(finished_at) where status=success group by pair`
  gives `last_completed_at`. Returns `dict[(module,code) → (status, completed)]`;
  pairs with no run are absent (caller = never-run). Window functions work on
  both Postgres and the sqlite test path.
- **Endpoint** `GET /internal/core-users/tasks-status` (`manager:read`) +
  DTO `TaskBriefStatus {module, code, status: str|None, last_completed_at}` —
  iterates `get_registry().all()` (so every registered task appears, even with
  no runs) and attaches brief status. Lives in core_users (owns the store +
  enqueue; monitoring is admin-only).
- **Frontend API** `web/src/api/tasks.ts` — `fetchTasksStatus()` +
  `requestTaskRun(m,c)` (`on403:'throw'` so business 403s surface inline).
- **Global store** `web/src/stores/tasks.ts` `useTasksStore` —
  `statuses` map keyed `module:code`, `loading/loaded/error`, per-task
  `requesting` flags; `fetchStatuses()`, `statusFor(m,c)`, `isRequesting(m,c)`,
  `requestRun(m,c)` (returns `false` on 409 "already queued" — info not error —
  rethrows otherwise; refreshes statuses on accept).
- **DS page** `views/design-system/data/TaskStatusView.vue` at
  `/design-system/task-status` (Data group, `IconActivityHeartbeat`) — VTable of
  registered tasks (code · status chip · last-completed · Run button wired to
  `store.requestRun`, local VSnackbar for accepted/duplicate/error) + a raw
  `CodeBlock` dump of `store.statuses`. Route + index card + i18n ru/en.
- **Tests** (`tests/modules/core_users/test_task_requests.py`, +3 → 18):
  `brief_status_all` reports latest status + last success; `tasks-status`
  requires manager; lists registered tasks with status (`success` for a run
  pair, `null` for a never-run pair).

## Addendum — TaskRunPanel component

Reusable `web/src/components/TaskRunPanel.vue` (props `module`/`code`/optional
`title`) modelled on `SwitchPanel`: a `VCard` with localized task name + last-run
status chip + "succeeded {rel}" (or "no successful runs yet") + a run button
wired to `store.requestRun`. Reads the global store and self-loads statuses on
mount, so it can be dropped on any page (the eventual mail-sync/filters control).
Shared strings under `common.task_panel.*` (ru/en). Demoed on the task-status DS
page (a "Run panel" section, one panel per registered task). The page snackbar
was dropped earlier per user — panels reflect status via the store after enqueue.

## Addendum — short task names

Added a `short` variant (task name without the `Module:` prefix) to every task
name in the i18n catalogs: per-feature `task.<code>.short` (conversations,
mail_sync, intercom, core_geo, twenty) + `core_monitoring.catalog.<module>.<code>.short`
(core/heartbeat, core_users/watch_task_requests, llm_providers/agent_dispatch —
these have no module prefix, so short == name). `useTaskText` gained
`taskNameShort` (key `short` → fall back to the resolved full name → backend
literal). `TaskRunPanel` now renders the short name (the panel context already
implies the module). `agents.catalog.conversation_insights` is not a scheduler
task → left untouched.

## Result

Reusable tasks store + brief-status endpoint + DS demo, all green: 18 core_users
tests (`--dbs 1-4`), vue-tsc clean. Changed: `src/core/crud/tasks.py`,
`src/modules/core_users/{api.py,dto/api.py}`, `web/src/api/tasks.ts` (new),
`web/src/stores/tasks.ts` (new), `web/src/views/design-system/data/TaskStatusView.vue`
(new), `web/src/router/design-system.ts`,
`web/src/views/design-system/DesignSystemIndexView.vue`,
`web/src/locales/design-system/{en,ru}.json`, test file.

## Addendum — first real placement

`TaskRunPanel` placed on `/mail-sync/mailboxes` above the filters, wired to
`mail_sync.gmail_api_update` (incremental import — user's choice over full
import). First production use of the store/panel outside the DS demo.

## Addendum — TaskStatusButton + final shape

- `TaskRunPanel` reshaped to a **bare row** (no VCard/padding): `[status chip]
  name` on top, "Последнее успешное выполнение: {rel}" below, run button right.
  Button hidden unless `user_request && enabled && $can('manage','manager')`;
  disabled+greyed «В очереди» on `request_pending`, «Уже запущена» when the last
  run is `running`. Backend: `TaskBriefStatus` carries `user_request/enabled/
  request_pending`; enqueue API rejects (409) when the task is already running.
- New `web/src/components/TaskStatusButton.vue` — primary button (label/title =
  shared `common.task_status.*` «Статус задач») opening a dialog that lists the
  passed `tasks` as `TaskRunPanel` rows. **Self-sufficient**: `fetchStatuses()`
  on each open, so a host page needs nothing wired. Drop-in: `<TaskStatusButton
  :tasks="[{module,code}…]" />`.
- Placements: `/mail-sync/mailboxes` (full import + update) and
  `/mail-sync/filters` (apply_mail_filter) now use the button (panels moved into
  the dialog, removed from page body). DS page `data/task-status` reworked:
  examples VCard (5 TaskRunPanel) + usage code blocks for both components.
- Disabled-button styling darkened globally (`main.scss`: text faint→muted, fill
  surface-hi→border, incl. a tonal-disabled override so tonal buttons grey out).
- Verified: vue-tsc clean; `--module=core_users,core_monitoring` 302 green;
  browser-checked mailboxes/filters/requests/DS pages. Ready for reuse on other
  pages — host on a manager-gated page (status read is `manager:read`).
