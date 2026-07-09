<script setup lang="ts">
import { onActivated, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconRefresh, IconSearch } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import TablePaginationBar from '@/components/TablePaginationBar.vue'
import { fmtDateTime } from '@/shared/utils/date'

import { useResearchesStore } from '../stores/researches.store'
import type { ResearchListRow } from '../api'

const { t } = useI18n()
const router = useRouter()
const store = useResearchesStore()

const SEARCH_DEBOUNCE_MS = 350
const queryInput = ref(store.query)
let queryTimer: ReturnType<typeof setTimeout> | null = null

watch(queryInput, (v) => {
  if ((v ?? '') === store.query) return
  if (queryTimer) clearTimeout(queryTimer)
  queryTimer = setTimeout(() => {
    store.query = v ?? ''
    store.resetPage()
    store.load()
  }, SEARCH_DEBOUNCE_MS)
})

watch(() => store.query, (v) => {
  if (v !== queryInput.value) queryInput.value = v
})

function clearAll() {
  queryInput.value = ''
  store.clearFilters()
  store.load()
}

function toggleSort() {
  store.sortDir = store.sortDir === 'desc' ? 'asc' : 'desc'
  store.resetPage()
  store.load()
}

function openResearch(_: unknown, row: { item: ResearchListRow }) {
  router.push(`/research/researches/${row.item.code}`)
}

function onPageChange(p: number) {
  store.page = p
  store.load()
}

function onPageSizeChange(size: number) {
  store.pageSize = size
  store.resetPage()
  store.load()
}

const DESCRIPTION_MAX = 128
const truncate = (s: string, n: number) => (s.length > n ? s.slice(0, n) + '…' : s)

const headers = [
  { title: t('research.research.col.research'), key: 'title', sortable: false },
  { title: t('research.research.col.areas'), key: 'area_count', sortable: false, width: 96, align: 'end' as const },
  { title: t('research.research.col.queries'), key: 'query_count', sortable: false, width: 96, align: 'end' as const },
  { title: t('research.research.col.kept'), key: 'document_kept', sortable: false, width: 104, align: 'end' as const },
  { title: t('research.research.col.filtered'), key: 'document_filtered', sortable: false, width: 104, align: 'end' as const },
  { title: t('research.research.col.updated_at'), key: 'updated_at', sortable: false, width: 170 },
]

onActivated(() => store.load())
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('research.research.list.title')"
      :description="t('research.research.list.description')"
    >
      <template #actions>
        <VBtn variant="text" :disabled="store.loading" @click="store.load()">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': store.loading }" /></template>
          {{ t('research.action.refresh') }}
        </VBtn>
      </template>
    </PageHeader>

    <VCard variant="outlined" rounded="lg" class="filter-panel mb-3">
      <div class="filter-grid">
        <VTextField
          v-model="queryInput"
          :label="t('research.research.filter.query')"
          :prepend-inner-icon="IconSearch"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="filter-grid__search"
        />
        <VBtn variant="outlined" density="comfortable" @click="toggleSort">
          {{ store.sortDir === 'desc' ? t('research.sort.newest') : t('research.sort.oldest') }}
        </VBtn>
      </div>

      <div v-if="store.hasActiveFilters" class="filter-chips">
        <VChip v-if="store.query" size="small" closable @click:close="queryInput = ''">
          {{ store.query }}
        </VChip>
        <VBtn variant="text" size="small" @click="clearAll">
          {{ t('research.action.clear_filters') }}
        </VBtn>
      </div>
    </VCard>

    <VAlert
      v-if="store.error"
      type="error"
      variant="tonal"
      closable
      class="mb-3"
      @click:close="store.error = null"
    >
      {{ store.error }}
    </VAlert>

    <VCard variant="outlined" rounded="lg">
      <VDataTable
        :headers="headers"
        :items="store.items"
        :loading="store.loading"
        :items-per-page="store.pageSize"
        item-value="code"
        density="comfortable"
        hover
        hide-default-footer
        :no-data-text="t('research.research.list.empty')"
        @click:row="openResearch"
      >
        <template #[`item.title`]="{ item }">
          <div class="topic-cell">{{ item.title }}</div>
          <div v-if="item.description" class="desc-cell">
            {{ truncate(item.description, DESCRIPTION_MAX) }}
          </div>
        </template>
        <template #[`item.area_count`]="{ item }">
          <span class="count-cell">{{ item.area_count }}</span>
        </template>
        <template #[`item.query_count`]="{ item }">
          <span class="count-cell">{{ item.query_count }}</span>
        </template>
        <template #[`item.document_kept`]="{ item }">
          <span class="count-cell count-cell--kept">{{ item.document_kept }}</span>
        </template>
        <template #[`item.document_filtered`]="{ item }">
          <span class="count-cell count-cell--filtered">{{ item.document_filtered }}</span>
        </template>
        <template #[`item.updated_at`]="{ item }">
          <span class="date-cell">{{ fmtDateTime(item.updated_at) }}</span>
        </template>
      </VDataTable>

      <TablePaginationBar
        :page="store.page"
        :page-size="store.pageSize"
        :total="store.total"
        :page-count="store.pageCount"
        @update:page="onPageChange"
        @update:page-size="onPageSizeChange"
      />
    </VCard>
  </PageLayout>
</template>

<style scoped>
.filter-panel {
  padding: 12px;
}

.filter-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: center;
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.topic-cell {
  font-weight: 500;
  line-height: 1.4;
}

.desc-cell {
  margin-top: 2px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.45;
}

.count-cell {
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.count-cell--kept {
  color: rgb(var(--v-theme-success));
}

.count-cell--filtered {
  color: var(--text-faint);
}

.date-cell {
  white-space: nowrap;
  color: var(--text-muted);
}

@media (max-width: 720px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
