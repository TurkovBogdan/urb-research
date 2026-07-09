# web_ingestion module — provider ENV tokens

- **Date:** 2026-06-29
- **Status:** completed
- **Area:** module / web_ingestion

## Request

Create a new module `web_ingestion` (responsibility: web search + site content fetching + standardization to markdown — the "raw data module" of the central research memory). Lay in ENV tokens for Tavily and Firecrawl, stored in `.env` and editable in the server settings page (`core_setup`).

## What was done

- New module `src/modules/web_ingestion/`:
  - `config.py` — `WebIngestionConfig(BaseSettings)` reading `TAVILY_API_KEY` / `FIRECRAWL_API_KEY` from `.env`.
  - `module.py` — `WebIngestionModule(Module)` (`name="web_ingestion"`, `config_cls=WebIngestionConfig`).
  - `__init__.py` — exports `WebIngestionModule`.
- Registered in `src/apps/app/modules.py` `build_modules()` (`[CoreSetupModule(), WebIngestionModule()]`).
- `core_setup/keys.py` — new group «Веб-источники» with two `secret` fields (`TAVILY_API_KEY`, `FIRECRAWL_API_KEY`) → appear on the settings page, write to `.env` + restart.
- `.env` — real tokens added (Tavily + Firecrawl). Placeholders added to `.env.example.dev` / `.env.example.prod`.
- Test `tests/modules/web_ingestion/test_config.py` (pure): config reads keys from env; module exposes `config_cls`.
- Docs hub `AGENTS/docs/web_ingestion/INDEX.md` + routing row in memory `MEMORY.md`.

## Result

Module loads with the app; tokens are env-backed (deploy-time Config) and editable in `core_setup`. No DB/router yet — raw-data tables + pipeline come later (design in `AGENTS/obsidian/general.canvas`).

## Notes / next

- Next layers (per `general.canvas`): `raw_response` (verbatim) → versioned `processor` → `document` (markdown), plus `source_ref` / `agent_result`.
- `.env.example.*` still carry stale `CORE_USERS_*` keys (removed module) — out of scope here.
