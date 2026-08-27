---
title: Markdown renderer — migrate marked → markdown-it
date: 2026-08-27
status: completed
description: "Replace marked with markdown-it in the frontend markdown pipeline, staged and verified: parity for every existing customisation, tables that actually render, raw HTML off at the parser."
tags: [frontend, markdown, renderer]
---

## Task

«Делай, осторожно и поэтапно, меняй реализацию на markdown-it» — implement the recommendation
of RESEARCH@8913d13581d04a807ff59f.

## Context

The renderer was marked v18 + DOMPurify + `v-html`, with renderer overrides for
code/codespan/link/image and a real inline extension for `TYPE@hash` pills. Two problems the
research surfaced: raw HTML is **on** by default in marked while our bodies come from an LLM
and from scraped pages, and the DOMPurify allowlist had no table tags at all, so every GFM
table (23 of them in the ComfyUI research alone) collapsed into run-on text.

## What was done

Staged, with a typecheck after each stage.

1. **Dependency.** `markdown-it@15.0.0` added; it ships its own types, so `@types/markdown-it`
   was installed and immediately removed. `marked@18` removed at the end.
2. **Parity rewrite** of the pipeline on markdown-it: `html: false`, `linkify` with
   `fuzzyLink: false` (bare `app.py` / `README.md` must not link — `.py`/`.md` are TLDs), core
   rule `entity_refs` (splits text tokens on `TYPE@hash`, skips code spans and link labels),
   core rule `task_list_checkboxes` (markdown-it has none), renderer rules for
   fence/code_block/code_inline, link_open (external → `target`/`rel`), image (loupe wrapper),
   table_open/table_close (scroll wrapper), th_open/td_open (alignment `style` → class).
3. **Tables fixed**: `div table thead tbody tr th td` and `s` added to the allowlist, plus the
   table CSS that never existed (bordered box, sticky header, zebra rows, `width: max-content`
   inside a scrolling wrapper, alignment classes).
4. **Split into two files**: `web/src/components/markdown/render.ts` (markdown → sanitised
   HTML, framework-free, testable outside the browser) and `MarkdownRenderer.vue` (labels,
   clicks, CSS). The sanitiser moved into `render.ts` so the whole pipeline is one contract.
5. **Verification** (no frontend test runner in the repo, so a throwaway harness): the module
   was bundled with the local esbuild and run under node with jsdom for DOMPurify. Checked:
   table survives sanitising with alignment classes; `<script>` / `<iframe srcdoc>` payloads
   escaped by the parser; `javascript:` / `data:` / `vbscript:` / mixed-case variants produce
   **no anchor at all** (markdown-it's link validation); entity pill href/label; pill left
   alone inside a code span and inside a link label; malformed codes not matched; task-list
   checkboxes (checked/unchecked); strikethrough; images off by default and on demand with the
   loupe wrapper; external vs internal link attributes; `breaks`. Real 44 KB research body:
   23 tables, 121 `th`, 965 `td`, 66 pills, 33 headings, parse 16 ms (parse + sanitise under
   jsdom 113 ms). jsdom removed afterwards.
6. **Design-system demo** extended with a table (incl. alignment), a task list, strikethrough,
   an external link and escaped raw HTML; the stale claim that links are stripped is gone.
7. **Docs** `AGENTS/docs/frontend/markdown-rendering.md` rewritten for the new pipeline
   (parser options and why, the rule table, the allowlist as a security contract, known gaps).
8. **Language resolution in the highlighter** (`useHighlighter.ts`): the hardcoded list of 13
   languages narrowed everything *before* shiki saw it, so ` ```js `, ` ```sh `, ` ```py `,
   ` ```yml ` and ` ```JSON ` all fell back to plain text. Now the fence language is trimmed,
   lower-cased and looked up in shiki's own `bundledLanguages` (aliases included), grammars
   load on demand (one in-flight promise per language) instead of thirteen up front, and an
   unknown id still degrades to `text`. Verified in node (js/sh/py/yml/`  TypeScript  `/rust
   all tokenise; `питон`, `text`, empty → plain) and in the browser: the design-system page
   fetches five language chunks (python, json, typescript, sql, shellscript) instead of
   thirteen, all 8 demo blocks highlight, console clean.
9. **Body code blocks became components.** A fence is no longer rendered as HTML: the parser
   returns `{ html, codeBlocks }` and leaves a `.md-code-slot[data-code-index]`, into which
   `MarkdownRenderer` mounts `CodeBlock` with Vue's standalone `render()` (the vnode carries
   the component's `appContext`; slots are unmounted before `v-html` swaps the container and
   on unmount). Bodies therefore get syntax highlighting, a language badge, a line-number
   toggle and copy — the same component the design-system and the MCP panel use.
10. **New `compact` variant of `CodeBlock`** for one-liners: no header, tight padding, copy
    button fading in over the right edge on hover. The renderer picks it automatically when
    the code has a single line (`icon` otherwise). Added to the design-system demo.
11. `web/dist` rebuilt.

## Problems

- markdown-it 15 exports the instance type as a named `MarkdownIt` while the default export is
  the callable class — `import type { MarkdownIt as MarkdownParser }` alongside the value
  import.
- The first harness run reported a false failure on `javascript:` URLs: the assertion searched
  the whole HTML, and the *literal text* of the rejected link contains the scheme. Re-checked
  by extracting `href` attributes — zero anchors produced.
- The live browser pass (on the dev instance, `:22040`, against a purpose-built fixture —
  RESEARCH@ef8a7d2f258de68b188bda in the dev DB, «Test: полный набор markdown-разметки»)
  found four things the node harness could not:
  1. **Column alignment did nothing** — `.md-align-right` (0-2-0) lost to `.md-table td`
     (0-2-1), which sets `text-align: left`. Fixed by scoping the classes to the cell.
  2. **A prose-heavy table stretched to 2186 px** and scrolled horizontally, because the
     table is sized by `max-content`. Fixed with `max-width: 60ch` on cells: the prose table
     now fits 894 px and wraps, the 12-column table still scrolls (1211 px).
  3. **Code blocks read as a stack of blue plates** — the app's global `code` rule paints an
     inline-code chip, and inside `<pre>` it repeats per line box. Pre-existing (marked
     produced the same markup); fixed by resetting background/border/padding on `.md-code`.
  4. **Task items kept their bullet** next to the checkbox. The core rule now marks the `<li>`
     `md-task`; CSS drops the marker and hangs wrapped lines under the text.
- A sticky table header was written and then removed: `overflow-x: auto` makes the wrapper a
  scroll container, so `position: sticky; top: 0` inside it never sticks to the viewport.

## Result

Changed:
- `web/src/components/markdown/render.ts` — **new**, the whole parse + sanitise pipeline
- `web/src/composables/useHighlighter.ts` — alias-aware language resolution, on-demand grammars
- `web/src/components/MarkdownRenderer.vue` — parser code removed, sanitising delegated, table
  and `s` CSS added, stale marked references gone
- `web/src/views/design-system/content/MarkdownView.vue` — richer sample
- `web/package.json`, `web/pnpm-lock.yaml` — `marked` out, `markdown-it` in
- `AGENTS/docs/frontend/markdown-rendering.md` — rewritten
- `web/dist/**` — rebuilt

Bundle: the lazily-loaded `MarkdownRenderer` chunk went 44.0 KiB raw / 13.8 KiB gz →
119.4 KiB raw / 50.1 KiB gz (+36 KiB gzip); the main `index` chunk is unchanged at 264.6 KB gz.

The browser pass ran against the fixture research RESEARCH@ef8a7d2f258de68b188bda (dev DB
only — created through the dev MCP because the stable instance still serves the old build).
Verified in the DOM: zero `script` / `iframe` / `svg` / `style` elements inside `.md-body`,
zero dangerous hrefs, 5 tables with wrappers, alignment classes applied, 6 reference pills with
resolved titles (unresolved one falls back to the short hash), 4 task checkboxes (2 checked),
no page-level horizontal overflow.

Body code blocks verified in the browser on the fixture: 11 slots → 11 mounted components, 4 of
them compact (including a one-liner nested in a list and one in a blockquote), 7 highlighted,
badges python / ts / bash / json / text / text / mermaid, no leftover `pre.md-pre`, console
clean. A last browser find: code inside an italic blockquote inherited the italics — reset.

Follow-ups: dual theme via CSS variables + `shiki/core` fine-grained bundle; fence metadata
(`title=`, `{1,3}`) is still dropped; no JS test runner exists, so the harness checks live only
in this record; the fixture is not in the stable DB. Unrelated pre-existing warning seen while
building: `SkeletonView.vue` uses SASS-style `&--modifier` nesting in a plain CSS block, so
those modifier rules never apply.
