<script setup lang="ts">
// Раздел с основным текстом артефакта: заголовок и карточка с markdown под ним.
//
// Общий на исследование и зону: это один и тот же раздел — самое длинное чтение страницы, — и
// порознь у него разъезжались бы поля карточки и вид пустого места. Отличаются только подписи,
// поэтому они приходят пропами: у исследования это «Исследование», у зоны — её результат.
import SectionHeader from '@/components/SectionHeader.vue'
import type { HeadingAnchor } from '@/components/markdown/render'

import ResearchBody from './ResearchBody.vue'

defineProps<{
  title: string
  text: string
  /** Текст на месте ненаписанного тела. */
  empty: string
}>()

/** Оглавление тела — странице для боковой навигации. */
const emit = defineEmits<{ headings: [items: HeadingAnchor[]] }>()
</script>

<template>
  <SectionHeader :title="title" />
  <VCard variant="outlined" rounded="lg" class="mb-4">
    <VCardText class="body-card">
      <ResearchBody v-if="text" :text="text" @headings="emit('headings', $event)" />
      <div v-else class="body-card__empty text-medium-emphasis">{{ empty }}</div>
    </VCardText>
  </VCard>
</template>

<style scoped>
/* Сверху и снизу воздуха больше, чем по бокам: текст читают страницами, и на кромке карточки
   первая строка выглядит обрезанной. По горизонтали добавлять нечего — там ширину держит сама
   зона чтения. */
.body-card {
  padding: 28px 16px;
}

.body-card__empty {
  padding: 16px 0;
  text-align: center;
}
</style>
