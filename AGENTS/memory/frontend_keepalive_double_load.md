---
name: frontend_keepalive_double_load
description: Routed views under global KeepAlive double-fire data load if both onMounted and onActivated call it
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bedbaac4-4793-4618-b870-99644bf54895
---

All routed views live under one global `<KeepAlive>` (`web/src/App.vue`). On the **first** show Vue fires **both** `onMounted` AND `onActivated` (re-entry fires only `onActivated`) → a view that loads data in both sends the request **twice** on first open.

**Rule:** load list/page data **only in `onActivated`** (it covers first paint + every re-entry). `onMounted` may keep only one-time idempotent setup (dict/providers warmup); if a sync prologue must run before the first load (e.g. `normalizeSort()` mutating sort state), put it in `onMounted` before any `await` — it runs before `onActivated`. Detail views with `:id` also rely on `onActivated` to reload on param change.

**Local-state leak across `:id`** (same KeepAlive cause): a detail view's instance is **reused** when only the route `:id` changes, so per-item local `ref`s (e.g. `showImages` in `ConversationView`/`ThreadView`) keep their value into the next item. Reset them at the top of `load(id)` (runs on first show + every id change), not just on mount.

**Why:** double fetch on every page open. **How to apply:** never pair `onMounted(load)` + `onActivated(load)`; canonical comment + pattern in `AdminsView.vue` / `MailboxesView.vue`. Fixed across all ~23 views 2026-06-11 (task `2026-06-11-frontend-keepalive-double-load`). Exceptions left as-is: `ProfileView` (`reset` is local, no fetch), `UserDetailView` (own first-mount guard). Related: [[frontend_pagelayout_meta_snapshot]].
