<script setup lang="ts">
// Раздел «Источники» целиком: заголовок со счётчиком, таблица и повтор получения материала —
// построчный из меню строки и массовый из окна плана.
//
// Общий на исследование и зону — вместе с обвязкой, а не одной таблицей: страницы одинаково
// показывают источники и одинаково их чинят, и порознь эти три части разъезжались бы по мелочи
// (счётчик у одного, не у другого; тост про повтор в одном месте из двух).
//
// Строки приходят пропом: ими владеет стор страницы — по ним же идёт её поиск.
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconRefresh } from '@tabler/icons-vue'

import SectionHeader from '@/components/SectionHeader.vue'

import DocumentsTable from './DocumentsTable.vue'
import SourcesRefetchDialog from './SourcesRefetchDialog.vue'
import { useSourcesRefetch } from '../composables/useSourcesRefetch'
import type { SourceDocumentRow, SourcesLevel } from '../api'

const props = defineProps<{
  items: SourceDocumentRow[]
  loading?: boolean
  /** Чей это раздел — от него зависит, что возьмёт в починку массовый повтор. */
  level: SourcesLevel
  code: string
}>()

/** Материал добрался — страница перечитывает раздел: чинится он не построчно. */
const emit = defineEmits<{ reload: [] }>()

const { t } = useI18n()

const { refetchingCode, refetchOneSource } = useSourcesRefetch(() => emit('reload'))

// Кнопка появляется, когда на виду есть что чинить; сколько именно не получено на всём уровне,
// считает само окно — раздел показывает строки, суженные поиском по странице.
const hasBroken = computed(() => props.items.some((item) => item.status === 'error'))

const bulkOpen = ref(false)
</script>

<template>
  <SectionHeader :title="t('research.doc.section')" :count="items.length">
    <template #right>
      <VBtn
        v-if="hasBroken"
        variant="tonal"
        size="small"
        :prepend-icon="IconRefresh"
        @click="bulkOpen = true"
      >
        {{ t('research.doc.action.refetch_broken') }}
      </VBtn>
    </template>
  </SectionHeader>

  <DocumentsTable
    :items="items"
    :loading="loading"
    :refetching-code="refetchingCode"
    @refetch-one="refetchOneSource"
  />

  <SourcesRefetchDialog
    v-model="bulkOpen"
    :level="level"
    :code="code"
    @done="emit('reload')"
  />
</template>
