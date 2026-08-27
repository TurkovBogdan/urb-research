---
title: Research — universal readable fonts with Cyrillic support
date: 2026-08-26
status: completed
description: "Run a research through the urb-research-stable MCP: pick an open-source (or free-for-non-commercial) typeface / font set optimised for easy reading, with strong Cyrillic coverage and universal applicability (UI, long-form, code)."
tags: [research, design, typography]
---

## Task

«Через urb-research-stable запусти исследование на следующую тему: Дизайн: универсальные шрифты для лёгкого чтения текста. Особый упор в универсальность с поддержкой кириллицы. Нужен качественный open-source или разрешённый для некоммерческого использования шрифт или набор шрифтов.»

## Context

The research registry (`research` module) is used as the working surface: research → areas → source-queries → reviewed sources → synthesis. This run is a content task, not a code change — no `src/` edits.

## What was done

- Created `RESEARCH@1b464e08943f77787fbc11` and split it into six areas: readability criteria, Cyrillic quality, sans candidates, serif/mono candidates, licensing, and (on a follow-up request) non-obvious picks.
- Ran 13 source-queries, reviewed all 79 sources (kept / filtered with a reason each), wrote a synthesis body per area plus the top-level recommendation.
- Follow-up request «поищи неявные, непопсовые интересные решения» — added the sixth area and a section in the research body.

## Problems

- Every source came back with `body = null` while its status stayed `pending` (never `fetch_error`), so page-level evidence was the search engine's `summary` field; key pages were re-fetched out-of-band with WebFetch. Logged as `NOTE@7e76dbbbe5c7176596b988` — an empty fetch arguably ought to be surfaced as `fetch_error`.
- `type.today` does not resolve from this host, so the expert Cyrillic reviews (the backbone of the verdicts) were used via summaries only. Logged in `NOTE@d1ad1d46e99bf0e7fe10f2`.

## Result

`RESEARCH@1b464e08943f77787fbc11` in urb-research-stable — 6 areas, 13 queries, 79 reviewed sources, 5 notes.

Substantive findings: no typeface is measurably "most readable" and dyslexia-specific fonts show no benefit (`NOTE@9a8efe6f9e778360936d08`); the recommendation is a role-based OFL set (Golos Text/UI + Literata + JetBrains Mono, or IBM Plex, or the PT family). Verified against `google/fonts` `METADATA.pb` that **Atkinson Hyperlegible Next/Mono, Luciole and B612 carry no Cyrillic** — SIL Andika is the substitute (`NOTE@44d04c7f005e4b6e73f873`); the metadata-check method is recorded in `NOTE@2c6d90b1e906a5d73a7471`.

No files in `src/` or `web/` were touched.
