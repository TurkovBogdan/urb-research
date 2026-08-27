---
title: Research — markdown rendering engine for the frontend
date: 2026-08-26
status: completed
description: "Run a research through the urb-research-stable MCP on markdown rendering engines: ready-made libraries vs a custom solution, with an eye on high-quality output and customisation."
tags: [research, frontend, markdown]
---

## Task

«Через urb-research-stable запусти исследование на следующую тему: Код: мне нужна машинка рендера markdown текста, возможно кастомизированная. Или своё решение для качественного рендера, тут не уверен. Нужен ресёч какие есть решения».

## Context

The topic was given without a target platform, so it was grounded on the project's own frontend (that is where markdown rendering actually lives): Vue 3.5 + Vuetify 4 + Vite + TS, today marked v18 + DOMPurify + shiki with renderer overrides and a home-grown `TYPE@hash` reference pill implemented as a regex post-pass over the rendered string. No prior research covered markdown rendering; the closest neighbour is the typography research RESEARCH@2a0d3e1d7e626c8bc4baf0.

## What was done

- Read the current renderer baseline from the code (`web/package.json`, `web/src/components/MarkdownRenderer.vue`) and recorded it as a `memory` note in the research.
- Created RESEARCH@8913d13581d04a807ff59f with six areas: parser landscape, customisation & rendering into Vue components, security/sanitisation, output quality (highlighting/GFM/math/diagrams), performance & streaming, and when a custom solution is justified.
- Ran one web search per area (6 runs, 43 sources), reviewed **all** sources (35 kept / 8 filtered) with relevance ratings and notes.
- Wrote the synthesis: a body for each of the six areas plus the research body (recommendation + cheap wins that hold regardless of the engine choice).
- Added notes: baseline snapshot, two `result` notes (split parser vs render layer; marked's raw-HTML default), one `memory` note on the methodological limitation of this run.
- Follow-up on request («поищи неявные, непопсовые решения»): a seventh area on non-mainstream solutions — djot, Markdoc, MDC, micro streaming parsers (smd/Semidown), wasm parsers, Expressive Code / rehype-pretty-code / shiki-magic-move, md-block — 3 more searches, 25 sources reviewed (22 kept / 3 filtered), each finding tagged applicable / idea-only / not for us. Added an `idea` note on schema-validated custom constructs and a «неочевидные находки» section to the research body.

- Second follow-up: verified the research claims against the actual code and audited the markup census of RESEARCH@7a9d3845b310fa4fb184d5 (how the agent really writes tables). Corrected one wrong claim in the record (the `TYPE@hash` pill is a real marked inline extension, not a regex post-pass — only the label swap is a `DOMParser` post-pass) across the research body, the customisation area and the Markdoc idea note; rewrote the baseline note from the code.
- Found a live defect and recorded it as NOTE@e65dd17c5b9ee8854e7bae: `MarkdownRenderer.vue`'s DOMPurify allowlist has no `table`/`thead`/`tbody`/`tr`/`th`/`td` (nor `del`), so every GFM table in a body collapses into run-on text; there are no table CSS rules either. Also: shiki is imported from the `shiki` root (full bundle — ~460 lazy language chunks in `web/dist/assets`) with a single `github-dark` theme, and it is **not** wired into the markdown renderer at all — body code blocks are unhighlighted.
- Markup census recorded as NOTE@20af94caad74bac5ca7144: 23 pipe tables (up to 12 columns, rows up to 318 chars, zero colon alignment), zero HTML tags, emoji as status columns, 66 inline `SOURCE@` refs.

No code was changed — this was a research task only.

## Problems

`query_search_run` returned every source with an empty body (`source_get` → `body: null`): the search engine worked, the content fetch stored nothing. Compensated by reading the key pages directly; github.com refused connections and npmjs.com / markstream returned 403, so those sources are used from the search-engine annotations only (flagged in NOTE@53d4943acc8d8a8af3b9a2). Worth checking the `fetch_engine` setting and the scraper daemon on the stable instance.

## Result

Research RESEARCH@8913d13581d04a807ff59f in the stable registry:

- 6 areas, all with written bodies;
- 43 sources, all reviewed (35 kept, 8 filtered);
- 4 notes (baseline, 2 results, 1 methodological memory);
- recommendation: keep a third-party parser, switch marked → markdown-it (`html:false` by default, real parser extension points), write the render layer ourselves as a tokens → VNode visitor instead of `v-html`, keep DOMPurify as the last line, keep shiki but fine-grained; never write a markdown parser of our own.

No repository files were changed other than this task record.
