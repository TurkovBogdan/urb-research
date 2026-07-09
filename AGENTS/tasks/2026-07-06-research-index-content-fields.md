# research: research_index content fields (drop status)

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** module `research` — refactor/rebuild (iteration 2)

## Goal

Turn `research_index` into a knowledge artifact. Remove the research-level `status`; replace
`topic`/`overview` with `title` (≤128, NOT NULL), `description` (≤512, nullable), `body`
(unlimited Text, nullable). Query-level `research_query.status` is untouched.

Decision (user skipped the clarifying prompt → recommended defaults): replace both `topic`+`overview`;
`title` required, `description`+`body` nullable.

## What was done

- **constants.py**: removed all `RESEARCH_*` statuses + `RESEARCH_STATUSES` (query statuses + `sql_in` kept).
- **models/research.py**: dropped `topic`/`status`/`overview` + CheckConstraint; added
  `title:String(128)` NOT NULL, `description:String(512)` nullable, `body:Text` nullable.
- **migrations/rem_001**: rebuilt columns (`code`, `title`, `description`, `body`, timestamps), no CHECK.
- **crud/research.py**: `_filtered` by `title`; `research_create(*, title, description=None, body=None)`;
  dropped `status` from list/count; `research_set_overview` → `research_update(code, title?, description?, body?)`
  (None = keep).
- **dto.py**: `ResearchRow` = code/title/description/dates; `ResearchDetail` carries `body`;
  removed `ResearchOverview`.
- **api.py**: list drops `status` param; detail returns `body`.
- **mcp**: `research_start(title, description?, body?)`, `research_get` → `ResearchDetail` (body + queries),
  `research_set_overview`/`research_get_overview` → single `research_update`; instructions rewritten.
- **bench** `seed_queues_research.py`: `research_create(title=…)` + `research_update(body=…)`; dropped
  research-status set (+ unused `Research`/`RESEARCH_DONE` imports).
- **frontend**: `api.ts` (drop `ResearchStatus`, `topic`/`status`→`title`/`description`, `overview`→`body`),
  `labels.ts` (drop research statuses), `researches.store` (drop status filter), `ResearchesView`
  (drop status column/filter/chip, `topic`→`title` + description column), `ResearchView` (title + description,
  drop status badge, `overview`→`body`), `locales/ru.json`.

## Verification

- Dev DB rebuilt (backend WAS running → stopped it first per the deleted-inode rule → backed up 12 settings →
  drop → `migrate upgrade` → restore → **restarted backend**, health 200). PRAGMA: `title VARCHAR(128)` NOT NULL,
  `description VARCHAR(512)` nullable, `body TEXT` nullable. `migrate check` up to date.
- In-memory smoke: create(title,description) → body None; `research_update(body=…)` keeps title/desc; get + title filter ok.
- `uv run pytest --core` — 266 passed. `vue-tsc --noEmit` — EXIT 0. Live `GET /internal/research/researches` → `{items:[],total:0}`.

## Problems

Backend was running at rebuild time — stopped backend/worker before dropping the sqlite file (deleted-inode
hang risk), rebuilt, restarted. Vite left untouched.

## Result

`research_index` is now title/description/body (no status). Frontend list shows name + description;
detail shows title + description + body. MCP surface: `research_start`/`research_update`/`research_get`.
`web/dist` not rebuilt (dev = Vite; no pnpm on PATH) — rebuild before prod deploy. Cosmetic: `.topic-cell`/
`.topic-text` CSS class names left as-is.
