<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import Spoiler from '@/components/Spoiler.vue'
import CodeBlock from '@/components/CodeBlock.vue'

const { t } = useI18n()

const basic = ref(false)
const defaultOpen = ref(true)
const disabled = ref(false)
const customColor = ref(false)

const variants = ['default', 'minimal', 'card'] as const
const variantOpen = reactive<Record<string, boolean>>(
  Object.fromEntries(variants.map(v => [v, false])),
)

// Usage example — how to import and use the component. `<\/script>` / `<\/template>`
// are escaped so the literal closing tags don't terminate this SFC's blocks.
const usageCode = `<script setup lang="ts">
import { ref } from 'vue'
import Spoiler from '@/components/Spoiler.vue'

const open = ref(false)
<\/script>

<template>
  <!-- Title + content, default theme -->
  <Spoiler v-model="open" title="Technical details">
    Hidden content goes here.
  </Spoiler>

  <!-- Minimal theme — borderless uppercase label -->
  <Spoiler title="Quoted history" variant="minimal">
    <p>Older messages…</p>
  </Spoiler>

  <!-- Custom title + trailing actions -->
  <Spoiler variant="card">
    <template #title>Attachments</template>
    <template #actions>
      <VChip size="x-small">3</VChip>
    </template>
    <p>Files…</p>
  </Spoiler>

  <!-- Custom header colours: resting (color) + hover (active-color) -->
  <Spoiler
    variant="minimal"
    title="Danger zone"
    color="var(--text-faint)"
    active-color="var(--error)"
  >
    <p>Irreversible actions…</p>
  </Spoiler>
<\/template>`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.spoiler.title')" :description="t('design-system.page.spoiler.description')" back-to="/design-system" />

    <!-- Basic -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.spoiler.basic') }}</h6>
      <div class="ds-stack">
        <Spoiler v-model="basic" :title="t('design-system.section.spoiler.sample.title')">
          {{ t('design-system.section.spoiler.sample.body') }}
        </Spoiler>
        <Spoiler v-model="defaultOpen" :title="t('design-system.section.spoiler.sample.openTitle')">
          {{ t('design-system.section.spoiler.sample.body') }}
        </Spoiler>
      </div>
    </section>

    <!-- Variants -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.spoiler.variants') }}</h6>
      <div class="ds-card">
        <div v-for="v in variants" :key="v" class="ds-row">
          <span class="ds-tag">{{ v }}</span>
          <div class="ds-controls">
            <Spoiler
              v-model="variantOpen[v]"
              :variant="v"
              :title="t(`design-system.section.spoiler.variantSample.${v}`)"
            >
              {{ t('design-system.section.spoiler.sample.body') }}
            </Spoiler>
          </div>
          <span class="ds-spec">variant="{{ v }}"</span>
        </div>
      </div>
    </section>

    <!-- Slots -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.spoiler.slots') }}</h6>
      <div class="ds-stack">
        <Spoiler variant="card">
          <template #title>{{ t('design-system.section.spoiler.sample.attachments') }}</template>
          <template #actions>
            <VChip size="x-small" variant="tonal">3</VChip>
          </template>
          {{ t('design-system.section.spoiler.sample.body') }}
        </Spoiler>
      </div>
    </section>

    <!-- States -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.spoiler.states') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls">
            <Spoiler v-model="disabled" disabled :title="t('design-system.section.spoiler.sample.disabledTitle')">
              {{ t('design-system.section.spoiler.sample.body') }}
            </Spoiler>
          </div>
          <span class="ds-spec">disabled</span>
        </div>
      </div>
    </section>

    <!-- Custom colours -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.spoiler.colors') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">accent</span>
          <div class="ds-controls">
            <Spoiler
              v-model="customColor"
              variant="minimal"
              color="var(--text-faint)"
              active-color="var(--accent)"
              :title="t('design-system.section.spoiler.sample.colorTitle')"
            >
              {{ t('design-system.section.spoiler.sample.body') }}
            </Spoiler>
          </div>
          <span class="ds-spec">color / active-color</span>
        </div>
        <div class="ds-row">
          <span class="ds-tag">error</span>
          <div class="ds-controls">
            <Spoiler
              variant="minimal"
              color="var(--text-faint)"
              active-color="var(--error)"
              :title="t('design-system.section.spoiler.sample.dangerTitle')"
            >
              {{ t('design-system.section.spoiler.sample.body') }}
            </Spoiler>
          </div>
          <span class="ds-spec">active-color="var(--error)"</span>
        </div>
      </div>
    </section>

    <!-- Usage -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.spoiler.usage') }}</h6>
      <CodeBlock :code="usageCode" lang="vue" />
    </section>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }
.ds-section { margin-bottom: 28px; }

.ds-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

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
