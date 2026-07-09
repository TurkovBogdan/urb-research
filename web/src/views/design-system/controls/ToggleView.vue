<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

// VCheckbox
const cb_basic    = ref(true)
const cb_false    = ref(false)
const cb_indet    = ref(false)
const cb_group    = ref<string[]>(['vue', 'ts'])

// VRadio
const radio_basic = ref('option1')
const radio_inline = ref('b')
const radio_icon  = ref('card')

// VSwitch
const sw_basic    = ref(true)
const sw_off      = ref(false)
const sw_loading  = ref(true)
const sw_inset    = ref(true)
const sw_color    = ref(true)

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.toggle.title')"
      :description="t('design-system.page.toggle.description')" back-to="/design-system" />

    <!-- VCheckbox — variants -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.toggle.checkboxVariants') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">checked</span>
          <div class="ds-controls">
            <VCheckbox v-model="cb_basic" label="Active" hide-details />
          </div>
          <span class="ds-spec">v-model=true</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">unchecked</span>
          <div class="ds-controls">
            <VCheckbox v-model="cb_false" label="Inactive" hide-details />
          </div>
          <span class="ds-spec">v-model=false</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">indeterminate</span>
          <div class="ds-controls">
            <VCheckbox v-model="cb_indet" label="Partial" indeterminate hide-details />
          </div>
          <span class="ds-spec">indeterminate</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls">
            <VCheckbox :model-value="true" label="Cannot uncheck" disabled hide-details />
            <VCheckbox :model-value="false" label="Cannot check" disabled hide-details />
          </div>
          <span class="ds-spec">disabled</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">error</span>
          <div class="ds-controls">
            <VCheckbox :model-value="false" label="Required field"
              :error-messages="['You must agree']" />
          </div>
          <span class="ds-spec">error-messages</span>
        </div>

      </div>
    </section>

    <!-- VCheckbox — group -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.toggle.checkboxGroup') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">group</span>
          <div class="ds-controls">
            <VCheckbox v-model="cb_group" label="Vue" value="vue" hide-details />
            <VCheckbox v-model="cb_group" label="TypeScript" value="ts" hide-details />
            <VCheckbox v-model="cb_group" label="Vite" value="vite" hide-details />
          </div>
          <span class="ds-spec">shared v-model (array)</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">color</span>
          <div class="ds-controls">
            <VCheckbox :model-value="true" label="Primary" color="primary" hide-details />
            <VCheckbox :model-value="true" label="Success" color="success" hide-details />
            <VCheckbox :model-value="true" label="Error" color="error" hide-details />
          </div>
          <span class="ds-spec">color prop</span>
        </div>

      </div>
    </section>

    <!-- VRadio -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.toggle.radioGroup') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">vertical</span>
          <div class="ds-controls">
            <VRadioGroup v-model="radio_basic" hide-details>
              <VRadio label="Option 1" value="option1" />
              <VRadio label="Option 2" value="option2" />
              <VRadio label="Option 3" value="option3" />
            </VRadioGroup>
          </div>
          <span class="ds-spec">VRadioGroup vertical</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">inline</span>
          <div class="ds-controls">
            <VRadioGroup v-model="radio_inline" inline hide-details>
              <VRadio label="Day" value="a" />
              <VRadio label="Week" value="b" />
              <VRadio label="Month" value="c" />
            </VRadioGroup>
          </div>
          <span class="ds-spec">inline</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls">
            <VRadioGroup v-model="radio_basic" inline hide-details>
              <VRadio label="Full-time" value="full" />
              <VRadio label="Part-time" value="part" disabled />
              <VRadio label="Project-based" value="project" />
            </VRadioGroup>
          </div>
          <span class="ds-spec">disabled on a single radio</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">icon cards</span>
          <div class="ds-controls">
            <VRadioGroup v-model="radio_icon" inline hide-details class="radio-cards">
              <VRadio value="card" class="radio-card">
                <template #label><span class="radio-card__label">Cards</span></template>
              </VRadio>
              <VRadio value="list" class="radio-card">
                <template #label><span class="radio-card__label">List</span></template>
              </VRadio>
              <VRadio value="map" class="radio-card">
                <template #label><span class="radio-card__label">Map</span></template>
              </VRadio>
            </VRadioGroup>
          </div>
          <span class="ds-spec">custom label slot</span>
        </div>

      </div>
    </section>

    <!-- VSwitch -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.toggle.switchVariants') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">on / off</span>
          <div class="ds-controls">
            <VSwitch v-model="sw_basic" label="On" color="primary" inset hide-details />
            <VSwitch v-model="sw_off" label="Off" color="primary" inset hide-details />
          </div>
          <span class="ds-spec">basic</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">inset</span>
          <div class="ds-controls">
            <VSwitch v-model="sw_inset" label="Inset" color="primary" inset hide-details />
          </div>
          <span class="ds-spec">inset — knob inside the track</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">color</span>
          <div class="ds-controls">
            <VSwitch v-model="sw_color" label="Accent" color="primary" inset hide-details />
            <VSwitch :model-value="true" label="Success" color="success" inset hide-details />
            <VSwitch :model-value="true" label="Error" color="error" inset hide-details />
          </div>
          <span class="ds-spec">color prop</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">loading</span>
          <div class="ds-controls">
            <VSwitch v-model="sw_loading" label="Loading..." loading inset hide-details />
          </div>
          <span class="ds-spec">loading</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls">
            <VSwitch :model-value="true" label="Cannot turn off" disabled inset hide-details />
            <VSwitch :model-value="false" label="Cannot turn on" disabled inset hide-details />
          </div>
          <span class="ds-spec">disabled</span>
        </div>

      </div>
    </section>

    <!-- Density -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.toggle.density') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <VCheckbox :model-value="true" label="Checkbox" color="primary" hide-details />
            <VSwitch :model-value="true" label="Switch" color="primary" inset hide-details />
          </div>
          <span class="ds-spec">density="default"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">comfortable</span>
          <div class="ds-controls">
            <VCheckbox :model-value="true" label="Checkbox" color="primary" density="comfortable" hide-details />
            <VSwitch :model-value="true" label="Switch" color="primary" density="comfortable" inset hide-details />
          </div>
          <span class="ds-spec">density="comfortable"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">compact</span>
          <div class="ds-controls">
            <VCheckbox :model-value="true" label="Checkbox" color="primary" density="compact" hide-details />
            <VSwitch :model-value="true" label="Switch" color="primary" density="compact" inset hide-details />
          </div>
          <span class="ds-spec">density="compact"</span>
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
  gap: 4px 16px;
}

/* Radio cards */
.radio-cards {
  display: flex;
  flex-direction: row;
  gap: 8px;
}

.radio-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 6px 12px 6px 8px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;

  &:has(.v-radio--is-focused),
  &:has(input:checked) {
    border-color: rgb(var(--v-theme-primary));
    background: var(--accent-soft);
  }
}

.radio-card__label {
  font-size: 13px;
  font-weight: 500;
}
</style>
