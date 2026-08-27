# Markdown rendering pipeline

Client-side rendering of markdown bodies: research / area / note bodies written by the agent,
scraped page bodies, settings-field descriptions.

## Two files, two jobs

| File | Job |
|---|---|
| `web/src/components/markdown/render.ts` | markdown → **sanitised** HTML: markdown-it parser + project rules + DOMPurify |
| `web/src/components/MarkdownRenderer.vue` | the view: reference labels, click handling (router / lightbox), all CSS |

`renderMarkdown(text, { breaks, allowImages })` is the whole contract of the first file: it
returns `{ html, codeBlocks }`. It is pure and framework-free — it can be exercised outside the
browser (bundle it with esbuild and run it in node; DOMPurify needs a DOM, so give it jsdom).

## Code blocks are components, not HTML

A fenced block never becomes `<pre>` in the sanitised string. The parser pushes `{ code,
language }` into `env.codeBlocks` and emits an empty `.md-code-slot[data-code-index]`;
`MarkdownRenderer` then mounts a `CodeBlock` into each slot with Vue's standalone `render()`
(the vnode is given the component's `appContext`, so globally registered components inside
`CodeBlock` still resolve). Slots are unmounted before `v-html` replaces the container and on
component unmount — otherwise those instances would leak.

Which variant a block gets is decided by its shape:

- **one line → `compact`**: no header, tight padding, copy button fading in over the right
  edge on hover — a command reads as a chip, not as a panel;
- **more than one line → `icon`**: language badge, line-number toggle, copy button.

This is what wires body code blocks to shiki: highlighting comes from `CodeBlock`, so a body,
the design-system demo and the MCP panel all render code the same way.

## Parser

**markdown-it 15**, one instance per `breaks` value (at most two, cached in a module map —
`breaks` is an instance option, so a shared instance would flip under a sibling renderer).

Options that matter:

- `html: false` — bodies come from an LLM and from scraped pages; raw HTML never reaches the
  sanitiser in the first place. **Do not turn this on.**
- `linkify: true` with `fuzzyLink: false` / `fuzzyEmail: false` — only schema'd URLs autolink.
  Bare `app.py` / `README.md` must not become links (`.py` and `.md` are real TLDs). The cost
  is that a scheme-less `www.example.com` no longer autolinks — write it as a markdown link.
- GFM tables, strikethrough (`<s>`) and autolinks are built in; there is no `typographer`.

### Project rules on top

| Rule | What it does |
|---|---|
| `entity_refs` (core) | splits plain-text tokens on `TYPE@<22-hex>` and emits an `entity_ref` token → a `.md-ref` pill linking to the entity page. Skipped inside code spans/fences (separate token types) and inside link labels (`<a>` cannot nest). |
| `task_list_checkboxes` (core) | markdown-it has no task-list rule: a leading `[ ]` / `[x]` in a list item's first paragraph becomes a disabled `<input type="checkbox">`. |
| `fence` / `code_block` | **not rendered as HTML**: the code goes back to the caller in `env.codeBlocks` and its place is held by `<div class="md-code-slot" data-code-index="N">`, where the view mounts the real `CodeBlock` component. |
| `code_inline` | `md-codespan` class on the inline chip. |
| `link_open` | external links get `target="_blank" rel="noopener noreferrer"`; internal (`/…`) are left for the router. |
| `image` | wrapped in `<span class="md-img">` so the hover loupe has an anchor. |
| `table_open` / `table_close` | wrapped in `<div class="md-table-wrap">` — a wide table scrolls in its own box instead of stretching the page column. |
| `th_open` / `td_open` | column alignment arrives as an inline `style`; it is converted to `md-align-left/center/right` so `style` stays out of the allowlist. |

A task item also gets `class="md-task"` on its `<li>` so the CSS can drop the bullet — the
checkbox is the marker.

## Sanitiser

DOMPurify runs as the **closing** step, never before parsing. The allowlist names attributes,
not just tags:

```
tags:  h1..h6 p ul ol li blockquote pre code hr strong em s a br input
       div table thead tbody tr th td            (+ img span when allowImages)
attrs: class href target rel type checked disabled title data-code-index
                                                  (+ src alt when allowImages)
```

Anything outside the list is dropped: `iframe`, `style`, `on*` handlers, `svg`/`math`.
Dangerous URL schemes never even reach it — markdown-it's own link validation rejects
`javascript:`, `data:`, `vbscript:` and the link stays plain text.

> Adding a tag to the allowlist is a security decision, not a styling one. Prefer emitting a
> class from a renderer rule over widening the attribute list.

## CSS contract

Output is wrapped in `.md-body`; all styling lives in `MarkdownRenderer.vue` and targets a mix
of tag selectors and `md-*` classes. Elements that carry a class: `md-codespan`, `md-ref`,
`md-img`, `md-table-wrap`, `md-table`, `md-align-*`, `md-task`, `md-code-slot`. Everything
else (headings, paragraphs, lists, blockquote, `s`, `hr`, `a`) is styled by tag inside
`.md-body`.

These rules exist because a browser pass caught them, and they break if simplified:

- **Alignment classes must name the cell** (`.md-table .md-align-right`): the plain
  `.md-align-right` loses to the `.md-table td` rule that sets `text-align: left`.
- **Cells are capped at `max-width: 60ch`**: the table is sized by `max-content`, so one
  prose-heavy cell would otherwise claim its full one-line width and a two-column table would
  scroll like a wide one.
- **Code inside a blockquote is reset to `font-style: normal`**: the quote is italic, and an
  italic monospace block reads as a mistake.

## Component

```vue
<MarkdownRenderer :text="body" :ref-labels="labels" compact />
```

Props: `text`, `compact` (smaller type, tighter spacing), `breaks` (single newline → `<br>`,
for plain-text bodies), `allowImages` (off by default), `refLabels` (`TYPE@hash` → entity
title; the pill then shows the truncated title instead of the short hash). Emits `imageClick`
for the lightbox. `html` is a `computed`, so a re-render costs nothing while `text` is stable.

`ResearchBody.vue` is the research-side wrapper: it extracts codes from the text, asks the
references store for titles and passes them as `refLabels`.

## Syntax highlighting

`web/src/composables/useHighlighter.ts` owns the single shiki instance:

- the fence language is **normalised** (trimmed, lower-cased) and looked up in shiki's own
  `bundledLanguages`, so aliases work out of the box — `js`, `sh`, `py`, `yml`, `JSON`;
- an unknown id (`питон`, an empty fence) degrades to `text` — shiki has **no**
  auto-detection, and an unregistered id throws instead of rendering;
- grammars load **on demand** (`loadLanguage`, one in-flight promise per language) rather than
  a fixed list up front: the design-system page now fetches five language chunks instead of
  thirteen.

Do not reintroduce a local list of supported languages — it can only narrow what shiki
already knows.

## Known gaps

- **One theme** (`github-dark`) and the full-bundle `shiki` entry. A dual theme via CSS
  variables and a `shiki/core` fine-grained bundle are the remaining steps.
- Fence metadata beyond the language (`title="app.py"`, `{1,3}`) is parsed and dropped.
- No footnotes, no `[!NOTE]` alerts, no math — the agent does not write them today.

## Design-system demo

Route `/design-system/markdown` (`MarkdownView.vue`): a `compact` toggle, a live textarea ↔
preview editor, and a full-elements sample (headings, lists, table with alignment, code,
quote, task list, strikethrough, external link, escaped raw HTML). `CodeBlock`'s own variants —
including `compact` — live at `/design-system/code-block`.
