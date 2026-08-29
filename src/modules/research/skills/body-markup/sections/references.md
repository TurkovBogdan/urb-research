# References: codes as links

Any entity code written into a body is turned into a link to that entity's page: a source, an
area, a note, a search, a research, a group alike. The link is labelled with the entity's own
**title**, not with the code, so the reader never sees the hash.

## Write it plain

```
The censor moved from blocking the protocol to knocking out AS prefixes SOURCE@1a2b…
```

That is the whole syntax. No backticks, no quotes, no brackets, no parentheses around it, no
markdown link wrapper. The code is recognised in running text and nowhere else.

**Where a code is NOT converted** — these all leave dead text on the page:

- inside backticks or a fenced code block (code spans are deliberately left alone);
- inside the label of a markdown link — `[SOURCE@…](…)` renders as literal text, because a link
  cannot nest inside a link.

## Write around the label, not around the code

The reader sees the title. So a sentence built around the code reads correctly only if it would
also read correctly with the title in that spot.

- Good: `Подробный разбор лимитов — AREA@…` → «Подробный разбор лимитов — Сколько инструментов…»
- Bad: `см. в AREA@… подробнее` → the title lands mid-sentence in the wrong case.

A dash before the code, or a code at the end of the sentence, almost always reads well. A code
in the middle of a grammatical construction almost always does not.

## Cite honestly

- Cite only sources you read with `source_get` and kept with `source_review`. A filtered source
  or one still `pending` is not evidence.
- Never invent a code. Codes come back from `query_search_run`, `sources_list`, and the
  create tools — nowhere else.
- Pass a code back exactly as you received it, prefix included.
- Cross-link siblings by code rather than by name: the link survives a rename, the name doesn't.

## Cost

A pill inside a table cell is capped and its label ellipsises, so a cell holding three citations
turns into three truncated chips. Cite in prose; keep tables for values.
