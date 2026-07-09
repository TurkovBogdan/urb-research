# research: research_index + code PK

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — refactor/rebuild (iteration 1)

## Goal

Rename the root research table `research` → `research_index`, and switch its PK from
surrogate int `id` to a readable string `code` (prefix `RS_` + `random_hash()`), mirroring
the web_search code scheme (`WQ_`/`WD_`). No dedup on topic → random hash.

Scope of this iteration: **only** `research_index`. The child FK
`research_query.research_id` → `research_code:String(25)` (soft target `research_index.code`)
is changed minimally. Query/document/report tables keep their int ids for now (next iterations
→ `RQ_`/`RD_`/`RR_`).

## Prefix scheme (agreed)

R-family (domain = research), 2nd letter = entity:
`RS_` research (root), later `RQ_` query, `RD_` document, `RR_` report.

## What was done

- **Model** `models/research.py`: `__tablename__` `research`→`research_index`, PK int `id`→`code:String(25)`,
  CHECK `ck_research_status`→`ck_research_index_status`. `models/query.py`: FK `research_id:int`→
  `research_code:String(25)` (→`research_index.code`, CASCADE), index `…_research_id`→`…_research_code`.
- **Migrations** (in-place, revision ids kept): `rem_001` builds `research_index` with `code` PK;
  `rem_002` builds `research_query` with `research_code` FK + renamed index.
- **CRUD** `crud/research.py`: new `RESEARCH_CODE_PREFIX="RS_"` + `research_code()` = `RS_<random_hash()>`;
  `research_create` generates code; `research_get`/`research_set_overview` keyed by code; list tiebreak by code.
  `crud/query.py`: `query_count_by_research_ids`→`query_count_by_research_codes`, `query_create_many(research_code=…)`,
  `query_list_by_research(research_code)`.
- **DTO**: `ResearchRow.id`→`code:str`, `ResearchQueryRow.research_id`→`research_code:str`,
  `ResearchOverview.research_id`→`research_code`.
- **API** `api.py`: `/researches/{research_code}` (str), count-by-codes, `ResearchListRow` keyed by code.
- **MCP** `mcp/research.py` + `mcp/__init__` instructions: all `research_id`→`research_code`.
- **Frontend**: `api.ts` (types + `getResearch(code)`), `routes.ts` (`:id`→`:code`), `research-detail.store`
  (`load(code)`), `ResearchesView` (`item-value="code"`, nav by code), `ResearchView` (watch `route.params.code`,
  no `Number()`), `QueryView` (back-link `research_code`).
- **Bench** `dev/bench/research/seed_queues_research.py`: `_RESET_TABLES` `research`→`research_index`,
  `research.id`→`research.code`, `research_code=` kwarg.
- **Dev DB rebuilt**: backend down → backed up `core_modules_settings` (11 rows) → dropped `runtime/dev/app.sqlite3`
  → `migrate upgrade` → restored settings.

## Verification

- `migrate check` — up to date; PRAGMA confirms `research_index.code VARCHAR(25)` PK + FK `research_code→research_index.code`.
- In-memory smoke: create→`RS_`+22hex (len 25), FK propagates to queries, get/count-by-code, missing→None.
- `uv run pytest --core` — 266 passed. `vue-tsc --noEmit` — EXIT 0.

## Problems

None. Engine-init in the standalone smoke needed a shared temp sqlite file (plain `:memory:` gives each
connection a fresh DB without StaticPool).

## Result

Iteration 1 done: root table is `research_index`, keyed by readable `RS_<hash>` code end-to-end
(model→migration→CRUD→DTO→API→MCP→frontend→bench). Next iterations: `research_query`/`research_document`/
`research_report` → `RQ_`/`RD_`/`RR_` codes. `web/dist` not rebuilt (dev serves via Vite; no pnpm on PATH) —
rebuild before prod deploy.
