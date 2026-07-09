<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import BarChart, { type BarMode, type BarOrientation, type BarSeries } from '@/components/chart/BarChart.vue'

// ── Synthetic data ────────────────────────────────────────────────────────────
function seedRandom(seed: number) {
  let s = seed
  return () => {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
}

function build(n: number, base: number, jitter: number, seed: number): number[] {
  const rand = seedRandom(seed)
  return Array.from({ length: n }, () => Math.max(0, Math.round(base + (rand() - 0.5) * 2 * jitter)))
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const CHANNELS = ['Email', 'Chat', 'Phone', 'Web', 'API']

const SINGLE: BarSeries[] = [
  { name: 'Conversations', data: build(6, 240, 60, 1) },
]

const GROUPED: BarSeries[] = [
  { name: 'Agent A', data: build(6, 180, 40, 11) },
  { name: 'Agent B', data: build(6, 120, 35, 22) },
  { name: 'Agent C', data: build(6, 80, 25, 33) },
]

const STACKED: BarSeries[] = [
  { name: 'Open',   data: build(7, 60, 18, 41) },
  { name: 'Closed', data: build(7, 140, 30, 51) },
  { name: 'Snoozed', data: build(7, 25, 10, 61) },
]

const HORIZONTAL: BarSeries[] = [
  { name: 'Volume', data: build(5, 300, 120, 71) },
]

// ── Playground ─────────────────────────────────────────────────────────────────
const mode = ref<BarMode>('grouped')
const orientation = ref<BarOrientation>('vertical')
const showGrid = ref(true)
const showLegend = ref(true)
const radius = ref(3)
const height = ref(300)

const modeItems: { value: BarMode; title: string }[] = [
  { value: 'grouped', title: 'Grouped' },
  { value: 'stacked', title: 'Stacked' },
]
const orientationItems: { value: BarOrientation; title: string }[] = [
  { value: 'vertical', title: 'Vertical' },
  { value: 'horizontal', title: 'Horizontal' },
]

const playgroundSeries = computed<BarSeries[]>(() => GROUPED)

const { t } = useI18n()
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.bar-chart.title')"
        :description="t('design-system.page.bar-chart.description')"
        back-to="/design-system"
      />

      <!-- 1. Single series -->
      <section class="ds-section">
        <p class="ds-label">basic — single series, vertical, hover</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <BarChart :categories="MONTHS" :series="SINGLE" />
        </VCard>
      </section>

      <!-- 2. Grouped -->
      <section class="ds-section">
        <p class="ds-label">grouped — three series side by side</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <BarChart :categories="MONTHS" :series="GROUPED" :height="300" />
        </VCard>
      </section>

      <!-- 3. Stacked -->
      <section class="ds-section">
        <p class="ds-label">stacked — segments stacked per category</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <BarChart :categories="WEEKDAYS" :series="STACKED" mode="stacked" :height="300" />
        </VCard>
      </section>

      <!-- 4. Horizontal -->
      <section class="ds-section">
        <p class="ds-label">horizontal — single series, long category labels</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <BarChart
            :categories="CHANNELS"
            :series="HORIZONTAL"
            orientation="horizontal"
            :height="260"
            :padding="{ left: 64 }"
          />
        </VCard>
      </section>

      <!-- 5. Horizontal stacked -->
      <section class="ds-section">
        <p class="ds-label">horizontal + stacked</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <BarChart
            :categories="WEEKDAYS"
            :series="STACKED"
            mode="stacked"
            orientation="horizontal"
            :height="300"
            :padding="{ left: 48 }"
          />
        </VCard>
      </section>

      <!-- 6. Compact -->
      <section class="ds-section">
        <p class="ds-label">compact — height 140, no grid, no legend</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <BarChart
            :categories="MONTHS"
            :series="SINGLE"
            :height="140"
            :grid="false"
            :legend="false"
            :padding="{ left: 32, top: 6 }"
          />
        </VCard>
      </section>

      <!-- 7. Playground -->
      <section class="ds-section">
        <p class="ds-label">playground — parameters on the fly</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <div class="ds-controls">
            <VSelect
              v-model="mode"
              :items="modeItems"
              item-title="title"
              item-value="value"
              label="Mode"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 180px"
            />
            <VSelect
              v-model="orientation"
              :items="orientationItems"
              item-title="title"
              item-value="value"
              label="Orientation"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 180px"
            />
            <VSwitch v-model="showGrid"   label="Grid"   density="compact" hide-details color="primary" />
            <VSwitch v-model="showLegend" label="Legend" density="compact" hide-details color="primary" />
            <VTextField
              v-model.number="radius"
              label="Radius"
              type="number"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 120px"
            />
            <VTextField
              v-model.number="height"
              label="Height"
              type="number"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 120px"
            />
          </div>
          <BarChart
            class="mt-4"
            :categories="MONTHS"
            :series="playgroundSeries"
            :mode="mode"
            :orientation="orientation"
            :grid="showGrid"
            :legend="showLegend"
            :radius="radius"
            :height="height"
            :padding="orientation === 'horizontal' ? { left: 48 } : undefined"
          />
        </VCard>
      </section>
    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 1100px; }
.ds-section { margin-bottom: 32px; }
.ds-label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  margin-bottom: 8px;
}
.ds-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
</style>
