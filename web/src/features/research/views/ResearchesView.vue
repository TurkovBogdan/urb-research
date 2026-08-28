<script setup lang="ts">
import { computed, onActivated, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconRefresh, IconSearch, IconSortAscending, IconSortDescending } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import SectionError from '@/components/SectionError.vue'
import { useSettingsStore } from '@/stores/settings'
import { RESEARCH_LIST_VIEWS } from '@/constants/lists'

import GroupSelect from '../components/GroupSelect.vue'
import ResearchesList from '../components/ResearchesList.vue'
import { useGroupCatalogStore } from '../stores/group-catalog.store'
import { useResearchesStore } from '../stores/researches.store'
import { RESEARCH_SORT_FIELDS, UNGROUPED_CODE, type ResearchSortBy } from '../api'

const { t } = useI18n()
const store = useResearchesStore()
// Справочник полок нужен странице не ради выбора (его держит `GroupSelect`), а ради подписи
// на чипе активного фильтра: там стоит имя выбранной полки.
const groupCatalog = useGroupCatalogStore()
// Тот же ключ, что и на странице настроек: выбор здесь — не «на этот раз», а смена предпочтения.
const settings = useSettingsStore()

const sortOptions = computed(() =>
  RESEARCH_SORT_FIELDS.map((field) => ({ title: t(`research.sort.by.${field}`), value: field })),
)

// null — все полки; UNGROUPED_CODE — только не разложенные (бэк читает пустой код именно так).
const groupFilterTitle = computed(() => {
  if (store.groupFilter === null) return t('research.group.select.all')
  if (store.groupFilter === UNGROUPED_CODE) return t('research.group.ungrouped.title')
  return groupCatalog.items.find((group) => group.code === store.groupFilter)?.title ?? ''
})

const SEARCH_DEBOUNCE_MS = 350
const queryInput = ref(store.query)
let queryTimer: ReturnType<typeof setTimeout> | null = null

watch(queryInput, (v) => {
  if ((v ?? '') === store.query) return
  if (queryTimer) clearTimeout(queryTimer)
  queryTimer = setTimeout(() => {
    store.query = v ?? ''
    store.resetPage()
    store.load()
  }, SEARCH_DEBOUNCE_MS)
})

watch(() => store.query, (v) => {
  if (v !== queryInput.value) queryInput.value = v
})

function clearAll() {
  queryInput.value = ''
  store.clearFilters()
  store.load()
}

function reload() {
  store.resetPage()
  store.load()
}

function selectGroup(code: string | null) {
  store.groupFilter = code
  reload()
}

function selectSortBy(field: ResearchSortBy) {
  store.sortBy = field
  reload()
}

function toggleSortDir() {
  store.sortDir = store.sortDir === 'desc' ? 'asc' : 'desc'
  reload()
}

// Стор общий с деталью полки, поэтому реестр каждый раз снимает с себя её контекст —
// иначе после возврата из группы список остался бы отфильтрованным. Выбранная в панели
// полка (groupFilter) — наоборот, переживает уход со страницы, как и строка поиска.
onActivated(() => {
  if (store.groupCode !== null) {
    store.groupCode = null
    store.resetPage()
  }
  store.load()
})
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('research.research.list.title')"
      :description="t('research.research.list.description')"
    >
      <template #actions>
        <VBtn variant="text" :disabled="store.loading" @click="store.load()">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': store.loading }" /></template>
          {{ t('research.action.refresh') }}
        </VBtn>
      </template>
    </PageHeader>

    <SectionError v-if="store.error" :error="store.error" />

    <!-- Фильтры отдаются таблице слотом: они рисуются в её карточке над линейкой, как панель
         фильтров у таблицы источников. -->
    <ResearchesList v-else>
      <template #filters>
        <div class="filter-grid">
          <VTextField
            v-model="queryInput"
            :label="t('research.research.filter.query')"
            :prepend-inner-icon="IconSearch"
            variant="outlined"
            density="comfortable"
            hide-details
            clearable
            class="filter-grid__search"
          />
          <GroupSelect
            :model-value="store.groupFilter"
            with-all
            with-ungrouped
            class="filter-grid__select"
            @update:model-value="selectGroup"
          />
          <!-- Поле и направление — одна ручка (`.field-group`, см. /design-system/selects):
               направление сортировки без поля, по которому сортируют, ничего не значит. -->
          <div class="field-group filter-grid__sort">
            <VSelect
              :model-value="store.sortBy"
              :items="sortOptions"
              :label="t('research.sort.label')"
              variant="outlined"
              density="comfortable"
              hide-details
              @update:model-value="selectSortBy"
            />
            <VBtn
              variant="outlined"
              density="comfortable"
              icon
              class="field-group__btn"
              :aria-label="t(`research.sort.${store.sortDir}`)"
              @click="toggleSortDir"
            >
              <IconSortAscending v-if="store.sortDir === 'asc'" :size="16" />
              <IconSortDescending v-else :size="16" />
              <VTooltip activator="parent" location="top">
                {{ t(`research.sort.${store.sortDir}`) }}
              </VTooltip>
            </VBtn>
          </div>

          <!-- Раскладка стоит последней и отбита от фильтров: она не сужает список, а меняет
               то, как он нарисован. `mandatory` — снять обе кнопки нельзя, раскладка всегда есть. -->
          <VBtnToggle
            v-model="settings.lists.researchView"
            mandatory
            density="comfortable"
            variant="outlined"
            divided
            class="filter-grid__view"
          >
            <VBtn v-for="view in RESEARCH_LIST_VIEWS" :key="view.code" :value="view.code" icon>
              <component :is="view.icon" :size="18" />
              <VTooltip activator="parent" location="top">{{ t(view.label) }}</VTooltip>
            </VBtn>
          </VBtnToggle>
        </div>

        <div v-if="store.hasActiveFilters" class="filter-chips">
          <VChip v-if="store.query" size="small" closable @click:close="queryInput = ''">
            {{ store.query }}
          </VChip>
          <VChip
            v-if="store.groupFilter !== null"
            size="small"
            closable
            @click:close="selectGroup(null)"
          >
            {{ groupFilterTitle }}
          </VChip>
          <VBtn variant="text" size="small" @click="clearAll">
            {{ t('research.action.clear_filters') }}
          </VBtn>
        </div>
      </template>
    </ResearchesList>
  </PageLayout>
</template>

<style scoped>
/* Панель живёт внутри карточки таблицы, поэтому отступ несёт она сама — как у фильтров
   источников (`.doc-filters`). Чипы дотягивают тот же отступ снизу, если они есть. */
.filter-grid {
  display: grid;
  grid-template-columns: 1fr auto auto auto;
  gap: 12px;
  align-items: center;
  padding: 12px;
}

/* Отбивка от сортировки: направление принадлежит ей, а раскладка — сама по себе. */
.filter-grid__view {
  margin-left: 4px;
}

.filter-grid__select {
  width: 220px;
}

/* Ширину держит поле; кнопка направления приросла к нему справа и в неё не входит. */
.filter-grid__sort .v-select {
  width: 220px;
}

.filter-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 0 12px 12px;
}

/* Узкий экран: каждый фильтр на свою строку во всю ширину, а кнопка направления остаётся
   рядом с выбором поля — она читается только вместе с ним. */
@media (max-width: 720px) {
  .filter-grid {
    grid-template-columns: 1fr auto;
  }

  .filter-grid__search,
  .filter-grid__select {
    grid-column: 1 / -1;
    width: auto;
  }

  .filter-grid__sort {
    grid-column: 1;
  }
}
</style>
