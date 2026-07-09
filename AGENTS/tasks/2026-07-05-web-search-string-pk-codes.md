---
title: web_search — string primary keys (WQ_/WD_ codes) for query + page
date: 2026-07-05
status: completed  # in-work | completed | deferred
description: "Replace numeric ids on web_search_query/page with human-readable string PKs so the research MCP/LLM can distinguish queries from documents and reference them unambiguously. Query PK = WQ_<22hex> (random), page PK = WD_<22hex> (deterministic url-hash → dedup). Added hashing.random_hash(). Clean DB + rerun migrations."
tags: [web_search, research_registry, primary-key, hashing, mcp]
---

## Task

«первичный идентификатор в виде строки, в формате WQ_<22>/WD_<22>» — числовые id путают
нейронку; строковый префиксный код даёт ей понятную возможность различать запросы (WQ_) и
документы (WD_) и ссылаться на них. Добавить генератор случайного хеша в `hashing.py` и
использовать его. Плюс: очистить базу и перезапустить миграции.

## Design (confirmed by request)

- `hashing.random_hash()` — 22-char random hex (`secrets.token_hex(11)`), та же длина/алфавит,
  что и `text_hash`/`dict_hash`.
- `web_search/normalize.py`: `query_code()` = `WQ_` + `random_hash()` (случайный — у прогона нет
  естественного ключа); `page_code(url)` = `WD_` + `text_hash(normalize_url)` (детерминированный —
  код = ключ дедупа по url). Оба `String(25)` (3 префикс + 22 hex).
- **query PK** = `code` (drop numeric id). **page PK** = `code` (drop numeric id + separate unique).
- **result** оставляет суррогатный int `id`; FK `query_id`→`query_code` (String25), `page_code` String25;
  unique `(query_code, page_code)`, index `ix_web_search_result_query_code`.
- List ordering `id`→`created_at` (+ `code` tiebreaker) — числового id больше нет.
- Cross-module soft-refs в research_registry: `research_query.search_id:int`→`search_code:String25`;
  `research_document.page_code` `String(22)`→`String(25)`.

## What was done

- `src/core/utils/hashing.py` — `random_hash()` (+ export).
- `web_search/normalize.py` — `query_code()` (WQ_/random) + `page_code()` now WD_-prefixed;
  `PAGE_CODE_PREFIX`/`QUERY_CODE_PREFIX`.
- models query/page — `code` String(25) PK, dropped numeric id; result — `query_code` FK + page_code widened.
- migrations `wsm_001_query`/`wsm_002_page` (code PK, no id) / `wsm_003_result` (query_code FK).
- crud query (generate code, key by code, order by created_at) / page (order by created_at) /
  result (query_code) ; services save+searcher key by `query_code`/`row.code`.
- dto — `QueryRow.code` (was id), `PageRow` dropped id.  api — `/queries/{code}`.
- research_registry — `research_query.search_code` (String25, was Integer search_id) + dto field;
  `research_document.page_code` String(25). (research_registry has no migrations → create_all.)
- tests — codes everywhere (query_get(code), result_add(query_code=…), body["code"], WQ_/WD_ format +
  length asserts, query uniqueness per run); ordering tests made tie-safe (filter/count/pagination).

## Verification

- `uv run pytest` → **312 passed**; `--module=web_search` 40 passed.
- Codes verified: `random_hash()` 22 chars; `query_code()`→`WQ_…`; `page_code(url)`→`WD_…`; PKs = `code`.
- **DB cleaned + migrations rerun** (per request): backed up `core_gateway` API keys → wiped dev sqlite →
  `migrate upgrade` (8 migrations, fresh) → create_all filled research_* → restored gateway keys.
  Verified `web_search_query` PK=`code`, `research_query` has `search_code`, 6 gateway settings restored.

## Result

Done end-to-end. `web_search_query`/`web_search_page` now use string code PKs (`WQ_<22>` random /
`WD_<22>` url-hash), numeric id removed; `web_search_result` keeps surrogate id + `query_code`/`page_code`
FKs. `hashing.random_hash()` added. research_registry soft-refs retyped (`search_code`, page_code 25).
Frontend routes queries by `code` (subagent, build PASS); docs + MEMORY describe the string-PK scheme
(subagent). Full `uv run pytest` → **312 passed**; `migrate check` up to date; dev DB wiped + migrations
rerun (gateway API keys preserved). No stale numeric-id refs remain.
