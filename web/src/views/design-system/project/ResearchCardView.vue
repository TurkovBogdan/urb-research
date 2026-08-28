<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'
import ResearchCard from '@/features/research/components/ResearchCard.vue'
import type { ResearchListRow } from '@/features/research/api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const row = (over: Partial<ResearchListRow>): ResearchListRow => ({
  code: 'RESEARCH@ef8a7d2f258de68b188bda',
  title: 'PostgreSQL: безопасная конфигурация и полная изоляция подключения извне',
  description:
    'Как закрыть боевую PostgreSQL от внешнего мира и что оставить внутри: доступы, TLS, pg_hba, сеть.',
  group_code: 'GROUP@0632ba069422e69f3410bd',
  group_name: 'DevOps: настройка сервера',
  group_icon: 'server',
  group_color: 'sky',
  area_count: 5,
  query_count: 5,
  document_kept: 8,
  document_filtered: 15,
  updated_at: '2026-08-27 23:14:00',
  ...over,
})

const filed = row({})
const ungrouped = row({ code: 'RESEARCH@1b464e08943f77787fbc11', group_code: null, group_name: '' })

const longTitle = row({
  code: 'RESEARCH@95870b6e72eb40e293c564',
  title:
    'Intercom Messenger: параметры виджета (boot/update, предзаполнение email, кастом-атрибуты, auth vs anonymous)',
  group_name: 'Командные коммуникации: чат-платформы',
  group_icon: 'message',
  group_color: 'violet',
})

const bare = row({ code: 'RESEARCH@9095d573a3038110079356', description: '' })

const usageSnippet = `<script setup lang="ts">
import ResearchCard from '@/features/research/components/ResearchCard.vue'
<\/script>

<template>
  <ResearchCard
    :research="item"
    :group-filterable="true"
    @open="router.push(\`/research/researches/\${item.code}\`)"
    @rename="openRenameDialog(item)"
    @group="openGroupDialog(item)"
    @detach="detach(item)"
    @remove="openDeleteDialog(item)"
    @filter-group="filterByGroup"
  />

  <!-- Разложено по полкам: полку назвал заголовок раздела -->
  <ResearchCard :research="item" :with-group="false" @open="open(item)" />
<\/template>`
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.research-card.title')"
        :description="t('design-system.page.research-card.description')"
        back-to="/design-system"
      />

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.research-card.base') }}</h6>
        <div class="ds-host ds-grid">
          <ResearchCard :research="filed" group-filterable />
          <ResearchCard :research="ungrouped" group-filterable />
        </div>
        <p class="ds-note">
          Подвал несёт полку и дату обновления. Без полки остаётся одна дата — плашки «без
          группы» нет, её отсутствие и есть ответ.
        </p>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.research-card.group') }}</h6>
        <div class="ds-host ds-grid">
          <ResearchCard :research="filed" :with-group="false" />
          <ResearchCard :research="filed" />
        </div>
        <p class="ds-note">
          <code>with-group="false"</code> — плашка полки скрыта: так плитка выглядит в раскладке
          по группам, где полку уже назвал заголовок раздела. Слева скрыта, справа показана, но
          <code>group-filterable</code> не задан, поэтому плашка — просто метка: кликом она
          выставляет фильтр только там, где список ещё не сужен полкой.
        </p>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.research-card.edges') }}</h6>
        <div class="ds-host ds-grid">
          <ResearchCard :research="longTitle" group-filterable />
          <ResearchCard :research="bare" group-filterable />
        </div>
        <p class="ds-note">
          Длинное название переносится, описание режется на 128 символах, а подвал прижат к низу —
          плитки в ряду заканчиваются одной линией независимо от длины текста.
        </p>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.research-card.usage') }}</h6>
        <CodeBlock :code="usageSnippet" lang="vue" />
        <p class="ds-note">
          Плитка только сообщает: куда вести, что перезагружать и какие окна открывать, решает
          список. Здесь обработчики не заданы, поэтому пункты меню ничего не делают.
        </p>
      </section>
    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }
.ds-section { margin-bottom: 28px; }

.ds-host {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 16px;
}

/* Две колонки — минимум, на котором видно выравнивание подвалов у соседок по ряду. */
.ds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}

.ds-note {
  margin: 8px 2px 0;
  font-size: 12px;
  color: var(--text-faint);
}

.ds-note code {
  font-family: var(--font-mono);
  font-size: 11px;
}
</style>
