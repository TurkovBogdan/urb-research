<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { IconAlertTriangle, IconInfoCircle } from '@tabler/icons-vue'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import Callout from '@/components/Callout.vue'
import CodeBlock from '@/components/CodeBlock.vue'

const { t } = useI18n()

const usageSnippet = `<!-- Пояснение под полем формы (описание выбранного движка поиска) -->
<VSelect v-model="engine" :items="engineOptions" hide-details="auto" />
<Callout dense :icon="IconInfoCircle">{{ engineDescription }}</Callout>

<!-- С зачином, для заметки уровня страницы -->
<Callout tone="warn" title="Движок выключен" :icon="IconAlertTriangle">
  Поиск этим движком вернёт ошибку, пока он выключен в настройках коннекторов.
</Callout>`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader
      :title="t('design-system.page.callout.title')"
      :description="t('design-system.page.callout.description')"
      back-to="/design-system"
    />

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.callout.tones') }}</h6>
      <div class="ds-card ds-stack">
        <Callout :icon="IconInfoCircle">
          {{ t('design-system.section.callout.sample.info') }}
        </Callout>
        <Callout tone="muted">{{ t('design-system.section.callout.sample.muted') }}</Callout>
        <Callout tone="warn" :icon="IconAlertTriangle">
          {{ t('design-system.section.callout.sample.warn') }}
        </Callout>
        <Callout tone="error" :icon="IconAlertTriangle">
          {{ t('design-system.section.callout.sample.error') }}
        </Callout>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.callout.title_lead') }}</h6>
      <div class="ds-card ds-stack">
        <Callout
          tone="warn"
          :icon="IconAlertTriangle"
          :title="t('design-system.section.callout.sample.lead_title')"
        >
          {{ t('design-system.section.callout.sample.lead_text') }}
        </Callout>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.callout.dense') }}</h6>
      <div class="ds-card ds-stack">
        <VSelect
          :items="['tavily', 'firecrawl', 'xai']"
          :model-value="'tavily'"
          :label="t('design-system.section.callout.sample.field')"
          variant="outlined"
          density="comfortable"
          hide-details
        />
        <Callout dense :icon="IconInfoCircle">
          {{ t('design-system.section.callout.sample.dense') }}
        </Callout>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.callout.vs_alert') }}</h6>
      <div class="ds-card ds-stack">
        <p class="ds-note">{{ t('design-system.section.callout.vs_alert_note') }}</p>
        <VAlert type="error" variant="tonal" density="compact">
          {{ t('design-system.section.callout.sample.alert') }}
        </VAlert>
        <Callout :icon="IconInfoCircle">
          {{ t('design-system.section.callout.sample.callout') }}
        </Callout>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.callout.usage') }}</h6>
      <CodeBlock :code="usageSnippet" lang="vue" />
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
  padding: 16px;
}

.ds-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ds-note {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
