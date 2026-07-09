# Remove non-core modules

- **Date:** 2026-06-24
- **Status:** completed
- **Area:** modules / app composition / frontend / records

## Goal

Heavy cleanup of the forked semaphore core: delete every non-`core_` module so only the platform core remains.

Removed modules: `content_processors`, `conversation_insights`, `conversations`, `intercom`, `llm_providers`, `mail_sync`, `twenty`, `user_contacts` (phase 1), then `core_geo` (ph3), `core_security` (ph4), `core_monitoring` (ph5), then the **last three — `core_mcp`, `core_storage`, `core_users` (ph6)**.
**End state: ZERO modules — bare `src/core`** (module framework, scheduler, DB/Alembic, router zones + guard registry, settings-store, loggers, locks, MCP-mount infra). No auth, no permission model.

## What was done

- **Backend:** `git rm` the 8 module dirs + their `tests/modules/<m>`. Rewrote `src/apps/app/modules.py::build_modules` to register only the 5 wired core modules. `version_locations` is derived from `build_modules`, so migration locations dropped automatically — no separate list to edit. Updated `tests/apps/test_modules_build.py` (was asserting `ContentProcessorsModule` → now `CoreUsersModule`).
- **Frontend:** `git rm` features `agents` (llm_providers UI), `conversation_insights`, `conversations`, `intercom`, `mail_sync`, `twenty`. Surgical `administration`: kept `users` (core `/core-users`), removed only contacts (ContactsView, contacts.store, ContactDialog/ContactsFilters/TransferContactDialog, the `/user-contacts` block in `api.ts`, the `/administration/contacts` route, `administrationContactsNav`, contacts locale keys ru/en). Trimmed `router/index.ts`, `AppSidebar.vue` (nav imports + now-empty sections commerce/import/agent_runs), and the orphan `common.nav` keys in `web/src/locales/{ru,en}.json`. Fixed a doc-only stale import in the design-system `MessageContentView.vue` usage snippet.
- **Records:** removed 6 module doc hubs (`AGENTS/docs/{conversation_insights,conversations,intercom,llm_providers,mail_sync,twenty}`), 9 deleted-module benches under `dev/bench/`, and 20 module-specific memory files. Trimmed `MEMORY.md` (routing table → core only, module gotchas block, MCP/LLM section, settings-store email-body tail) and fixed the symlink note direction. Trimmed `docs/INDEX.md` module section + 3 illustrative stale lines.

## Verification

- `build_modules()` smoke → `['core_users','core_monitoring','core_mcp','core_storage','core_geo']`; zero residual `modules.<deleted>` refs in `src`/`tests`.
- `tests/apps` (test-group) → **27 passed** (covers build_modules + app composition).
- Frontend: zero dangling imports of deleted feature paths / removed administration-contacts exports / orphan nav keys. Full `vue-tsc` could NOT run — the pnpm `node_modules` store is broken (missing `vue-tsc` bin target), pre-existing env issue.

## Decisions

- **DB untouched** (per user: «не трогай БД, мы не переподключили её»). No retirement/tombstone migrations — a future fresh DB will only carry core branches; the dead modules' alembic branches simply never get created. (Contrast: [[alembic_retire_module_branch]] is the procedure if existing DBs ever need graceful retirement.)

## Phase 2 — JS + AGENTS docs cleanup (2026-06-24)

Follow-up pass on user request to also clean frontend JS and `AGENTS` docs of the deleted modules.

- **Frontend:** removed dead `settings.catalog.llm_providers` + `core_monitoring.catalog.llm_providers` locale namespaces (the catalog mechanism + `core`/`core_users` entries stay); updated `settingText.ts`/`taskText.ts` namespace comments; reworded stale doc-comments naming deleted modules in `MessageContent.vue`, `SourceLinks.vue`, `TablePaginationBar.vue`, `api/client/internal.ts`, `shared/{mcp_tool_icons,file-types,utils/messageText}.ts`, and the `MessageContentView` demo snippet. All edited locale JSON validated. Design-system mock-data strings (EdgeScroller/Kanban sample rows) left as throwaway showcase content.
- **Docs:** rewrote `docs/mcp/INDEX.md` (infra stays; documented that no module currently ships an MCP server, dropped the "4 servers restored" section + deleted-test references); `docs/frontend/markdown-rendering.md` (client-side only, dropped the `core_nlp` server half); fixed `module-system.md` current-module table (core-only) + `benches.md` bench table; cleaned `docs/INDEX.md` MCP/i18n/migrations example lines. Two parallel sub-agents swept the rest (platform: dates/loggers/permissions/soft-delete/database/migrations/module-state/architecture/api-zones/testing; conventions+frontend: backend/frontend/db-migrations/code-style/i18n/rules/api-client/core_monitoring/core_security/core_storage) — re-pointing current-state examples to surviving core modules, keeping historical "why" prose (mail_sync incident, FK-overlap incidents, swept-codebase note). Also cleaned `agent-primary.md` + `agent-docs-maintenance.md` example refs. Verified: no broken links to deleted doc hubs; remaining mentions are protected historical rationale + the kept `core_nlp` bench row.

## Phase 3 — remove core_geo (2026-06-24)

User decided to also drop `core_geo`. Same playbook:

- **Code:** `git rm` `src/modules/core_geo` + `tests/modules/core_geo` (+ rm leftover `__pycache__`); dropped `CoreGeoModule` from `build_modules` (now 4: core_users/core_monitoring/core_mcp/core_storage); fixed `core_security/__init__.py` docstring example; `module.py` prefix-comment example `/core-geo`→`/core-users`.
- **Frontend:** `git rm` `web/src/features/core_geo`; removed `coreGeoRoutes`/`coreGeoNav` from router + sidebar + the now-empty «Данные» section + `common.nav.data` locale key; world-map components (`continents.ts`/`iso3166.ts`) **kept** (used by the design-system WorldMap demo, not core_geo) — only their stale `core_geo` comments reworded; `internal.ts` example path re-pointed.
- **Test breakage fixed (was failing since phase 1, lives in `tests/core` so the earlier `tests/apps`-only check missed it):** `test_migrations.py::test_every_module_chain_is_linear_with_single_head` hardcoded module set → `{core, core_storage, core_users}`; the heavy `test_full_tree_upgrade_builds_model_schema_with_seeds` queried deleted `mail_sync_filters`/`mail_sync_mailboxes` seeds → removed those asserts (+ unused `text` import). Also re-pointed deleted-module sample strings in `test_app.py` (`--worker-module`/`worker_modules_set`), `test_crud_module_state.py` (`module_store`), `test_hashing.py` comment, `conftest.py` + `tests/README.md` `--module` examples.
- **Docs:** removed `AGENTS/docs/core_geo` hub + `dev/bench/core_geo`; a sub-agent re-pointed ~17 platform/conventions/frontend docs from core_geo examples to **core_users** (the foundational survivor; i18n reference-feature → core_monitoring); cleaned `docs/INDEX.md`, `MEMORY.md` routing, `project_app_path_tmp` memory, `agent-primary.md`.
- **Verify:** `build_modules()` → `['core_users','core_monitoring','core_mcp','core_storage']`; `--core` (pure+db) **235 passed**; heavy migration suite **3 passed** (full tree builds clean on fresh DB); zero residual `core_geo` in live code/docs (only historical task-log + research/plans + design-system mock remain).

> **Example-target note:** examples now use `core_users` (auth — foundational, lowest deletion risk). If more core modules get cut later, prefer genericizing over re-pointing again.

## Phase 4 — remove core_security (2026-06-24)

`core_security` was the unregistered pure-utility module (`sanitize_html` / `sanitize_svg`). `sanitize_html` had no live caller (its mail caller was gone). `sanitize_svg` was still used by **kept** `core_storage`'s `SvgValidator` (defangs stored SVGs — an XSS boundary). User chose to **drop SVG sanitization** rather than relocate it.

- **Code:** `git rm` `src/modules/core_security` (+ tests/bench/docs). In `core_storage`: removed `SvgValidator` (`validators/image/svg.py` + its import/export in `validators/image/__init__.py` + registration in `validators/registry.py`). **Kept** `SvgDetector` + mime/file-type maps — so an uploaded SVG is still *typed* `image/svg+xml` but, with no enabled validator, the admission policy **refuses** it (`registration.py`: `validator_for(mime) is None` → `rejected`, no bytes on disk). Reworded the `HtmlValidator`/`SvgDetector` docstrings + `SafeEmailBody.vue` comment that referenced the removed sanitizer. `lxml` stays a dep (still used by `pptx.py`).
- **Tests:** deleted `test_svg_validator.py`; in `test_storage_service.py` replaced `test_svg_pipeline_sanitizes_active_content` with `test_svg_detected_but_refused_without_validator` (asserts mime=svg, safety=rejected, validator_version="", not on disk) + fixed the `SvgValidator` import; dropped svg from `test_is_supported.py`'s supported list. `test_detectors`/`test_mime`/`test_file_types`/`test_freshness` unchanged (detector kept).
- **Docs:** removed `docs/core_security` hub + bench row + the `## Not registered` block in `module-system.md` (its only live entry was core_security; the other was an ancient `intercom_insights` tombstone); cleaned `docs/INDEX.md` + `MEMORY.md` routing (now lists core_users/core_monitoring/core_storage/core_mcp).
- **Verify:** `build_modules()` → 4 core; `--module=core_storage` **579 passed** (`-n0`; xdist has a pre-existing flaky collection-mismatch in `test_zip_validator` — non-deterministic zip-sample bytes, unrelated); `--core` **235 passed**. Zero `core_security` in live code/docs.

## Phase 5 — remove core_monitoring (2026-06-24)

`core_monitoring` = the tasks/locks **presentation** surface (the scheduler itself is core and stays). Deleting it took the whole monitoring UI chain with it.

- **Code:** `git rm` `src/modules/core_monitoring` + tests; dropped `CoreMonitoringModule` from `build_modules` (now 3: core_users/core_mcp/core_storage); reworded the docstring mentions in `src/core/router/internal.py` + `src/core/api/__init__.py` (the `/internal/tasks*` + `/monitor` endpoints are gone).
- **Frontend (whole task-monitoring chain — all consumers were deleted modules):** `git rm` `features/core_monitoring`, the global `stores/tasks.ts` + `api/tasks.ts`, shared `components/{TaskRunPanel,TaskStatusButton}.vue`, and the design-system `TaskStatusView` demo (+ its route + nav entry + unused `IconActivityHeartbeat`). Removed `coreMonitoring*` from router/sidebar + the now-empty «Мониторинг» section + `common.nav.monitoring` locale key.
- **Tests:** removed the heavy `test_app_factory::test_core_tasks_endpoint_returns_registered_tasks` (tested the deleted `/internal/tasks` endpoint — only surfaced under `--heavy`, missed by the earlier `--core` checks); re-pointed `test_crud_module_state` KV-namespace string to `core_users`.
- **Docs:** removed `docs/core_monitoring` hub; a sub-agent re-pointed 12 platform/conventions/frontend docs (examples → core_users/settings/administration; **kept** all core-scheduler mechanics — `tasks`/`tasks/{code}` channels, `logs/tasks.log`, `register()` convention); cleaned `docs/INDEX.md`, `MEMORY.md`, `agent-primary.md`, `mcp/INDEX.md`, `table_pagination_bar` memory.
- **Verify:** `build_modules()` → 3 core; `--core` **235 passed**; heavy core **9 passed**. Zero `core_monitoring` in live code/docs; no broken hub links.

## Phase 6 — remove the last 3 core modules → bare core (2026-06-24)

`core_mcp` (MCP introspection page), `core_storage` (file storage), `core_users` (**auth** — the whole permission model). This is the foundational step: the core itself depended on `core_users`.

- **Core had to change to build with zero modules** (not just deletion): `core_users` provided the `auth`/`ability`/`self`/`token_owner` guards, and `validate_guard_rules` fails on an unregistered guard kind. Fixes (decision: **no auth → `allow_all`**): `INTERNAL_DEFAULT_GUARDS` and `STORAGE_DEFAULT_GUARDS` `["auth"]`→`["allow_all"]`; the core settings API's two `@guard("ability","admin:update")` → `@guard("allow_all")`. `mount_mcp_servers` already short-circuits on zero servers (no fix needed). `build_modules()` now returns `[]`.
- **Verified the app actually builds with zero modules:** `create_app(build_modules(), Config())` → 5 routes (`/internal/health` + the 4 core-settings routes). `--core` **235 passed**, heavy core **9 passed**.
- **Tests:** rewrote `test_modules_build` (asserts `build_modules() == []`); `test_migrations` module-set → `{"core"}` + relaxed the `assert seen` in the cross-module-`depends_on` test (pure core has none); re-pointed arbitrary-string fixtures (`module_store`, `--worker-module`, `worker_modules_set`) to neutral placeholders.
- **Docs:** **deleted `platform/permissions.md`** (the level+action auth model is gone) + the `core_users`/`core_storage` hubs; a sub-agent re-pointed ~16 platform/conventions/frontend docs to **generic placeholders** (`my_module`, `<module>`) — no module survives as an anchor — keeping all core mechanics (guard registry + built-ins, scheduler, DB, zones, MCP-mount infra); I cleaned `docs/INDEX.md` (dropped permissions + the now-empty Modules section), `MEMORY.md` (modules routing → "none"), `mcp/INDEX.md` (removed the core_mcp introspection-page section, genericized auth), `agent-primary.md`.

> **Frontend NOT touched** (per the leave-it default): `web/` still compiles but every API call now hits a non-existent backend (no auth/login, no feature endpoints). Gutting/rebuilding the frontend for the bare core is a separate task.

## Phase 7 — clean dead web features (2026-06-26)

User: «Очисти веб .../web/src/features». Scope limited to `features/` (recommended default; auth-shell left for a later task). Of 4 features, 3 were backend-dead, `settings` stayed (its backend `/internal/core/settings` survives in bare core).

- **Removed:** `git rm -r` `features/{administration,core_mcp,user-profile}` (users CRUD → core_users gone; MCP page → core_mcp gone; profile/tokens/password → core_users gone).
- **Wiring fixed:** `router/index.ts` dropped the 3 route imports + spreads (left `designSystemRoutes` + `settingsRoutes`). `AppSidebar.vue` dropped the `administrationNav`/`coreMcpNav`/`ProfileNavCard` imports, the now-orphan «AI-интеграция» + «Администрирование» nav sections, and the `<ProfileNavCard>` `#append` block (nav now = «Разработка» section + design-system link; `auth.user` still drives `visibleNav`). Per-feature i18n auto-globs, so deleting the dirs drops their namespaces with no edit.
- **Locales:** removed orphan `nav.ai` + `nav.administration` from `web/src/locales/{en,ru}.json` (only `nav.development` still referenced).
- **Kept (auth-shell, out of scope):** `views/auth/LoginView`, `router/guards.ts`, `plugins/casl`, `stores/auth` (`isLoggedIn` still used by `App.vue` + guards). These are meaningless without a backend auth module but were explicitly left for a separate task.
- **Verify:** grep clean — zero residual refs to the 3 features or their symbols (`administrationNav`/`coreMcpNav`/`*Routes`/`ProfileNavCard`/`nav.ai`/`nav.administration`). `vue-tsc`/`vite` still un-runnable (incomplete `web/node_modules` pnpm store — pre-existing env issue, not these edits).

## Phase 8 — strip old-module references from docs (2026-06-26)

User: «Из доков нужно удалить информацию о старых модулях» — reverses the phase-2 decision to keep historical "why" prose naming deleted modules. Audit found `docs/` already structurally clean (no Modules section, every `INDEX.md` link resolves), but six files still **named** dead modules in examples/notes. Genericized each, keeping the mechanism/lesson:

- `platform/api-zones.md` — all `core_users` refs (the archived auth-design narrative) → "the auth module" / `AuthModule` / `/my-module`.
- `platform/router.md` — dropped "приходили из удалённого `core_users`" from the auth-guards note.
- `mcp/INDEX.md` — folded the `app.state.mcp_servers`-stash fact into the current-state note; removed the `core_mcp` introspection-page blockquote.
- `conventions/backend.md` — mail_sync hard-delete incident → generic "change-feed incident" (kept the worked lesson).
- `conventions/db-migrations.md` — cross-module-FK examples (`conversation_insights`/`conversations`/`ci01_init`/`c05`/`c07`/`c12`/`c13`) → placeholder `module_a`/`module_b` + `am_*`/`bm_*` migration ids.
- `frontend/rules.md` — single-root sweep list (twenty/intercom/mail_sync/agents/…) + `McpEditDialog`/`AgentConfigEditDialog` → generic wording.

Verify: `grep -rE '<all deleted module names>' AGENTS/docs` → **zero hits**. Memory tier (broken wikilinks, stale `user_profile_feature`, etc.) reported separately — NOT touched here (scope = docs only).

## Open items for the user (decisions pending)

- 🔴 **Frontend auth-shell still backend-less** — `features/` cleaned (ph7), but `LoginView`/`guards`/`casl`/`stores/auth` remain and call a non-existent `/me`/login backend. Decide: strip the auth-shell → authless shell (settings + design-system), rebuild for the new project, or remove `web/` outright. Separate task.
- **`AGENTS/research/`** — also `python-html-sanitization` (core_security) and the auth/storage research if any. Keep vs delete — pending.
- ✅ **`CLAUDE.md` symlink** — RESOLVED: user repointed it. `CLAUDE.md` + `AGENTS.md` now symlink to this fork's own `AGENTS/agent-primary.md` (relative, gitignored — local pointers; canonical file is git-tracked `AGENTS/agent-primary.md`).
- **`AGENTS/research/`** — logs of deleted modules' external services (intercom-api, gmail-import, anthropic-structured-output, llm-scoring-best-practices, lmstudio-api; maybe python-rate-limiting; **+ country-business-data** for core_geo; **+ python-html-sanitization** for core_security). Keep (reference) vs delete — user did not answer; left untouched.
- **`AGENTS/plans/`** — active plans for deleted modules (conversation_insights ×5, mail_sync ×3, user_contacts, mail-parser, intercom-attachments; **+ 2026-05-25-core-geo-module**). Archive vs delete — user did not answer; left untouched.
- **`AGENTS/education/lazy-loading.md`** — worked-example learning page built entirely on deleted `llm_providers`/`core_nlp` code. Rewrite (the surviving `src/core/mcp` fastmcp lazy-import is a valid replacement example) vs delete — pending decision.
- `dev/bench/core_nlp` left in place (core-named, predecessor of content_processors) — likely orphan.
- `AGENTS/tasks/*` history + `LOST-AND-FOUND.md` intentionally left referencing old modules (work log = history).
