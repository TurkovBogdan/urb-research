<script setup lang="ts">
import { ref, useSlots, onMounted, onBeforeUnmount } from 'vue'

const props = withDefaults(defineProps<{
  empty?: boolean
  emptyText?: string
  loading?: boolean
  width?: number
  gap?: number
}>(), {
  width: 840,
  gap: 22,
})

const slots = useSlots()

const scrollEl = ref<HTMLElement | null>(null)
const contentEl = ref<HTMLElement | null>(null)

// Stay pinned to the bottom while the content grows under us — message iframes measure their
// height asynchronously after mount, so a one-shot scrollToBottom() lands too early. We keep
// re-pinning as long as the user hasn't scrolled away from the bottom (a chat's natural feel).
const STICK_THRESHOLD = 80
const stick = ref(true)
let contentObserver: ResizeObserver | null = null

function pinToBottom() {
  const el = scrollEl.value
  if (el) el.scrollTop = el.scrollHeight
}

function scrollToBottom() {
  stick.value = true
  pinToBottom()
}

function onScroll() {
  const el = scrollEl.value
  if (!el) return
  stick.value = el.scrollHeight - el.scrollTop - el.clientHeight <= STICK_THRESHOLD
}

onMounted(() => {
  if (!contentEl.value) return
  contentObserver = new ResizeObserver(() => { if (stick.value) pinToBottom() })
  contentObserver.observe(contentEl.value)
})

onBeforeUnmount(() => contentObserver?.disconnect())

defineExpose({ scrollToBottom, el: scrollEl })

// Placeholder bubbles for the loading state: alternating sides, varied widths.
const skeletonBubbles = [
  { right: false, w: '52%' },
  { right: true,  w: '66%' },
  { right: false, w: '44%' },
  { right: true,  w: '60%' },
  { right: false, w: '48%' },
]
</script>

<template>
  <div class="chat-feed-wrap">
    <div v-if="slots.toolbar && !loading" class="chat-feed__bar">
      <slot name="toolbar" />
    </div>

    <section
      ref="scrollEl"
      class="chat-feed"
      :style="{ '--chat-feed-width': `${props.width}px`, '--chat-feed-gap': `${props.gap}px` }"
      @scroll="onScroll"
    >
      <div ref="contentEl" class="chat-feed__content">
        <template v-if="loading">
          <div
            v-for="(b, i) in skeletonBubbles"
            :key="i"
            class="chat-feed-skel__row"
            :class="{ 'chat-feed-skel__row--right': b.right }"
          >
            <div class="chat-feed-skel__bubble" :style="{ width: b.w }">
              <VSkeletonLoader type="text" class="chat-feed-skel__bone chat-feed-skel__meta" />
              <VSkeletonLoader type="paragraph" class="chat-feed-skel__bone chat-feed-skel__body" />
            </div>
          </div>
        </template>

        <template v-else>
          <div v-if="empty" class="chat-feed__placeholder">
            <slot name="empty">
              <span class="chat-feed__placeholder-text">{{ emptyText }}</span>
            </slot>
          </div>
          <slot />
        </template>
      </div>
    </section>

    <div v-if="slots.composer && !loading" class="chat-feed__composer">
      <slot name="composer" />
    </div>
  </div>
</template>

<style scoped>
.chat-feed-wrap {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}

.chat-feed__bar {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 49px;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-soft);
  flex-shrink: 0;
  background: var(--surface);
}

.chat-feed__composer {
  flex-shrink: 0;
  border-top: 1px solid var(--border-soft);
  background: var(--surface);
}

.chat-feed {
  --chat-feed-gutter: 24px;
  flex: 1 1 0;
  min-height: 0;
  min-width: 0;
  overflow-y: auto;
  /* Centre a column capped at --chat-feed-width: the side padding grows to absorb the
     surplus so each row can be width:100% and still align its bubble to the column edge. */
  padding: 20px max(var(--chat-feed-gutter), calc((100% - var(--chat-feed-width, 840px)) / 2));
  background: var(--bg);
}

/* The growing content (a single ResizeObserver target for the stick-to-bottom logic) carries
   the column layout; the scroll container above only handles padding/overflow. min-height:100%
   lets the empty-state placeholder centre vertically as it did when the layout lived on .chat-feed. */
.chat-feed__content {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--chat-feed-gap);
}

.chat-feed__placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-feed__placeholder-text {
  font-size: 13px;
  color: var(--text-faint);
}

/* ── Loading skeleton ──────────────────────────────────────────────── */
/* Rows are direct feed children, so they inherit the centered column padding and gap;
   only the bone widths/box are set here. Loaders inherit colour/shimmer from the theme. */
.chat-feed-skel__row {
  display: flex;
  width: 100%;
  justify-content: flex-start;
}

.chat-feed-skel__row--right {
  justify-content: flex-end;
}

.chat-feed-skel__bubble {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-feed-skel__bone { padding: 0; background: transparent; }
.chat-feed-skel__meta { width: 38%; }
.chat-feed-skel__body { width: 100%; }
</style>
