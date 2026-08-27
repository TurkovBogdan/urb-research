<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconRefresh } from '@tabler/icons-vue'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'

const { t } = useI18n()

const levels = [1, 2, 3, 4] as const

const loadingDemo = ref(true)

const usageSnippet = `<!-- Секция внутри страницы: уровень задаёт и тег <h*>, и кегль -->
<SectionHeader :title="t('research.research.detail.areas')" :count="areas.length" />

<!-- Правый слот — кнопка или бейдж рядом с заголовком -->
<SectionHeader title="Источники" :count="12">
  <template #right>
    <VBtn variant="text" size="small" :prepend-icon="IconRefresh">Обновить</VBtn>
  </template>
</SectionHeader>

<!-- Шапка страницы собрана поверх того же компонента: PageHeader = кнопка «назад» + уровень 1 -->
<PageHeader title="Исследование" back-to="/research/researches" :loading="store.loading" />`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader
      :title="t('design-system.page.section-header.title')"
      :description="t('design-system.page.section-header.description')"
      back-to="/design-system"
    />

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.section-header.levels') }}</h6>
      <div class="ds-card">
        <div v-for="level in levels" :key="level" class="ds-row">
          <span class="ds-tag">h{{ level }}</span>
          <div class="ds-controls ds-controls--block">
            <SectionHeader
              :level="level"
              :title="t('design-system.section.section-header.sample.title')"
            />
          </div>
          <span class="ds-spec">:level="{{ level }}"</span>
        </div>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.section-header.parts') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">count</span>
          <div class="ds-controls ds-controls--block">
            <SectionHeader
              :title="t('design-system.section.section-header.sample.title')"
              :count="12"
            />
          </div>
          <span class="ds-spec">:count="12"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">description</span>
          <div class="ds-controls ds-controls--block">
            <SectionHeader
              :title="t('design-system.section.section-header.sample.title')"
              :description="t('design-system.section.section-header.sample.desc')"
            />
          </div>
          <span class="ds-spec">:description</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">right</span>
          <div class="ds-controls ds-controls--block">
            <SectionHeader
              :title="t('design-system.section.section-header.sample.title')"
              :count="12"
            >
              <template #right>
                <VBtn variant="text" size="small" :prepend-icon="IconRefresh">
                  {{ t('design-system.section.section-header.sample.action') }}
                </VBtn>
              </template>
            </SectionHeader>
          </div>
          <span class="ds-spec">#right</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">loading</span>
          <div class="ds-controls ds-controls--block">
            <SectionHeader
              :level="1"
              :loading="loadingDemo"
              :title="t('design-system.section.section-header.sample.title')"
              :description="t('design-system.section.section-header.sample.desc')"
            />
            <VBtn variant="text" size="small" @click="loadingDemo = !loadingDemo">
              {{ t('design-system.section.section-header.toggle') }}
            </VBtn>
          </div>
          <span class="ds-spec">:loading</span>
        </div>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.section-header.page_level') }}</h6>
      <div class="ds-card ds-card--padded">
        <p class="ds-note">{{ t('design-system.section.section-header.page_level_note') }}</p>
        <PageHeader
          :title="t('design-system.section.section-header.sample.page_title')"
          :description="t('design-system.section.section-header.sample.desc')"
          back-to="/design-system"
        >
          <template #actions>
            <VBtn variant="text" size="small" :prepend-icon="IconRefresh">
              {{ t('design-system.section.section-header.sample.action') }}
            </VBtn>
          </template>
        </PageHeader>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.section-header.usage') }}</h6>
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
  overflow: hidden;
}
.ds-card--padded { padding: 16px; }

.ds-row {
  display: grid;
  grid-template-columns: 100px 1fr 140px;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
}
.ds-row:last-child { border-bottom: none; }

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
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
/* Заголовок занимает всю ширину колонки: он и есть предмет показа, а не элемент в ряду. */
.ds-controls--block { display: block; }

.ds-note {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--text-muted);
}
</style>
