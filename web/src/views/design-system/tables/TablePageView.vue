<script setup lang="ts">
// Анатомия табличной страницы: из чего она собирается и в каком порядке. Отдельные части
// разобраны на соседних страницах раздела (VDataTable, VTable, пагинация) — здесь показано,
// как они складываются в одну страницу, потому что это правило живёт только в коде фич.
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconSearch } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import TablePaginationBar from '@/components/TablePaginationBar.vue'
import CodeBlock from '@/components/CodeBlock.vue'

const { t } = useI18n()

interface Row {
  code: string
  title: string
  areas: number
  sources: number
  updated: string
}

const ROWS: Row[] = [
  { code: 'RESEARCH@8c1f…', title: 'Ubuntu 26.04 LTS: первичная настройка', areas: 6, sources: 27, updated: '27.08.2026 23:48' },
  { code: 'RESEARCH@2a0d…', title: 'Типографика и система отступов', areas: 8, sources: 11, updated: '27.08.2026 08:22' },
  { code: 'RESEARCH@8913…', title: 'Движок рендера Markdown для фронта', areas: 7, sources: 9, updated: '27.08.2026 08:22' },
  { code: 'RESEARCH@c176…', title: 'Глобальные экраны ошибок портала', areas: 4, sources: 0, updated: '27.08.2026 08:21' },
]

const headers = [
  { title: t('design-system.section.table-page.column.title'), key: 'title' },
  { title: t('design-system.section.table-page.column.areas'), key: 'areas', width: 90, align: 'end' as const },
  { title: t('design-system.section.table-page.column.sources'), key: 'sources', width: 110, align: 'end' as const },
  { title: t('design-system.section.table-page.column.updated'), key: 'updated', width: 190 },
]

const query = ref('')
const page = ref(1)
const pageSize = ref(25)

const filtered = computed(() => {
  const needle = query.value.trim().toLowerCase()
  return needle ? ROWS.filter((row) => row.title.toLowerCase().includes(needle)) : ROWS
})

const anatomySnippet = `<!-- Панель фильтров ВНУТРИ карточки таблицы: строки своих рамок не имеют,
     поэтому панель и строки живут в одной карточке, отбитые линейкой. -->
<VCard variant="outlined" rounded="lg">
  <div class="filter-panel">…поля фильтров…</div>
  <VDivider />

  <VDataTable
    :headers="headers"
    :items="store.items"
    :loading="store.loading"
    :items-per-page="store.pageSize"
    item-value="code"
    density="comfortable"
    hover
    hide-default-footer
    :no-data-text="emptyText"
    @click:row="open"
  />

  <TablePaginationBar
    :page="store.page"
    :page-size="store.pageSize"
    :total="store.total"
    :page-count="store.pageCount"
    @update:page="onPageChange"
    @update:page-size="onPageSizeChange"
  />
</VCard>`

const gridSnippet = `<!-- Плитки: карточка сама себе рамка, и общая карточка вокруг дала бы рамку в рамке.
     Поэтому у панели и у постраничности СВОИ карточки, а сетка лежит на полотне. -->
<VCard variant="outlined" rounded="lg" class="filter-panel mb-3">…поля фильтров…</VCard>

<div class="cards__grid">…плитки…</div>

<VCard variant="outlined" rounded="lg" class="mt-3">
  <TablePaginationBar … :divider="false" />
</VCard>`
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.table-page.title')"
        :description="t('design-system.page.table-page.description')"
        back-to="/design-system"
      />

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.table-page.assembled') }}</h6>
        <p class="ds-note">{{ t('design-system.section.table-page.assembled_note') }}</p>

        <!-- Живая сборка ровно в том виде, в каком она стоит на страницах реестра, источников,
             запросов и запусков задач. -->
        <VCard variant="outlined" rounded="lg">
          <div class="filter-panel">
            <VTextField
              v-model="query"
              :label="t('design-system.section.table-page.filter')"
              :prepend-inner-icon="IconSearch"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </div>
          <VDivider />

          <VDataTable
            :headers="headers"
            :items="filtered"
            :items-per-page="pageSize"
            item-value="code"
            density="comfortable"
            hover
            hide-default-footer
            :no-data-text="t('design-system.section.table-page.empty')"
          />

          <TablePaginationBar
            :page="page"
            :page-size="pageSize"
            :total="filtered.length"
            :page-count="Math.max(1, Math.ceil(filtered.length / pageSize))"
            @update:page="page = $event"
            @update:page-size="pageSize = $event; page = 1"
          />
        </VCard>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.table-page.parts') }}</h6>
        <div class="ds-card">
          <div class="ds-row">
            <span class="ds-tag">filters</span>
            <p class="ds-part">{{ t('design-system.section.table-page.part.filters') }}</p>
            <span class="ds-spec">VCard &gt; .filter-panel</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">head</span>
            <p class="ds-part">{{ t('design-system.section.table-page.part.head') }}</p>
            <span class="ds-spec">11px / uppercase</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">rows</span>
            <p class="ds-part">{{ t('design-system.section.table-page.part.rows') }}</p>
            <span class="ds-spec">hover, @click:row</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">footer</span>
            <p class="ds-part">{{ t('design-system.section.table-page.part.footer') }}</p>
            <span class="ds-spec">TablePaginationBar</span>
          </div>
        </div>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.table-page.placement') }}</h6>
        <p class="ds-note">{{ t('design-system.section.table-page.placement_note') }}</p>
        <CodeBlock :code="anatomySnippet" lang="vue" />
        <div class="ds-gap" />
        <CodeBlock :code="gridSnippet" lang="vue" />
      </section>
    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 1100px; }
.ds-section { margin-bottom: 28px; }

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

.ds-gap { height: 12px; }

/* Панель фильтров: те же 12px, что и на всех страницах со списком. */
.filter-panel {
  padding: 12px;
}
</style>
