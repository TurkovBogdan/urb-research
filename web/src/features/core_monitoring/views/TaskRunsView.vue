<script setup lang="ts">
import { computed, onActivated, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconRefresh } from '@tabler/icons-vue'
import { fmtDateTimeSec, fmtRelative, fmtDuration, fmtTimeSec } from '@/shared/utils/date'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import TablePaginationBar from '@/components/TablePaginationBar.vue'
import { useTaskText } from '../taskText'
import {
  fetchTask,
  fetchTaskRuns,
  fetchTaskRunLogs,
  type TaskInfo,
  type TaskRunInfo,
  type TaskRunLog,
} from '../api'

const props = defineProps<{ module: string; code: string }>()
const { t } = useI18n()
const { taskName, taskDescription } = useTaskText()

const task = ref<TaskInfo | null>(null)
const runs = ref<TaskRunInfo[]>([])
const total = ref(0)
const loading = ref(true)        // первичная загрузка / смена задачи → скелет
const refreshing = ref(false)    // фоновое обновление (фильтр/сортировка/страница/кнопка)
const error = ref<string | null>(null)

const page = ref(1)
const pageSize = ref(25)
const statusFilter = ref<TaskRunInfo['status'] | null>(null)
const sortBy = ref<string>('started_at')
const sortDir = ref<'asc' | 'desc'>('desc')

const PAGE_SIZES = [10, 25, 50, 100, 200]
// running/success/error — значения enum статуса (оставляем литералами); null = все (clearable).
const STATUS_OPTIONS: { title: string; value: TaskRunInfo['status'] }[] = [
  { title: 'running', value: 'running' },
  { title: 'success', value: 'success' },
  { title: 'error',   value: 'error' },
]

const STATUS_COLOR: Record<TaskRunInfo['status'], string> = {
  running: 'info',
  success: 'success',
  error: 'error',
}

const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

async function loadRuns() {
  refreshing.value = true
  try {
    const r = await fetchTaskRuns(props.module, props.code, {
      limit: pageSize.value,
      offset: (page.value - 1) * pageSize.value,
      status: statusFilter.value,
      sortBy: sortBy.value,
      sortDir: sortDir.value,
    })
    runs.value = r.items
    total.value = r.total
    // При обновлении страницы/фильтра/сортировки инвалидируем кэш логов и схлопываем строки.
    expanded.value = []
    logsByRun.value = {}
    logsError.value = {}
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    refreshing.value = false
  }
}

// Полная (пере)загрузка деталки. Деталка НЕ кэшируется: на каждый вход показываем
// скелет и тянем свежие данные, чтобы не «подвисали» данные предыдущей задачи.
async function reload() {
  loading.value = true
  error.value = null
  task.value = null
  runs.value = []
  total.value = 0
  page.value = 1
  expanded.value = []
  logsByRun.value = {}
  logsError.value = {}
  try {
    task.value = await fetchTask(props.module, props.code)
    await loadRuns()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

onActivated(reload)
watch([() => props.module, () => props.code], reload)

// ── filter / pagination handlers (явные, без watch — чтобы не было двойной загрузки)
function onFilterChange(value: TaskRunInfo['status'] | null) {
  statusFilter.value = value
  page.value = 1
  loadRuns()
}

function onPageChange(p: number) {
  page.value = p
  loadRuns()
}

function onPageSizeChange(size: number) {
  pageSize.value = size
  page.value = 1
  loadRuns()
}

// ── server-side sort ────────────────────────────────────────────────────────
interface SortItem { key: string; order: 'asc' | 'desc' }

function onUpdateSortBy(value: SortItem[] | string[]) {
  const first = value[0] as SortItem | string | undefined
  if (!first) return
  if (typeof first === 'string') {
    sortBy.value = first
  } else {
    sortBy.value = first.key
    sortDir.value = first.order
  }
  page.value = 1
  loadRuns()
}

const tableSortBy = computed(() => [{ key: sortBy.value, order: sortDir.value }])

const fmtAbs = fmtDateTimeSec
const fmtRel = fmtRelative

const headers = computed(() => [
  { title: '', key: 'data-table-expand', width: 48, sortable: false },
  { title: '#', key: 'id', width: 70, sortable: true },
  { title: t('core_monitoring.runs.col.status'), key: 'status', width: 110, sortable: true },
  { title: t('core_monitoring.runs.col.started'), key: 'started_at', sortable: true },
  { title: t('core_monitoring.runs.col.finished'), key: 'finished_at', sortable: true },
  { title: t('core_monitoring.runs.col.duration'), key: 'duration', width: 130, sortable: true },
  { title: t('core_monitoring.runs.col.error'), key: 'error_text', sortable: false },
])

// VDataTable приводит item-value к строке.
const expanded = ref<string[]>([])
const logsByRun = ref<Record<number, TaskRunLog[]>>({})
const logsLoading = ref<Record<number, boolean>>({})
const logsError = ref<Record<number, string>>({})

const LEVEL_COLOR: Record<TaskRunLog['level'], string> = {
  debug: 'grey',
  info: 'info',
  warn: 'warning',
  error: 'error',
}

watch(expanded, (ids) => {
  for (const raw of ids) {
    const id = Number(raw)
    if (logsByRun.value[id] === undefined && !logsLoading.value[id]) {
      void loadRunLogs(id)
    }
  }
})

async function loadRunLogs(runId: number) {
  logsLoading.value = { ...logsLoading.value, [runId]: true }
  delete logsError.value[runId]
  try {
    const items = await fetchTaskRunLogs(props.module, props.code, runId)
    logsByRun.value = { ...logsByRun.value, [runId]: items }
  } catch (e) {
    logsError.value = { ...logsError.value, [runId]: e instanceof Error ? e.message : String(e) }
  } finally {
    logsLoading.value = { ...logsLoading.value, [runId]: false }
  }
}

const fmtTime = fmtTimeSec

function fmtPayload(p: Record<string, unknown> | null): string {
  if (!p) return '—'
  return JSON.stringify(p, null, 2)
}
</script>

<template>
  <PageLayout>
  <div class="d-flex flex-column h-100 pa-6">
    <PageHeader
      :title="task ? taskName(task) : t('core_monitoring.runs.fallback_title')"
      :description="task ? taskDescription(task) : `${module}.${code}`"
      back-to="/tasks"
    >
      <template #actions>
        <VBtn variant="text" :disabled="loading || refreshing" @click="loadRuns">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': refreshing }" /></template>
          {{ t('core_monitoring.action.refresh') }}
        </VBtn>
      </template>
    </PageHeader>

    <!-- Filter panel (standard) -->
    <VCard variant="outlined" rounded="lg" class="filter-panel mb-3">
      <div class="filter-row">
        <VSelect
          :model-value="statusFilter"
          :items="STATUS_OPTIONS"
          item-title="title"
          item-value="value"
          :label="t('core_monitoring.runs.filter_status')"
          variant="outlined"
          hide-details
          clearable
          :disabled="loading"
          style="max-width: 200px"
          @update:model-value="onFilterChange"
        />
      </div>
    </VCard>

    <!-- Open = fresh data: показываем скелет, а не данные предыдущей задачи -->
    <VCard v-if="loading" variant="outlined" rounded="lg" class="runs-card">
      <VSkeletonLoader type="table-row-divider@8" />
    </VCard>

    <VAlert v-else-if="error" type="error" variant="tonal">{{ error }}</VAlert>

    <template v-else>
      <VCard variant="outlined" rounded="lg" class="runs-card">
        <VDataTable
          v-model:expanded="expanded"
          fixed-header
          height="100%"
          :headers="headers"
          :items="runs"
          :items-per-page="-1"
          :sort-by="tableSortBy"
          :loading="refreshing"
          must-sort
          item-value="id"
          show-expand
          density="comfortable"
          hover
          :no-data-text="t('core_monitoring.runs.empty')"
          hide-default-footer
          @update:sort-by="onUpdateSortBy"
        >
          <template #item.status="{ item }">
            <VChip :color="STATUS_COLOR[item.status]" size="small" variant="tonal">
              {{ item.status }}
            </VChip>
          </template>

          <template #item.started_at="{ item }">
            <div>{{ fmtAbs(item.started_at) }}</div>
            <div class="text-caption text-medium-emphasis">{{ fmtRel(item.started_at) }}</div>
          </template>

          <template #item.finished_at="{ item }">
            <div>{{ fmtAbs(item.finished_at) }}</div>
            <div class="text-caption text-medium-emphasis">{{ fmtRel(item.finished_at) }}</div>
          </template>

          <template #item.duration="{ item }">
            {{ fmtDuration(item.started_at, item.finished_at) }}
          </template>

          <template #item.error_text="{ item }">
            <span class="text-error">{{ item.error_text || '' }}</span>
          </template>

          <template #expanded-row="{ columns, item }">
            <tr class="run-detail-row">
              <td :colspan="columns.length">
                <div class="d-flex flex-column ga-3 py-3">
                  <div>
                    <div class="text-caption text-medium-emphasis mb-1">Payload</div>
                    <pre class="detail-pre font-mono">{{ fmtPayload(item.payload) }}</pre>
                  </div>
                  <div>
                    <div class="d-flex align-center mb-1 ga-2">
                      <span class="text-caption text-medium-emphasis">{{ t('core_monitoring.runs.logs') }}</span>
                      <VSpacer />
                      <VBtn
                        size="x-small"
                        variant="text"
                        :icon="IconRefresh"
                        :loading="logsLoading[item.id]"
                        @click="loadRunLogs(item.id)"
                      />
                    </div>
                    <VProgressLinear v-if="logsLoading[item.id]" indeterminate height="2" />
                    <VAlert
                      v-else-if="logsError[item.id]"
                      type="error"
                      variant="tonal"
                      density="compact"
                    >
                      {{ logsError[item.id] }}
                    </VAlert>
                    <div
                      v-else-if="logsByRun[item.id] && logsByRun[item.id].length === 0"
                      class="text-caption text-medium-emphasis"
                    >
                      {{ t('core_monitoring.runs.logs_empty') }}
                    </div>
                    <div v-else-if="logsByRun[item.id]" class="d-flex flex-column ga-1">
                      <div
                        v-for="log in logsByRun[item.id]"
                        :key="log.id"
                        class="d-flex align-start ga-2 log-row"
                      >
                        <span class="text-caption text-medium-emphasis font-mono log-time">
                          {{ fmtTime(log.created_at) }}
                        </span>
                        <VChip
                          :color="LEVEL_COLOR[log.level]"
                          size="x-small"
                          variant="tonal"
                          class="log-level"
                        >
                          {{ log.level }}
                        </VChip>
                        <span class="font-mono log-msg">{{ log.message }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </VDataTable>

        <TablePaginationBar
          :page="page"
          :page-size="pageSize"
          :total="total"
          :page-count="pageCount"
          :page-sizes="PAGE_SIZES"
          @update:page="onPageChange"
          @update:page-size="onPageSizeChange"
        />
      </VCard>
    </template>
  </div>
  </PageLayout>
</template>

<style scoped>
.font-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.filter-panel {
  padding: 12px;
  flex: 0 0 auto;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.runs-card {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.runs-card :deep(.v-table) {
  flex: 1 1 0;
  min-height: 0;
}

.runs-card :deep(.v-data-table__tr td) {
  border-bottom: 1px solid var(--border-soft) !important;
  padding-top: 8px !important;
  padding-bottom: 8px !important;
}

.runs-card :deep(.v-data-table__tr:last-child td) {
  border-bottom: none !important;
}

.runs-card :deep(.v-data-table__tr:nth-child(even)) {
  background: rgba(var(--v-theme-on-surface), 0.015);
}

.runs-card :deep(.v-data-table__tr:hover) {
  background: rgba(var(--v-theme-primary), 0.06) !important;
}

.runs-card :deep(.run-detail-row > td) {
  background: rgba(var(--v-theme-on-surface), 0.025);
  border-bottom: 1px solid var(--border-soft) !important;
  padding: 0 16px !important;
}

.detail-pre {
  margin: 0;
  padding: 8px 12px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 6px;
  font-size: 0.78rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow: auto;
}

.log-row {
  font-size: 0.8rem;
  line-height: 1.5;
}

.log-time {
  flex: 0 0 auto;
  width: 90px;
}

.log-level {
  flex: 0 0 auto;
  min-width: 56px;
  justify-content: center;
}

.log-msg {
  flex: 1 1 auto;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
