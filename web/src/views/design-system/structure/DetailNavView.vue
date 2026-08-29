<script setup lang="ts">
// Стандарт страницы-деталки: липкая колонка навигации слева, содержимое справа, шапки нет.
// Правило проверяется автоматически (tests/apps/test_web_page_header.py), поэтому здесь оно не
// пересказывается прозой, а показывается живой панелью в обоих её видах — со своим действием
// страницы и без него.
import { useI18n } from 'vue-i18n'
import { IconFolderPlus } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import DetailNav from '@/layout/components/DetailNav.vue'
import DetailHead from '@/layout/components/DetailHead.vue'
import CodeBlock from '@/components/CodeBlock.vue'

const { t } = useI18n()

const SAMPLE_CODE = 'RESEARCH@bc854947af58733bd93c3d'

// Колонку страница не рисует — она её заполняет: рамка (`DetailShell`) стоит на маршруте-родителе
// и переживает переход с артефакта на артефакт.
const snippet = `// routes.ts — деталки дети общей рамки
{
  path: '/research',
  component: () => import('@/layout/templates/DetailShell.vue'),
  children: [
    { path: 'researches/:code', name: 'research-detail', component: … },
    { path: 'areas/:code',      name: 'research-area',   component: … },
  ],
}

// ResearchView.vue
useDetailRail(() => ({
  parent: PARENT_PATH,
  label: t('research.back.researches'),
  appearance: true,
  sections: navSections.value,
  search: {
    label: t('research.research.detail.search'),
    value: store.search,
    update: (query) => { store.search = query },
    summary: store.searching ? t('research.research.detail.found', { n: store.matchCount }) : '',
  },
}))`

const templateSnippet = `<template>
  <div>
    <SectionError v-if="store.error" :error="store.error" />

    <!-- Имя артефакта принадлежит артефакту, поэтому стоит над содержимым, а не в колонке.
         Действия — у правого края этой же строки, на всех деталках в одном месте. -->
    <DetailHead :code="store.research.code" :loading="store.loading" @refresh="reload">
      <template #above><GroupLink v-bind="shelf" /></template>
      <TitleEditor variant="title" :heading="1" :title="store.research.title" … />
    </DetailHead>

    <VCard variant="outlined" rounded="lg">…</VCard>
  </div>
</template>`

// Адрес — ОДИН УРОВЕНЬ выше, а не корень раздела: у источника это зона, а не исследование и не
// реестр. Он запасной — обычно кнопка идёт по истории, и до него дело доходит лишь при заходе по
// прямой ссылке.
const parentSnippet = `const parentPath = computed(() =>
  source.value ? \`/research/areas/\${source.value.area_code}\` : '/research/researches',
)`

const SAMPLE_PARENT = '/design-system/detail-nav'
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.detail-nav.title')"
        :description="t('design-system.page.detail-nav.description')"
        back-to="/design-system"
      />

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.detail-nav.rule') }}</h6>
        <p class="ds-note">{{ t('design-system.section.detail-nav.rule_note') }}</p>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.detail-nav.panel') }}</h6>
        <p class="ds-note">{{ t('design-system.section.detail-nav.panel_note') }}</p>
        <div class="ds-frame ds-rail">
          <DetailNav
            :parent="SAMPLE_PARENT"
            :label="t('design-system.section.detail-nav.sample.exit')"
            appearance
          />
        </div>
        <CodeBlock :code="parentSnippet" lang="ts" />
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.detail-nav.head') }}</h6>
        <p class="ds-note">{{ t('design-system.section.detail-nav.head_note') }}</p>
        <div class="ds-frame">
          <DetailHead :code="SAMPLE_CODE">
            <template #more>
              <VListItem :prepend-icon="IconFolderPlus">
                <VListItemTitle>
                  {{ t('design-system.section.detail-nav.sample.move_group') }}
                </VListItemTitle>
              </VListItem>
            </template>
            <template #above>
              <span class="ds-shelf">{{ t('design-system.section.detail-nav.sample.shelf') }}</span>
            </template>
            <h1 class="ds-title">{{ t('design-system.section.detail-nav.sample.title') }}</h1>
          </DetailHead>
        </div>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.detail-nav.parts') }}</h6>
        <div class="ds-card">
          <div class="ds-row">
            <span class="ds-tag">DetailLayout</span>
            <p class="ds-part">{{ t('design-system.section.detail-nav.part.layout') }}</p>
            <span class="ds-spec">320px + minmax(0, 1fr)</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">назад</span>
            <p class="ds-part">{{ t('design-system.section.detail-nav.part.back') }}</p>
            <span class="ds-spec">история → parent</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">оформление</span>
            <p class="ds-part">{{ t('design-system.section.detail-nav.part.appearance') }}</p>
            <span class="ds-spec">карточка под панелью</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">parent</span>
            <p class="ds-part">{{ t('design-system.section.detail-nav.part.parent') }}</p>
            <span class="ds-spec">один уровень вверх</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">code</span>
            <p class="ds-part">{{ t('design-system.section.detail-nav.part.code') }}</p>
            <span class="ds-spec">вторая и последняя кнопка</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">DetailHead</span>
            <p class="ds-part">{{ t('design-system.section.detail-nav.part.head') }}</p>
            <span class="ds-spec">надпись над карточками</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">обновить</span>
            <p class="ds-part">{{ t('design-system.section.detail-nav.part.refresh') }}</p>
            <span class="ds-spec">правый край первой строки</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">more</span>
            <p class="ds-part">{{ t('design-system.section.detail-nav.part.more') }}</p>
            <span class="ds-spec">слот, иначе кнопки нет</span>
          </div>
        </div>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.detail-nav.markup') }}</h6>
        <CodeBlock :code="snippet" lang="ts" />
        <CodeBlock :code="templateSnippet" lang="vue" />
      </section>
    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 1100px; }
.ds-section { margin-bottom: 28px; }

/* Колонка живёт на полотне страницы, поэтому в демо ей нужна не карточка, а очерченное поле.
   Ширина в поле — та самая, что в стандарте: на полной ширине подписи не переносятся, и не
   видно, как карточка ведёт себя на самом деле. */
.ds-frame {
  border: 1px dashed var(--border);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 12px;
}

.ds-rail {
  max-width: 320px;
}

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 120px 1fr 220px;
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

.ds-shelf {
  font-size: 12px;
  color: var(--text-muted);
}

.ds-title {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.02em;
}
</style>
