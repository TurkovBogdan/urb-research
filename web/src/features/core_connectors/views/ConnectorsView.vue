<script setup lang="ts">
import { computed, onActivated, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconRefresh } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import ConnectorBalance from '../components/ConnectorBalance.vue'
import { fetchConnectors, type ConnectorView } from '../api'

const { t } = useI18n()

const connectors = ref<ConnectorView[]>([])
const loading = ref(true)
const refreshing = ref(false)
const error = ref<string | null>(null)

async function load() {
  refreshing.value = true
  error.value = null
  try {
    connectors.value = await fetchConnectors()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

onActivated(load)

const enabledCount = computed(() => connectors.value.filter(c => c.info.enabled).length)

// Текст-заглушка, когда баланса нет: коннектор отключён или не умеет отдавать баланс.
function naText(view: ConnectorView): string {
  return view.info.enabled
    ? t('core_connectors.balance.unsupported')
    : t('core_connectors.balance.off')
}
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('core_connectors.page.title')"
      :description="t('core_connectors.page.description')"
    >
      <template #actions>
        <div v-if="!loading && !error && connectors.length" class="kpis">
          <div class="kpi">
            <div class="kpi__value">{{ enabledCount }}/{{ connectors.length }}</div>
            <div class="kpi__label">{{ t('core_connectors.kpi.enabled') }}</div>
          </div>
        </div>
        <VBtn variant="text" :disabled="refreshing" @click="load">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': refreshing }" /></template>
          {{ t('core_connectors.action.refresh') }}
        </VBtn>
      </template>
    </PageHeader>

    <div v-if="loading" class="conn-grid">
      <VCard v-for="c in 3" :key="c" variant="flat" class="conn-card skel-card">
        <VSkeletonLoader type="heading, text, text, text" />
      </VCard>
    </div>

    <VAlert v-else-if="error" type="error" variant="tonal">{{ error }}</VAlert>
    <VAlert v-else-if="connectors.length === 0" type="info" variant="tonal">
      {{ t('core_connectors.empty') }}
    </VAlert>

    <div v-else class="conn-grid">
      <VCard
        v-for="view in connectors"
        :key="view.info.service"
        variant="flat"
        class="conn-card"
        :class="{ 'conn-card--off': !view.info.enabled }"
      >
        <header class="conn-card__header">
          <h3 class="conn-card__title">{{ view.info.name }}</h3>
          <span class="badge" :class="view.info.enabled ? 'badge--ok' : 'badge--off'">
            {{ view.info.enabled ? t('core_connectors.badge.enabled') : t('core_connectors.badge.disabled') }}
          </span>
        </header>

        <p class="conn-card__desc">{{ view.info.description }}</p>

        <div class="conn-card__balance">
          <ConnectorBalance
            :metrics="view.balance?.metrics ?? []"
            :error="view.balance?.error ?? null"
            :placeholder="naText(view)"
          />
        </div>
      </VCard>
    </div>
  </PageLayout>
</template>

<style scoped>
.kpis {
  display: flex;
  align-items: center;
  gap: 28px;
  padding-right: 8px;
}

.kpi { display: flex; flex-direction: column; gap: 3px; }

.kpi__value {
  font-size: 22px;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--text);
  line-height: 1;
}

.kpi__label {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
}

.conn-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px;
}

.skel-card { min-height: 180px; }
.skel-card :deep(.v-skeleton-loader) { width: 100%; padding: 0; }

.conn-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
}

.conn-card--off { opacity: 0.6; filter: grayscale(1); }

.conn-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.conn-card__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
  line-height: 1.3;
  flex: 1;
  min-width: 0;
}

/* Описание фиксировано на 3 строки: короткие резервируют высоту, длинные обрезаются
   многоточием — карточки в ряду выравниваются по высоте. */
.conn-card__desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  margin: -6px 0 0;
  min-height: calc(1.5em * 3);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.conn-card__balance {
  border-top: 1px solid var(--border);
  padding-top: 14px;
  margin-top: auto;
}

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

.badge--ok { color: var(--accent); background: var(--accent-soft); }
.badge--off { color: var(--text-muted); background: var(--border); }
</style>
