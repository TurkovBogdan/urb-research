<script setup lang="ts">
import { computed, watch } from 'vue'

import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import { useReferencesStore } from '../stores/references.store'

// Тело исследования/области/заметки: markdown + разрешение ссылок-кодов (TYPE@hash) в
// заголовки сущностей. Извлекает коды из текста, дозапрашивает заголовки в кэш-стор и отдаёт
// карту в рендерер (пилюля ссылки покажет заголовок вместо короткого хеша).
const props = defineProps<{ text: string }>()

const store = useReferencesStore()

const REF_RE = /(?:RESEARCH|AREA|NOTE|QUERY|SOURCE)@[0-9a-f]{22}(?![0-9a-f])/g

const codes = computed(() => {
  const found = new Set<string>()
  for (const m of props.text.matchAll(REF_RE)) found.add(m[0])
  return [...found]
})

watch(
  codes,
  (list) => {
    if (list.length) store.ensure(list)
  },
  { immediate: true },
)

const refLabels = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {}
  for (const code of codes.value) {
    const title = store.labels[code]
    if (title) map[code] = title
  }
  return map
})
</script>

<template>
  <MarkdownRenderer :text="props.text" :ref-labels="refLabels" />
</template>
