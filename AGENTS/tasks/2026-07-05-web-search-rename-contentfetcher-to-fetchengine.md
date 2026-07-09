---
title: web_search — structure cleanup (FetchEngine + fetch registry + settings.py + inline normalize)
date: 2026-07-05
status: completed
description: "Symmetric provider naming: content-role ABC ContentFetcher → FetchEngine; content registry fns register_content/get_content/content_codes → register_fetch/get_fetch/fetch_codes. Search-role (SearchEngine, register_search/get_search/search_codes) unchanged. Settings layer (content_provider / active_content_provider) left as-is — it names the runtime setting, not the engine role. Renamed module file module_settings.py → settings.py (+ its test). Deleted normalize.py, colocating its helpers at point of use: normalize_url/page_code/domain_of → crud/page.py, query_code → crud/query.py."
tags: [web_search, providers, rename, refactor]
---

## Task

«SearchEngine и FetchEngine и создаём два реестра с аналогичными названиями» — align the
content-role class + registry with the search-role naming.

## What was done

- `providers/base.py` — `ContentFetcher` → `FetchEngine` (docstring + class + `__all__`).
- `providers/registry.py` — dict `_content` → `_fetch`; `register_content`/`get_content`/`content_codes`
  → `register_fetch`/`get_fetch`/`fetch_codes` (+ docstring + error message «Unknown fetch engine»).
- `providers/__init__.py` — re-exports updated.
- `providers/tavily/__init__.py`, `providers/firecrawl/__init__.py` — `register_content` → `register_fetch`.
- `providers/tavily/client.py`, `providers/firecrawl/client.py` — base class `ContentFetcher` → `FetchEngine`.
- `services/searcher.py` — import + `get_fetch(...)` + `_fetch_pages(fetcher: FetchEngine, ...)`.
- tests: `test_providers.py` (imports, `test_fetch_registry_...`, `get_fetch`), `test_search.py`
  (`_StubProvider(SearchEngine, FetchEngine)`, `registry.register_fetch`).
- docs/memory: `docs/web_search/INDEX.md` + `AGENTS/memory/MEMORY.md` web_search row updated to new names.

Second rename (file): `module_settings.py` → `settings.py` (`mv`) + its test `test_module_settings.py`
→ `test_settings.py`. Importers updated: `module.py`, `services/searcher.py` (alias `module_settings`
→ `settings`, 4 usages), `test_settings.py`; doc `settings.py`. Module still imports SCHEMA the same way.

Third change (delete + colocate): removed `normalize.py`; its helpers moved to their single point of
use — `normalize_url`/`page_code`/`domain_of` (+`PAGE_CODE_PREFIX`) into `crud/page.py`, `query_code`
(+`QUERY_CODE_PREFIX`) into `crud/query.py`. Updated importers: tests `test_save.py`/`test_crud.py`/
`test_search.py` import `page_code` from `crud.page`; model docstrings + `docs/web_search/INDEX.md`
point at the new homes.

Left unchanged deliberately: the settings key `content_provider` and helper `active_content_provider()`
(they name the runtime setting, not the engine role); `page_set_content` crud (page content, not a role).

## Verification

- `grep` for `ContentFetcher|register_content|get_content|content_codes` + `web_search.module_settings`
  + `web_search.normalize` in src+tests → none.
- `uv run pytest --module=web_search` → 40 passed; full `uv run pytest` → 312 passed (all three changes).
