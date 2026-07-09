<script setup lang="ts">
import { ref, nextTick, onMounted, onActivated } from 'vue'
import { useRoute, onBeforeRouteLeave } from 'vue-router'
import { useLayoutStore } from '../store'
import { scrollClass } from '@/router/meta'

const layout = useLayoutStore()
const route  = useRoute()

const contentRef  = ref<HTMLElement | null>(null)
let   savedScroll = 0

// Layout meta is snapshotted NON-reactively, not read live from `route`. PageLayout
// sits inside the content <Transition mode="out-in">, which keeps the leaving page
// mounted while the global route already points at the destination — a reactive read
// would flip this (still-visible) page's padding/scroll to the next page's values
// mid-animation and cause a jerk. We re-snapshot only when this page (re)becomes
// current (mount / KeepAlive activate), so the outgoing page keeps its own classes.
const contentClass = ref<string[]>([])
function syncLayoutMeta() {
  contentClass.value = [
    'page-layout__content',
    scrollClass(route.meta.scroll),
    route.meta.padding !== false ? 'page-layout__content--padded' : '',
  ]
}

onBeforeRouteLeave(() => {
  savedScroll = contentRef.value?.scrollTop ?? 0
})

onMounted(syncLayoutMeta)
onActivated(() => {
  syncLayoutMeta()
  nextTick(() => {
    if (contentRef.value) contentRef.value.scrollTop = savedScroll
  })
})
</script>

<template>
  <div class="page-layout">

    <div v-if="layout.showTopBar && $slots.toolbar" class="page-layout__top">
      <slot name="toolbar" />
    </div>

    <div ref="contentRef" :class="contentClass">
      <slot />
    </div>

    <div v-if="layout.showBottomBar && $slots.footer" class="page-layout__bottom">
      <slot name="footer" />
    </div>

  </div>
</template>
