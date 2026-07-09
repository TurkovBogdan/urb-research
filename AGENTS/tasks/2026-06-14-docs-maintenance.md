# 2026-06-14 — docs-maintenance sweep

Status: completed

## Goal

Run `agent-docs-maintenance` playbook. Memory already restructured (117 lines / 14.7 KB, in budget),
so a **lighter run**: Phase A (code-actuality audit) + Phase 5 (validation), catching drift introduced
by the recent heavy core_storage / mail_sync attachment work (many new tables, validators, migrations).

## Plan

- Phase A: read-only Explore fan-out, one per doc area, verify claims vs current code, fix stale facts,
  flag semantic conflicts.
- Phase 5: one Explore agent runs the 7 validation checks (links, orphans, budget, one-hop).
- Central: collate, surface conflicts, hand commit commands.

## What was done

Lighter run (Phase A audit + Phase 5 validation), 5 read-only Explore audit agents over disjoint doc
areas + 1 validation agent. Stale facts found by agents but applied centrally (Explore can't Edit):

- `docs/platform/module-system.md` — "Current modules" table was 11, code has **14**; inserted
  `MailParserModule`, `CoreStorageModule` (migrations+config), `UserContactsModule` (migrations).
- `docs/frontend/rules.md` — theme colors stale (`#4ade80`/`#4f8ef7`/`#e05555`) → real
  `primary #008890` (teal) / `success #4caf50` (green) / `error #F95053` from `vuetify.ts`.
- `docs/frontend/design-system.md` — "23 showcase pages" → **36** (regrouped by section from views/).
- `docs/core_users/INDEX.md` — `core_task_requests` → `core_users_task_requests` (real `__tablename__`).
- `docs/mcp/INDEX.md` — "All 5 per-module servers" → **4** (team retired).
- `MEMORY.md` §3 — added orphaned `gmail_api_import_perf` (was unlinked); rewrote stale core_storage
  line (rejected NOW writes a row w/ no bytes; versions are `code@version` via `signature()`, not "1.0").

Validation sweep: links ✅, budget 118 lines / 15 KB (limit ~24.4 KB) ✅, one-hop ✅, orphan fixed ✅.

## Problems

None blocking. Two Explore agents falsely claimed they "applied edits" — Explore is read-only; their
fixes were re-applied centrally after verifying against code.

## Open items — RESOLVED (2nd pass, user said "поправь")

1. **architecture.md datetime** — rewrote the «Datetime → фронт» section: `DatetimeGMT5`/`src.core.types`
   (nonexistent) → `DatetimeUTCStr`/`src.core.utils.date`, naive-UTC `"YYYY-MM-DD HH:MM:SS"` no offset,
   FE parses via `DateTime.fromSQL(s,{zone:'utc'})`; delegated full detail to `dates.md` (single-home).
2. **i18n.md fallback** — user decision: `fallbackLocale:'en'` is **by design**. Removed the ⚠️ mismatch
   warning, reframed "primary" as authoring-only, added "do not fix to 'ru'". Code untouched.
3. **core_users/INDEX.md guard_self** — code verified: no `self` guard kind (`Module.guards` =
   auth/ability/token_owner). Rewrote §"name field…": self = `PATCH /me/profile` (auth-only, actor
   `current_user`, no path id) + admin = `PATCH /users/{user_id}` (`@guard("ability", ADMIN_UPDATE)`);
   renamed the heading.
4. **core_storage hub** — created `docs/core_storage/INDEX.md` (folded the 78-line memory mini-doc,
   verified structure vs code: 2 tables, 3 admission entry points, safety model, registries/signatures,
   per-type notes, serving zone, config, SSRF). Promoted: **deleted** `memory/core_storage_safety_versions.md`,
   added the hub to MEMORY.md §2 routing + `docs/INDEX.md` library map, repointed the §3 gotcha to the hub.
5. **TokensView.vue:19** — fixed stale showcase label `#4ade80` → `#008890` (code edit, user-authorized).

Post-fix validation: no MEMORY.md/docs links to the deleted memory file; hub linked from §2+§3+docs/INDEX;
MEMORY.md 118 lines / 15 KB (in budget).

## Result

Docs/memory re-aligned to current code. All open items resolved this pass. Earlier-pass list (now closed):

1. **`docs/platform/architecture.md:91-102` — semantic conflict.** Describes `DatetimeGMT5` from
   `src.core.types` serializing DB-naive-UTC → GMT+5 with `+05:00` suffix. Reality: no `src/core/types`,
   no `DatetimeGMT5`; code uses `DatetimeUTCStr` (`src/core/utils/date.py`) → naive UTC string, no offset.
   `docs/platform/dates.md` already documents the UTC convention. Likely stale doc (behavior changed
   GMT+5→UTC), but the tz-behavior difference is a decision — rewrite architecture.md to UTC, or confirm
   GMT+5 was intended somewhere. Flagged, not edited.
2. **`docs/frontend/i18n.md` — known conflict (re-confirmed).** Doc says ru-primary; code
   `fallbackLocale:'en'` + `initialLocale` defaults 'en'. Pre-existing flag, design decision.
3. **`core_users/INDEX.md` — `guard_self` not implemented.** Doc describes a `@guard("self", …)` pattern;
   code uses `Depends(current_user)` for `/me/profile` + `guard_ability` for admin. Doc predicts an
   unbuilt feature.
4. **`core_storage` has no doc hub.** Substantial code (files+refs tables, detector/validator registries,
   SSRF url-fetch, migrations) lives under one §3 memory gotcha only. Recommend a `docs/core_storage/INDEX.md`
   hub + routing-table entry in a follow-up (out of scope for this lighter run).
5. Minor: `web/src/views/design-system/basics/TokensView.vue:19` still labels accent `#4ade80` (stale
   showcase label; real theme `#008890`) — code nit, not a doc issue.
