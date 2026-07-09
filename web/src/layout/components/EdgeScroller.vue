<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

// Horizontal scroll wrapper with edge-shadow affordances. Drop any wide content in
// the slot (a kanban flex track, a table, …) — it scrolls on the x axis when wider
// than the viewport, and a soft shadow fades in on whichever side still hides
// content.
//
// `bleed` breaks the content out of the PageLayout padding to the screen edges:
// it cancels --page-layout-pad with a negative margin and re-adds it as inner
// padding, so the content still lines up with the page header at rest while it
// scrolls under the edges. Assumes the component lives in a PageLayout content zone.
defineProps<{ bleed?: boolean }>()

const viewport = ref<HTMLElement | null>(null)
const content = ref<HTMLElement | null>(null)
const atStart = ref(true)
const atEnd = ref(true)

function update() {
  const el = viewport.value
  if (!el) return
  const { scrollLeft, scrollWidth, clientWidth } = el
  // 2px tolerance — sub-pixel widths never resolve to an exact equality.
  atStart.value = scrollLeft <= 2
  atEnd.value = scrollLeft + clientWidth >= scrollWidth - 2
}

// One observer for the viewport (clientWidth) and the content (its width), so the
// affordance re-evaluates on resize and when the content grows/shrinks.
let ro: ResizeObserver | null = null
onMounted(() => {
  update()
  ro = new ResizeObserver(update)
  if (viewport.value) ro.observe(viewport.value)
  if (content.value) ro.observe(content.value)
})
onBeforeUnmount(() => ro?.disconnect())
</script>

<template>
  <div class="edge-scroller" :class="{ 'show-left': !atStart, 'show-right': !atEnd, 'edge-scroller--bleed': bleed }">
    <div ref="viewport" class="edge-scroller__viewport" @scroll.passive="update">
      <div ref="content" class="edge-scroller__content">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
.edge-scroller {
  position: relative;
  /* Clip the outer half of each edge shadow's spill (it's cast symmetrically). */
  overflow: hidden;
}

.edge-scroller__viewport {
  overflow-x: auto;
  padding-top: 10px;
  padding-bottom: 10px;
}

.edge-scroller__content {
  /* Size to the content so it overflows (enabling scroll) and the ResizeObserver
     sees width changes. */
  width: max-content;
}

/* Full-bleed: cancel the PageLayout content padding with a negative margin so the
   content reaches the screen edges, then re-add it as inner padding so it still
   lines up with the page header at rest and keeps a trailing gap at the end.
   Mirrors the layout's responsive --page-layout-pad fallbacks (24px / 16px). */
.edge-scroller--bleed {
  margin-inline: calc(-1 * var(--page-layout-pad, 24px));
}
.edge-scroller--bleed .edge-scroller__content {
  padding-inline: var(--page-layout-pad, 24px);
}
@media (max-width: 959px) {
  .edge-scroller--bleed {
    margin-inline: calc(-1 * var(--page-layout-pad, 16px));
  }
  .edge-scroller--bleed .edge-scroller__content {
    padding-inline: var(--page-layout-pad, 16px);
  }
}

/* Inner edge shadows — ::before = left, ::after = right. A thin caster parked just
   OUTSIDE each edge throws a blurred box-shadow; the overflow:hidden clips the
   caster and its outer half, so only the inward blur shows as a soft edge shadow.
   top/bottom insets feather the vertical ends (and clear a bottom scrollbar).
   transform: translateZ(0) promotes each to its own compositing layer so the blur
   rasterizes the same regardless of the content's sub-pixel offset (otherwise it
   looks harder when shifted by a sidebar, softer at the screen edge — a subpixel
   artifact). pointer-events:none; z-index above content. Fade in per side. */
.edge-scroller::before,
.edge-scroller::after {
  content: '';
  position: absolute;
  top: 5px;
  bottom: 15px;
  width: 10px;
  z-index: 1;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.18s ease;
  transform: translateZ(0);
  backface-visibility: hidden;
}

.edge-scroller::before {
  left: -10px;
  box-shadow: 0 0 14px 0 rgba(0, 0, 0, 0.45);
}
.edge-scroller::after {
  right: -10px;
  box-shadow: 0 0 14px 0 rgba(0, 0, 0, 0.45);
}

.edge-scroller.show-left::before { opacity: 1; }
.edge-scroller.show-right::after { opacity: 1; }
</style>

<!-- Global (unscoped): a full-bleed scroller can't reach the right edge while the
     scrolling page reserves a scrollbar gutter (.scroll-y sets scrollbar-gutter:
     stable) AND clips horizontally (overflow-x: hidden). When a bled scroller is on
     the page, drop the reserved gutter so it reaches the true screen edge. -->
<style>
.page-layout__content:has(.edge-scroller--bleed) {
  scrollbar-gutter: auto;
}
</style>
