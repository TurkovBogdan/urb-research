# Markdown rendering pipeline

Client-side (Vue) rendering of markdown for chat/LLM content.

## CSS contract

Output is wrapped in `.md-body`; styling targets that scope. The `marked` renderer
overrides **only** `code`/`codespan` (→ `md-pre`/`md-code`/`md-codespan`); all other
block/inline elements fall through to marked's default renderer and carry **no class**.
So consumers style with a **mix** of tag selectors (within `.md-body`) and `md-*` class
selectors:

| Element | Client class (`MarkdownRenderer.vue`) | Style hook used in practice |
|---|---|---|
| `<h1>`–`<h6>` | *(none — default renderer)* | `:deep(h1)`…`:deep(h6)` |
| `<p>` | *(none)* | `:deep(p)` |
| `<ul>` / `<ol>` / `<li>` | *(none)* | `:deep(ul/ol/li)` |
| `<blockquote>` | *(none)* | `:deep(blockquote)` |
| `<pre>` | `md-pre` | `:deep(.md-pre)` |
| `<code>` (block) | `md-code` | `:deep(.md-code)` |
| `<code>` (inline) | `md-codespan` | `:deep(.md-codespan)` |
| `<strong>` / `<em>` / `<hr>` | *(none)* | `:deep(strong/em/hr)` |

> Don't rely on `md-h`/`md-p`/etc. existing — only `code`/`codespan` carry a class; target
> the rest by **tag** inside `.md-body`.

## `MarkdownRenderer.vue`

**Location:** `web/src/components/MarkdownRenderer.vue`

**Stack:** `marked` (custom `Renderer`) + `DOMPurify`.

```vue
<MarkdownRenderer :text="someMarkdown" :compact="true" />
```

Props:
- `text: string` — raw markdown source
- `compact?: boolean` — smaller font-size and tighter spacing

The `marked` renderer and DOMPurify config are module-level constants (not recreated per render). The `html` output is a `computed` so it only recalculates when `text` changes.

**Used in:** chat messages, design-system demo (`/design-system/markdown`).

## Design-system demo

Route `/design-system/markdown` (`MarkdownView.vue`):
- `compact` toggle
- Live editor: textarea ↔ rendered preview
- Full elements demo (all `md-*` classes)

## Adding a new consumer

1. Use `<MarkdownRenderer>`.
2. Wrap the output element in `.md-body`.
3. Add `:deep(.md-*)` styles (copy from an existing consumer or import from a shared CSS file if many consumers accumulate).
