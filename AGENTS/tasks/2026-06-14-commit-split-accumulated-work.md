# Task: split accumulated uncommitted work into zone-based commits

- **Date:** 2026-06-14
- **Status:** in work

## Goal

Branch `dev` carries ~40 tasks worth of uncommitted work (266 modified + ~120 new files). Break it into clean, dependency-ordered commits grouped **by zone** (~38 commits). AGENTS records + benches go in separate commits at the end. I prepare each commit by staging the right files and hand the user a one-line `git commit -m` (never commit myself).

## Cross-cutting refactors (isolated into their own commits)

- **X1** `manual_run`/`MANUAL_RUN` → `user_request`/`USER_REQUEST` (scheduler + 13 task files + core_monitoring + FE).
- **X2** `provider` → `source` (conversations + conversation_insights + c16 + FE).
- **X3** `conversations/providers/` → `importers/` (rename + `message_content_hash`).
- **X4** KeepAlive double-load fix `onMounted`→`onActivated` (~18-23 FE views + overlays.ts).

## Commit order (phases)

1. Foundation: config deps/env → core_storage → core_security svg → mail_parser.
2. Scheduler/task-requests: X1 → core_users task requests → core_monitoring gate → ghost fix → session/token.
3. conversations: X3 → X2 → body variants (c15) → purge (c14) → mail PK types → disable tasks → insights misc.
4. mail_sync (~5-6, shared files need `git add -p`): migrations → threading → parsing → owners → attachments → filters/seed → robustness.
5. intercom/twenty: i07 → i08 → i09 → content search → admin reconcile + user_contacts uc02 → twenty tw04.
6. frontend: X4 → tasks UI → attachments UI → source links/list polish → intercom UI → design-system.
7. records/infra: bench cleanup → dev/docker → AGENTS records.

## Progress

- [ ] 1. config (pyproject/uv.lock/.env)
