<script setup lang="ts">
/**
 * Renders a message body as literal text (not Markdown) — see shared/utils/messageText.
 * Images written as ![alt](src) become <img>; one shown smaller than its full resolution gets
 * a hover-zoom affordance whose click emits `imageClick` so the host can open a lightbox. Line
 * breaks split the text into paragraphs.
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { renderMessageText } from '@/shared/utils/messageText'

const props = defineProps<{
  text: string
  compact?: boolean
  showRemote?: boolean
}>()

const emit = defineEmits<{ imageClick: [src: string] }>()

const html = computed(() => renderMessageText(props.text, props.showRemote))

const root = ref<HTMLElement | null>(null)

// The lightbox can only enlarge an image up to its natural size, so zoom gains nothing once
// the image is already shown at (or above) full resolution — and a tiny image is never worth a
// modal even when downscaled. Only an image wider than this floor AND currently downscaled is
// offered the affordance.
const MIN_ZOOM_WIDTH = 480
// Sub-pixel layout rounding must not read as "downscaled".
const DOWNSCALE_SLACK = 2

function zoomWorthwhile(image: HTMLImageElement): boolean {
  if (!image.complete || image.naturalWidth < MIN_ZOOM_WIDTH) return false
  const displayedWidth = image.clientWidth
  if (displayedWidth === 0) return false
  return image.naturalWidth > displayedWidth + DOWNSCALE_SLACK
}

function refreshZoomable() {
  const container = root.value
  if (!container) return
  for (const image of Array.from(container.querySelectorAll('img'))) {
    image.closest('.msg-img')?.classList.toggle('msg-img--zoomable', zoomWorthwhile(image))
  }
}

// An image sharing its paragraph with text (e.g. a 👍 reaction) must sit on the text line,
// not as a block on its own row — flag it so the style middle-aligns it and drops the block
// gap. Structure-only, so it's evaluated on html change, not on resize. `.msg-img` holds no
// text of its own, so any text in the parent paragraph belongs to a sibling.
function markInlineImages() {
  const container = root.value
  if (!container) return
  for (const wrap of Array.from(container.querySelectorAll('.msg-img'))) {
    const sharesParagraphWithText = (wrap.parentElement?.textContent ?? '').trim() !== ''
    wrap.classList.toggle('msg-img--inline', sharesParagraphWithText)
  }
}

// Natural size is known only once an image decodes; displayed width changes when the bubble
// resizes — re-evaluate on both. New <img> nodes appear whenever the rendered html changes.
let resizeObserver: ResizeObserver | null = null

function bindImages() {
  const container = root.value
  if (!container) return
  markInlineImages()
  refreshZoomable()
  for (const image of Array.from(container.querySelectorAll('img'))) {
    if (!image.complete) image.addEventListener('load', refreshZoomable)
  }
}

onMounted(() => {
  resizeObserver = new ResizeObserver(refreshZoomable)
  if (root.value) resizeObserver.observe(root.value)
  bindImages()
})

watch(html, bindImages, { flush: 'post' })

onBeforeUnmount(() => resizeObserver?.disconnect())

function onClick(event: MouseEvent) {
  const wrap = (event.target as HTMLElement).closest('.msg-img--zoomable')
  const image = wrap?.querySelector('img')
  if (image) emit('imageClick', image.currentSrc || image.getAttribute('src') || '')
}
</script>

<template>
  <div ref="root" class="msg-body" :class="{ 'msg-body--compact': compact }" v-html="html" @click="onClick" />
</template>

<style scoped>
.msg-body {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text);
  overflow-wrap: anywhere;
}

.msg-body--compact {
  font-size: 13px;
  line-height: 1.6;
}

.msg-body :deep(p) {
  margin: 0 0 0.7em;
}

.msg-body :deep(p:last-child) {
  margin-bottom: 0;
}

.msg-body :deep(a) {
  color: rgb(var(--v-theme-primary));
  text-decoration: underline;
}

.msg-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  display: block;
}

.msg-body :deep(.msg-img) {
  position: relative;
  display: inline-block;
  max-width: 100%;
  margin-bottom: 6px;
}

/* Image inline with text (a reaction 👍 etc.) — centre it on the line and drop the
   block-image gap, so it reads as part of the sentence rather than a row of its own. */
.msg-body :deep(.msg-img--inline) {
  margin-bottom: 0;
  vertical-align: middle;
}

.msg-body :deep(.msg-img--zoomable) {
  cursor: pointer;
}

.msg-body :deep(.msg-img--zoomable)::after {
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

.msg-body :deep(.msg-img--zoomable):hover::after {
  opacity: 1;
}

/* Blocked remote image — a gray box with a cross, no <img> (no network request) until the
   safety toggle reveals it. Mirrors the HTML view's SafeEmailBody placeholder. */
.msg-body :deep(.msg-img-blocked) {
  display: inline-block;
  width: 120px;
  height: 90px;
  max-width: 100%;
  margin-bottom: 6px;
  border: 1px solid #ddd;
  border-radius: 6px;
  vertical-align: middle;
  background:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 24 24' fill='none' stroke='%23b0b0b0' stroke-width='2' stroke-linecap='round'%3E%3Cline x1='6' y1='6' x2='18' y2='18'/%3E%3Cline x1='18' y1='6' x2='6' y2='18'/%3E%3C/svg%3E") center / 28px no-repeat,
    #f2f2f2;
}
</style>
