<script setup lang="ts">
// Источники — карточка с панелью фильтров и таблицей. Строки приходят пропом: ими владеет стор
// страницы (по ним же ищет глобальный поиск деталки), а здесь остаются показ и собственные
// фильтры. Данные ограничены (≤ несколько сотен), поэтому фильтрация, сортировка и
// постраничность — клиентские, мгновенные и без запроса на каждое движение.
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  IconCheck,
  IconCopy,
  IconDotsVertical,
  IconExternalLink,
  IconFileText,
  IconRefresh,
  IconSearch,
} from '@tabler/icons-vue'

import StatusBadge from '@/components/StatusBadge.vue'
import TablePaginationBar from '@/components/TablePaginationBar.vue'
import { useClipboard } from '@/composables/useClipboard'
import { fmtDateTime } from '@/shared/utils/date'

import { type SourceDocumentRow, type SourceStatus } from '../api'
import { SOURCE_STATUS_COLOR } from '../labels'

const props = defineProps<{
  items: SourceDocumentRow[]
  loading?: boolean
  /** Код строки, материал которой сейчас качается. */
  refetchingCode?: string | null
}>()

// Само действие принадлежит странице: у неё свой стор источников, который она и перечитывает.
const emit = defineEmits<{ refetchOne: [code: string] }>()

const { t } = useI18n()
const router = useRouter()
const { copy, isCopied } = useClipboard()

// Полосы релевантности вместо десяти отдельных значений: у балла спрашивают «стоит ли читать»,
// а не «ровно ли восемь». Отдельная полоса — «не оценён» (relevance = null).
type RelevanceBand = 'high' | 'medium' | 'low' | 'unrated'

const RELEVANCE_BANDS: Record<RelevanceBand, (relevance: number | null) => boolean> = {
  high: (relevance) => relevance !== null && relevance >= 8,
  medium: (relevance) => relevance !== null && relevance >= 4 && relevance <= 7,
  low: (relevance) => relevance !== null && relevance <= 3,
  unrated: (relevance) => relevance === null,
}

const STATUSES: SourceStatus[] = ['kept', 'filtered', 'pending', 'error']

const query = ref('')
const status = ref<SourceStatus | null>(null)
const relevanceBand = ref<RelevanceBand | null>(null)
const page = ref(1)
const pageSize = ref(25)

function clearFilters() {
  query.value = ''
  status.value = null
  relevanceBand.value = null
  page.value = 1
}

const counts = computed(() => {
  const map: Record<string, number> = {}
  for (const doc of props.items) map[doc.status] = (map[doc.status] ?? 0) + 1
  return map
})

// В списке статусов только встречающиеся: пустой пункт обещает выборку, которой нет.
const statusItems = computed(() =>
  STATUSES.filter((s) => (counts.value[s] ?? 0) > 0).map((s) => ({
    title: `${t(`research.source.status.${s}`)} · ${counts.value[s]}`,
    value: s,
  })),
)

const relevanceItems = computed(() =>
  (Object.keys(RELEVANCE_BANDS) as RelevanceBand[]).map((band) => ({
    title: t(`research.doc.relevance.${band}`),
    value: band,
  })),
)

// Ищем по тому, что видно в строке, — заголовку и адресу. Тела и заметки в таблице нет, и
// попадание в невидимый текст читалось бы как сбой фильтра. (Глобальный поиск деталки —
// наоборот, смотрит и в разбор источника: там вопрос «где про X», а не «сузь список».)
function matchesRow(doc: SourceDocumentRow, needle: string): boolean {
  return `${doc.title ?? ''} ${doc.url ?? ''}`.toLowerCase().includes(needle)
}

const filtered = computed(() => {
  const needle = query.value.trim().toLowerCase()
  const band = relevanceBand.value
  return props.items.filter((doc) => {
    if (status.value && doc.status !== status.value) return false
    if (band && !RELEVANCE_BANDS[band](doc.relevance)) return false
    return !needle || matchesRow(doc, needle)
  })
})

const hasActiveFilters = computed(
  () => !!query.value || status.value !== null || relevanceBand.value !== null,
)

const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))

// Схлопнувшаяся выборка не должна оставлять человека на несуществующей странице.
watch(filtered, () => {
  if (page.value > pageCount.value) page.value = 1
})

const headers = [
  { title: '', key: 'actions', sortable: false, width: 84 },
  {
    title: t('research.doc.col.title'),
    key: 'title',
    // Сортируем по тому же тексту, что и показываем: без заголовка в ячейке стоит адрес.
    value: (item: SourceDocumentRow) => item.title || item.url || '',
  },
  { title: t('research.doc.col.status'), key: 'status', width: 150 },
  { title: t('research.doc.col.relevance'), key: 'relevance', width: 140, align: 'end' as const },
  { title: t('research.doc.col.updated_at'), key: 'updated_at', width: 170 },
]

const sourcePath = (code: string) => `/research/sources/${code}`

function openSource(_: unknown, row: { item: SourceDocumentRow }) {
  router.push(sourcePath(row.item.code))
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
}
</script>

<template>
  <VCard variant="outlined" rounded="lg">
    <div class="doc-filters">
      <VTextField
        v-model="query"
        :label="t('research.doc.filter.query')"
        :prepend-inner-icon="IconSearch"
        variant="outlined"
        density="comfortable"
        hide-details
        clearable
        class="doc-filters__search"
      />
      <VSelect
        v-model="status"
        :items="statusItems"
        :label="t('research.doc.filter.status')"
        variant="outlined"
        density="comfortable"
        hide-details
        clearable
      />
      <VSelect
        v-model="relevanceBand"
        :items="relevanceItems"
        :label="t('research.doc.filter.relevance')"
        variant="outlined"
        density="comfortable"
        hide-details
        clearable
      />
    </div>

    <div v-if="hasActiveFilters" class="doc-filters__chips">
      <VChip v-if="query" size="small" closable @click:close="query = ''">{{ query }}</VChip>
      <VChip v-if="status" size="small" closable @click:close="status = null">
        {{ t(`research.source.status.${status}`) }}
      </VChip>
      <VChip v-if="relevanceBand" size="small" closable @click:close="relevanceBand = null">
        {{ t(`research.doc.relevance.${relevanceBand}`) }}
      </VChip>
      <VBtn variant="text" size="small" @click="clearFilters">
        {{ t('research.action.clear_filters') }}
      </VBtn>
    </div>

    <VDivider />

    <VDataTable
      v-model:page="page"
      :headers="headers"
      :items="filtered"
      :loading="loading"
      :items-per-page="pageSize"
      item-value="code"
      density="comfortable"
      hover
      hide-default-footer
      :no-data-text="t('research.doc.empty')"
      @click:row="openSource"
    >
      <!-- Действия строки: клик по ним не должен уводить на карточку источника. -->
      <template #[`item.actions`]="{ item }">
        <div class="doc-actions" @click.stop>
          <VMenu location="bottom start" :offset="4">
            <template #activator="{ props: menu }">
              <VBtn
                v-bind="menu"
                icon
                variant="text"
                class="doc-actions__btn"
                :title="t('research.doc.action.actions')"
              >
                <IconDotsVertical :size="16" :stroke-width="1.6" />
              </VBtn>
            </template>

            <VList density="compact">
              <VListItem :prepend-icon="IconFileText" :to="sourcePath(item.code)">
                <VListItemTitle>{{ t('research.doc.action.open_card') }}</VListItemTitle>
              </VListItem>
              <VListItem
                :prepend-icon="IconExternalLink"
                :disabled="!item.url"
                :href="item.url ?? undefined"
                target="_blank"
                rel="noopener noreferrer"
              >
                <VListItemTitle>{{ t('research.doc.action.open_source') }}</VListItemTitle>
              </VListItem>

              <VDivider class="my-1" />

              <!-- Работает в любом статусе: материал качается заново, поэтому прежний разбор
                   снимается и источник возвращается в очередь. -->
              <VListItem
                :prepend-icon="IconRefresh"
                :disabled="props.refetchingCode === item.code"
                @click="emit('refetchOne', item.code)"
              >
                <VListItemTitle>{{ t('research.doc.action.refetch_one') }}</VListItemTitle>
              </VListItem>
            </VList>
          </VMenu>

          <VBtn
            icon
            variant="text"
            class="doc-actions__btn"
            :title="isCopied(item.code) ? t('research.doc.action.copied') : t('research.doc.action.copy')"
            @click="copy(item.code)"
          >
            <IconCheck
              v-if="isCopied(item.code)"
              :size="16"
              :stroke-width="1.6"
              class="doc-actions__btn--done"
            />
            <IconCopy v-else :size="16" :stroke-width="1.6" />
          </VBtn>
        </div>
      </template>

      <template #[`item.title`]="{ item }">
        <div class="doc-title">{{ item.title || item.url }}</div>
        <div v-if="item.url" class="doc-url">{{ item.url }}</div>
      </template>
      <template #[`item.status`]="{ item }">
        <StatusBadge :color="SOURCE_STATUS_COLOR[item.status]">
          {{ t(`research.source.status.${item.status}`) }}
        </StatusBadge>
      </template>
      <template #[`item.relevance`]="{ item }">
        <span class="doc-relevance">{{ item.relevance ?? '—' }}</span>
      </template>
      <template #[`item.updated_at`]="{ item }">
        <span class="doc-date">{{ fmtDateTime(item.updated_at) }}</span>
      </template>
    </VDataTable>

    <TablePaginationBar
      :page="page"
      :page-size="pageSize"
      :total="filtered.length"
      :page-count="pageCount"
      @update:page="page = $event"
      @update:page-size="onPageSizeChange"
    />
  </VCard>
</template>

<style scoped>
.doc-filters {
  display: grid;
  grid-template-columns: 1fr 200px 200px;
  gap: 12px;
  padding: 12px;
}

@media (max-width: 899px) {
  .doc-filters {
    grid-template-columns: 1fr;
  }
}

.doc-filters__chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 0 12px 12px;
}

/* Обе кнопки — одна группа управления, поэтому между собой они теснее, чем до края ячейки. */
.doc-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

/* Коробка задана здесь, а не пропсами `size`/`density`: у иконочной кнопки Vuetify считает сторону
   как `--v-btn-height + 12px`, а density правит только высоту. Незаслоённое правило перебивает
   `@layer vuetify-components` (см. docs/frontend/vuetify-css-patterns). */
.doc-actions__btn {
  width: 26px;
  min-width: 26px;
  height: 26px;
  color: var(--text-faint);
}

.doc-actions__btn:hover { color: var(--text); }

.doc-actions__btn--done { color: var(--success); }

.doc-title {
  font-weight: 500;
}

.doc-url {
  font-size: 12px;
  color: var(--text-faint);
  word-break: break-all;
}

.doc-relevance {
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.doc-date {
  white-space: nowrap;
  color: var(--text-muted);
}
</style>
