<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { IconClock } from '@tabler/icons-vue'
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

// --- Date ---
const dateValue = ref<Date | null>(new Date(2026, 4, 25))

// --- Time ---
const timeValue = ref<string>('14:30')
const timeMenu = ref(false)

// --- DateTime ---
const dtDate = ref<Date | null>(new Date(2026, 4, 25))
const dtTime = ref<string>('09:00')
const dtTimeMenu = ref(false)
const dtSummary = computed(() => {
  if (!dtDate.value) return '—'
  const d = dtDate.value
  const ymd = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  return `${ymd} ${dtTime.value}`
})

// --- Range ---
const rangeValue = ref<Date[]>([
  new Date(2026, 4, 20),
  new Date(2026, 4, 21),
  new Date(2026, 4, 22),
  new Date(2026, 4, 23),
  new Date(2026, 4, 24),
  new Date(2026, 4, 25),
])
const rangeSummary = computed(() => {
  const arr = rangeValue.value
  if (!arr?.length) return '—'
  const fmt = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  const sorted = [...arr].sort((a, b) => a.getTime() - b.getTime())
  return `${fmt(sorted[0])} … ${fmt(sorted[sorted.length - 1])} · ${sorted.length} d.`
})

// --- Range via two fields (alternative) ---
const rangeFrom = ref<Date | null>(new Date(2026, 4, 20))
const rangeTo = ref<Date | null>(new Date(2026, 4, 25))

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.date-pickers.title')" :description="t('design-system.page.date-pickers.description')" back-to="/design-system" />

    <!-- Date -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.date-pickers.date') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">date</span>
          <div class="ds-controls">
            <VDateInput v-model="dateValue" label="Date" />
          </div>
          <span class="ds-spec">VDateInput</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">min/max</span>
          <div class="ds-controls">
            <VDateInput label="Constrained" :min="new Date(2026, 0, 1)" :max="new Date(2026, 11, 31)" />
          </div>
          <span class="ds-spec">:min · :max</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">clearable</span>
          <div class="ds-controls">
            <VDateInput label="Optional" clearable />
          </div>
          <span class="ds-spec">clearable</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">readonly</span>
          <div class="ds-controls">
            <VDateInput label="Read only" :model-value="new Date(2026, 4, 25)" readonly />
          </div>
          <span class="ds-spec">readonly</span>
        </div>
      </div>
    </section>

    <!-- Time -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.date-pickers.time') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">time</span>
          <div class="ds-controls">
            <VTextField
              v-model="timeValue"
              label="Time"
              :append-inner-icon="IconClock"
              readonly
              density="compact"
              hide-details
              style="max-width: 220px"
            >
              <VMenu v-model="timeMenu" activator="parent" :close-on-content-click="false" location="bottom">
                <VTimePicker v-model="timeValue" @update:model-value="timeMenu = false" />
              </VMenu>
            </VTextField>
          </div>
          <span class="ds-spec">VTextField + VMenu → VTimePicker</span>
        </div>

        <div class="ds-row ds-row--start">
          <span class="ds-tag" style="padding-top: 10px">inline</span>
          <div class="ds-controls">
            <VTimePicker v-model="timeValue" />
          </div>
          <span class="ds-spec" style="padding-top: 10px">VTimePicker directly</span>
        </div>
      </div>
    </section>

    <!-- Date + time -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.date-pickers.dateTime') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">datetime</span>
          <div class="ds-controls" style="gap: 12px">
            <VDateInput v-model="dtDate" label="Date" style="max-width: 220px" />
            <VTextField
              v-model="dtTime"
              label="Time"
              :append-inner-icon="IconClock"
              readonly
              density="compact"
              hide-details
              style="max-width: 160px"
            >
              <VMenu v-model="dtTimeMenu" activator="parent" :close-on-content-click="false" location="bottom">
                <VTimePicker v-model="dtTime" @update:model-value="dtTimeMenu = false" />
              </VMenu>
            </VTextField>
          </div>
          <span class="ds-spec">VDateInput + VTimePicker</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">value</span>
          <div class="ds-controls">
            <code class="ds-code">{{ dtSummary }}</code>
          </div>
          <span class="ds-spec">computed</span>
        </div>
      </div>
    </section>

    <!-- Date range -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.date-pickers.range') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">range</span>
          <div class="ds-controls">
            <VDateInput
              v-model="rangeValue"
              label="Period"
              multiple="range"
              style="max-width: 320px"
            />
          </div>
          <span class="ds-spec">VDateInput multiple="range"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">value</span>
          <div class="ds-controls">
            <code class="ds-code">{{ rangeSummary }}</code>
          </div>
          <span class="ds-spec">array of dates</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">two fields</span>
          <div class="ds-controls" style="gap: 12px">
            <VDateInput v-model="rangeFrom" label="From" :max="rangeTo ?? undefined" style="max-width: 200px" />
            <VDateInput v-model="rangeTo" label="To" :min="rangeFrom ?? undefined" style="max-width: 200px" />
          </div>
          <span class="ds-spec">two VDateInput · :min/:max</span>
        </div>
      </div>
    </section>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }

.ds-section { margin-bottom: 28px; }

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 100px 1fr 240px;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
  &.ds-row--start { align-items: start; }
}

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
}

.ds-controls {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 8px;
}

.ds-code {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text);
  background: var(--surface-hi);
  padding: 4px 8px;
  border-radius: 4px;
}
</style>
