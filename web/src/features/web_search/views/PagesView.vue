<script setup lang="ts">
import { computed, onActivated, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconRefresh, IconSearch } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import TablePaginationBar from '@/components/TablePaginationBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { fmtDateTime, fmtRelative } from '@/shared/utils/date'

import { usePagesStore } from '../stores/pages.store'
import { PAGE_STATUSES, PAGE_STATUS_COLOR } from '../labels'
import type { WebSearchPageRow, PageStatus } from '../api'

const { t } = useI18n()
const router = useRouter()
const store = usePagesStore()

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

const statusItems = PAGE_STATUSES.map((s) => ({
  value: s,
  title: t(`web_search.page.status.${s}`),
}))

function onFilterChange() {
  store.resetPage()
  store.load()
}

function clearAll() {
  queryInput.value = ''
  store.clearFilters()
  store.load()
}

interface SortItem { key: string; order: 'asc' | 'desc' }

function onUpdateSortBy(value: SortItem[]) {
  const first = value[0]
  if (!first) return
  store.sortBy = first.key
  store.sortDir = first.order
  store.resetPage()
  store.load()
}

const tableSortBy = computed(() => [{ key: store.sortBy, order: store.sortDir }])

function openPage(_: unknown, row: { item: WebSearchPageRow }) {
  router.push(`/web-search/pages/${encodeURIComponent(row.item.code)}`)
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

const headers = [
  { title: t('web_search.page.col.url'), key: 'url', sortable: true },
  { title: t('web_search.page.col.domain'), key: 'domain', sortable: true, width: 200 },
  { title: t('web_search.page.col.status'), key: 'status', sortable: true, width: 130 },
  { title: t('web_search.page.col.created_at'), key: 'created_at', sortable: true, width: 190 },
  { title: t('web_search.page.col.fetched_at'), key: 'fetched_at', sortable: true, width: 190 },
]

onActivated(() => store.load())
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('web_search.page.list.title')"
      :description="t('web_search.page.list.description')"
    >
      <template #actions>
        <VBtn variant="text" :disabled="store.loading" @click="store.load()">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': store.loading }" /></template>
          {{ t('web_search.action.refresh') }}
        </VBtn>
      </template>
    </PageHeader>

    <VCard variant="outlined" rounded="lg" class="filter-panel mb-3">
      <div class="filter-grid">
        <VTextField
          v-model="queryInput"
          :label="t('web_search.page.filter.query')"
          :prepend-inner-icon="IconSearch"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="filter-grid__search"
        />
        <VSelect
          v-model="store.status"
          :items="statusItems"
          :label="t('web_search.page.filter.status')"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          :chips="false"
          @update:model-value="onFilterChange"
        />
      </div>

      <div v-if="store.hasActiveFilters" class="filter-chips">
        <VChip v-if="store.query" size="small" closable @click:close="queryInput = ''">
          {{ store.query }}
        </VChip>
        <VChip
          v-if="store.status"
          size="small"
          closable
          @click:close="store.status = null; onFilterChange()"
        >
          {{ t(`web_search.page.status.${store.status as PageStatus}`) }}
        </VChip>
        <VChip
          v-if="store.domain"
          size="small"
          closable
          @click:close="store.domain = null; onFilterChange()"
        >
          {{ store.domain }}
        </VChip>
        <VBtn variant="text" size="small" @click="clearAll">
          {{ t('web_search.action.clear_filters') }}
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
        :sort-by="tableSortBy"
        must-sort
        item-value="code"
        density="comfortable"
        hover
        hide-default-footer
        :no-data-text="t('web_search.page.list.empty')"
        @click:row="openPage"
        @update:sort-by="onUpdateSortBy"
      >
        <template #[`item.url`]="{ item }">
          <span class="url-cell">{{ item.url }}</span>
        </template>
        <template #[`item.domain`]="{ item }">
          <span class="domain-cell">{{ item.domain ?? '—' }}</span>
        </template>
        <template #[`item.status`]="{ item }">
          <StatusBadge :color="PAGE_STATUS_COLOR[item.status]">
            {{ t(`web_search.page.status.${item.status}`) }}
          </StatusBadge>
        </template>
        <template #[`item.created_at`]="{ item }">
          <div class="date-cell">{{ fmtDateTime(item.created_at) }}</div>
          <div class="date-rel">{{ fmtRelative(item.created_at) }}</div>
        </template>
        <template #[`item.fetched_at`]="{ item }">
          <template v-if="item.fetched_at">
            <div class="date-cell">{{ fmtDateTime(item.fetched_at) }}</div>
            <div class="date-rel">{{ fmtRelative(item.fetched_at) }}</div>
          </template>
          <span v-else class="date-cell">—</span>
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
  grid-template-columns: 1fr minmax(0, 200px);
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

.url-cell {
  font-weight: 500;
  word-break: break-all;
}

.domain-cell {
  color: var(--text-muted);
}

.date-cell {
  white-space: nowrap;
  color: var(--text-muted);
}

.date-rel {
  white-space: nowrap;
  font-size: 12px;
  color: var(--text-faint);
}

@media (max-width: 720px) {
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
