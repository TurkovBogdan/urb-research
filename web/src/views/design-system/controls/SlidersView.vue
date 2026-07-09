<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

// VSlider
const sl_basic    = ref(40)
const sl_step     = ref(50)
const sl_ticks    = ref(3)
const sl_thumb    = ref(60)
const sl_color    = ref(70)
const sl_readonly = ref(55)
const sl_disabled = ref(30)

// VRangeSlider
const range_basic    = ref<[number, number]>([20, 70])
const range_salary   = ref<[number, number]>([60000, 180000])
const range_exp      = ref<[number, number]>([1, 5])

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.sliders.title')" :description="t('design-system.page.sliders.description')" back-to="/design-system" />

    <!-- VSlider — basic variants -->
    <section class="ds-section">
      <h6 class="mb-3">VSlider</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">basic</span>
          <div class="ds-controls ds-controls--slider">
            <VSlider v-model="sl_basic" :min="0" :max="100" hide-details />
          </div>
          <span class="ds-spec">basic · {{ sl_basic }}</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">step</span>
          <div class="ds-controls ds-controls--slider">
            <VSlider v-model="sl_step" :min="0" :max="100" :step="10" hide-details />
          </div>
          <span class="ds-spec">:step="10" · {{ sl_step }}</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">ticks</span>
          <div class="ds-controls ds-controls--slider">
            <VSlider v-model="sl_ticks" :min="0" :max="5" :step="1"
              show-ticks="always" hide-details />
          </div>
          <span class="ds-spec">show-ticks · {{ sl_ticks }}</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">thumb label</span>
          <div class="ds-controls ds-controls--slider">
            <VSlider v-model="sl_thumb" :min="0" :max="100"
              thumb-label="always" hide-details />
          </div>
          <span class="ds-spec">thumb-label="always"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">label</span>
          <div class="ds-controls ds-controls--slider">
            <VSlider v-model="sl_basic" :min="0" :max="100"
              label="Volume" hide-details />
          </div>
          <span class="ds-spec">label prop</span>
        </div>

      </div>
    </section>

    <!-- VSlider — states -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.sliders.states') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">error</span>
          <div class="ds-controls ds-controls--slider">
            <VSlider v-model="sl_color" :min="0" :max="100"
              color="error" hide-details />
          </div>
          <span class="ds-spec">color="error"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">readonly</span>
          <div class="ds-controls ds-controls--slider">
            <VSlider v-model="sl_readonly" :min="0" :max="100" readonly hide-details />
          </div>
          <span class="ds-spec">readonly</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls ds-controls--slider">
            <VSlider v-model="sl_disabled" :min="0" :max="100" disabled hide-details />
          </div>
          <span class="ds-spec">disabled</span>
        </div>

      </div>
    </section>

    <!-- VRangeSlider -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.sliders.range') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">basic</span>
          <div class="ds-controls ds-controls--slider">
            <VRangeSlider v-model="range_basic" :min="0" :max="100"
              thumb-label="always" hide-details />
          </div>
          <span class="ds-spec">{{ range_basic[0] }} — {{ range_basic[1] }}</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">step</span>
          <div class="ds-controls ds-controls--slider">
            <VRangeSlider v-model="range_basic" :min="0" :max="100" :step="5"
              hide-details />
          </div>
          <span class="ds-spec">:step="5"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">salary</span>
          <div class="ds-controls ds-controls--slider">
            <div class="range-labels">
              <span class="range-val">{{ range_salary[0].toLocaleString('en') }} ₽</span>
              <span class="range-sep">—</span>
              <span class="range-val">{{ range_salary[1].toLocaleString('en') }} ₽</span>
            </div>
            <VRangeSlider v-model="range_salary"
              :min="0" :max="500000" :step="5000"
              color="primary" hide-details />
          </div>
          <span class="ds-spec">salary · step=5000</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">experience</span>
          <div class="ds-controls ds-controls--slider">
            <div class="range-labels">
              <span class="range-val">from {{ range_exp[0] }} yrs</span>
              <span class="range-sep">—</span>
              <span class="range-val">to {{ range_exp[1] }} yrs</span>
            </div>
            <VRangeSlider v-model="range_exp"
              :min="0" :max="10" :step="1"
              show-ticks="always" color="primary" hide-details />
          </div>
          <span class="ds-spec">experience · step=1 · ticks</span>
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

.ds-controls { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }

.ds-controls--slider {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-block: 4px;
  .v-slider, .v-range-slider { width: 100%; }
}

.range-labels {
  display: flex;
  align-items: center;
  gap: 6px;
}

.range-val {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.range-sep {
  font-size: 11px;
  color: var(--text-faint);
}
</style>
