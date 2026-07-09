# codes: prefixes out of storage → presentation-only word tags

- **Date:** 2026-07-06
- **Status:** completed (code) · dev rebuild pending (gated)
- **Area:** web_search + research — code prefix scheme

## Outcome (superseded the 3-letter plan)

The 2→3-letter debate resolved into a better design: **a stored code is a bare 22-hex hash;
the type prefix is presentation only, added at the boundary, never in the database.** This kills
the column-width / migration problem entirely (schema unchanged) and makes any future prefix rename
free (edit one constant, no migration, no data touch). Prefixes became full readable words (zero
decode): the winning form the user picked.

## Prefix map (presentation words)

| Entity | Prefix |
|---|---|
| research_index | `RESEARCH_` |
| research_area | `AREA_` |
| research_note | `NOTE_` |
| research_source_query | `QUERY_` |
| research_source_document | `SOURCE_` |
| web_search_query | `SEARCH_` |
| web_search_page | `PAGE_` |

Domain reads from the word itself (SEARCH_/PAGE_ = web; the rest = research); QUERY_ (research
link) vs SEARCH_ (web run) are distinct words.

## Design — bare inside, tagged at the edge

- **Codec** `src/core/utils/codes.py`: `strip_prefix(value)` (rpartition on last `_`; idempotent on
  a bare hash — hex has no `_`) + `prefixed(prefix)` → an `Annotated[str, PlainSerializer(...,
  when_used="json")]` type that tags a code field's JSON form (a `model_dump()` python round-trip
  stays bare, so the model_dump-respread pattern in tools/api is safe).
- **Prefix constants**: presentation prefixes live in each module's `constants.py`
  (`RESEARCH_/AREA_/NOTE_/SOURCE_QUERY_(QUERY_)/SOURCE_DOCUMENT_(SOURCE_)`; web `SEARCH_/PAGE_`).
- **CRUD** generates **bare** codes (`random_hash()` / `text_hash(url)`; the old `*_CODE_PREFIX`
  concat is gone) and stays pure (bare in, bare out).
- **Output tagging (DTO)**: code fields annotated with the `prefixed(...)` types. The SAME DTOs
  feed both MCP tools and the HTTP API, so tagging both surfaces is one change per field.
- **Input untag (boundary)**: explicit `strip_prefix(...)` at every MCP tool code param and every
  API path param (deterministic — no framework-magic dependency).
- **Schema unchanged**: columns stay `String(25)` (bare code = 22, slack is harmless); **no
  migration**. Width tightening to 22 deferred as trivial.

## Verification

- End-to-end via fastmcp in-memory Client: `research_start` → tagged `RESEARCH_…`; passing the
  tagged code back into `research_get` resolves (input untag); `area_add` → `AREA_…`; nested
  area code inside `ResearchDetail` also tagged (model_dump-respread path).
- FastAPI path confirmed by tests (body code = `SEARCH_…`); bare code in a path still resolves
  (strip idempotent).
- `--core` + `--module=web_search` = 323 passed; `vue-tsc` 0 (frontend treats codes as opaque —
  no prefix literals in `web/`); app builds; `migrate check` up to date (no drift).
- Updated: model/crud/hashing docstrings, MCP server instructions (codes with new prefixes),
  bench fake code, canvas (badges + code lines + legend + edge labels).

## Pending (gated — needs explicit go)

Dev rebuild to clear old prefixed rows: stop backend → delete only research + web_search rows
(FK order) → keep `com_*` core tables (connector settings) → restart. Old dev rows carry old
prefixed codes and would double-tag on read; new data is bare + tagged correctly.

## Result

Prefixes are a presentation layer; the DB stores bare hashes. Renaming/rescheme is now a
one-constant change. Deferred: `String(25)`→22 tightening, frontend research views, web/dist.
