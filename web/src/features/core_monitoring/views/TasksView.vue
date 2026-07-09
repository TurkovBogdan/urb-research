<script setup lang="ts">
import { computed, onActivated, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { storeToRefs } from 'pinia'
import { IconRefresh, IconListDetails, IconSearch, IconChevronRight } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { useTasksStore } from '../stores/tasks.store'
import { useTaskText } from '../taskText'
import type { TaskInfo } from '../api'

const router = useRouter()
const { t, locale } = useI18n()
const { taskName, taskDescription } = useTaskText()
const store = useTasksStore()
const {
  loading, refreshing, error, loadedAt,
  search, statusFilter,
  grouped, summary,
} = storeToRefs(store)

const now = ref(Date.now())

let tick: number | undefined
onActivated(() => {
  store.load()
  if (!tick) tick = window.setInterval(() => { now.value = Date.now() }, 5000)
})
onUnmounted(() => { if (tick) window.clearInterval(tick) })

function openRuns(t: TaskInfo) {
  router.push(`/tasks/${t.module}/${t.code}`)
}

const updatedLabel = computed(() => {
  if (loadedAt.value == null) return ''
  const sec = Math.max(0, Math.floor((now.value - loadedAt.value) / 1000))
  if (sec < 30) return t('core_monitoring.updated.just_now')
  if (sec < 60) return t('core_monitoring.updated.sec', { n: sec })
  const min = Math.floor(sec / 60)
  if (min < 60) return t('core_monitoring.updated.min', { n: min })
  const h = Math.floor(min / 60)
  return t('core_monitoring.updated.hour', { n: h })
})

const description = computed(() =>
  loadedAt.value
    ? t('core_monitoring.page.description_updated', { rel: updatedLabel.value })
    : t('core_monitoring.page.description')
)

function fmtNum(n: number): string {
  return n.toLocaleString(locale.value === 'en' ? 'en-US' : 'ru-RU')
}

function errRate(t: TaskInfo): number {
  return t.stats_24h.total > 0 ? t.stats_24h.error / t.stats_24h.total : 0
}
</script>

<template>
  <PageLayout>
    <PageHeader :title="t('core_monitoring.page.title')" :description="description">
      <template #actions>
        <div v-if="!loading && !error && store.tasks.length" class="kpis">
          <div class="kpi">
            <div class="kpi__value">{{ summary.enabled }}/{{ summary.total }}</div>
            <div class="kpi__label">{{ t('core_monitoring.kpi.enabled') }}</div>
          </div>
          <div class="kpi">
            <div class="kpi__value" :class="{ 'is-accent': summary.running > 0 }">
              {{ summary.running }}
            </div>
            <div class="kpi__label">{{ t('core_monitoring.kpi.running') }}</div>
          </div>
          <div class="kpi">
            <div class="kpi__value" :class="{ 'is-error': summary.errors > 0 }">
              {{ summary.errors }}
            </div>
            <div class="kpi__label">{{ t('core_monitoring.kpi.errors24h') }}</div>
          </div>
        </div>
        <VBtn
          variant="text"
          :disabled="refreshing"
          @click="store.load()"
        >
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': refreshing }" /></template>
          {{ t('core_monitoring.action.refresh') }}
        </VBtn>
      </template>
    </PageHeader>

    <VCard
      v-if="!loading && !error && store.tasks.length"
      variant="outlined"
      rounded="lg"
      class="filter-panel mb-3"
    >
      <div class="filter-row">
        <VBtnToggle
          v-model="statusFilter"
          mandatory
          variant="outlined"
          divided
          density="compact"
        >
          <VBtn value="all" size="small">{{ t('core_monitoring.filter.all') }}</VBtn>
          <VBtn value="running" size="small">{{ t('core_monitoring.filter.running') }}</VBtn>
          <VBtn value="errors" size="small">{{ t('core_monitoring.filter.errors') }}</VBtn>
        </VBtnToggle>
        <VTextField
          v-model="search"
          :label="t('core_monitoring.filter.search.label')"
          :placeholder="t('core_monitoring.filter.search.placeholder')"
          :prepend-inner-icon="IconSearch"
          variant="outlined"
          hide-details
          clearable
          class="filter-search"
        />
      </div>
    </VCard>

    <!-- Initial-load skeleton: 2 groups × 3 cards -->
    <div v-if="loading" class="task-groups">
      <section v-for="g in 2" :key="g" class="task-group">
        <header class="group-sep">
          <VSkeletonLoader type="text" class="skel-sep" />
        </header>
        <div class="task-grid">
          <VCard v-for="c in 3" :key="c" variant="flat" class="task-card skel-card">
            <VSkeletonLoader type="heading, text, text" />
          </VCard>
        </div>
      </section>
    </div>

    <VAlert v-else-if="error" type="error" variant="tonal">{{ error }}</VAlert>
    <VAlert v-else-if="store.tasks.length === 0" type="info" variant="tonal">
      {{ t('core_monitoring.empty.none') }}
    </VAlert>

    <VAlert v-else-if="grouped.length === 0" type="info" variant="tonal">
      {{ t('core_monitoring.empty.filtered') }}
    </VAlert>

    <div v-else class="task-groups">
      <section
        v-for="g in grouped"
        :key="g.module"
        class="task-group"
      >
        <header class="group-sep">
          <span class="group-sep__name">{{ g.module }}</span>
          <span class="group-sep__count">{{ g.tasks.length }}</span>
          <span class="group-sep__rule" />
        </header>

        <div class="task-grid">
          <VCard
            v-for="t in g.tasks"
            :key="`${t.module}.${t.code}`"
            variant="flat"
            link
            class="task-card"
            :class="{ 'task-card--off': !t.enabled }"
            role="button"
            tabindex="0"
            @click="openRuns(t)"
            @keydown.enter="openRuns(t)"
          >
        <header class="task-card__header">
          <h3 class="task-card__title">{{ taskName(t) }}</h3>
        </header>

        <p class="task-card__desc">{{ taskDescription(t) }}</p>

        <div class="task-card__meta">
          <span class="badge" :class="t.enabled ? 'badge--ok' : 'badge--off'">
            {{ t.enabled ? $t('core_monitoring.badge.enabled') : $t('core_monitoring.badge.disabled') }}
          </span>
          <span v-if="t.schedule" class="badge badge--accent">{{ t.schedule }}</span>
          <span v-else class="badge">{{ $t('core_monitoring.badge.manual') }}</span>
          <span class="badge">{{ $t('core_monitoring.badge.ttl', { n: t.ttl }) }}</span>
        </div>

        <div class="task-card__stats">
          <div class="stats-label">{{ $t('core_monitoring.stats.last24h') }}</div>
          <div class="stats-row">
            <div class="stats-cell">
              <div class="stats-value">{{ fmtNum(t.stats_24h.total) }}</div>
              <div class="stats-key">{{ $t('core_monitoring.stats.runs') }}</div>
            </div>
            <div class="stats-cell">
              <div
                class="stats-value"
                :class="{ 'is-accent': t.stats_24h.running > 0 }"
              >{{ t.stats_24h.running }}</div>
              <div class="stats-key">{{ $t('core_monitoring.stats.running') }}</div>
            </div>
            <div class="stats-cell">
              <div class="stats-value">{{ fmtNum(t.stats_24h.success) }}</div>
              <div class="stats-key">{{ $t('core_monitoring.stats.success') }}</div>
            </div>
            <div class="stats-cell">
              <div
                class="stats-value"
                :class="{
                  'is-error': errRate(t) > 0.05,
                  'is-warn': errRate(t) > 0 && errRate(t) <= 0.05,
                }"
              >{{ t.stats_24h.error }}</div>
              <div class="stats-key">{{ $t('core_monitoring.stats.errors') }}</div>
            </div>
          </div>
        </div>

        <footer class="task-card__footer">
          <span class="task-card__open">
            <IconListDetails :size="14" />
            {{ $t('core_monitoring.action.logs') }}
            <IconChevronRight :size="14" />
          </span>
        </footer>
          </VCard>
        </div>
      </section>
    </div>
  </PageLayout>
</template>

<style scoped>
/* ── Header KPIs ──────────────────────────────────────────── */
.kpis {
  display: flex;
  align-items: center;
  gap: 28px;
  padding-right: 8px;
}

.kpi {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.kpi__value {
  font-size: 22px;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--text);
  line-height: 1;
}

.kpi__value.is-accent { color: var(--accent); }
.kpi__value.is-error  { color: var(--error); }

.kpi__label {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
}

/* ── Filter panel ─────────────────────────────────────────── */
.filter-panel {
  padding: 12px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-search {
  flex: 1;
}

/* высота тоггла под строку поиска (VField density=compact → 36px) */
.filter-row :deep(.v-btn-toggle .v-btn) {
  --v-btn-height: 34px;
}

@media (max-width: 720px) {
  .filter-row { flex-direction: column; align-items: stretch; }
}

/* ── Skeleton ─────────────────────────────────────────────── */
/* кости заданы глобально (main.scss); тут — раскладка под карточку */
.skel-sep {
  width: 160px;
}
.skel-sep :deep(.v-skeleton-loader) {
  width: 100%;
}

.skel-card {
  /* высота примерно как у реальной карточки, чтобы layout не прыгал */
  min-height: 150px;
}
.skel-card :deep(.v-skeleton-loader) {
  width: 100%;
  padding: 0;
}

/* ── Groups ───────────────────────────────────────────────── */
.task-groups {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.group-sep {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.group-sep__name {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.02em;
}

.group-sep__count {
  font-size: 11px;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--text-muted);
  background: var(--border);
  padding: 1px 8px;
  border-radius: 20px;
}

.group-sep__rule {
  flex: 1;
  height: 1px;
  background: var(--border);
}

/* ── Grid ─────────────────────────────────────────────────── */
.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px;
}

/* ── Card ─────────────────────────────────────────────────── */
/* surface / border / radius / hover / focus — глобальный дефолт .v-card + .v-card--link */
.task-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
}

.task-card--off { opacity: 0.6; filter: grayscale(1); }

.task-card__header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.task-card__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
  line-height: 1.3;
}

.task-card__desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  margin: -6px 0 0;
}

.task-card__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* Единая плашка для состояния, расписания и TTL */
.badge {
  display: inline-flex;
  align-items: center;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.04em;
  padding: 2px 8px;
  border-radius: 5px;
  white-space: nowrap;
  color: var(--text-muted);
  background: var(--border);
}

.badge--ok,
.badge--accent {
  color: var(--accent);
  background: var(--accent-soft);
}

.badge--off {
  color: var(--text-muted);
  background: var(--border);
}

/* ── Stats ────────────────────────────────────────────────── */
.task-card__stats {
  border-top: 1px solid var(--border);
  padding-top: 12px;
}

.stats-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-faint);
  margin-bottom: 8px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stats-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.stats-value {
  font-size: 18px;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--text);
  line-height: 1.1;
}

.stats-value.is-accent { color: var(--accent); }
.stats-value.is-warn   { color: var(--warn); }
.stats-value.is-error  { color: var(--error); }

.stats-key {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-faint);
}

/* ── Footer ───────────────────────────────────────────────── */
.task-card__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 4px;
  margin-top: auto;
}

/* Подсказка «провалиться в логи» — карточка кликабельна целиком */
.task-card__open {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-faint);
  transition: color 120ms ease;
}

.task-card:hover .task-card__open { color: var(--accent); }
</style>
