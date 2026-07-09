<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import LineChart, { type CurveKind, type LineSeries } from '@/components/chart/LineChart.vue'

// ── Synthetic data generators ────────────────────────────────────────────────
function daysAgo(n: number): Date {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() - n)
  return d
}

function seedRandom(seed: number) {
  let s = seed
  return () => {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
}

function buildDaily(days: number, base: number, jitter: number, trend: number, seed: number) {
  const rand = seedRandom(seed)
  const out = []
  for (let i = days - 1; i >= 0; i--) {
    const t = (days - 1 - i) / days
    const noise = (rand() - 0.5) * 2 * jitter
    out.push({ x: daysAgo(i), y: Math.max(0, Math.round(base + trend * t + noise)) })
  }
  return out
}

// ── Datasets ─────────────────────────────────────────────────────────────────
const SINGLE_SERIES: LineSeries[] = [
  { name: 'Sessions', data: buildDaily(30, 120, 30, 80, 1) },
]

const MULTI_SERIES: LineSeries[] = [
  { name: 'Agent A', data: buildDaily(30, 100, 25, 90, 11) },
  { name: 'Agent B', data: buildDaily(30, 70, 18, 45, 22) },
  { name: 'Agent C', data: buildDaily(30, 40, 15, 20, 33), dashed: true },
]

const AREA_SERIES: LineSeries[] = [
  { name: 'Inbound', data: buildDaily(60, 200, 60, 100, 7), area: true },
]

const STACKED_LIKE: LineSeries[] = [
  { name: 'Tokens (in)',  data: buildDaily(45, 8000, 1500, 3500, 41), area: true },
  { name: 'Tokens (out)', data: buildDaily(45, 3500, 900,  1800, 51), area: true },
]

const TINY: LineSeries[] = [
  { name: 'RPS', data: buildDaily(14, 12, 2, 5, 91) },
]

// Numeric X (not time) — e.g. epoch number, distribution
const NUMERIC_X: LineSeries[] = [
  {
    name: 'p50',
    data: Array.from({ length: 50 }, (_, i) => ({ x: i, y: 30 + Math.sin(i / 4) * 8 + i * 0.3 })),
  },
  {
    name: 'p95',
    data: Array.from({ length: 50 }, (_, i) => ({ x: i, y: 80 + Math.sin(i / 4 + 1) * 14 + i * 0.6 })),
  },
]

// ── Playground state ─────────────────────────────────────────────────────────
const curve = ref<CurveKind>('smooth')
const showGrid = ref(true)
const showLegend = ref(true)
const showPoints = ref(false)
const strokeWidth = ref(2)
const height = ref(280)

const curveItems: { value: CurveKind; title: string }[] = [
  { value: 'smooth', title: 'Smooth (monotone)' },
  { value: 'linear', title: 'Straight segments' },
  { value: 'step',   title: 'Stepped' },
]

const { t } = useI18n()

const playgroundSeries = computed<LineSeries[]>(() => MULTI_SERIES)
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.line-chart.title')"
        :description="t('design-system.page.line-chart.description')"
        back-to="/design-system"
      />

      <!-- 1. Basic -->
      <section class="ds-section">
        <p class="ds-label">basic — single series, time axis, hover</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <LineChart :series="SINGLE_SERIES" />
        </VCard>
      </section>

      <!-- 2. Multi-series -->
      <section class="ds-section">
        <p class="ds-label">multi-series — three series, distinct colors, dashed for the third</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <LineChart :series="MULTI_SERIES" :height="300" />
        </VCard>
      </section>

      <!-- 3. Area -->
      <section class="ds-section">
        <p class="ds-label">area — fill under the line</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <LineChart :series="AREA_SERIES" :height="240" />
        </VCard>
      </section>

      <!-- 4. Double area (overlay) -->
      <section class="ds-section">
        <p class="ds-label">two areas — overlay (semi-transparent fills, separate lines)</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <LineChart :series="STACKED_LIKE" :height="280" />
        </VCard>
      </section>

      <!-- 5. Numeric X axis -->
      <section class="ds-section">
        <p class="ds-label">numeric X axis — e.g. percentile distribution</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <LineChart :series="NUMERIC_X" :height="260" x-type="number" />
        </VCard>
      </section>

      <!-- 6. Sparkline-ish -->
      <section class="ds-section">
        <p class="ds-label">compact — height 120, no legend, no grid</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <LineChart
            :series="TINY"
            :height="120"
            :grid="false"
            :legend="false"
            :padding="{ left: 32, right: 8, top: 6, bottom: 22 }"
          />
        </VCard>
      </section>

      <!-- 7. Playground -->
      <section class="ds-section">
        <p class="ds-label">playground — parameters on the fly</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <div class="ds-controls">
            <VSelect
              v-model="curve"
              :items="curveItems"
              item-title="title"
              item-value="value"
              label="Curve"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 220px"
            />
            <VSwitch v-model="showGrid"   label="Grid"  density="compact" hide-details color="primary" />
            <VSwitch v-model="showLegend" label="Legend" density="compact" hide-details color="primary" />
            <VSwitch v-model="showPoints" label="Points" density="compact" hide-details color="primary" />
            <VTextField
              v-model.number="strokeWidth"
              label="Stroke width"
              type="number"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 140px"
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
          <LineChart
            class="mt-4"
            :series="playgroundSeries"
            :curve="curve"
            :grid="showGrid"
            :legend="showLegend"
            :show-points="showPoints"
            :stroke-width="strokeWidth"
            :height="height"
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
