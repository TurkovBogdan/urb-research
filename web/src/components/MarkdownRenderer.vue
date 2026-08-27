<script setup lang="ts">
import { computed, getCurrentInstance, h, nextTick, onBeforeUnmount, onMounted, ref, render, watch } from 'vue'
import { useRouter } from 'vue-router'
import CodeBlock from './CodeBlock.vue'
import { useAfterRouteTransition } from '@/composables/useRouteTransition'
import { renderMarkdown, type HeadingAnchor } from './markdown/render'

const router = useRouter()

const props = defineProps<{
  text: string
  compact?: boolean
  // Документ целиком, а не подпись под полем: разбор и раскладка такого тела занимают главный
  // поток на десятки миллисекунд, и выпади они на переход между страницами — съели бы его
  // анимацию. Помеченное так тело ждёт конца перехода; всё остальное рисуется сразу.
  heavy?: boolean
  // Render Markdown images as <img> (off by default: the agent chat strips them).
  allowImages?: boolean
  // Treat single newlines as <br> — preserves line breaks of plain-text email bodies.
  breaks?: boolean
  // Map `TYPE@hash` → entity title. When a reference pill's code resolves here, the pill
  // shows the (truncated) title instead of the short hash.
  refLabels?: Record<string, string>
}>()

const REF_LABEL_MAX = 48

const emit = defineEmits<{
  imageClick: [src: string]
  // Оглавление тела: заголовки с проставленными `id`. Отдаём событием, а не через expose —
  // потребителю (боковой навигации) нужен готовый список, а не доступ внутрь рендерера.
  headings: [items: HeadingAnchor[]]
}>()

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

// Пустой текст, пока идёт переход, — это и есть отсрочка: разбор не запускается, оглавление
// приезжает вместе с телом, и ни один потребитель не узнаёт про ожидание ничего сверх того,
// что тело пока пустое.
const settled = useAfterRouteTransition()

const source = computed(() => (props.heavy && !settled.value ? '' : props.text))

const rendered = computed(() => renderMarkdown(source.value, {
  breaks: props.breaks ?? false,
  allowImages: props.allowImages ?? false,
}))

const html = computed(() => withRefLabels(rendered.value.html))

watch(() => rendered.value.headings, (items) => emit('headings', items), { immediate: true })

// Code blocks are not part of the HTML: the parser leaves an empty slot for each one and the
// real component is mounted into it here, so a body gets highlighting, a copy button and a
// language badge. A one-liner takes the compact variant — a command reads as a chip, not as a
// panel with a header.
const body = ref<HTMLElement | null>(null)
const appContext = getCurrentInstance()?.appContext ?? null
let mountedSlots: HTMLElement[] = []

function unmountCodeBlocks() {
  for (const slot of mountedSlots) render(null, slot)
  mountedSlots = []
}

function mountCodeBlocks() {
  const container = body.value
  if (!container) return
  container.querySelectorAll<HTMLElement>('.md-code-slot').forEach((slot) => {
    const block = rendered.value.codeBlocks[Number(slot.dataset.codeIndex)]
    if (!block) return
    const isOneLiner = !block.code.trim().includes('\n')
    const vnode = h(CodeBlock, {
      code: block.code.replace(/\n$/, ''),
      lang: block.language || undefined,
      variant: isOneLiner ? 'compact' : 'icon',
    })
    vnode.appContext = appContext
    render(vnode, slot)
    mountedSlots.push(slot)
  })
}

// v-html replaces the container's children, so the previous instances are unmounted first —
// while their slots (detached by then or not) are still known here.
watch(html, () => {
  unmountCodeBlocks()
  nextTick(mountCodeBlocks)
})

onMounted(mountCodeBlocks)
onBeforeUnmount(unmountCodeBlocks)

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
  <div ref="body" class="md-body" :class="{ 'md-body--compact': compact }" v-html="html" @click="onClick" />
</template>

<style scoped>
/* The reading zone. A research body is read top to bottom rather than scanned, so it
   runs on the reading font role and a larger base than the interface — and every size
   below is expressed in `em`, which leaves `--prose-size` as the single knob the
   compact variant has to move. */
.md-body {
  /* `--reading-size` is the user's choice, written onto <html> by the settings store; the
     literal is what the zone falls back to before the store has run. */
  --prose-size: var(--reading-size, 14px);
  /* One indent for lists and for the task-list hanging indent, so the two cannot drift. */
  --prose-indent: 1.5em;

  font-family: var(--font-reading);
  font-size: var(--prose-size);
  line-height: 1.7;
  color: var(--text);
  /* Reset inherited white-space (chat bubbles set pre-wrap for plain-text bodies): the parser
     emits literal newlines between block tags, which under pre-wrap render as phantom empty
     lines (bottom gap after a lone paragraph, huge gaps inside blockquotes). Intentional
     line breaks come from the `breaks` option as real <br>, unaffected by this. */
  white-space: normal;
}

/* main.scss styles bare `p` and `h1`–`h6` for the views that are not prose, and those rules
   sit outside any cascade layer — inheriting from `.md-body` does not beat them. So the zone
   restates the properties they claim; without this a paragraph keeps the interface font at
   13px no matter what the body is set to. */
.md-body :deep(:is(p, h1, h2, h3, h4, h5, h6)) {
  font-family: inherit;
}
.md-body :deep(p) {
  font-size: 1em;
  line-height: inherit;
}

/* Measure — the width running text is allowed to reach on a wide monitor. The value is the
   user's choice, written onto <html> by the settings store in `ch`, so the column follows the
   reading family when it is switched; the literal is the fallback before the store has run.
   Running text only: tables, code blocks and images keep the whole width — they are scanned,
   not read line by line. */
.md-body :deep(:is(p, ul, ol, blockquote, h1, h2, h3, h4, h5, h6)) {
  max-width: var(--reading-measure, 92ch);
}

/* Two different wrapping jobs, so two different values.
   `balance` evens the line lengths of a block that is short by nature — a heading, a cell —
   where a one-word second line reads as a mistake. On running text it does the wrong thing:
   a two-line paragraph gets pulled away from the right edge into two half-width lines.
   `pretty` leaves the ragged edge alone and only prevents the last line from being a single
   orphaned word, which is what running text actually needs. */
.md-body :deep(:is(th, td, h1, h2, h3, h4, h5, h6)) {
  text-wrap: balance;
}
.md-body :deep(:is(p, li, blockquote)) {
  text-wrap: pretty;
}

/* A block's first element never adds a top margin: it would stack with the padding of
   whatever card or panel the body sits in. */
.md-body :deep(> :first-child) {
  margin-top: 0;
}

/* ── Headings ─────────────────────────────────────────────── */

.md-body :deep(:is(h1, h2, h3, h4, h5, h6)) {
  font-weight: 600;
  color: var(--text);
  /* Trims the half-leading the browser adds above and below a text box — without it the
     margins below are not the distances actually seen, and the gap depends on the chosen
     font. Silently ignored where unsupported, which only restores the old spacing. */
  text-box: trim-both cap alphabetic;
}

/* Space above a heading is several times the space below it: the heading belongs to the
   text that follows, and that asymmetry is what separates one section from the previous.
   Tracking tightens as the size grows — the gaps that read as normal at text size look
   slack once the glyphs are half again as large. */
.md-body :deep(h1) { font-size: 1.5em;   line-height: 1.25; margin: 1.6em 0 0.6em;  letter-spacing: -0.018em; }
.md-body :deep(h2) { font-size: 1.25em;  line-height: 1.3;  margin: 2em 0 0.75em;   letter-spacing: -0.012em; }
.md-body :deep(h3) { font-size: 1.125em; line-height: 1.35; margin: 1.6em 0 0.5em;  letter-spacing: -0.006em; }
.md-body :deep(:is(h4, h5, h6)) { font-size: 1em; line-height: 1.4; margin: 1.4em 0 0.4em; }

/* Below h3 the size stops carrying the level — three more steps would land inside the noise
   of the body text. The distinction moves to colour and case instead: h4 stays a full-strength
   heading, h5 steps back, h6 becomes a label. */
.md-body :deep(h5) { color: var(--text-muted); }
.md-body :deep(h6) {
  font-size: 0.875em;
  text-transform: uppercase;
  /* Uppercase needs the extra room: without positive tracking capitals set solid. */
  letter-spacing: 0.06em;
  color: var(--text-faint);
}

/* A heading immediately followed by a deeper one is a single heading block — «Списки» then
   «Маркированный» — so the gap between them collapses. The pairs are spelled out descending
   on purpose: when a *shallower* heading follows (h6 then h2) that is the next section
   starting, and it keeps its full space above. */
.md-body :deep(h1 + h2),
.md-body :deep(h2 + h3),
.md-body :deep(h3 + h4),
.md-body :deep(h4 + h5),
.md-body :deep(h5 + h6) {
  margin-top: 0.6em;
}

/* ── Paragraph ────────────────────────────────────────────── */

.md-body :deep(p) {
  margin: 0 0 1em;
}
.md-body :deep(p:last-child) {
  margin-bottom: 0;
}

/* ── Lists ────────────────────────────────────────────────── */

.md-body :deep(:is(ul, ol)) {
  margin: 0.75em 0 1em;
  padding-left: var(--prose-indent);
}
.md-body :deep(:is(ul, ol):last-child) {
  margin-bottom: 0;
}
.md-body :deep(ul) { list-style: disc; }
.md-body :deep(ol) { list-style: decimal; }

.md-body :deep(li) {
  margin: 0.35em 0;
  line-height: 1.6;
}

/* The marker is punctuation, not content: at full text colour a column of bullets reads as
   a second column of text down the left edge. */
.md-body :deep(li)::marker {
  color: var(--text-faint);
}

/* Nested lists */
.md-body :deep(li > :is(ul, ol)) {
  margin: 0.35em 0;
}

/* Task list: the checkbox replaces the bullet, so the item gives back the marker indent; the
   negative text-indent keeps wrapped lines hanging under the text rather than the checkbox. */
.md-body :deep(li.md-task) {
  list-style: none;
  margin-left: calc(var(--prose-indent) * -1);
  padding-left: var(--prose-indent);
  text-indent: calc(var(--prose-indent) * -1);
}
.md-body :deep(li input[type="checkbox"]) {
  margin-right: 0.4em;
  cursor: default;
  accent-color: rgb(var(--v-theme-primary));
}

/* ── Blockquote ───────────────────────────────────────────── */

/* Marked by the rule and by the space around it, not by italics: a quote in these bodies
   runs to a full paragraph, and italics at that length measurably slow reading down. */
.md-body :deep(blockquote) {
  /* The rule is the whole signal here, so it is drawn off the text colour rather than the
     border token — at `--border` it sinks into the card and a one-line quote stops reading
     as a quote at all. */
  border-left: 3px solid color-mix(in srgb, var(--text) 22%, transparent);
  margin: 1.4em 0;
  padding: 0.2em 0 0.2em 1em;
  color: var(--text-muted);
}
.md-body :deep(blockquote:last-child) {
  margin-bottom: 0;
}

/* ── Code ─────────────────────────────────────────────────── */

/* A fenced block is a mounted CodeBlock component; this only spaces it in the flow.
   A self-contained block gets more air than a paragraph — the more autonomous the
   element, the wider the gap that reads as "this is a separate thing". */
.md-body :deep(.md-code-slot) {
  margin: 1.5em 0;
}
.md-body :deep(.md-code-slot:last-child) {
  margin-bottom: 0;
}
/* These bodies are dense with inline code — a sentence often carries three or four spans. A
   bordered chip on each one turns the paragraph into a row of boxes and the prose stops being
   the thing you see first, so the border is gone and the fill is only just enough to read as
   a distinct run. Padding is in `em` so the chip keeps its proportions at any prose size. */
.md-body :deep(.md-codespan) {
  font-family: var(--font-mono);
  /* A monospace face looks bigger than a proportional one at the same size; 0.875em is the
     correction, and in `em` it follows the prose scale instead of freezing at one pixel size. */
  font-size: 0.875em;
  color: var(--text);
  /* A film of the text colour rather than a surface token: this zone is rendered on cards,
     panels and chat bubbles of different shades, and a fixed fill washes out against half
     of them. */
  background: color-mix(in srgb, var(--text) 10%, transparent);
  /* Explicit, not inherited-away: the bare `code` rule in main.scss draws an accent-coloured
     outline, and dropping it here is the whole point of the block above. */
  border: none;
  border-radius: 4px;
  padding: 0.1em 0.35em;
  /* A span that wraps mid-token is two fragments; without this the padding and the rounding
     go to the outer edges only and the halves read as one broken plate. */
  box-decoration-break: clone;
  -webkit-box-decoration-break: clone;
}

/* ── Table ────────────────────────────────────────────────── */

/* Bodies carry wide comparison tables (up to a dozen columns): the wrapper scrolls, the table
   keeps its natural width instead of squeezing cells into vertical strings. */
.md-body :deep(.md-table-wrap) {
  overflow-x: auto;
  margin: 2em 0;
  border: 1px solid var(--border-soft);
  border-radius: 6px;
}
.md-body :deep(.md-table-wrap:last-child) {
  margin-bottom: 0;
}
.md-body :deep(.md-table) {
  border-collapse: collapse;
  width: max-content;
  min-width: 100%;
  /* A table is scanned, not read: one step below the prose size fits more of it on
     screen without crossing into unreadable. */
  font-size: 0.875em;
}
.md-body :deep(.md-table th),
.md-body :deep(.md-table td) {
  border-right: 1px solid var(--border-soft);
  border-bottom: 1px solid var(--border-soft);
  /* Figures line up into columns instead of drifting by the width of a `1` — these bodies
     compare sizes, prices and limits, and a ragged numeric column is read as noise. */
  font-variant-numeric: tabular-nums;
  padding: 0.45em 0.65em;
  text-align: left;
  vertical-align: top;
  line-height: 1.5;
  /* Without a cap a prose-heavy cell claims its full one-line width (the table is sized by
     max-content) and a two-column table scrolls like a wide one. */
  max-width: 60ch;
}
.md-body :deep(.md-table th:last-child),
.md-body :deep(.md-table td:last-child) { border-right: none; }
.md-body :deep(.md-table tbody tr:last-child td) { border-bottom: none; }
.md-body :deep(.md-table th) {
  background: var(--surface-hi);
  font-weight: 600;
  white-space: nowrap;
}
.md-body :deep(.md-table tbody tr:nth-child(even)) {
  background: color-mix(in srgb, var(--surface-hi) 45%, transparent);
}
/* A pill never breaks in prose, but a cell is sized by its content: a title-labelled reference
   would otherwise widen the column past the page and send the whole table into horizontal
   scroll. Inside a cell it wraps like text instead. */
.md-body :deep(.md-table .md-ref) {
  white-space: normal;
  /* The cell cap alone doesn't help: the table is sized by max-content, so a pill labelled with
     a title claims one long line and widens the column. Capping the pill itself makes the label
     wrap inside it and keeps the column near the width of the prose around it. */
  max-width: 30ch;
  /* A wrapped label is a paragraph, not a chip: the glyph belongs beside its first line (centring
     it against the whole block reads as a bullet), and the lines need room to breathe. */
  align-items: baseline;
  line-height: 1.35;
}
/* Column alignment has to out-specify the cell rule above, so it names the cell too. */
.md-body :deep(.md-table .md-align-left)   { text-align: left; }
.md-body :deep(.md-table .md-align-center) { text-align: center; }
.md-body :deep(.md-table .md-align-right)  { text-align: right; }

/* ── Misc ─────────────────────────────────────────────────── */

.md-body :deep(s) { text-decoration: line-through; color: var(--text-muted); }

/* The widest gap in the body: a rule separates whole parts, so it needs more air than
   any heading — otherwise it reads as decoration on the paragraph above it. */
.md-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-soft);
  margin: 3em 0;
}
.md-body :deep(strong) { font-weight: 600; }
.md-body :deep(em)     { font-style: italic; }

/* A link in running text is underlined, not just tinted: colour alone is the one distinction
   that disappears for a colour-blind reader, and in a body this dense a blue word is easy to
   miss. The rule is set faint and dropped below the baseline so it marks the word without
   cutting through its descenders; hover brings it up to full strength. `md-ref` is excluded —
   it is a pill with its own shape and an underline would only smear it. */
.md-body :deep(a:not(.md-ref)) {
  color: rgb(var(--v-theme-primary));
  text-decoration: underline;
  text-decoration-color: color-mix(in srgb, rgb(var(--v-theme-primary)) 40%, transparent);
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
}
.md-body :deep(a:not(.md-ref):hover) {
  text-decoration-color: currentColor;
}

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
  /* `cap` is the cap height of the current font, so the glyph tracks the text it sits in
     instead of freezing at a size picked for one prose scale. The px pair above is the
     fallback for engines without the unit. */
  width: 1cap;
  height: 1cap;
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

/* Compact is the interface role, not the reading one: it renders setting descriptions and
   chat bubbles, which live inside UI chrome. So it takes the interface family and size,
   drops the measure cap (its container is already narrow) and tightens every gap back to
   what a dense panel wants. */
.md-body--compact {
  /* Pinned, not `--reading-size`: this is interface chrome, and it has to stay in step with
     the labels and rows around it whatever size the reading zone is set to. */
  --prose-size: 13px;
  font-family: var(--font);
  line-height: 1.6;
}
.md-body--compact :deep(:is(p, ul, ol, blockquote, h1, h2, h3, h4, h5, h6)) { max-width: none; }
.md-body--compact :deep(p)                       { margin-bottom: 0.5em; }
.md-body--compact :deep(:is(ul, ol))             { margin: 0.4em 0 0.5em; }
.md-body--compact :deep(:is(h1, h2, h3, h4, h5, h6)) { margin-top: 0.8em; margin-bottom: 0.3em; }
.md-body--compact :deep(blockquote)              { margin: 0.6em 0; }
.md-body--compact :deep(.md-code-slot)           { margin: 0.6em 0; }
.md-body--compact :deep(.md-table-wrap)          { margin: 0.7em 0; }
.md-body--compact :deep(hr)                      { margin: 1em 0; }
</style>
