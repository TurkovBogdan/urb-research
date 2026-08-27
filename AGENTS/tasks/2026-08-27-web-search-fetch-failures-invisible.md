---
title: Page fetch failures are silent — diagnosis
date: 2026-08-27
status: in-work  # in-work | completed | deferred
description: "The MCP kept failing to fetch pages and the user never learned about it. Audit of the web_search fetch path + the research source surface: find why failures happen and why nothing surfaces them."
tags: [web_search, research, mcp, observability]
---

## Task

«Этот mcp всё время выдавал ошибки по получению страниц а я даже не знал об этом. Проверяй код, что не так с получением».

## Context

`fetch_engine` setting = `web_scrapper`; the local daemon `daemon-web-scrapper` (127.0.0.1:19020)
is not running. Every batch fetch therefore raises `httpx.ConnectError`, the page row goes
terminal `error`, and no layer above reports it.

## What was done

Diagnosis only (no code changed yet). Dev DB evidence:

- `web_search_page` by status/error: `error/ConnectError/web_scrapper` — **3119**;
  `done/web_scrapper` — 460; `done/firecrawl` — 548; `error/empty/web_scrapper` — 187;
  `error/HTTPStatusError/firecrawl` — 16; `error/ReadTimeout/firecrawl` — 1.
- ConnectError spread over ~every day since 2026-07 → daemon has been down/absent for months.
- `research_source_document` × page status: **kept + page error = 2406**, **filtered + page
  error = 1375**, pending + page error = 75. I.e. ~3.8k sources were "reviewed" with an empty
  body; 3021 distinct dead pages are referenced by sources.
- `DOC_FETCH_ERROR` (`fetch_error`) exists in `research/constants.py` and in the
  `rem_005` CHECK constraint but is **never assigned anywhere** — zero rows carry it.

Defects found:

1. **Fetch engine unreachable, silently** — `web_scrapper` daemon is not running;
   `WebScrapperGateway.BASE_URL` is a hardcoded localhost port. `_fetch_pages`
   (`services/searcher.py`) swallows the exception into `page_set_error` and the run still
   ends `done`.
2. **`query_search_run` hides the outcome** — it returns sources regardless of
   `run.status`/`run.error`, and a search that errored returns `[]` with no reason.
3. **Source DTOs carry no fetch signal** — `ResearchSourceDocumentRow`/`Detail`
   (`research/dto.py::_source_document_fields`) expose neither `page.status` nor `page.error`;
   `source_get` returns `body: null` and the agent cannot tell "empty page" from "fetch failed".
4. **`fetch_error` is dead code** — `source_document_create` always writes `DOC_PENDING`, so the
   status designed for this case never appears and `sources_list(status="fetch_error")` is a
   no-op filter.
5. **Dedup poisoning: an `error` page is never re-fetched** — `_store_results` only returns
   pages that are `pending` after `page_upsert`; a page already in `error` (deduped by url hash)
   is reused as-is forever, so the 3021 dead pages stay dead even after the daemon comes back.
   There is no retry, no reaper for page rows (only for stale `processing` queries).
6. **Fetch engine availability is never gated** — `_run` checks `engine.available()` for the
   search engine only; a disabled/unreachable fetch engine is discovered per-batch as a network
   error instead of up front.

## Live reproduction (2026-08-27)

Ran a throwaway research through the MCP end to end (`RESEARCH@69a6859a09e878772e28b6`,
«Test: высота Эйфелевой башни»). Six sources came back, all `pending`, all looking healthy.
Underneath: 4 pages created that minute and dead (`ConnectError`), 2 with bodies **fetched on
2026-07-12** — reused by url-dedup from an unrelated research, i.e. this run downloaded nothing
at all. The query itself finished `done` with `error = NULL`.

Two findings this added to the list above:

- The run is indistinguishable from a successful one at every level the agent can see. The only
  signal is `body: null` from `source_get`, and only if the agent opens the source.
- `summary` is the **search engine's snippet**, not the material — and for a simple question it
  already contains the answer (330 m with antenna, 300 m structural, 312 m with flagpole). So an
  agent can produce a plausible, even factually correct synthesis without a single body. That is
  what happened across the ~3.8k historical sources: the failure is not merely hidden, it is
  masked by coherent text.
- `pending` is overloaded: `FETCH_STATUS_PENDING` (fetch not started, transient) vs `DOC_PENDING`
  (not reviewed, waits for the agent). The agent sees only the latter but reads it as "still
  loading" → waits or re-polls forever, since fetch is terminal and has no retry.

## What was done

Visibility half only (fix 1/2/4 from the defect list; refetch + backfill deliberately left out):

- `research/dto.py` — `ResearchSourceDocumentRow` / `…Detail` gained `fetch_status` /
  `fetch_error`, filled in `_source_document_fields` from the joined page. A null `body` is now
  self-explaining in both `sources_list` and `source_get`.
- `research/mcp/research.py` — new `_initial_source_status(page)`: a source whose page is
  `FETCH_STATUS_ERROR` is created as `DOC_FETCH_ERROR` instead of `DOC_PENDING`. This is the
  missing bridge between the two modules' status machines; `DOC_FETCH_ERROR` stops being dead
  code and `sources_list(status="fetch_error")` stops being a no-op filter.
- Agent-facing wording — `query_search_run` docstring, `source_get` docstring and the server
  instructions (`mcp/__init__.py`) now state that fetching is separate from searching, that
  `fetch_error` is terminal so waiting/polling is pointless, and that `summary` is the engine's
  snippet and must not be reviewed in place of the material.

Tests (`tests/modules/research/`):

- `conftest.py` — the search stub gained `fetch_raises` (whole-batch failure = unreachable fetch
  engine); a url absent from `pages` already yielded `error`/`empty`.
- `test_search_sources.py` — `_SOURCE_KEYS` extended; new cases: source marked `fetch_error` on
  an empty page, on an unreachable engine (`ConnectionError` name recorded), the broken source
  being absent from the `pending` review queue while `status="fetch_error"` finds it, and
  `source_get` explaining a null body. The happy-path case now asserts `fetch_status == "done"`.

Migration `rem_008_source_doc_error_status` carries both halves of the change. **Schema:** the
status set swaps the never-assigned `fetch_error` for `error`. **Data:** the same rule the forward
path now applies is applied to the rows that predate it, **including already reviewed ones** — a
source whose page sits in `error` becomes `error` regardless of a prior `kept`/`filtered` verdict,
because a verdict reached without the material is not a verdict. `relevance` / `note` are left
untouched, so the old assessment stays readable and the source returns to the queue once its page
is refetched. `depends_on = "wsm_002_page"` (reads another module's table; `wsm_002` is a non-head,
per `docs/conventions/db-migrations.md`).

Order matters inside it: the CHECK is rewritten **before** the backfill, because SQLite's batch
mode copies rows into a table that already carries the new constraint — the copy has to happen
while every row still holds a review status. `downgrade` restores the old constraint and parks the
`error` rows back in `pending`; which status each held before is recorded nowhere.

The backend was stopped before every apply (`.env` ships `DB_AUTO_MIGRATE=true` + `--reload` → two
writers on one SQLite file).

Dev DB before → after:

| source status | page | before | after |
|---|---|---|---|
| kept | error | 2406 | 0 |
| filtered | error | 1375 | 0 |
| pending | error | 79 | 0 |
| error | error | 3 | **3863** |
| kept / filtered / pending | done | 1459 | 1459 (untouched) |

Of the 3863, 3781 kept their `relevance` and 3737 their `note`.

Verified: `uv run pytest -q` → **562 passed**. Then live through the MCP after a backend restart —
the same search returns `status: "error"` with `body: null` for the dead sources and `pending` for
the live ones, and `sources_list(RESEARCH@…, status="error")` returns exactly the broken ones.

### Follow-up: three error fields collapsed into one status + one cause

The first cut shipped `status: "fetch_error"` **plus** `fetch_status` **plus** `fetch_error` —
three fields saying one thing, and `fetch_status` was pure restatement of the status. On the
user's push-back the source row was reduced to the same shape the page itself uses:

```json
{"status": "error", "body": null}
```

The cause field went too, on a second push-back: the research agent is a consumer, the retry
decision is not its call, so `ConnectError` vs `empty` buys it nothing. `web_search_page.error`
still records the cause for the human — the web UI's pages section shows it with a filter. The
earlier argument for the longer status name — "two `error` keys would collide in one object" —
only held while the redundant fields existed.

`DOC_FETCH_ERROR` → `DOC_ERROR = "error"`. This was first shipped as a second migration on top of
the backfill; both were then **collapsed into the single `rem_008_source_doc_error_status`** above,
since neither had reached any DB but the local dev one — a migration that writes a value and a
follow-up that renames it is history nobody should have to read. Dev's `alembic_version` was
repointed by hand from the retired `rem_009` id (data and schema were already in the target state;
the row was verified to be exactly one before the UPDATE).

Worth remembering from the retired two-step version: renaming a **checked** value cannot be done
in the obvious order. The old CHECK rejects the new value, and batch mode copies rows into a table
that already carries the new CHECK — so a rename needs widen-to-both → move data → narrow, while a
plain swap (as here, where no row holds the old value) can rewrite the CHECK first. Getting that
wrong died mid-copy with `IntegrityError: CHECK constraint failed`, and because alembic's SQLite
dialect is non-transactional it left an orphan `_alembic_tmp_research_source_document` behind (data
and `alembic_version` intact) that had to be dropped by hand before re-running.

### Verified against the stable instance's DB

`urb-research-stable` sits at `rem_005_source_document` (the groups migrations never reached it),
so the whole pending chain is rehearsed there before shipping. Its live DB was first duplicated
into `runtime/dev/backup/app.sqlite3.rem_005_source_document.2026-08-27` — named after the
research head it is frozen at, and inside the gitignored `runtime/dev/` (verified with
`git check-ignore`, the file is 40 MB). The rehearsal then runs against a **copy** of that backup
via `DB_PATH=/tmp/…`, never the original.

Chain applied in one run: `rem_006_group` → `rem_007_research_group_code` →
`rem_008_source_doc_error_status`. Result on stable's real data: 4096 `error` / 862 `kept` /
579 `filtered` / 14 `pending`, and the join against `web_search_page` is a clean diagonal — every
`error` source sits on an `error` page and every reviewed source on a `done` one, no crossover.
4021 of the 4096 kept their `relevance`, 3977 their `note`. `PRAGMA integrity_check` ok,
`foreign_key_check` empty, no orphan `_alembic_tmp_*`, final CHECK
`status IN ('error','pending','kept','filtered')`, and the groups tables from `rem_006`/`rem_007`
landed alongside. Identical numbers to the pre-collapse two-migration run. A from-scratch build
(empty file → head) lands on the same constraint.

**Rehearse-on-stable is the standard for this project**: back up stable's DB into its
`runtime/dev/backup/` tagged with the head revision, then apply the pending chain to a copy and
diff the outcome before shipping.

Frontend followed the rename (`features/research/api.ts` `SourceStatus`, `labels.ts` badge colour,
`locales/ru.json`, `DocumentsTable.vue` filter list) and `web/dist` was rebuilt.

### Refetch: `sources_refetch` + the dedup one-liner

The visibility half left 3863 sources parked in `error` with no way for an agent to revive them.
Two complementary fixes:

- `_store_results` (`web_search/services/searcher.py`) now hands `error` pages to the fetch step
  alongside `pending` ones. Url-dedup is permanent, so previously a page that failed once could
  never download again; now an ordinary repeat search heals itself.
- `Searcher.refetch(page_codes)` — a public facade entry next to `search` / `submit`, a thin
  wrapper over the existing `_fetch_pages`. No search engine is involved, so no slot gate; a
  fetch engine disabled in settings raises before any network call rather than dropping a hundred
  pages into `error` one by one.
- `sources_refetch(code)` (MCP, `research/mcp/source_document.py`) — takes SOURCE@ / QUERY@ /
  AREA@ / RESEARCH@, the same prefix dispatch `sources_list` uses plus the single-source level,
  and returns **only the sources it touched** with their new status: `pending` = the material
  arrived and it is now yours to review, `error` = it failed again. No new DTO, no counters — the
  agent already speaks in source rows, and rows carry the codes a summary would not.

The sharp bit is `source_document_revive_by_pages`: statuses are recomputed **by `page_code`, not
by the requested scope**. One page is deduped across researches (stable: 4096 sources on ~3558
pages), so a revived page has to clear `error` from every source hanging off it — otherwise a
neighbouring research keeps an `error` source on a page that now has a body. Reviewed sources
(`kept` / `filtered`) are left alone: their verdict was reached on the material.

Tests (+8, 570 total): revival once the material arrives, a source that fails again, the single
SOURCE@ level, an empty result when nothing is broken, cross-research revival through a shared
page, both bad-code paths, and in `web_search` — `_store_results` returning a previously failed
page for another attempt. The research stub's `results` / `pages` / `fetch_raises` became public
so a test can stage "the fetch service came back up" between runs.

Live check: the scraper daemon happened to be running by then, so
`sources_refetch(RESEARCH@69a6859a09e878772e28b6)` on the Eiffel fixture returned 7 rows — 6
`pending`, 1 `error` — and the pages behind them now hold real bodies (5–163 KB). The one failure
is `tass.ru` with cause `empty`: the scraper reached it and extracted nothing, which is a property
of the page rather than a transport failure. Both AP News sources (found by two different runs on
one deduped page) revived together, which is the by-page rule working.

### `interface_open` + MCP server version 0.3

A separate ask, landed in the same pass: one tool that turns **any** system code into an app page
and opens it in the user's browser — the bridge from agent output to the user's eyes.

`research/mcp/interface.py` (its own file: the tool is about any entity, not about sources).
Section is picked by code prefix — research routes carry the **prefixed** code, exactly as the
frontend builds its own links (`/research/sources/SOURCE@…`), while `SEARCH@` / `PAGE@` map to
`/web-search/{queries,pages}/<bare>` because web_search does not prefix its codes. Unknown or
untyped code → `ValueError`. Returns the address as well as opening it, so the agent can paste it
into the chat.

The base url is `server_host` + `server_port`, the same one the stdio shim opens — the app is
local and the backend serves the built SPA itself, so this address works in dev and prod alike.
Tool docstring and server instructions both say the call acts on the user's machine and is not
something to fire after every step.

`_SERVER_VERSION` in `core/mcp/factory.py`: 0.1 → **0.3** (one constant, shared by every mounted
MCP server). Confirmed over the wire: `initialize` returns
`serverInfo: {name: research, version: 0.3}`.

Tests: 10 cases — all eight code types mapped to their page, plus untyped and unknown-type codes
rejected; `webbrowser.open` is monkeypatched and asserted to receive exactly the returned url.
Live: all three sample codes returned their address and the routes answer 200 `text/html`.

## Problems

The three source files touched (`dto.py`, `mcp/research.py`, `mcp/__init__.py`) already carried
uncommitted changes from the research-groups task, so they cannot be staged cleanly for this work
alone — flagged to the user rather than resolved.

## Result

Changed: `src/modules/research/dto.py`, `src/modules/research/mcp/research.py`,
`src/modules/research/mcp/__init__.py`, `src/modules/research/mcp/source_document.py`,
`tests/modules/research/conftest.py`, `tests/modules/research/test_search_sources.py`.
Added: `src/modules/research/migrations/versions/rem_008_source_doc_error_status.py`.
Also changed by the rename: `src/modules/research/constants.py`,
`src/modules/research/models/source_document.py`, `web/src/features/research/api.ts`,
`web/src/features/research/labels.ts`, `web/src/features/research/locales/ru.json`,
`web/src/features/research/components/DocumentsTable.vue`, `web/dist/` (rebuilt).

Live check after the backfill: `sources_list(RESEARCH@ac7bcfb520ca700afb1fea, status="kept")` —
the research that yesterday looked fully reviewed — now returns `[]`, and its sources report
`fetch_error` / `ConnectError` with the old `relevance` and `note` still attached.

## UI wording pass (after the rename)

Swept the interface for the renamed status: `SourceStatus`, `SOURCE_STATUS_COLOR` (red `error`),
`DocumentsTable`'s `STATUSES` and the locale key were all already on `error` — the only leftover was
the label text, still reading «Ошибка загрузки». Now «Ошибка», matching the status's new meaning
(the material never arrived — the cause is not necessarily the fetch). One string serves all four
places that show it: the badge in `SourceView`, the badge and the filter chip in `DocumentsTable`,
the badge in `QueryView`.

Checked live on `RESEARCH@45b8e9843e939d2f7c50d8` (202 error sources): filter chip «Ошибка · 202»,
red badges in the table, badge on the source page, badge on the search page; no «Ошибка загрузки»
and no raw i18n key left in the DOM, console clean. `vue-tsc` 0, `web/dist` rebuilt,
`--module=research` 191 passed, full suite **562 passed**, `migrate check` up to date at
`rem_009_source_doc_error_status`.

Also changed by the refetch step: `src/modules/web_search/services/searcher.py`,
`src/modules/web_search/crud/page.py`, `src/modules/research/crud/source_document.py`,
`tests/modules/web_search/test_store_results.py`.

Still open: marking `summary` as the search engine's snippet rather than presenting it alongside
the body — the live runs showed it is what tempts an agent to review a source it never read. No
automated test covers the backfill migration itself (`db` tests bypass Alembic and `heavy` needs
Postgres); it was verified against the dev DB and rehearsed on a copy of stable's.

### Refetch reaches the interface + the tool takes a batch of codes

The refetch step existed only as an MCP tool, so a human looking at a research full of `error`
sources had no way to fix them. Added, by explicit user decision, on **any** row rather than only
broken ones:

- **Backend.** `services/refetch.py::refetch_sources(documents)` — the shared step behind the MCP
  tool and the new HTTP handles: download the pages, then fix statuses by two different rules —
  `source_document_revive_by_pages` clears `error` from every source on those pages (a page is
  deduped across researches, a neighbour's verdict is not ours to touch), and the new
  `source_document_reset_by_codes` recomputes the **requested** sources from their page: page
  `done` → `pending`, otherwise `error`. The latter is what drops a `kept`/`filtered` verdict —
  it was reached on material that has just been re-downloaded; `relevance` and `note` survive so
  the old assessment stays readable.
- **HTTP.** `POST /researches/{code}/documents/refetch` and `/areas/{code}/documents/refetch`
  (scope = sources in `error`), `POST /source-documents/{code}/refetch` (that one source, any
  status). A disabled fetch engine is a 400, not a silent empty run.
- **Frontend.** `DocumentsTable` got the bulk button and a row-menu item; the action itself lives
  in `useSourcesRefetch` (busy flags, toast, reload) so both the research and the area page wire it
  in three lines. Tests: +7 API cases.

Two things the live run corrected: the button first sat in the filter grid as a fourth column and
squeezed the search field down to its icon at 1233px — moved to its own right-aligned row above the
filters; and the toast is the only trace the action leaves when nothing revives, since a row that
failed again looks exactly as it did before the click.

**`sources_refetch` now takes up to 6 codes** (`SOURCES_REFETCH_MAX`), levels may be mixed, and
returns `SourcesRefetched {sources, skipped}` instead of a bare list — `skipped` carries a per-code
reason (`nothing_to_fix` / `not_found` / `not_a_source_code`). A bad code no longer aborts the call:
on a batch of six, one miss must not cancel the work on the other five, so misses go into the report
and exceptions are left for what breaks the call as a whole (empty list, over the cap, disabled
engine). Overlapping codes (a research and its own area) download nothing twice — sources are keyed
by their own code before fetching. Tests rewritten for the new signature, +6 cases; **636 passed**.

⚠ Not addressed, and it is the real limit: the whole path is **blocking**. One HTTP request holds
until every page is downloaded, and the frontend client aborts at 20 s (`REQUEST_TIMEOUT_MS`), so a
research with hundreds of dead pages cannot be healed from the interface. The scheduler exists and
is idle (`core/heartbeat` is its only task; `WORKER_ENABLED=false` in dev) — the fix is to have the
handle only reset statuses and let a `web_search` task drain `pending` pages in batches. Discussed
with the user, deliberately deferred.
