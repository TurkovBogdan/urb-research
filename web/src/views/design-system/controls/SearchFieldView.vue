<script setup lang="ts">
// Поле поиска с переключателями области. Демо идёт на нашем материале — заголовок / тела зон /
// заметки: именно так поиск по реестру и устроен, а выдуманные области показывали бы механику
// на данных, которых в приложении нет.
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconFileText, IconNote, IconLink } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'
import SearchField from '@/components/SearchField.vue'
import type { SearchScope } from '@/components/SearchField.vue'

const { t } = useI18n()

const scopes = computed<SearchScope[]>(() => [
  { key: 'areas', icon: IconFileText, label: t('design-system.section.search-field.scope.areas') },
  { key: 'notes', icon: IconNote, label: t('design-system.section.search-field.scope.notes') },
  { key: 'sources', icon: IconLink, label: t('design-system.section.search-field.scope.sources') },
])

const query = ref('')
const active = ref<string[]>(['areas'])

const plain = ref('')

const hinted = ref('')
const hintedScopes = ref<string[]>(['areas'])

const panelQuery = ref('')
const panelScopes = ref<string[]>(['areas', 'notes'])
const group = ref<string | null>(null)
const groupOptions = [
  { title: 'Laravel и PHP', value: 'laravel' },
  { title: 'Фронтенд', value: 'frontend' },
  { title: 'Инфраструктура', value: 'infra' },
]

// Обе модели в тех же кавычках, в каких уходят наружу: текст — строка, области — массив ключей.
const modelLiteral = computed(
  () => `query = '${query.value}' · scopes = [${active.value.map((key) => `'${key}'`).join(', ')}]`,
)

const usageSnippet = `<SearchField
  v-model="queryInput"
  v-model:active-scopes="store.searchScopes"
  :scopes="SEARCH_SCOPES"
  :label="t('research.research.filter.query')"
/>

<!-- Набор объявляется рядом с фильтром: ключ уходит в запрос, подпись — в подсказку. -->
const SEARCH_SCOPES: SearchScope[] = [
  { key: 'areas', icon: IconFileText, label: t('research.research.filter.scope_areas') },
  { key: 'notes', icon: IconNote, label: t('research.research.filter.scope_notes') },
]`

const reloadSnippet = `// Область меняет стог, а не сам запрос: перезапрашивать имеет смысл только тогда,
// когда запрос непустой — иначе выдача та же самая.
watch(() => store.searchScopes, () => {
  if (!queryInput.value) return
  store.resetPage()
  store.load()
})`
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.search-field.title')"
        :description="t('design-system.page.search-field.description')"
        back-to="/design-system"
      />

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.search-field.basic') }}</h6>
        <div class="ds-card">
          <div class="ds-row">
            <span class="ds-tag">scopes</span>
            <div class="ds-controls">
              <SearchField
                v-model="query"
                v-model:active-scopes="active"
                :scopes="scopes"
                :label="t('design-system.section.search-field.label')"
              />
              <p class="ds-value">{{ modelLiteral }}</p>
            </div>
            <span class="ds-spec">v-model, v-model:active-scopes</span>
          </div>

          <div class="ds-row">
            <span class="ds-tag">plain</span>
            <div class="ds-controls">
              <SearchField
                v-model="plain"
                :label="t('design-system.section.search-field.label')"
              />
              <p class="ds-value">{{ t('design-system.section.search-field.plain_note') }}</p>
            </div>
            <span class="ds-spec">без :scopes</span>
          </div>

          <!-- Пояснение под полем меняется вместе с областью: одной подписи на оба состояния не
               хватает, потому что состав стога у них разный. -->
          <div class="ds-row">
            <span class="ds-tag">hint</span>
            <div class="ds-controls">
              <SearchField
                v-model="hinted"
                v-model:active-scopes="hintedScopes"
                :scopes="scopes"
                :label="t('design-system.section.search-field.label')"
                :hint="t(hintedScopes.length
                  ? 'design-system.section.search-field.hint_deep'
                  : 'design-system.section.search-field.hint_labels')"
              />
            </div>
            <span class="ds-spec">:hint</span>
          </div>

          <div class="ds-row">
            <span class="ds-tag">density</span>
            <div class="ds-controls">
              <SearchField
                :scopes="scopes"
                :label="t('design-system.section.search-field.label')"
                density="compact"
              />
            </div>
            <span class="ds-spec">density="compact"</span>
          </div>
        </div>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.search-field.parts') }}</h6>
        <div class="ds-card">
          <div class="ds-row">
            <span class="ds-tag">query</span>
            <p class="ds-part">{{ t('design-system.section.search-field.part.query') }}</p>
            <span class="ds-spec">v-model</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">toggles</span>
            <p class="ds-part">{{ t('design-system.section.search-field.part.toggles') }}</p>
            <span class="ds-spec">#append-inner</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">focus</span>
            <p class="ds-part">{{ t('design-system.section.search-field.part.focus') }}</p>
            <span class="ds-spec">@mousedown.prevent</span>
          </div>
          <div class="ds-row">
            <span class="ds-tag">state</span>
            <p class="ds-part">{{ t('design-system.section.search-field.part.state') }}</p>
            <span class="ds-spec">tonal / text, aria-pressed</span>
          </div>
        </div>
      </section>

      <!-- Ради чего поле и заведено: оно стоит в панели фильтров рядом с прочими полями, и
           переключатели не должны ломать её сетку. -->
      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.search-field.panel') }}</h6>
        <p class="ds-note">{{ t('design-system.section.search-field.panel_note') }}</p>
        <VCard variant="outlined" rounded="lg" class="filter-panel">
          <div class="filter-grid">
            <SearchField
              v-model="panelQuery"
              v-model:active-scopes="panelScopes"
              :scopes="scopes"
              :label="t('design-system.section.search-field.label')"
            />
            <VSelect
              v-model="group"
              :items="groupOptions"
              :label="t('design-system.section.search-field.group')"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
            />
          </div>
        </VCard>
      </section>

      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.search-field.usage') }}</h6>
        <CodeBlock :code="usageSnippet" lang="vue" />
        <div class="ds-gap" />
        <p class="ds-note">{{ t('design-system.section.search-field.reload_note') }}</p>
        <CodeBlock :code="reloadSnippet" lang="ts" />
      </section>
    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 900px; }
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
}
.ds-row:last-child { border-bottom: none; }

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  padding-top: 10px;
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
  padding-top: 10px;
}

.ds-controls { min-width: 0; }

.ds-value {
  margin: 8px 0 0;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
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

.filter-panel { padding: 12px; }

/* Поиск тянется, справочный селект держит свою ширину — та же раскладка, что на страницах со списком. */
.filter-grid {
  display: grid;
  grid-template-columns: 1fr minmax(0, 220px);
  gap: 12px;
  align-items: center;
}
</style>
