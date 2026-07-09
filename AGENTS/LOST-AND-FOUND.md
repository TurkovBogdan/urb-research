# LOST-AND-FOUND — loose ends from tasks/plans

Follow-ups, deferred items, and TODOs harvested from task/plan bodies, re-verified against the code
each run by [`agent-tasks-maintenance`](agent-tasks-maintenance.md). Appended, not overwritten.
Dedup key = (source + item).

Scope note: loose ends buried inside **completed** task bodies + operational/manual steps live here.
Open **in-work** tasks and the **Deferred** section tasks (`mcp-per-server-access-levels`,
`world-map-component`, `fastmcp-fork-migration`) keep their own rows in `tasks/INDEX.md` — they are
tracked there, not duplicated here.

## Open

| Item | Source | First seen | Last checked | Notes |
|------|--------|-----------|--------------|-------|
| core_storage reprocess pipeline (find stale-by-signature → re-admit; source-driven, original bytes not stored) | tasks/2026-06-14-core-storage-handler-signatures.md | 2026-06-14 | 2026-06-14 | OPEN — not in code; explicit "next, separate go" |
| Record size-gate (empty/oversized) rejections + optional `rejection_reason` column | tasks/2026-06-14-core-storage-handler-signatures.md | 2026-06-14 | 2026-06-14 | OPEN — design choice; size-gate still returns None, no row |
| Pure test for `_inline_disposition` RFC5987 latin-1 helper | tasks/2026-06-14-core-storage-protected-filename-encoding.md | 2026-06-14 | 2026-06-14 | OPEN — fix landed, test not written (verified by hand) |
| URL fetcher DNS-rebinding residual window (pin resolved IP across connect) | tasks/2026-06-14-core-storage-url-downloader.md | 2026-06-14 | 2026-06-14 | OPEN — documented residual window in `services/url_fetch.py` |
| Lazy proxy-on-reveal cache for remote body images (tracking-pixel-safe) | tasks/2026-06-13-core-storage-downloader-security.md | 2026-06-14 | 2026-06-14 | OPEN — design stance; never ingest untrusted URLs at import |
| Async `process_body` + inline-image rehosting refactor in `services/mail_body.py` | tasks/2026-06-13-mail-sync-body-assembly-service.md | 2026-06-14 | 2026-06-14 | OPEN — `process_body` still sync; rehost path deferred |
| conversations `_list_accepted_threads` reads mail_sync models directly (route via CRUD) | tasks/2026-06-12-mail-sync-robustness-cleanup.md | 2026-06-14 | 2026-06-14 | OPEN — cosmetic convention break, left open by author |
| thread_builder union/merge component tests (coverage ~79%) | tasks/2026-06-12-mail-sync-module-review.md | 2026-06-14 | 2026-06-14 | OPEN — `_DisjointSet.union`/`_apply_components` merge branches untested |
| Prod direction recompute or full re-import after sender-based direction switch | tasks/2026-06-12-mail-sync-direction-from-sender.md | 2026-06-14 | 2026-06-14 | OPEN — manual (prod data op) |
| Investigate missing early-2025 outbound replies (thread 11321 / gmail tid 1946062d6eae89f4) | tasks/2026-06-11-mail-sync-import-review.md | 2026-06-14 | 2026-06-14 | OPEN — manual; SENT-label/date-window gap, no follow-up task yet |
| Verify Gmail deep-link format live + surface owner links in ThreadView | tasks/2026-06-13-mail-sync-message-user-links.md | 2026-06-14 | 2026-06-14 | OPEN — MessageView wired; live-verify + ThreadView pending |
| mail_sync filter curation groups B/C/D + calendar `Accepted:` subject-based filter | tasks/2026-06-12-mail-sync-filter-curation-groupA.md | 2026-06-14 | 2026-06-14 | OPEN — manual; only group A seeded; calendar mime-tag (calendar-status) ≠ subject auto-reply filter |
| conversations message-body variants impl (body_plain/body_history/body_original; mail processor, bench, view-original UI, feed history to insights, dev full_import) | tasks/2026-06-13-conversations-message-body-variants.md | 2026-06-14 | 2026-06-14 | OPEN — design agreed, impl via in-work plan `2026-06-13-mail-parser-module` |
| Prod nginx `/storage/protected` regex config | tasks/2026-06-13-core-storage-module.md | 2026-06-14 | 2026-06-14 | OPEN — manual; dev nginx fixed, prod template TBD |
| Browser-verify intercom content-search toggle + detail-layout parity (header/logo align, centered feed) | tasks/2026-06-13-intercom-conversations-content-search.md; tasks/2026-06-13-intercom-detail-layout-parity.md | 2026-06-14 | 2026-06-14 | OPEN — manual; code landed, browser check pending |
| Trigger re-import for intercom HTML bodies (PARSER_VERSION 2.0) | tasks/2026-06-14-intercom-message-html-body.md | 2026-06-14 | 2026-06-14 | OPEN — manual; sync tasks disabled, version bumped |
| Centralize ability-label literals (llm_providers/core_mcp/core_monitoring/mail_sync/conversation_insights + core `_settings`) to a shared constants home | tasks/2026-06-10-core-users-crud-actor-split.md | 2026-06-14 | 2026-06-14 | OPEN — coupling-vs-centralization decision deferred |
| Plans `2026-06-10-core-module-state-store` + `2026-06-10-mail-sync-mailboxes` done, but their downstream task `2026-06-10-mail-sync-gmail-api-import` (first consumer) is still in-work — plans left unarchived | plans/2026-06-10-core-module-state-store.md; plans/2026-06-10-mail-sync-mailboxes.md | 2026-06-14 | 2026-06-14 | OPEN — Job-2 hold; archive plans once gmail-api-import completes |

## Resolved (verified landed in code)

| Item | Source | Resolved on | Evidence |
|------|--------|-------------|----------|
| Re-import / re-process existing mail rows so the nh3 sanitizer applies to historical data | tasks/2026-05-30-mail-html-sanitizer.md | 2026-06-07 | user-confirmed done (operational re-import run) |
| Switch fingerprint-derived `tagger_version` → per-rule manual `version: float` + "bump version" button | tasks/2026-05-27-conversation-insights-frontend.md | 2026-06-07 | `src/modules/conversation_insights/models/tagging_rule.py:33-35` (`version: Mapped[Decimal]`, `server_default="1.0"`) + `mcp/tagging_rule.py:189` (`tagging_rule_bump_version`) |
| FE tasks/monitoring section admin-gating (route meta `action`/`subject`) | tasks/2026-06-04-core-monitoring-module.md | 2026-06-07 | `web/src/features/core_monitoring/routes.ts:9,15` (`action:'manage', subject:'admin'`) |
| Frontend nav entries gated by permission (Administration / Agent-runs / Monitoring) | tasks/2026-06-04-frontend-auth-permissions.md | 2026-06-07 | `web/src/features/{administration,agents,core_monitoring}/nav.ts:11-12` + `layout/AppSidebar.vue:87-110` (`can(action,subject)`) |
| core_users `name`: FE profile self-edit page + name shown in admin UsersView | tasks/2026-06-05-core-users-self-guard-name.md | 2026-06-07 | `web/src/features/user-profile/views/ProfileView.vue` (name edit) + `features/administration/views/UsersView.vue:35` (name column) |
| MCP introspection/info page (`core_mcp` module) | tasks/2026-06-06-mcp-server-surface.md | 2026-06-07 | `src/modules/core_mcp/api.py` + `web/src/features/core_mcp/` |
| Docs still referencing removed per-module MCP servers | tasks/2026-06-04-remove-module-mcp-servers.md | 2026-06-07 | servers were restored; `AGENTS/docs/mcp/INDEX.md:44-51` reflects the current `/mcp/<code>` surface (residual "Qt/MCP apps removed" wording in `platform/overview.md` is historically accurate) |
| MEMORY.md index-bloat (fat inline entries) | tasks/2026-06-07-memory-db-schema-pruning.md | 2026-06-07 | `AGENTS/memory/MEMORY.md` = 97 lines, 3-part router (rules / routing table / atomic gotchas) |
| Remove Qt deps (PySide6/qasync/pyinstaller-runtime) from pyproject | tasks/2026-06-03-server-layout-refactor.md | 2026-06-07 | `pyproject.toml` — no PySide6/qasync; pyinstaller only in build group |
| conversation_insights hub doc covering tagger_version/reports | tasks/2026-06-07-memory-docs-boundary.md | 2026-06-07 | `AGENTS/docs/conversation_insights/INDEX.md:65-78,84,107-112` |
| Volume report in-browser visual verification | tasks/2026-05-31-conversation-insights-volume-report.md | 2026-06-07 | done by `tasks/2026-06-06-interface-responsive-adaptation.md` (volume report debugged @360/600/960/1280, PieChart narrow-legend fix) |
