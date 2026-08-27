<script setup lang="ts">
// Стандарт шапки страницы: одна анатомия на все страницы приложения. Правило проверяется
// автоматически (tests/apps/test_web_page_header.py), поэтому здесь оно не пересказывается
// прозой, а показывается в двух формах, которые только и встречаются.
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconCopy, IconRefresh } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'

const { t } = useI18n()

const loadingDemo = ref(true)

const listSnippet = `<!-- Страница списка: имя раздела, что в нём лежит, действия над списком.
     Возврата нет — в раздел приходят из меню, а не из другой страницы. -->
<PageHeader :title="t('research.research.list.title')" :description="t('research.research.list.description')">
  <template #actions>
    <VBtn variant="text" :disabled="store.loading" @click="store.load">…Обновить…</VBtn>
  </template>
</PageHeader>`

const detailSnippet = `<!-- Страница объекта: возврат, имя самого объекта, действия над ним.
     Описания нет — под ним уже лежит сам объект, и вторая подпись была бы шумом. -->
<PageHeader :title="research?.title || t('…detail.title')" :loading="store.loading" back-to="/research/researches">
  <!-- Слот заменяет заголовок целиком вместе с тегом — под правку названия на месте. -->
  <template v-if="store.research" #title>
    <TitleEditor variant="title" :heading="1" :title="store.research.title" @save="store.rename" />
  </template>
  <template #actions>…</template>
</PageHeader>`
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.page-header.title')"
        :description="t('design-system.page.page-header.description')"
        back-to="/design-system"
      />

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.page-header.rule') }}</h6>
        <p class="ds-note">{{ t('design-system.section.page-header.rule_note') }}</p>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.page-header.list_form') }}</h6>
        <p class="ds-note">{{ t('design-system.section.page-header.list_note') }}</p>
        <div class="ds-frame">
          <PageHeader
            :title="t('design-system.section.page-header.sample.list_title')"
            :description="t('design-system.section.page-header.sample.list_desc')"
          >
            <template #actions>
              <VBtn variant="text">
                <template #prepend><IconRefresh :size="16" /></template>
                {{ t('design-system.section.page-header.sample.refresh') }}
              </VBtn>
            </template>
          </PageHeader>
        </div>
        <CodeBlock :code="listSnippet" lang="vue" />
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.page-header.detail_form') }}</h6>
        <p class="ds-note">{{ t('design-system.section.page-header.detail_note') }}</p>
        <div class="ds-frame">
          <PageHeader
            :title="t('design-system.section.page-header.sample.detail_title')"
            back-to="/design-system/page-header"
          >
            <template #actions>
              <VBtn variant="text">
                <template #prepend><IconRefresh :size="16" /></template>
                {{ t('design-system.section.page-header.sample.refresh') }}
              </VBtn>
              <VBtn variant="text">
                <template #prepend><IconCopy :size="16" /></template>
                {{ t('design-system.section.page-header.sample.copy') }}
              </VBtn>
            </template>
          </PageHeader>
        </div>
        <CodeBlock :code="detailSnippet" lang="vue" />
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.page-header.parts') }}</h6>
        <div class="ds-card">
          <div class="ds-row">
            <span class="ds-tag">back-to</span>
            <p class="ds-part">{{ t('design-system.section.page-header.part.back') }}</p>
            <span class="ds-spec">align-items: flex-start</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">title</span>
            <p class="ds-part">{{ t('design-system.section.page-header.part.title') }}</p>
            <span class="ds-spec">SectionHeader :level="1"</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">description</span>
            <p class="ds-part">{{ t('design-system.section.page-header.part.description') }}</p>
            <span class="ds-spec">только у списков</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">actions</span>
            <p class="ds-part">{{ t('design-system.section.page-header.part.actions') }}</p>
            <span class="ds-spec">variant="text"</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">loading</span>
            <p class="ds-part">{{ t('design-system.section.page-header.part.loading') }}</p>
            <span class="ds-spec">:loading</span>
          </div>
        </div>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.page-header.loading') }}</h6>
        <p class="ds-note">{{ t('design-system.section.page-header.loading_note') }}</p>
        <div class="ds-frame">
          <PageHeader
            :title="t('design-system.section.page-header.sample.detail_title')"
            :loading="loadingDemo"
            back-to="/design-system/page-header"
          />
        </div>
        <VBtn variant="outlined" size="small" @click="loadingDemo = !loadingDemo">
          {{ t('design-system.section.page-header.toggle') }}
        </VBtn>
      </section>
    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 1100px; }
.ds-section { margin-bottom: 28px; }

/* Шапка живёт на полотне страницы, поэтому в демо ей нужна не карточка, а очерченное поле:
   иначе непонятно, где её границы и сколько места она занимает. */
.ds-frame {
  border: 1px dashed var(--border);
  border-radius: var(--radius);
  padding: 16px 16px 0;
  margin-bottom: 12px;
}

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 100px 1fr 220px;
  align-items: start;
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

.ds-part {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}

.ds-note {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 12px;
  max-width: 720px;
}
</style>
