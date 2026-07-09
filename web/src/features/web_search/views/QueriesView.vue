<script setup lang="ts">
import { computed, onActivated, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconPlus, IconRefresh, IconSearch } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import TablePaginationBar from '@/components/TablePaginationBar.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { fmtDateTime, fmtRelative } from '@/shared/utils/date'

import { useQueriesStore } from '../stores/queries.store'
import { QUERY_STATUSES, QUERY_STATUS_COLOR, SEARCH_PROVIDERS } from '../labels'
import type { QueryRow, QueryStatus } from '../api'

const { t } = useI18n()
const router = useRouter()
const store = useQueriesStore()

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

const statusItems = QUERY_STATUSES.map((s) => ({
  value: s,
  title: t(`web_search.query.status.${s}`),
}))

const searchEngineItems = SEARCH_PROVIDERS.map((p) => ({ value: p, title: p }))

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

// ── создание запроса (fire-and-forget) ──────────────────────────────────────
const dialog = ref(false)
const createError = ref<string | null>(null)
const createForm = ref({ query: '', pages: 10, searchEngine: '', fetchEngine: '' })

const searchEngineOptions = computed(() =>
  (store.engines?.search ?? []).map((c) => ({ value: c, title: c })),
)
const fetchEngineOptions = computed(() =>
  (store.engines?.fetch ?? []).map((c) => ({ value: c, title: c })),
)
const canSubmit = computed(() => createForm.value.query.trim().length > 0)

function openCreate() {
  createError.value = null
  createForm.value = {
    query: '',
    pages: 10,
    searchEngine: store.engines?.searchDefault ?? '',
    fetchEngine: store.engines?.fetchDefault ?? '',
  }
  dialog.value = true
}

async function submitCreate() {
  if (!canSubmit.value) return
  createError.value = null
  try {
    await store.create({
      query: createForm.value.query.trim(),
      search_engine: createForm.value.searchEngine || null,
      fetch_engine: createForm.value.fetchEngine || null,
      max_results: createForm.value.pages,
    })
    dialog.value = false
  } catch (e) {
    createError.value = e instanceof Error ? e.message : String(e)
  }
}

function openQuery(_: unknown, row: { item: QueryRow }) {
  router.push(`/web-search/queries/${encodeURIComponent(row.item.code)}`)
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
  { title: t('web_search.query.col.query'), key: 'query', sortable: true },
  { title: t('web_search.query.col.search_engine'), key: 'search_engine', sortable: true, width: 140 },
  { title: t('web_search.query.col.fetch_engine'), key: 'fetch_engine', sortable: true, width: 140 },
  { title: t('web_search.query.col.status'), key: 'status', sortable: true, width: 130 },
  { title: t('web_search.query.col.created_at'), key: 'created_at', sortable: true, width: 190 },
]

onActivated(() => {
  store.load()
  store.loadEngines()
})
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('web_search.query.list.title')"
      :description="t('web_search.query.list.description')"
    >
      <template #actions>
        <VBtn color="primary" variant="flat" @click="openCreate">
          <template #prepend><IconPlus :size="16" /></template>
          {{ t('web_search.action.create') }}
        </VBtn>
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
          :label="t('web_search.query.filter.query')"
          :prepend-inner-icon="IconSearch"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          class="filter-grid__search"
        />
        <VSelect
          v-model="store.searchEngine"
          :items="searchEngineItems"
          :label="t('web_search.query.filter.search_engine')"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          :chips="false"
          @update:model-value="onFilterChange"
        />
        <VSelect
          v-model="store.status"
          :items="statusItems"
          :label="t('web_search.query.filter.status')"
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
          v-if="store.searchEngine"
          size="small"
          closable
          @click:close="store.searchEngine = null; onFilterChange()"
        >
          {{ store.searchEngine }}
        </VChip>
        <VChip
          v-if="store.status"
          size="small"
          closable
          @click:close="store.status = null; onFilterChange()"
        >
          {{ t(`web_search.query.status.${store.status as QueryStatus}`) }}
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
        :no-data-text="t('web_search.query.list.empty')"
        @click:row="openQuery"
        @update:sort-by="onUpdateSortBy"
      >
        <template #[`item.query`]="{ item }">
          <span class="request-cell">{{ item.query }}</span>
        </template>
        <template #[`item.status`]="{ item }">
          <StatusBadge :color="QUERY_STATUS_COLOR[item.status]">
            {{ t(`web_search.query.status.${item.status}`) }}
          </StatusBadge>
        </template>
        <template #[`item.created_at`]="{ item }">
          <div class="date-cell">{{ fmtDateTime(item.created_at) }}</div>
          <div class="date-rel">{{ fmtRelative(item.created_at) }}</div>
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

    <VDialog v-model="dialog" max-width="560">
      <VCard rounded="lg">
        <VCardTitle>{{ t('web_search.query.create.title') }}</VCardTitle>
        <VCardText>
          <VAlert
            v-if="createError"
            type="error"
            variant="tonal"
            density="compact"
            class="mb-3"
          >
            {{ createError }}
          </VAlert>
          <VTextarea
            v-model="createForm.query"
            :label="t('web_search.query.create.query')"
            :placeholder="t('web_search.query.create.query_ph')"
            variant="outlined"
            density="comfortable"
            rows="2"
            auto-grow
            autofocus
            hide-details
            @keydown.enter.exact.prevent="submitCreate"
          />
          <div class="create-grid">
            <VSelect
              v-model="createForm.searchEngine"
              :items="searchEngineOptions"
              :label="t('web_search.query.field.search_engine')"
              variant="outlined"
              density="comfortable"
              hide-details
              :chips="false"
            />
            <VSelect
              v-model="createForm.fetchEngine"
              :items="fetchEngineOptions"
              :label="t('web_search.query.field.fetch_engine')"
              variant="outlined"
              density="comfortable"
              hide-details
              :chips="false"
            />
            <VTextField
              v-model.number="createForm.pages"
              type="number"
              :min="1"
              :max="50"
              :label="t('web_search.query.create.pages')"
              variant="outlined"
              density="comfortable"
              hide-details
            />
          </div>
        </VCardText>
        <VCardActions>
          <VSpacer />
          <VBtn variant="text" @click="dialog = false">
            {{ t('web_search.query.create.cancel') }}
          </VBtn>
          <VBtn
            color="primary"
            variant="flat"
            :disabled="!canSubmit"
            :loading="store.creating"
            @click="submitCreate"
          >
            {{ t('web_search.query.create.submit') }}
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </PageLayout>
</template>

<style scoped>
.filter-panel {
  padding: 12px;
}

.filter-grid {
  display: grid;
  grid-template-columns: 1fr minmax(0, 200px) minmax(0, 200px);
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

.request-cell {
  font-weight: 500;
}

.create-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
}

.create-grid > :last-child {
  grid-column: 1 / -1;
  max-width: 160px;
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
