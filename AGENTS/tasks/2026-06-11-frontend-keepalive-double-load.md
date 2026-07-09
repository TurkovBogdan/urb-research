---
date: 2026-06-11
status: completed
---

# Frontend — KeepAlive double data-load on routed views

## Request

`/mail-sync/mailboxes`: the message/mailbox list is fetched **twice** on page open. Debug, then check **all** views and record the problem in memory.

## Root cause

All routed views live under one global `<KeepAlive>` (`web/src/App.vue`). On the **first** show Vue fires **both** `onMounted` AND `onActivated` (re-entry fires only `onActivated`). Any view that calls its data `load()` in both hooks sends the request twice on first open. The store `load()` has no dedup, so two identical `listMailboxes` requests go out.

## What was done

Audited every routed view (`grep onActivated`). Canonical fix (already used in `AdminsView`/`ModelsView`/reports): **load list/page data only in `onActivated`**; keep one-time idempotent setup (dict/providers warmup) in `onMounted`.

Fixed 23 views:

- **onMounted removed entirely** (was a pure duplicate `load`): `MailboxesView`*, `FiltersView`, `AgentSessionDetailView`, `AgentSessionsView`, `McpView`, `McpServersView`, `UsersView`, `TaggingRulesView`, core_geo `Languages/Continents/Countries/Timezones/GeoIndex`. (`McpView`/`TaggingRulesView` keep the one-shot `loading=false` cold-start flag — moved into `onActivated`.) Dropped now-unused `onMounted` import in each.
- **onMounted kept for one-time dicts only** (dropped the duplicate `load`): twenty `People/Companies/Opportunities`, intercom `Contacts/Conversations`, mail_sync `Threads/Messages` (`loadDicts`), conversations `Conversations` (`dicts.ensure`), administration `Contacts` (`users.load`), `ParticipantsView` (country/lang dicts). `ProcessedConversationsView`: kept `normalizeSort()` (mutates sort state — must run before the first load) + `ensureTagRules()` in `onMounted`'s synchronous prologue, list `load` only in `onActivated`.
- **Left as-is**: `ProfileView` (`onMounted/onActivated(reset)` — `reset` is local form state from `auth.user`, no fetch; idempotent), `UserDetailView` (already has its own first-mount guard — `onMounted(load)` + `onActivated(syncRouteUser)`).

(* `MailboxesView` fixed in the first turn before the full sweep.)

## Result

`vue-tsc --noEmit` clean (exit 0). No dangling `onMounted` imports. No remaining `onMounted(load)`+`onActivated(load)` pairs. Memory gotcha recorded: [[frontend_keepalive_double_load]].
