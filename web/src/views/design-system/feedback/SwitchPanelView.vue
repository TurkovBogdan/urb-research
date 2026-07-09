<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import SwitchPanel from '@/components/SwitchPanel.vue'
import CodeBlock from '@/components/CodeBlock.vue'

const { t } = useI18n()

const active = ref(true)
const withDescription = ref(false)
const titleOnly = ref(true)
const paused = ref(false)
const disabledOn = ref(true)

const tones = ['default', 'primary', 'info', 'success', 'warning', 'error', 'transparent'] as const
const toneState = reactive<Record<string, boolean>>(
  Object.fromEntries(tones.map(tn => [tn, true])),
)

const switchTones = ['primary', 'info', 'success', 'warning', 'error'] as const
const switchToneState = reactive<Record<string, boolean>>(
  Object.fromEntries(switchTones.map(tn => [tn, true])),
)

// Usage example — how to import and use the component. `<\/script>` / `<\/template>`
// are escaped so the literal closing tags don't terminate this SFC's blocks.
const usageCode = `<script setup lang="ts">
import { ref } from 'vue'
import SwitchPanel from '@/components/SwitchPanel.vue'

const active = ref(true)
const paused = ref(false)
<\/script>

<template>
  <!-- Common title + description -->
  <SwitchPanel
    v-model="active"
    title="Mailbox active"
    description="Email import is enabled."
  />

  <!-- Separate text for the on / off state -->
  <SwitchPanel
    v-model="paused"
    title-on="Import enabled"
    title-off="Import disabled"
    description-on="Emails are synced on schedule."
    description-off="Synchronization is paused."
  />

  <!-- Semantic tone — changes the panel background and the switch color -->
  <SwitchPanel
    v-model="active"
    tone="warning"
    title="Heads up"
    description="This action affects every mailbox."
  />

  <!-- Neutral panel, coloured switch only — switchTone overrides just the switch -->
  <SwitchPanel
    v-model="paused"
    switch-tone="error"
    title="Exclude from processing"
    description="The item won't be processed."
  />
<\/template>`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.switch-panel.title')" :description="t('design-system.page.switch-panel.description')" back-to="/design-system" />

    <!-- Basic -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.switch-panel.basic') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">title + desc</span>
          <div class="ds-controls">
            <SwitchPanel
              v-model="withDescription"
              :title="t('design-system.section.switch-panel.sample.title')"
              :description="t('design-system.section.switch-panel.sample.desc')"
            />
          </div>
          <span class="ds-spec">v-model · title · description</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">title only</span>
          <div class="ds-controls">
            <SwitchPanel
              v-model="titleOnly"
              :title="t('design-system.section.switch-panel.sample.activeTitle')"
            />
          </div>
          <span class="ds-spec">title</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">slot</span>
          <div class="ds-controls">
            <SwitchPanel v-model="active">
              {{ t('design-system.section.switch-panel.sample.slot') }}
            </SwitchPanel>
          </div>
          <span class="ds-spec">default slot — rich text</span>
        </div>

      </div>
    </section>

    <!-- Per-state text -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.switch-panel.stateText') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">on / off</span>
          <div class="ds-controls">
            <SwitchPanel
              v-model="paused"
              :title-on="t('design-system.section.switch-panel.sample.onTitle')"
              :title-off="t('design-system.section.switch-panel.sample.offTitle')"
              :description-on="t('design-system.section.switch-panel.sample.onDesc')"
              :description-off="t('design-system.section.switch-panel.sample.offDesc')"
            />
          </div>
          <span class="ds-spec">titleOn/Off · descriptionOn/Off</span>
        </div>

      </div>
    </section>

    <!-- Tones -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.switch-panel.tones') }}</h6>
      <div class="ds-card">

        <div v-for="tn in tones" :key="tn" class="ds-row">
          <span class="ds-tag">{{ tn }}</span>
          <div class="ds-controls">
            <SwitchPanel
              v-model="toneState[tn]"
              :tone="tn"
              :title="t(`design-system.section.switch-panel.toneSample.${tn}`)"
              :description="t('design-system.section.switch-panel.toneDesc')"
            />
          </div>
          <span class="ds-spec">tone="{{ tn }}"</span>
        </div>

      </div>
    </section>

    <!-- Switch tone (neutral panel, coloured switch only) -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.switch-panel.switchTone') }}</h6>
      <div class="ds-card">

        <div v-for="tn in switchTones" :key="tn" class="ds-row">
          <span class="ds-tag">{{ tn }}</span>
          <div class="ds-controls">
            <SwitchPanel
              v-model="switchToneState[tn]"
              :switch-tone="tn"
              :title="t(`design-system.section.switch-panel.toneSample.${tn}`)"
              :description="t('design-system.section.switch-panel.switchToneDesc')"
            />
          </div>
          <span class="ds-spec">switch-tone="{{ tn }}"</span>
        </div>

      </div>
    </section>

    <!-- States -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.switch-panel.states') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls">
            <SwitchPanel
              v-model="disabledOn"
              disabled
              :title="t('design-system.section.switch-panel.sample.disabledTitle')"
              :description="t('design-system.section.switch-panel.sample.disabledDesc')"
            />
          </div>
          <span class="ds-spec">disabled</span>
        </div>

      </div>
    </section>

    <!-- Usage -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.switch-panel.usage') }}</h6>
      <CodeBlock :code="usageCode" lang="vue" />
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
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
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
  flex-direction: column;
  gap: 8px;
}
</style>
