<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

// control-variant demos
const v_default  = ref(5)
const v_stacked  = ref(5)
const v_split    = ref(5)

// inset / hide-input
const v_inset    = ref(3)
const v_hide     = ref(0)

// step / precision
const v_step     = ref(0)
const v_prec     = ref(1.5)

// currency
const salary     = ref<number | null>(null)
const budget     = ref(180000)
const range_from = ref(50000)
const range_to   = ref(200000)

const { t } = useI18n()

</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.numbers.title')" :description="t('design-system.page.numbers.description')" back-to="/design-system" />

    <!-- control-variant -->
    <section class="ds-section">
      <h6 class="mb-3">control-variant</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <VNumberInput v-model="v_default" :min="0" :max="99"
              label="Quantity" variant="outlined" control-variant="default"
              hide-details />
          </div>
          <span class="ds-spec">control-variant="default"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">stacked</span>
          <div class="ds-controls">
            <VNumberInput v-model="v_stacked" :min="0" :max="99"
              label="Quantity" variant="outlined" control-variant="stacked"
              hide-details />
          </div>
          <span class="ds-spec">control-variant="stacked"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">split</span>
          <div class="ds-controls">
            <VNumberInput v-model="v_split" :min="0" :max="99"
              label="Quantity" variant="outlined" control-variant="split"
              hide-details />
          </div>
          <span class="ds-spec">control-variant="split"</span>
        </div>

      </div>
    </section>

    <!-- Modifiers -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.numbers.modifiers') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">inset</span>
          <div class="ds-controls">
            <VNumberInput v-model="v_inset" :min="0" :max="20"
              label="Pages" variant="outlined" control-variant="stacked"
              inset hide-details />
          </div>
          <span class="ds-spec">inset — shortened divider</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">hide-input</span>
          <div class="ds-controls">
            <VNumberInput v-model="v_hide" :min="0" :max="10"
              variant="outlined" control-variant="stacked"
              hide-input hide-details />
          </div>
          <span class="ds-spec">hide-input — buttons only</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">reverse</span>
          <div class="ds-controls">
            <VNumberInput v-model="v_stacked" :min="0" :max="99"
              label="Quantity" variant="outlined" control-variant="default"
              reverse hide-details />
          </div>
          <span class="ds-spec">reverse — buttons on the left</span>
        </div>

      </div>
    </section>

    <!-- Step and precision -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.numbers.stepPrecision') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">step=5</span>
          <div class="ds-controls">
            <VNumberInput v-model="v_step" :min="0" :max="100" :step="5"
              label="Multiple of 5" variant="outlined" control-variant="split"
              hide-details />
          </div>
          <span class="ds-spec">:step="5"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">precision=1</span>
          <div class="ds-controls">
            <VNumberInput v-model="v_prec" :min="0" :max="10" :step="0.5"
              :precision="1" label="Experience" variant="outlined"
              control-variant="default" suffix="yrs" hide-details />
          </div>
          <span class="ds-spec">:step="0.5" :precision="1"</span>
        </div>

      </div>
    </section>

    <!-- Currency -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.numbers.currency') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">salary</span>
          <div class="ds-controls">
            <VNumberInput v-model="salary" :min="0" :step="1000"
              label="Desired salary" variant="outlined"
              control-variant="stacked" suffix="₽" inset hide-details />
          </div>
          <span class="ds-spec">step=1000 · suffix · inset</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">budget</span>
          <div class="ds-controls">
            <VNumberInput v-model="budget" :min="0" :step="5000"
              label="Budget" variant="outlined"
              control-variant="default" suffix="₽" hide-details />
          </div>
          <span class="ds-spec">prefilled · step=5000</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">range</span>
          <div class="ds-controls">
            <div class="range-inputs">
              <VNumberInput v-model="range_from" :min="0" :max="range_to" :step="5000"
                label="From" variant="outlined" control-variant="stacked"
                suffix="₽" inset hide-details />
              <span class="range-sep">—</span>
              <VNumberInput v-model="range_to" :min="range_from" :max="500000" :step="5000"
                label="To" variant="outlined" control-variant="stacked"
                suffix="₽" inset hide-details />
            </div>
          </div>
          <span class="ds-spec">range "from — to"</span>
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
  grid-template-columns: 100px 1fr 200px;
  align-items: start;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
  &.ds-row--center { align-items: center; }
}

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  padding-top: 10px;
  .ds-row--center & { padding-top: 0; }
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
  padding-top: 10px;
  .ds-row--center & { padding-top: 0; }
}

.ds-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.v-number-input { min-width: 200px; max-width: 300px; }

/* Range inputs */
.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
  .v-number-input { min-width: 160px; max-width: 190px; }
}

.range-sep {
  font-size: 13px;
  color: var(--text-muted);
  flex-shrink: 0;
}

</style>
