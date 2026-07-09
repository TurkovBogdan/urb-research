import DOMPurify from 'dompurify'

/**
 * Renders a message body as literal text — NOT Markdown.
 *
 * The text view supplied by the caller is plain text for plain bodies and near-plain
 * (images kept as ![alt](src)) for HTML bodies. Running it through
 * a Markdown parser misreads e-mail punctuation: a line like `# of VMs` becomes an <h1>, `1.`
 * starts an ordered list, `>` a blockquote, and so on. This renderer therefore only:
 *   - splits the text into paragraphs on line breaks (each break starts a new <p>),
 *   - keeps images written as ![alt](src),
 *   - turns Markdown links [text](url) into anchors,
 *   - turns **bold** / *italic* into <strong> / <em> (the emphasis the backend emits from
 *     <b>/<strong>/<i>/<em>); markers must hug the text (no inner space) to avoid catching
 *     stray asterisks in plain-text bodies,
 *   - turns bare http(s) URLs into links (upgrading http → https),
 *   - escapes everything else.
 * No headings, lists or quotes are ever inferred.
 */

// One pass over a segment, matching whichever inline construct comes first: an image ![alt](src)
// or link [text](url), bold (**…**) before italic (*…*) so `**` wins, then a bare URL. Bold/italic
// recurse so emphasis can wrap a link (an email's <b>5. <a>…</a>.</b> → **5. [..](..).**). Each
// emphasis marker must hug a non-space char (no `* foo *` / bullet `* ` / `2 * 3` matches).
const INLINE_TOKEN =
  /(!?)\[([^\]]*)\]\(([^)\s]+)\)|\*\*(?=\S)([\s\S]*?\S)\*\*(?!\*)|\*(?=\S)([\s\S]*?\S)\*|(https?:\/\/[^\s<>()[\]"']+)/g
const TRAILING_PUNCTUATION = /[.,;:!?'")\]]+$/

// A remote resource gated behind the safety toggle: absolute http(s) or protocol-relative.
// Same-origin paths (e.g. inline attachments rehosted to /storage/...) are not remote and load.
const REMOTE_URL = /^(?:https?:|\/\/)/i

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function upgradeToHttps(url: string): string {
  return url.replace(/^http:\/\//i, 'https://')
}

// A remote image is replaced by an inert placeholder (no <img>, so no network request) until
// the safety toggle reveals it — same anti-tracking gate as the HTML view's SafeEmailBody.
function renderImage(alt: string, src: string, showRemote: boolean): string {
  if (REMOTE_URL.test(src) && !showRemote) {
    return `<span class="msg-img-blocked" title="${escapeHtml(alt || 'image')}"></span>`
  }
  return `<span class="msg-img"><img src="${escapeHtml(src)}" alt="${escapeHtml(alt || 'image')}"></span>`
}

function renderLink(text: string, url: string): string {
  const href = upgradeToHttps(url)
  return `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(text || url)}</a>`
}

function renderBareUrl(raw: string): string {
  const trailing = raw.match(TRAILING_PUNCTUATION)?.[0] ?? ''
  const url = trailing ? raw.slice(0, -trailing.length) : raw
  const href = upgradeToHttps(url)
  return (
    `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a>` +
    escapeHtml(trailing)
  )
}

// Render one segment: media, emphasis and bare URLs, escaping everything else. Bold/italic recurse
// so their content can itself contain a link/image or nested emphasis.
function renderInline(raw: string, showRemote: boolean): string {
  let html = ''
  let cursor = 0
  for (const match of raw.matchAll(INLINE_TOKEN)) {
    const start = match.index ?? 0
    html += escapeHtml(raw.slice(cursor, start))
    const [whole, bang, label, target, bold, italic, url] = match
    if (target !== undefined) html += bang === '!' ? renderImage(label, target, showRemote) : renderLink(label, target)
    else if (bold !== undefined) html += `<strong>${renderInline(bold, showRemote)}</strong>`
    else if (italic !== undefined) html += `<em>${renderInline(italic, showRemote)}</em>`
    else if (url !== undefined) html += renderBareUrl(url)
    cursor = start + whole.length
  }
  html += escapeHtml(raw.slice(cursor))
  return html
}

export function renderMessageText(text: string, showRemote = false): string {
  const paragraphs = text.split(/\n+/).filter((paragraph) => paragraph.trim() !== '')
  const html = paragraphs.map((paragraph) => `<p>${renderInline(paragraph, showRemote)}</p>`).join('')

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['a', 'img', 'span', 'p', 'strong', 'em'],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'src', 'alt', 'class', 'title'],
  })
}
