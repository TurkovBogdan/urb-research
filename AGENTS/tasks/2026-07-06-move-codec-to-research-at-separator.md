# codec → research module + `@` separator + web_search de-prefix

- **Date:** 2026-07-06
- **Status:** completed
- **Area:** research + web_search codes · core/utils

## Goal

Two coupled decisions taken while working through the research MCP surface:
1. **Separator `@`** — the readable wire form becomes `type@hash` (was `type_hash`), reading as a
   namespaced reference; `@` never occurs in a hex hash.
2. **Prefixing is research-only** — research is the *only* module with an MCP surface, so it owns the
   codec + prefix words. The codec moves **out of core** into the research module; **web_search stops
   prefixing entirely** (stores and returns bare codes).

Prompted by: "а откуда в ядре эта система префиксов? … она только для модуля ресёча".

## Why web_search must go bare

research depends on web_search (not vice versa). If the codec lives in research, web_search can't
import it → web_search returns bare codes, and research tags the `search_code` / `page_code` it
references itself (`SEARCH@` / `PAGE@`). Clean: the human web_search frontend doesn't need type-tags.

## What was done

### Codec
- `mv src/core/utils/codes.py → src/modules/research/codes.py`. Separator flipped `_`→`@`:
  `strip_prefix` = `rpartition("@")[2]` (idempotent on bare hex); `_tag` = `f"{prefix}@{value}"`.
  Docstrings updated; module docstring notes it's the research agent surface.
- `research/constants.py` now owns **all seven** prefix words incl. the referenced `SEARCH_CODE_PREFIX` /
  `PAGE_CODE_PREFIX` (bare words; codec adds `@`). `research/dto.py` imports `prefixed` from
  `research.codes` and the two web_search prefixes from `research.constants`.
- research imports of `strip_prefix` swapped `core.utils.codes` → `research.codes` (api.py + 4 mcp tools).

### web_search de-prefix
- Removed `prefixed`/`SearchCode`/`PageCode` from `models/{query,page,query_result}.py` → code fields
  are plain `str`. Removed `strip_prefix` from `api.py` (path params arrive bare). Dropped
  `SEARCH_CODE_PREFIX`/`PAGE_CODE_PREFIX` from `web_search/constants.py`. Docstrings/comments note
  "web_search коды не типизирует".

### Docstrings / records
- All wire examples `PREFIX_…` → `PREFIX@…` (mcp/__init__ instructions, mcp/research.py, crud + model
  comments). `wsm_001` migration docstring `WQ_<22 hex>` → bare. core `hashing.py` docstring no longer
  points at a module-specific codec.
- Tests: `test_api.py` (bare code asserts, dropped `strip_prefix` import), `test_crud.py` docstring.
- Memory `codes_bare_storage_prefix_boundary.md` + MEMORY.md router line; `docs/web_search/INDEX.md`;
  canvas `research-tables.canvas` (badges/legend/edges → `@`, research-owned note).

## Verification

`--core --module=web_search` → **323 passed**. Codec smoke: `strip_prefix("RESEARCH@abc")=abc`, bare→bare;
DTO json tags `RESEARCH@…`/`SOURCE@…`/`PAGE@…`/`QUERY@…`, python-mode `model_dump()` stays bare. No
`core.utils.codes` / wire-`_` refs left in `src/`. Canvas JSON valid.

## Notes / deferred

- research has **no test suite yet** (draft surface, not in `build_modules` / test area map) — codec
  covered only via import smoke + DTO round-trip, not module tests.
- Still open (the step this detoured from): rewrite `research_list` / `research_create` / `research_get`
  per the new spec (list sorted by `updated_at`, create returns code only, get = fields + notes[] +
  areas[]). Deferred earlier: `String(25)`→22, frontend research views, web/dist.
