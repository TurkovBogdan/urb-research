<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import PieChart, { type PieSlice } from '@/components/chart/PieChart.vue'

// ── Datasets ──────────────────────────────────────────────────────────────────
const CHANNELS: PieSlice[] = [
  { name: 'Email', value: 420 },
  { name: 'Chat', value: 310 },
  { name: 'Phone', value: 180 },
  { name: 'Web', value: 140 },
  { name: 'API', value: 60 },
]

const STATUS: PieSlice[] = [
  { name: 'Closed', value: 740 },
  { name: 'Open', value: 210 },
  { name: 'Snoozed', value: 90 },
]

const SMALL: PieSlice[] = [
  { name: 'Resolved', value: 88 },
  { name: 'Pending', value: 12 },
]

const MANY: PieSlice[] = [
  { name: 'Germany', value: 320 },
  { name: 'France', value: 240 },
  { name: 'Spain', value: 180 },
  { name: 'Italy', value: 160 },
  { name: 'Poland', value: 90 },
  { name: 'Other', value: 70 },
]

// ── Playground ─────────────────────────────────────────────────────────────────
const donut = ref(0.6)
const showLegend = ref(true)
const showLabels = ref(true)
const padAngle = ref(0.012)
const height = ref(280)

const playgroundData = computed<PieSlice[]>(() => CHANNELS)
const totalChannels = computed(() => CHANNELS.reduce((a, s) => a + s.value, 0))

const { t } = useI18n()
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.pie-chart.title')"
        :description="t('design-system.page.pie-chart.description')"
        back-to="/design-system"
      />

      <!-- 1. Basic pie -->
      <section class="ds-section">
        <p class="ds-label">basic — pie with legend, percentage labels, hover</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <PieChart :data="CHANNELS" />
        </VCard>
      </section>

      <!-- 2. Donut with center total -->
      <section class="ds-section">
        <p class="ds-label">donut — ring with center total</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <PieChart :data="STATUS" :donut="0.62" center-sub-label="conversations" />
        </VCard>
      </section>

      <!-- 3. Two slices -->
      <section class="ds-section">
        <p class="ds-label">two slices — share split</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <PieChart :data="SMALL" :donut="0.55" :center-label="`88%`" center-sub-label="resolved" />
        </VCard>
      </section>

      <!-- 4. Many slices -->
      <section class="ds-section">
        <p class="ds-label">many slices — six categories</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <PieChart :data="MANY" :height="300" />
        </VCard>
      </section>

      <!-- 5. No labels, no legend -->
      <section class="ds-section">
        <p class="ds-label">compact — donut, no slice labels, no legend (hover for detail)</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <PieChart :data="CHANNELS" :donut="0.6" :show-labels="false" :legend="false" :height="180" />
        </VCard>
      </section>

      <!-- 6. Playground -->
      <section class="ds-section">
        <p class="ds-label">playground — parameters on the fly</p>
        <VCard variant="outlined" rounded="lg" class="pa-4">
          <div class="ds-controls">
            <div class="ds-slider">
              <span class="ds-slider__label">Donut {{ donut.toFixed(2) }}</span>
              <VSlider v-model="donut" :min="0" :max="0.9" :step="0.05" density="compact" hide-details color="primary" />
            </div>
            <div class="ds-slider">
              <span class="ds-slider__label">Pad angle {{ padAngle.toFixed(3) }}</span>
              <VSlider v-model="padAngle" :min="0" :max="0.05" :step="0.002" density="compact" hide-details color="primary" />
            </div>
            <VSwitch v-model="showLegend" label="Legend" density="compact" hide-details color="primary" />
            <VSwitch v-model="showLabels" label="Labels" density="compact" hide-details color="primary" />
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
          <PieChart
            class="mt-4"
            :data="playgroundData"
            :donut="donut"
            :pad-angle="padAngle"
            :legend="showLegend"
            :show-labels="showLabels"
            :height="height"
            :center-label="`${totalChannels}`"
            center-sub-label="total"
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
  gap: 12px 20px;
}
.ds-slider {
  display: flex;
  flex-direction: column;
  min-width: 200px;
}
.ds-slider__label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  margin-bottom: 2px;
}
</style>
