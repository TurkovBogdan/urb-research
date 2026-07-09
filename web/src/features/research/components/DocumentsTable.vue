<script setup lang="ts">
import { computed, onActivated, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconExternalLink } from '@tabler/icons-vue'

import StatusBadge from '@/components/StatusBadge.vue'
import {
  listAreaDocuments,
  listResearchDocuments,
  type SourceDocumentRow,
  type SourceStatus,
} from '../api'
import { SOURCE_STATUS_COLOR } from '../labels'

// Все найденные документы области или исследования: таблица + фильтр по статусу по клику.
// Данные ограничены (≤ несколько сотен) → грузим разом, фильтруем на клиенте (мгновенно).
const props = defineProps<{ scope: 'area' | 'research'; code: string }>()

const { t } = useI18n()
const router = useRouter()

const docs = ref<SourceDocumentRow[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const status = ref<SourceStatus | null>(null)

let current = ''

async function load() {
  const key = `${props.scope}:${props.code}`
  current = key
  loading.value = true
  error.value = null
  try {
    const rows =
      props.scope === 'area'
        ? await listAreaDocuments(props.code)
        : await listResearchDocuments(props.code)
    if (current !== key) return
    docs.value = rows
  } catch (e) {
    if (current !== key) return
    error.value = e instanceof Error ? e.message : String(e)
    docs.value = []
  } finally {
    if (current === key) loading.value = false
  }
}

onActivated(load)
watch(() => `${props.scope}:${props.code}`, () => (status.value = null))
watch(() => [props.scope, props.code], load, { immediate: true })

const STATUSES: SourceStatus[] = ['kept', 'filtered', 'pending', 'fetch_error']

const counts = computed(() => {
  const map: Record<string, number> = {}
  for (const d of docs.value) map[d.status] = (map[d.status] ?? 0) + 1
  return map
})

const visibleStatuses = computed(() => STATUSES.filter((s) => (counts.value[s] ?? 0) > 0))

const filtered = computed(() =>
  status.value ? docs.value.filter((d) => d.status === status.value) : docs.value,
)

function toggle(s: SourceStatus) {
  status.value = status.value === s ? null : s
}

function openSource(_: unknown, row: { item: SourceDocumentRow }) {
  router.push(`/research/sources/${row.item.code}`)
}

const headers = [
  { title: t('research.doc.col.title'), key: 'title', sortable: false },
  { title: t('research.doc.col.status'), key: 'status', sortable: false, width: 130 },
  { title: t('research.doc.col.relevance'), key: 'relevance', sortable: false, width: 110 },
  { title: '', key: 'open', sortable: false, width: 52 },
]
</script>

<template>
  <div>
    <div class="doc-filters">
      <VChip
        size="small"
        :variant="status === null ? 'flat' : 'tonal'"
        :color="status === null ? 'primary' : undefined"
        @click="status = null"
      >
        {{ t('research.doc.filter.all') }} · {{ docs.length }}
      </VChip>
      <VChip
        v-for="s in visibleStatuses"
        :key="s"
        size="small"
        :variant="status === s ? 'flat' : 'tonal'"
        :color="status === s ? SOURCE_STATUS_COLOR[s] : undefined"
        @click="toggle(s)"
      >
        {{ t(`research.source.status.${s}`) }} · {{ counts[s] }}
      </VChip>
    </div>

    <VAlert v-if="error" type="error" variant="tonal" density="compact" class="mb-2">
      {{ error }}
    </VAlert>

    <VDataTable
      :headers="headers"
      :items="filtered"
      :loading="loading"
      :items-per-page="20"
      item-value="code"
      density="comfortable"
      hover
      :no-data-text="t('research.doc.empty')"
      @click:row="openSource"
    >
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
        <span class="relevance">{{ item.relevance ?? '—' }}</span>
      </template>
      <template #[`item.open`]="{ item }">
        <VBtn
          v-if="item.url"
          :href="item.url"
          target="_blank"
          rel="noopener noreferrer"
          icon
          variant="text"
          size="small"
          @click.stop
        >
          <IconExternalLink :size="16" />
        </VBtn>
      </template>
    </VDataTable>
  </div>
</template>

<style scoped>
.doc-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.doc-filters .v-chip {
  cursor: pointer;
}

.doc-title {
  font-weight: 500;
}

.doc-url {
  font-size: 12px;
  color: var(--text-faint);
  word-break: break-all;
}

.relevance {
  font-family: var(--font-mono);
  color: var(--text-faint);
}
</style>
