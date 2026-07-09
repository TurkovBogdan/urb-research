---
title: web_search — split provider into search engine + content fetcher (two defaults)
date: 2026-07-05
status: completed  # in-work | completed | deferred
description: "Module now distinguishes two functions of the external web — search (returns links) and content fetching (returns page markdown) — each with its own default provider setting. Search engines: Tavily/Firecrawl/Grok(xAI). Content fetchers: Tavily/Firecrawl (Grok can only search). Added xai search provider on top of core_gateway."
tags: [web_search, providers, xai, grok, settings]
---

## Task

«Две разные функции: (1) поисковый запрос → ссылки, (2) получение контента страниц.
Грок умеет искать; firecrawl и tavily — и искать, и получать контент. На уровне модуля —
выбор поискового движка по умолчанию + выбор сервиса получения контента по умолчанию.»

## Design

- Split `SearchProvider` → two ABCs in `providers/base.py`: `SearchEngine` (`search(request)->links`)
  and `ContentFetcher` (`fetch_pages(urls)->md`, `pages_per_request`). Provider may implement both.
- Two registries (`providers/registry.py`): `register_search`/`register_content`,
  `get_search`/`get_content`, `search_codes`/`content_codes`.
- Providers: `tavily` + `firecrawl` register in BOTH; new `providers/xai/` (`XaiSearchEngine`) registers
  in SEARCH only — Grok search = core_gateway `responses()` + `web_search` tool, urls from `url_citation`
  annotations (fallback `web_search_call.action.sources`), dedup + truncate to `max_results`.
- Two settings (`module_settings.py`): `search_provider` (tavily|firecrawl|xai, default tavily) +
  `content_provider` (tavily|firecrawl, default tavily); kept `fetch_concurrency`/`default_pages`; dropped
  single `provider`.
- Query records both: `web_search_query.provider` → `search_provider` + `content_provider` (String64).
- Pipeline (`services/searcher.search`): search engine → links → `store_results` (pending pages, no inline
  content) → content fetcher pulls markdown → finish. Dropped the Tavily inline-content shortcut
  (`with_content`) — search & content are independent now. `active_search_provider`/`active_content_provider`.

## What was done

- providers: `base.py` (SearchEngine/ContentFetcher), `registry.py` (two registries), `tavily`/`firecrawl`
  clients implement both + register in both, new `xai/` package (search-only), `__init__` exports.
- `module_settings.py` — two choice settings + helpers `search_provider()`/`content_provider()`.
- model/migration `web_search_query`: `search_provider` + `content_provider` columns (was `provider`).
- crud/query (query_create both providers, filter by search_provider), dto QueryRow, api list filter.
- services/searcher (two-provider pipeline), services/save (dropped inline-content branch).
- tests: crud/save/search/searcher/providers/module_settings/api updated (stub implements both roles,
  registered in both registries; settings test asserts search opts include xai, content excludes it).
- frontend (subagent): QueryRow two provider fields, separate columns + search-engine filter
  (tavily/firecrawl/xai), detail shows both, labels; build PASS.
- docs/memory (subagent): web_search INDEX + MEMORY rewritten to the two-role split + xai search engine.

## Verification

- `uv run pytest` → **312 passed**; `--module=web_search` 40 passed.
- Registries: search = {firecrawl, tavily, xai}, content = {firecrawl, tavily}; settings keys =
  search_provider/content_provider/fetch_concurrency/default_pages.
- Dev web_search schema rebuilt (query has search_provider+content_provider); fresh-sqlite migration apply OK.

## Result

Done end-to-end. web_search now has two independent provider roles with separate defaults: search engine
(Tavily/Firecrawl/Grok) + content fetcher (Tavily/Firecrawl). Grok added as a search-only engine over
core_gateway. Query records both providers; pipeline searches then fetches content separately (inline
shortcut dropped). Frontend shows both + search-engine filter (build PASS); docs+MEMORY updated.
Verification: `uv run pytest` → **312 passed**; offline end-to-end (stub in both registries) confirms
search_provider+content_provider recorded and content fetched; xAI citation parsing unit-checked
(dedup, cited>visited, fallback to sources) — no network. Dev DB clean.
