<script setup lang="ts">
// Раздел «Источники» целиком: заголовок со счётчиком, таблица и повтор получения материала.
//
// Общий на исследование и зону — вместе с обвязкой, а не одной таблицей: страницы одинаково
// показывают источники и одинаково их чинят, и порознь эти три части разъезжались бы по мелочи
// (счётчик у одного, не у другого; тост про повтор в одном месте из двух).
//
// Строки приходят пропом: ими владеет стор страницы — по ним же идёт её поиск.
import { useI18n } from 'vue-i18n'

import SectionHeader from '@/components/SectionHeader.vue'

import DocumentsTable from './DocumentsTable.vue'
import { useSourcesRefetch } from '../useSourcesRefetch'
import type { SourceDocumentRow } from '../api'

defineProps<{
  items: SourceDocumentRow[]
  loading?: boolean
}>()

/** Материал добрался — страница перечитывает раздел: чинится он не построчно. */
const emit = defineEmits<{ reload: [] }>()

const { t } = useI18n()

const { refetchingCode, refetchOneSource } = useSourcesRefetch(() => emit('reload'))
</script>

<template>
  <SectionHeader :title="t('research.doc.section')" :count="items.length" />
  <DocumentsTable
    :items="items"
    :loading="loading"
    :refetching-code="refetchingCode"
    @refetch-one="refetchOneSource"
  />
</template>
