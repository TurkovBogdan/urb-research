<script setup lang="ts">
import { ref, nextTick, onMounted, onActivated, watch } from 'vue'
import { useRoute, onBeforeRouteLeave } from 'vue-router'
import { useLayoutStore } from '../store'
import { scrollClass } from '@/router/meta'
import { isBackNavigation } from '@/router/scroll'
import { restoreScrollTop } from '@/composables/useScrollRestore'

// `nested` ставит рамка, внутри которой живёт вложенный `RouterView` (`DetailShell`): она
// переживает смену адреса, и потому обязана сама начать новую страницу — снять её метаданные и
// увести прокрутку в начало. Обычная страница этого не делает: её раскладка уходит вместе с ней.
const props = withDefaults(defineProps<{ nested?: boolean }>(), { nested: false })

const layout = useLayoutStore()
const route  = useRoute()

const contentRef = ref<HTMLElement | null>(null)

// Позиция чтения принадлежит адресу, а не вьюхе: KeepAlive держит ОДИН экземпляр на маршрут, и
// два исследования подряд делят его вместе с этой позицией — без ключа второе открывалось бы на
// прокрутке первого.
const scrollByPath = new Map<string, number>()

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
  scrollByPath.set(route.fullPath, contentRef.value?.scrollTop ?? 0)
})

// Возврат по истории (кнопка «назад» со страницы зоны или заметки) возвращает и позицию чтения:
// человек продолжает там, где отвлёкся. Обычный переход — открытие документа, а не продолжение,
// поэтому список и полка приводят в начало, даже если это исследование уже читали.
// «Вернули или пришли» спрашиваем В `nextTick`, а не сразу: роутер отвечает на это в обработчике
// прокрутки, а тот запускается тиком позже смены адреса. Прочитанный сразу ответ был бы от
// ПРЕДЫДУЩЕГО перехода, и возврат открывался бы с начала (у страниц-рамок, которые ждут анимации
// ухода, разница не видна — у вложенных видна сразу).
function startPage(path: string) {
  syncLayoutMeta()
  nextTick(() => {
    const restored = isBackNavigation() ? scrollByPath.get(path) ?? 0 : 0
    if (contentRef.value) restoreScrollTop(contentRef.value, restored)
  })
}

onMounted(syncLayoutMeta)
onActivated(() => startPage(route.fullPath))

// Вложенная рамка не активируется заново — вместо неё меняется вложенный адрес, и это тот же
// самый момент: позиция чтения уходящей страницы запоминается, пришедшая открывается сначала.
watch(() => route.fullPath, (path, previous) => {
  if (!props.nested) return
  scrollByPath.set(previous, contentRef.value?.scrollTop ?? 0)
  startPage(path)
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
