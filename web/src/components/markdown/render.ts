// Markdown → sanitised HTML for research bodies: CommonMark + GFM (markdown-it) with the
// project's own rendering decisions on top — entity-reference pills, task-list checkboxes,
// scrollable tables, external-link targets — and a DOMPurify pass as the closing step.
import MarkdownIt from 'markdown-it'
import type { Env, MarkdownIt as MarkdownParser, StateCore, Token } from 'markdown-it'
import DOMPurify from 'dompurify'

// Research entity cross-references: a `TYPE@<22-hex>` code in a body (RESEARCH / AREA /
// NOTE / QUERY / SOURCE) becomes a link to that entity's page. Codes are exactly 22 hex
// chars (research.codes / hashing._HASH_LEN); the negative lookahead rejects a longer hex run.
const REF_ROUTE: Record<string, string> = {
  RESEARCH: 'researches',
  AREA: 'areas',
  NOTE: 'notes',
  QUERY: 'queries',
  SOURCE: 'sources',
}
const REF_CODE = new RegExp(`(${Object.keys(REF_ROUTE).join('|')})@([0-9a-f]{22})(?![0-9a-f])`, 'g')

// A code is recognised only inside plain text: code spans and fences are separate token
// types, and a code sitting in a link label must stay text (an <a> cannot nest an <a>).
function entityRefs(state: StateCore): void {
  for (const block of state.tokens) {
    if (block.type !== 'inline' || !block.children) continue
    block.children = splitRefsOutOfText(block.children, state)
  }
}

function splitRefsOutOfText(children: Token[], state: StateCore): Token[] {
  const result: Token[] = []
  let linkDepth = 0
  for (const token of children) {
    if (token.type === 'link_open') linkDepth += 1
    if (token.type === 'link_close') linkDepth -= 1
    if (token.type === 'text' && linkDepth === 0) result.push(...refTokens(token, state))
    else result.push(token)
  }
  return result
}

function refTokens(text: Token, state: StateCore): Token[] {
  const parts: Token[] = []
  let cursor = 0
  for (const match of text.content.matchAll(REF_CODE)) {
    const start = match.index
    if (start > cursor) parts.push(textToken(text.content.slice(cursor, start), text.level, state))
    const ref = new state.Token('entity_ref', '', 0)
    ref.level = text.level
    ref.meta = { refType: match[1], hash: match[2] }
    parts.push(ref)
    cursor = start + match[0].length
  }
  if (!parts.length) return [text]
  if (cursor < text.content.length) parts.push(textToken(text.content.slice(cursor), text.level, state))
  return parts
}

function textToken(content: string, level: number, state: StateCore): Token {
  const token = new state.Token('text', '', 0)
  token.content = content
  token.level = level
  return token
}

// GFM task list: markdown-it has no rule for it, so a leading `[ ]` / `[x]` of a list item's
// first paragraph becomes a disabled checkbox token (the default renderer prints the <input>).
// The item itself is marked `md-task` so the CSS can drop its bullet — the checkbox is the marker.
const TASK_MARKER = /^\[([ xX])\]\s+/

function taskListCheckboxes(state: StateCore): void {
  const tokens = state.tokens
  for (let index = 2; index < tokens.length; index += 1) {
    const inline = tokens[index]
    const listItem = tokens[index - 2]
    const startsListItem = tokens[index - 1].type === 'paragraph_open' && listItem.type === 'list_item_open'
    if (inline.type !== 'inline' || !startsListItem) continue
    const marker = TASK_MARKER.exec(inline.content)
    const firstChild = inline.children?.[0]
    if (!marker || firstChild?.type !== 'text') continue
    inline.content = inline.content.slice(marker[0].length)
    firstChild.content = firstChild.content.slice(marker[0].length)
    const checkbox = new state.Token('task_checkbox', 'input', 0)
    checkbox.attrs = [['type', 'checkbox'], ['disabled', 'disabled']]
    if (marker[1] !== ' ') checkbox.attrPush(['checked', 'checked'])
    inline.children?.unshift(checkbox)
    listItem.attrJoin('class', 'md-task')
  }
}

// Column alignment arrives as an inline `style` attribute; the sanitiser allowlist has no
// `style` (and should not), so it is carried by a class instead.
const ALIGN_CLASS: Record<string, string> = {
  'text-align:left': 'md-align-left',
  'text-align:center': 'md-align-center',
  'text-align:right': 'md-align-right',
}

function alignByClass(cell: Token): void {
  const style = cell.attrGet('style')
  if (style === null) return
  cell.attrs?.splice(cell.attrIndex('style'), 1)
  const className = ALIGN_CLASS[String(style).replace(/\s+/g, '')]
  if (className) cell.attrJoin('class', className)
}

// Headings get an `id` so the page can link to them (table of contents, deep links), and the
// list of them comes back to the caller as data — building it here is free, while re-parsing the
// rendered HTML afterwards would mean a second pass over every body.
export interface HeadingAnchor {
  id: string
  /** 1…6 — the `h` level, for nesting in a table of contents. */
  level: number
  /** Plain text: emphasis, links and reference codes are stripped. */
  text: string
}

// `md-` prefix keeps generated ids out of the page's own namespace and guarantees the id never
// starts with a digit; the dash also makes it unusable as a JS identifier, so a heading cannot
// clobber a global by name.
const ANCHOR_PREFIX = 'md-'
const ANCHOR_MAX = 60

function slug(text: string, used: Map<string, number>): string {
  const base = text.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-+|-+$/g, '')
  const candidate = ANCHOR_PREFIX + (base.slice(0, ANCHOR_MAX) || 'heading')
  const seen = used.get(candidate) ?? 0
  used.set(candidate, seen + 1)
  return seen ? `${candidate}-${seen + 1}` : candidate
}

function headingAnchors(state: StateCore): void {
  const env = state.env as RenderEnv
  const used = new Map<string, number>()
  state.tokens.forEach((token, index) => {
    if (token.type !== 'heading_open') return
    const inline = state.tokens[index + 1]
    // Renders children as plain text — markup drops out, and so do the reference pills, whose
    // 22-hex code would be noise in a table of contents.
    const text = state.md.renderer
      .renderInlineAsText(inline?.children ?? [], state.md.options, state.env)
      .trim()
    const id = slug(text, used)
    token.attrSet('id', id)
    env.headings.push({ id, level: Number(token.tag.slice(1)), text })
  })
}

// A fenced block is not rendered as HTML: it is handed back to the caller as data and its
// place is held by an empty slot, so the view can mount the real CodeBlock component there
// (highlighting, copy button, line numbers). `env` carries the list — it is per-render state,
// while the parser instance is shared.
export interface CodeBlockSource {
  code: string
  language: string
}

interface RenderEnv extends Env {
  codeBlocks: CodeBlockSource[]
  headings: HeadingAnchor[]
}

const CODE_LANGUAGE = /^[\w+-]+$/

function codeSlot(code: string, language: string, env: RenderEnv): string {
  const index = env.codeBlocks.push({ code, language }) - 1
  return `<div class="md-code-slot" data-code-index="${index}"></div>\n`
}

function createParser(breaks: boolean): MarkdownParser {
  // `html: false` — bodies come from an LLM agent and from scraped pages, so raw HTML never
  // reaches the sanitiser in the first place. `fuzzyLink: false` keeps linkify to schema'd
  // URLs: bare `app.py` / `README.md` would otherwise link (`.py`, `.md` are real TLDs).
  const md = new MarkdownIt({ html: false, linkify: true, breaks })
  md.linkify.set({ fuzzyLink: false, fuzzyEmail: false })

  md.core.ruler.push('entity_refs', entityRefs)
  md.core.ruler.push('task_list_checkboxes', taskListCheckboxes)
  // After `entity_refs`, so a heading's reference codes are already separate tokens by the time
  // its plain-text label is built.
  md.core.ruler.push('heading_anchors', headingAnchors)

  md.renderer.rules.fence = (tokens, idx, _options, env) => {
    const info = tokens[idx].info.trim().split(/\s+/)[0] ?? ''
    const language = CODE_LANGUAGE.test(info) ? info : ''
    return codeSlot(tokens[idx].content, language, env as RenderEnv)
  }
  md.renderer.rules.code_block = (tokens, idx, _options, env) => codeSlot(tokens[idx].content, '', env as RenderEnv)
  md.renderer.rules.code_inline = (tokens, idx) => `<code class="md-codespan">${md.utils.escapeHtml(tokens[idx].content)}</code>`

  // External links open in a new tab so they never navigate the SPA away (e.g. a settings
  // token link would otherwise discard unsaved input). Internal links (href starting with
  // `/`) stay in-app — the router intercepts them in onClick.
  md.renderer.rules.link_open = (tokens, idx, options, _env, self) => {
    const link = tokens[idx]
    if (!String(link.attrGet('href') ?? '').startsWith('/')) {
      link.attrSet('target', '_blank')
      link.attrSet('rel', 'noopener noreferrer')
    }
    return self.renderToken(tokens, idx, options)
  }

  // An image is wrapped in a positioned <span> so the hover loupe affordance has an anchor
  // (an <img> can't carry ::after).
  md.renderer.rules.image = (tokens, idx, options, env, self) => {
    const image = tokens[idx]
    image.attrSet('alt', self.renderInlineAsText(image.children ?? [], options, env))
    return `<span class="md-img">${self.renderToken(tokens, idx, options)}</span>`
  }

  // A wide table (bodies carry up to a dozen columns) scrolls inside its own box instead of
  // stretching the page column.
  md.renderer.rules.table_open = () => '<div class="md-table-wrap">\n<table class="md-table">\n'
  md.renderer.rules.table_close = () => '</table>\n</div>\n'
  md.renderer.rules.th_open = (tokens, idx, options, _env, self) => {
    alignByClass(tokens[idx])
    return self.renderToken(tokens, idx, options)
  }
  md.renderer.rules.td_open = (tokens, idx, options, _env, self) => {
    alignByClass(tokens[idx])
    return self.renderToken(tokens, idx, options)
  }

  // The 22-hex hash is opaque in prose — show a short prefix as the transient label, keep the
  // full code in href (navigation) + title (tooltip); a resolved title replaces it later.
  // Both parts of the code come from the regex above (fixed word + hex), so they need no escaping.
  md.renderer.rules.entity_ref = (tokens, idx) => {
    const { refType, hash } = tokens[idx].meta as { refType: string; hash: string }
    const code = `${refType}@${hash}`
    return `<a class="md-ref" href="/research/${REF_ROUTE[refType]}/${code}" title="${code}">${hash.slice(0, 6)}</a>`
  }

  return md
}

// Two parsers at most: `breaks` is an instance option, and a shared instance re-configured
// per render would flip under a sibling renderer using the other mode.
const parsers = new Map<boolean, MarkdownParser>()

function parser(breaks: boolean): MarkdownParser {
  const existing = parsers.get(breaks)
  if (existing) return existing
  const created = createParser(breaks)
  parsers.set(breaks, created)
  return created
}

// The parser never emits raw HTML (`html: false`), so the sanitiser is the second line rather
// than the only one — it still runs, and its allowlist names attributes, not just tags.
const ALLOWED_TAGS = [
  'h1','h2','h3','h4','h5','h6',
  'p','ul','ol','li','blockquote','pre','code','hr',
  'strong','em','s','a','br','input',
  'div','table','thead','tbody','tr','th','td',
]
const ALLOWED_ATTR = ['class','href','target','rel','type','checked','disabled','title','id','data-code-index']
const IMAGE_TAGS = ['img', 'span']
const IMAGE_ATTR = ['src', 'alt']

export interface RenderOptions {
  // Treat single newlines as <br> — preserves line breaks of plain-text bodies.
  breaks: boolean
  // Keep <img> elements (off by default: the agent chat strips them).
  allowImages: boolean
}

export interface RenderedMarkdown {
  html: string
  // Code blocks pulled out of the HTML; `.md-code-slot[data-code-index]` marks where each goes.
  codeBlocks: CodeBlockSource[]
  // Headings in document order, each with the `id` set on it in the HTML.
  headings: HeadingAnchor[]
}

export function renderMarkdown(text: string, { breaks, allowImages }: RenderOptions): RenderedMarkdown {
  const env: RenderEnv = { codeBlocks: [], headings: [] }
  const html = parser(breaks).render(text, env)
  return {
    html: DOMPurify.sanitize(html, {
      ALLOWED_TAGS: allowImages ? [...ALLOWED_TAGS, ...IMAGE_TAGS] : ALLOWED_TAGS,
      ALLOWED_ATTR: allowImages ? [...ALLOWED_ATTR, ...IMAGE_ATTR] : ALLOWED_ATTR,
    }),
    codeBlocks: env.codeBlocks,
    headings: env.headings,
  }
}
