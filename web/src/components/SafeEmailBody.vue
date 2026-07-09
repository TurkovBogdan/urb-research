<script setup lang="ts">
/**
 * Renders an untrusted HTML body safely at render time:
 *   1. DOMPurify sanitizes the markup in the browser.
 *   2. The result is written into an <iframe srcdoc> whose `sandbox` has NO
 *      `allow-scripts` — so even if something slipped through, no JS can run.
 *   3. A CSP inside the srcdoc blocks all network by default; remote images are
 *      revealed only after the user opts in (anti-tracking — a remote <img> is a
 *      read receipt / IP leak).
 *
 * Plain-text bodies (no markup) are shown as escaped text, never as HTML.
 */
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import DOMPurify from 'dompurify'
import { IconAlertTriangle, IconEye } from '@tabler/icons-vue'

const props = defineProps<{
  body: string | null
  showRemote?: boolean
  hideBar?: boolean
  // Force the iframe (HTML) path regardless of auto-detection — for callers that
  // already know the body is markup (e.g. an assembled view with <details> spoilers,
  // whose tags the heuristic below does not list).
  forceHtml?: boolean
  // Extra CSS appended inside the iframe, after the base reset and render fixes — for
  // call-site-specific tweaks. The standing render fixes live in FRAME_FIXES_CSS.
  fixes?: string
}>()

// Our own placeholder for blocked remote images — a gray box with a cross. Inlined as a
// data: URI so it loads under the strict CSP (img-src always allows data:) and can never
// render as a "broken image". The <img> keeps its original width/height; the SVG scales.
const PLACEHOLDER_SVG =
  "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='90' preserveAspectRatio='none'>" +
  "<rect width='120' height='90' fill='#f2f2f2'/>" +
  "<rect x='0.5' y='0.5' width='119' height='89' fill='none' stroke='#dddddd'/>" +
  "<g stroke='#b0b0b0' stroke-width='3' stroke-linecap='round'>" +
  "<line x1='50' y1='35' x2='70' y2='55'/><line x1='70' y1='35' x2='50' y2='55'/></g></svg>"
const BLOCKED_IMG_SRC = 'data:image/svg+xml,' + encodeURIComponent(PLACEHOLDER_SVG)

// A remote resource we must gate: absolute http(s) or protocol-relative.
const REMOTE_URL = /^(?:https?:|\/\/)/i

// Base reset inside the iframe — typography + neutralized inert links. `overflow:hidden`
// on <html> suppresses the iframe's own scrollbar: the parent always sizes the frame to the
// content height, so an inner scrollbar is never wanted — and a width-constrained image
// (max-width:100%) whose height depends on the available width would otherwise oscillate
// (scrollbar steals width → image taller → scrollbar needed) and leave a phantom scrollbar.
const FRAME_BASE_CSS =
  'html{overflow:hidden}' +
  'html,body{margin:0;padding:0}' +
  'body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:13px;line-height:1.55;' +
  'color:#1a1a1a;background:transparent;word-break:break-word}' +
  'hr{box-sizing:border-box}' +
  'a[data-inert]{pointer-events:none;cursor:default;text-decoration:none;color:inherit}'

// Minimal-variant chevron (Tabler chevron-right, faint), baked with its color so it loads as a
// background-image under the iframe CSP (img-src data:); rotated 90° when the spoiler is open.
const SPOILER_CHEVRON =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' " +
  "viewBox='0 0 24 24' fill='none' stroke='%239CA3AF' stroke-width='2' stroke-linecap='round' " +
  "stroke-linejoin='round'%3E%3Cpath d='M9 6l6 6-6 6'/%3E%3C/svg%3E\")"

// Render fixes for real-world email markup. Primary goal: WIDTH CONTAINMENT — keep every
// element within the frame so a wide table, a fixed-px layout, oversized media or a long
// unbreakable string can never force the body wider than the frame (horizontal overflow).
// Also styles the assembled-view spoilers (forwarded/history <details>) in the MINIMAL variant —
// a borderless chevron + uppercase faint label, matching the Spoiler component's `minimal` theme
// and the text view (MessageContent). The empty <summary> gets its localized label from the
// per-kind `::after` rule MessageContent passes in `fixes`. Tokens hardcoded as hex because the
// iframe is isolated from the app's CSS variables (--text-faint/--text-muted).
const FRAME_FIXES_CSS =
  '*{max-width:100%!important}' +
  'img,video{height:auto}' +
  'table{table-layout:auto}' +
  'td,th{word-break:break-word}' +
  'pre{white-space:pre-wrap;word-break:break-word}' +
  '.mc-spoiler>summary{display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none;' +
  'list-style:none;padding:4px 0;font-size:11px;font-weight:600;letter-spacing:.06em;' +
  'text-transform:uppercase;color:#9CA3AF;transition:color .15s ease}' +
  '.mc-spoiler>summary::-webkit-details-marker{display:none}' +
  `.mc-spoiler>summary::before{content:"";flex:0 0 auto;width:14px;height:14px;` +
  `background:${SPOILER_CHEVRON} center/contain no-repeat;transition:transform .2s ease}` +
  '.mc-spoiler[open]>summary::before{transform:rotate(90deg)}' +
  '.mc-spoiler>summary:hover{color:#6B7480}' +
  '.mc-spoiler[open]>summary{margin-bottom:6px}' +
  '.mc-quote{padding-left:24px}' +
  // the quoted block's own <blockquote> default margin (browser: ~40px left) stacks on the
  // .mc-quote indent — neutralize it so .mc-quote's indent is the only one.
  '.mc-quote blockquote{margin:0}'

// srcset is a comma-separated list of "<url> [descriptor]" — true if any URL is remote.
function srcsetHasRemote(value: string): boolean {
  return value.split(',').some((part) => REMOTE_URL.test(part.trim().split(/\s+/)[0] || ''))
}

// Layout/active markup → render as HTML; otherwise treat as plain text.
const LOOKS_HTML =
  /<\s*(?:html|head|body|div|p|br|table|tr|td|span|a|blockquote|ul|ol|li|img|font|b|i|u|strong|em|h[1-6]|style|center|hr|pre)(?=[\s/>])|<!doctype/i

const isHtml = computed(() => props.forceHtml || LOOKS_HTML.test(props.body || ''))

const internalShowRemote = ref(false)
const effectiveShowRemote = computed(() =>
  props.hideBar ? props.showRemote : internalShowRemote.value,
)
const hasRemote = ref(false)   // body contains at least one remote resource
const frameH     = ref(0)
const frame      = ref<HTMLIFrameElement | null>(null)
// False from a rebuild until the new document is parsed, bound and first-measured — drives the
// skeleton overlay. Stays true across parent show/hide toggles (no rebuild), so switching the
// view mode never re-shows the skeleton.
const ready      = ref(false)

function buildSrcdoc(raw: string, allowRemote: boolean): { html: string; remote: boolean } {
  let remote = false

  DOMPurify.removeAllHooks()
  DOMPurify.addHook('afterSanitizeAttributes', (node) => {
    const el = node as Element
    if (el.tagName === 'A') {
      const href = el.getAttribute('href') || ''
      const safe = /^(?:https?:|mailto:)/i.test(href)
      if (safe && allowRemote) {
        el.setAttribute('target', '_blank')
        el.setAttribute('rel', 'noopener noreferrer nofollow')
      } else {
        // Links are gated behind the same opt-in as remote images: until the user
        // reveals content, every link is inert (no href/target → click does nothing,
        // no about:blank popup). A real link counts as blocked content so the bar shows.
        if (safe) remote = true
        el.removeAttribute('href')
        el.removeAttribute('target')
        el.setAttribute('data-inert', '1')
      }
    }
    if (el.tagName === 'IMG') {
      const src = el.getAttribute('src') || ''
      const srcset = el.getAttribute('srcset') || ''
      if (REMOTE_URL.test(src) || srcsetHasRemote(srcset)) {
        remote = true
        if (!allowRemote) {
          // Pin to our placeholder and drop srcset — the browser prefers srcset
          // over src, so leaving it would skip the placeholder and try the remote.
          el.setAttribute('src', BLOCKED_IMG_SRC)
          el.setAttribute('data-blocked', '1')
          el.removeAttribute('srcset')
        }
      }
    }
    // <picture> serves images via <source srcset>, which the browser picks over the
    // <img> fallback. Stripping a remote <source>'s srcset makes it fall through to
    // the <img> — which already carries the placeholder.
    if (el.tagName === 'SOURCE') {
      const srcset = el.getAttribute('srcset') || ''
      if (srcsetHasRemote(srcset)) {
        remote = true
        if (!allowRemote) el.removeAttribute('srcset')
      }
    }
  })

  // DOMPurify defaults already drop script/on*/javascript: and sanitize CSS; we
  // additionally forbid the embedding/active tags outright. `style`/`<style>` and
  // presentational attributes are kept so the layout survives.
  const clean = DOMPurify.sanitize(raw, {
    FORBID_TAGS: ['script', 'iframe', 'frame', 'object', 'embed', 'applet', 'form',
      'input', 'button', 'textarea', 'select', 'base', 'link', 'meta'],
    ADD_ATTR: ['target'],
  })
  DOMPurify.removeAllHooks()

  // CSP: no third-party network by default. Same-origin images ('self') always load —
  // these are our own resources (e.g. inline attachments rehosted to /storage/...), not
  // a tracking risk. data: is inline. Remote https: images stay gated until the user opts in.
  const imgSrc = allowRemote ? "'self' https: data:" : "'self' data:"
  const csp = `default-src 'none'; img-src ${imgSrc}; style-src 'unsafe-inline'; font-src data:`

  const html =
    '<!doctype html><html><head><meta charset="utf-8">' +
    `<meta http-equiv="Content-Security-Policy" content="${csp}">` +
    '<base target="_blank">' +
    '<style>' + FRAME_BASE_CSS + FRAME_FIXES_CSS + (props.fixes || '') + '</style></head><body>' +
    clean +
    '</body></html>'

  return { html, remote }
}

const srcdoc = ref('')

let resizeObserver: ResizeObserver | null = null
let docPoll = 0
let loadingTimer = 0
// Guards against the observer reacting to our OWN height write (which resizes the inner
// document too) and looping; released on the next frame, after that write has settled.
let remeasuring = false
// True from a rebuild until the new document's subresources settle. While loading, a re-measure
// may only GROW the frame: a just-revealed image is height:auto=0 until it decodes, so the
// content momentarily collapses — shrinking to it would flash a blank frame before the image
// grows it back. After loading, spoiler toggles shrink the frame normally.
let frameLoading = false

function rebuild() {
  if (!isHtml.value) { srcdoc.value = ''; ready.value = true; return }
  ready.value = false
  const previousDoc = frame.value?.contentDocument ?? null
  const { html, remote } = buildSrcdoc(props.body || '', effectiveShowRemote.value)
  hasRemote.value = remote
  srcdoc.value = html
  // Bind to the NEW document as soon as it swaps in, without waiting for the iframe `load`
  // event: a single hung remote image delays `load` indefinitely, and the ResizeObserver
  // (re-bound only on load) would keep watching the OLD, detached body — so a late-decoding
  // image grows the content past the stale frame height and the bottom is clipped.
  frameLoading = true
  clearTimeout(loadingTimer)
  loadingTimer = window.setTimeout(() => { frameLoading = false; measure(true); ready.value = true }, 4000)
  awaitNewDocument(previousDoc)
}

// Poll (rAF) for the freshly parsed srcdoc document — a different Document object than the
// previous one (or the iframe's initial about:blank) — then bind to its body.
function awaitNewDocument(previousDoc: Document | null) {
  cancelAnimationFrame(docPoll)
  let attempts = 0
  const poll = () => {
    const doc = frame.value?.contentDocument
    if (doc && doc !== previousDoc && doc.body && doc.URL !== 'about:blank') {
      bindToFrame()
    } else if (attempts++ < 180) {
      docPoll = requestAnimationFrame(poll)
    }
  }
  docPoll = requestAnimationFrame(poll)
}

function measure(allowShrink: boolean) {
  const el = frame.value
  const doc = el?.contentDocument
  if (!el || !doc) return
  // Hidden via the parent's v-show (display:none) → no layout, scrollHeight reads 0; skip so a
  // background re-measure can't clobber the kept height while the view mode is on the text side.
  if (el.offsetParent === null) return
  // documentElement.scrollHeight reports max(content, viewport), so reading it while the
  // frame is taller than its content (e.g. the fallback height) just echoes the frame back
  // and it can never shrink. Collapse the frame first so the viewport can't inflate the
  // reading — then scrollHeight is the true content height, including the body margins an
  // email's own <style> may set (which body.scrollHeight alone omits, causing inner scroll).
  remeasuring = true
  el.style.height = '0px'
  const content = doc.documentElement.scrollHeight
  const h = allowShrink ? content : Math.max(content, frameH.value)
  el.style.height = h + 'px'
  frameH.value = h
  requestAnimationFrame(() => { remeasuring = false })
}

// Re-measure whenever the rendered content changes size — a <details> spoiler toggled open, a
// remote image revealed and decoded late, a web-font swap. The sandbox runs no scripts, so the
// parent watches the (same-origin) inner document: a ResizeObserver on BODY (documentElement
// fills the viewport we sized, so its box never changes; body is content-sized and grows), plus
// a per-image load/error handler — a hung image delays the iframe `load`, so each image that
// does decode must re-measure on its own.
function bindToFrame() {
  const doc = frame.value?.contentDocument
  if (!doc?.body) return
  measure(!frameLoading)
  resizeObserver?.disconnect()
  resizeObserver = new ResizeObserver(() => { if (!remeasuring) measure(!frameLoading) })
  resizeObserver.observe(doc.body)
  for (const img of Array.from(doc.images)) {
    if (img.complete) continue
    const remeasure = () => measure(!frameLoading)
    img.addEventListener('load', remeasure)
    img.addEventListener('error', remeasure)
  }
  ready.value = true
}

// `sandbox` allows same-origin (so the parent can measure content height) and popups
// (so links open externally) — but NOT scripts or forms: no code can execute inside.
function onFrameLoad() {
  frameLoading = false
  clearTimeout(loadingTimer)
  ready.value = true
  nextTick(bindToFrame)
}

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  cancelAnimationFrame(docPoll)
  clearTimeout(loadingTimer)
})

watch(() => [props.body, effectiveShowRemote.value, props.fixes], rebuild, { immediate: true })

defineExpose({ isHtml })
</script>

<template>
  <div class="email-body">
    <template v-if="isHtml">
      <VAlert
        v-if="hasRemote && !effectiveShowRemote && !props.hideBar"
        class="remote-bar"
        color="warning"
        variant="tonal"
        density="compact"
        :icon="IconAlertTriangle"
      >
        <div class="remote-bar__row">
          <span class="remote-bar__text">{{ $t('common.safe_html.tracking_blocked') }}</span>
          <VBtn
            class="remote-bar__btn"
            size="small"
            variant="flat"
            color="warning"
            :prepend-icon="IconEye"
            @click="internalShowRemote = true"
          >
            {{ $t('common.safe_html.show_images') }}
          </VBtn>
        </div>
      </VAlert>
      <div class="email-frame-wrap">
        <iframe
          ref="frame"
          class="email-frame"
          :class="{ 'email-frame--loading': !ready }"
          :srcdoc="srcdoc"
          sandbox="allow-same-origin allow-popups allow-popups-to-escape-sandbox"
          referrerpolicy="no-referrer"
          :style="{ height: frameH ? frameH + 'px' : '240px' }"
          @load="onFrameLoad"
        />
        <div v-if="!ready" class="email-frame-skel">
          <VSkeletonLoader type="text@4" />
        </div>
      </div>
    </template>
    <pre v-else class="email-text">{{ body || $t('common.safe_html.empty_body') }}</pre>
  </div>
</template>

<style scoped>
.email-body { width: 100%; }

.remote-bar {
  margin-bottom: 10px;
  font-size: 12.5px;
}

/* Text + action on one line, wrapping the button below on narrow widths. */
.remote-bar__row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.remote-bar__text {
  flex: 1 1 auto;
  min-width: 0;
}

.remote-bar__btn {
  margin-left: auto;
  flex-shrink: 0;
}

.email-frame-wrap { position: relative; }

.email-frame {
  width: 100%;
  border: none;
  display: block;
  background: transparent;
  border-radius: 6px;
}

/* Keep the frame in flow (its height holds the skeleton's box) but hidden until the document is
   parsed and measured — the skeleton overlay covers it meanwhile. */
.email-frame--loading { opacity: 0; }

.email-frame-skel {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.email-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.55;
  color: var(--text);
  margin: 0;
}
</style>
