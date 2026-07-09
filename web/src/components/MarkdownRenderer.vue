<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const router = useRouter()

const props = defineProps<{
  text: string
  compact?: boolean
  // Render Markdown images as <img> (off by default: the agent chat strips them).
  allowImages?: boolean
  // Treat single newlines as <br> — preserves line breaks of plain-text email bodies.
  breaks?: boolean
  // Map `TYPE@hash` → entity title. When a reference pill's code resolves here, the pill
  // shows the (truncated) title instead of the short hash.
  refLabels?: Record<string, string>
}>()

const REF_LABEL_MAX = 48

const emit = defineEmits<{ imageClick: [src: string] }>()

function escapeAttr(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

// Only override elements without inline children — block elements with nested
// content (list, listitem, heading, paragraph, blockquote, strong, em) require
// this.parser.parseInline() in marked v18 and must be left to the default renderer.
// Style them via tag selectors in CSS. Images are wrapped in a positioned <span> so
// the hover loupe affordance has an anchor (an <img> can't carry ::after).
marked.use({
  renderer: {
    code({ text, lang }) {
      const cls = lang ? ` language-${lang}` : ''
      return `<pre class="md-pre"><code class="md-code${cls}">${text}</code></pre>\n`
    },
    codespan({ text }) {
      return `<code class="md-codespan">${text}</code>`
    },
    // External links open in a new tab so they never navigate the SPA away (e.g. a
    // settings token link would otherwise discard unsaved input). Internal links
    // (href starting with `/`) stay in-app — the router intercepts them in onClick.
    link({ href, title, tokens }) {
      const text = this.parser.parseInline(tokens)
      const titleAttr = title ? ` title="${escapeAttr(title)}"` : ''
      const isExternal = !!href && !href.startsWith('/')
      const externalAttrs = isExternal ? ' target="_blank" rel="noopener noreferrer"' : ''
      return `<a href="${escapeAttr(href ?? '')}"${titleAttr}${externalAttrs}>${text}</a>`
    },
    image({ href, title, text }) {
      const titleAttr = title ? ` title="${escapeAttr(title)}"` : ''
      return `<span class="md-img"><img src="${escapeAttr(href ?? '')}" alt="${escapeAttr(text ?? '')}"${titleAttr}></span>`
    },
  },
})

// Research entity cross-references: a `TYPE@<22-hex>` token in a body (RESEARCH / AREA /
// NOTE / QUERY / SOURCE) becomes a link to that entity's page. Codes are exactly 22 hex
// chars (research.codes / hashing._HASH_LEN); the negative lookahead rejects a longer hex
// run. The tokenizer runs during inline parsing, so a code inside a `code span` is untouched.
const REF_ROUTE: Record<string, string> = {
  RESEARCH: 'researches',
  AREA: 'areas',
  NOTE: 'notes',
  QUERY: 'queries',
  SOURCE: 'sources',
}
const REF_TYPES = Object.keys(REF_ROUTE).join('|')
const REF_HEAD = new RegExp(`(?:${REF_TYPES})@`)
const REF_TOKEN = new RegExp(`^(${REF_TYPES})@([0-9a-f]{22})(?![0-9a-f])`)
marked.use({
  extensions: [
    {
      name: 'entityRef',
      level: 'inline',
      start(src: string) {
        const m = REF_HEAD.exec(src)
        return m ? m.index : undefined
      },
      tokenizer(src: string) {
        const match = REF_TOKEN.exec(src)
        if (!match) return undefined
        return { type: 'entityRef', raw: match[0], refType: match[1], hash: match[2] }
      },
      renderer(token) {
        const t = token as unknown as { refType: string; hash: string }
        const code = `${t.refType}@${t.hash}`
        // The 22-hex hash is opaque in prose — show a short prefix as the transient label,
        // keep the full code in href (navigation) + title (tooltip); a resolved title replaces it.
        return `<a class="md-ref" href="/research/${REF_ROUTE[t.refType]}/${code}" title="${code}">${t.hash.slice(0, 6)}</a>`
      },
    },
  ],
})

const ALLOWED_TAGS = [
  'h1','h2','h3','h4','h5','h6',
  'p','ul','ol','li','blockquote','pre','code','hr',
  'strong','em','a','br','input',
]
const ALLOWED_ATTR = ['class','href','target','rel','type','checked','disabled','title']

// Swap each reference pill's label from the short hash to the resolved entity title
// (truncated). Runs on the already-sanitized HTML; textContent/setAttribute escape, so no
// re-sanitize is needed. The href/code stay untouched. Key = `TYPE@hash` (last href segment).
function withRefLabels(sanitized: string): string {
  const labels = props.refLabels
  if (!labels || typeof window === 'undefined') return sanitized
  const doc = new DOMParser().parseFromString(sanitized, 'text/html')
  let changed = false
  doc.querySelectorAll('a.md-ref').forEach((a) => {
    const code = (a.getAttribute('href') ?? '').split('/').pop() ?? ''
    const title = labels[code]
    if (!title) return
    a.textContent = title.length > REF_LABEL_MAX ? title.slice(0, REF_LABEL_MAX) + '…' : title
    a.setAttribute('title', title)
    changed = true
  })
  return changed ? doc.body.innerHTML : sanitized
}

const html = computed(() => {
  const tags = props.allowImages ? [...ALLOWED_TAGS, 'img', 'span'] : ALLOWED_TAGS
  const attr = props.allowImages ? [...ALLOWED_ATTR, 'src', 'alt', 'title'] : ALLOWED_ATTR
  const rendered = marked(props.text, { breaks: props.breaks ?? false }) as string
  const clean = DOMPurify.sanitize(rendered, { ALLOWED_TAGS: tags, ALLOWED_ATTR: attr })
  return withRefLabels(clean)
})

function onClick(event: MouseEvent) {
  const anchor = (event.target as HTMLElement).closest('a')
  if (anchor) {
    const href = anchor.getAttribute('href') ?? ''
    // Internal links (source citations et al.) navigate via the router — no full reload.
    // Modifier-click falls through to the browser so open-in-new-tab keeps working.
    if (href.startsWith('/') && !event.metaKey && !event.ctrlKey && !event.shiftKey) {
      event.preventDefault()
      router.push(href)
    }
    return
  }
  if (!props.allowImages) return
  const image = (event.target as HTMLElement).closest('img')
  if (image) emit('imageClick', (image as HTMLImageElement).currentSrc || image.getAttribute('src') || '')
}
</script>

<template>
  <div class="md-body" :class="{ 'md-body--compact': compact }" v-html="html" @click="onClick" />
</template>

<style scoped>
.md-body {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text);
  /* Reset inherited white-space (chat bubbles set pre-wrap for plain-text bodies): marked
     emits literal newlines between block tags, which under pre-wrap render as phantom empty
     lines (bottom gap after a lone paragraph, huge gaps inside blockquotes). Intentional
     line breaks come from the `breaks` option as real <br>, unaffected by this. */
  white-space: normal;
}

/* ── Headings ─────────────────────────────────────────────── */

.md-body :deep(h1),
.md-body :deep(h2),
.md-body :deep(h3),
.md-body :deep(h4),
.md-body :deep(h5),
.md-body :deep(h6) {
  font-weight: 600;
  color: var(--text);
  line-height: 1.3;
  margin: 1.1em 0 0.4em;
}
.md-body :deep(h1) { font-size: 20px; }
.md-body :deep(h2) { font-size: 17px; }
.md-body :deep(h3) { font-size: 15px; }
.md-body :deep(h4),
.md-body :deep(h5),
.md-body :deep(h6) { font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }

/* ── Paragraph ────────────────────────────────────────────── */

.md-body :deep(p) {
  margin: 0 0 0.75em;
}
.md-body :deep(p:last-child) {
  margin-bottom: 0;
}

/* ── Lists ────────────────────────────────────────────────── */

.md-body :deep(ul),
.md-body :deep(ol) {
  margin: 0.4em 0 0.75em;
  padding-left: 20px;
}
.md-body :deep(ul:last-child),
.md-body :deep(ol:last-child) {
  margin-bottom: 0;
}
.md-body :deep(ul) { list-style: disc; }
.md-body :deep(ol) { list-style: decimal; }

.md-body :deep(li) {
  margin: 0.2em 0;
  line-height: 1.6;
}

/* Nested lists */
.md-body :deep(li > ul),
.md-body :deep(li > ol) {
  margin: 0.2em 0;
}

/* Task list */
.md-body :deep(li input[type="checkbox"]) {
  margin-right: 6px;
  cursor: default;
  accent-color: rgb(var(--v-theme-primary));
}

/* ── Blockquote ───────────────────────────────────────────── */

.md-body :deep(blockquote) {
  border-left: 3px solid var(--border);
  margin: 0.6em 0;
  padding: 0.3em 0 0.3em 14px;
  color: var(--text-muted);
  font-style: italic;
}

/* ── Code ─────────────────────────────────────────────────── */

.md-body :deep(.md-pre) {
  background: var(--surface-hi);
  border: 1px solid var(--border-soft);
  border-radius: 6px;
  padding: 12px 14px;
  overflow-x: auto;
  margin: 0.6em 0;
}
.md-body :deep(.md-code) {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text);
}
.md-body :deep(.md-codespan) {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text);
  background: var(--surface-hi);
  border: 1px solid var(--border-soft);
  border-radius: 3px;
  padding: 1px 5px;
}

/* ── Misc ─────────────────────────────────────────────────── */

.md-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-soft);
  margin: 1em 0;
}
.md-body :deep(strong) { font-weight: 600; }
.md-body :deep(em)     { font-style: italic; }

.md-body :deep(a) {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
}
.md-body :deep(a:hover) { text-decoration: underline; }

/* Entity reference (TYPE@<code>): a compact inline pill with a link glyph. Renders like a
   footnote marker in prose — the short hash (or resolved title) is the label, the full code
   lives in the tooltip/href. */
.md-body :deep(.md-ref) {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-family: var(--font-mono);
  font-size: 0.78em;
  line-height: 1;
  padding: 1.5px 6px 1.5px 5px;
  margin: 0 1px;
  border-radius: 9px;
  color: rgb(var(--v-theme-primary));
  background: color-mix(in srgb, rgb(var(--v-theme-primary)) 9%, transparent);
  border: 1px solid color-mix(in srgb, rgb(var(--v-theme-primary)) 22%, transparent);
  text-decoration: none;
  white-space: nowrap;
  vertical-align: baseline;
  cursor: pointer;
  transition: background 0.12s ease, border-color 0.12s ease;
}
.md-body :deep(.md-ref)::before {
  content: "";
  flex: none;
  width: 11px;
  height: 11px;
  background: currentColor;
  -webkit-mask: var(--md-ref-icon) center / contain no-repeat;
  mask: var(--md-ref-icon) center / contain no-repeat;
}
.md-body :deep(.md-ref:hover) {
  text-decoration: none;
  background: color-mix(in srgb, rgb(var(--v-theme-primary)) 18%, transparent);
  border-color: color-mix(in srgb, rgb(var(--v-theme-primary)) 45%, transparent);
}
.md-body {
  --md-ref-icon: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%23000' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 15l6-6'/%3E%3Cpath d='M11 6l.463-.536a5 5 0 0 1 7.071 7.072L18 13'/%3E%3Cpath d='M13 18l-.397.534a5.07 5.07 0 0 1-7.127 0 4.97 4.97 0 0 1 0-7.071L6 11'/%3E%3C/svg%3E");
}

.md-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  display: block;
}

.md-body :deep(.md-img) {
  position: relative;
  display: inline-block;
  max-width: 100%;
  margin-bottom: 6px;
  cursor: zoom-in;
}

.md-body :deep(.md-img)::after {
  content: "";
  position: absolute;
  top: 10px;
  right: 10px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55)
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E")
    center / 17px no-repeat;
  opacity: 0;
  transition: opacity 0.15s ease;
  pointer-events: none;
}

.md-body :deep(.md-img):hover::after {
  opacity: 1;
}

/* ── Compact mode ─────────────────────────────────────────── */

.md-body--compact { font-size: 13px; line-height: 1.6; }
.md-body--compact :deep(p)           { margin-bottom: 0.5em; }
.md-body--compact :deep(ul),
.md-body--compact :deep(ol)          { margin-bottom: 0.5em; }
.md-body--compact :deep(h1),
.md-body--compact :deep(h2),
.md-body--compact :deep(h3),
.md-body--compact :deep(h4),
.md-body--compact :deep(h5),
.md-body--compact :deep(h6)          { margin-top: 0.8em; }
</style>
