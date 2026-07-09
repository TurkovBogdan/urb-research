---
name: codes_bare_storage_prefix_boundary
description: Entity codes are stored as a bare 22-hex hash; the readable type prefix (RESEARCH@/SOURCE@/SEARCH@/…) is presentation-only, owned by the research module, added at the boundary, never in the DB.
metadata:
  type: project
---

A stored code (PK / FK / cross-module soft-ref) is a **bare 22-hex hash** (`random_hash()` /
`text_hash(url)`). The readable **type prefix is presentation only** — added at the agent/API
boundary, never persisted. Renaming a prefix or rescheming is a one-constant change: **no migration,
no data touch**. Wire form is **`type@hash`** (`@` separator — reads as a namespaced ref, never in a hash).

**Prefixing is research-only.** research is the *only* module with an MCP surface, so it **owns** the
codec + prefix words — its own entities *and* the web_search codes it references. **web_search stores
and returns bare codes** (no `prefixed`/`strip_prefix` in its models/api). So the codec lives in
`src/modules/research/codes.py` (moved out of core 2026-07-06); web_search can't import it (research→web_search
dep direction), which is exactly why web_search stays bare.

**Prefixes (full words, `@` sep):** research_index `RESEARCH@`, research_area `AREA@`, research_note
`NOTE@`, research_source_query `QUERY@`, research_source_document `SOURCE@`, and the referenced
web_search codes `SEARCH@` (query) / `PAGE@` (page) — all seven words defined in `research/constants.py`.

**Codec** `src/modules/research/codes.py`:
- `strip_prefix(value)` — `rpartition("@")[2]`; idempotent on a bare hash (hex has no `@`), safe on
  internal values too. Applied explicitly at **every** research MCP tool code param + research API path param.
- `prefixed(prefix)` → `Annotated[str, PlainSerializer(..., when_used="json")]`. Tags a code field's
  **JSON** form only, so a python-mode `model_dump()` round-trip stays bare → the model_dump-respread
  pattern (research_get / get_research) is safe. research output DTOs are shared by its MCP + API, so
  one annotation tags both surfaces.

CRUD stays pure (bare in, bare out); the old `*_CODE_PREFIX` concat is gone. Columns stay
`String(25)` (bare code = 22, slack harmless) → **no schema change**. `web_search_page` dedup key is
still deterministic (bare `text_hash(url)`).

Gotcha: mixing an API-returned (tagged) code with a direct CRUD call needs `strip_prefix` first
(e.g. tests). Related: [[dev_query_hits_postgres_not_sqlite]], [[project_src_pythonpath_shadow]].
