<script setup lang="ts">
// Деталь полки: карточка группы + тот же список исследований, что и в реестре, но
// суженный до этой полки. Адрес — /research/researches/GROUP@<code>: сегмент общий с
// карточкой исследования, маршруты разведены по префиксу кода (см. routes.ts).
//
// Пустой хеш (GROUP@) — псевдо-полка «Без группы»: строки в БД у неё нет, поэтому за карточкой
// не ходим, а заголовок и описание берём из словаря. Список при этом фильтруется тем же
// параметром — бэк понимает пустой код как «только не разложенные».
import { computed, onActivated, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconRefresh } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import SectionError from '@/components/SectionError.vue'
import SearchField from '@/components/SearchField.vue'

import ResearchesList from '../components/ResearchesList.vue'
import { deeperScope, deeperScopeModel } from '../search'
import { useResearchesStore } from '../stores/researches.store'
import { getGroup, UNGROUPED_CODE, type GroupRow } from '../api'

const { t } = useI18n()
const route = useRoute()
const store = useResearchesStore()

const group = ref<GroupRow | null>(null)
const error = ref<unknown>(null)

const groupCode = computed(() => {
  const code = route.params.code
  return typeof code === 'string' ? code : ''
})

const ungrouped = computed(() => groupCode.value === UNGROUPED_CODE)

const title = computed(() => (
  ungrouped.value ? t('research.group.ungrouped.title') : group.value?.title ?? t('research.group.detail.title')
))

const description = computed(() => (
  ungrouped.value
    ? t('research.group.ungrouped.description')
    : group.value?.description || t('research.group.detail.description')
))

async function load() {
  error.value = null
  // Стор общий с реестром и с соседними полками, а строка поиска в нём переживает уход со
  // страницы. Смена контекста её снимает: чужой запрос, приехавший сюда, дал бы пустой список
  // без видимой причины. Возврат на ту же полку запрос сохраняет — это уже твой поиск.
  if (store.groupCode !== groupCode.value) {
    store.groupCode = groupCode.value
    store.query = ''
    store.resetPage()
  }
  if (ungrouped.value) {
    group.value = null
  } else {
    try {
      // Отказ показывает сама страница (SectionError) — тост дублировал бы его.
      group.value = await getGroup(groupCode.value, { report: false })
    } catch (e) {
      group.value = null
      error.value = e
      return
    }
  }
  await store.load()
}

// KeepAlive держит вьюху живой между визитами — перезагружаем и на активации,
// и на смене кода в адресе, иначе показали бы предыдущую полку.
//
// Пустой код грузить нельзя, и это не редкий случай: вьюха остаётся живой после ухода, а
// `groupCode` читает ГЛОБАЛЬНЫЙ маршрут — возврат в список групп обнуляет его и будит этот
// наблюдатель. Полки с пустым кодом не существует (у псевдо-полки «Без группы» код `GROUP@`),
// так что пустой означает ровно одно: адрес больше не наш. Тот же гейт стоит у соседних деталок.
onActivated(load)
watch(groupCode, (code) => {
  if (code) load()
})

// Поиск идёт на бэк и по всему тексту исследования (тела зон и заметок до клиента не доходят),
// поэтому строка отложена — та же задержка, что в реестре и на странице групп.
const SEARCH_DEBOUNCE_MS = 350
const queryInput = ref(store.query)
let queryTimer: ReturnType<typeof setTimeout> | null = null

watch(queryInput, (value) => {
  if (queryTimer) clearTimeout(queryTimer)
  queryTimer = setTimeout(() => {
    store.query = value ?? ''
    store.resetPage()
    store.load()
  }, SEARCH_DEBOUNCE_MS)
})

// Синхронизация в обратную сторону: строку чистит `load()` при смене полки, поле обязано
// последовать — иначе в нём остался бы текст, которому уже ничего не соответствует.
watch(() => store.query, (value) => {
  if (value !== queryInput.value) queryInput.value = value
})

// Та же кнопка, что на странице групп, и то же правило: спуститься на слой ниже показанного.
// Здесь показаны исследования, поэтому слой ниже — их тексты (тело, зоны, заметки); выключено
// значит «только названия и описания». Подпись поля и пояснение следуют за кнопкой.
const searchScopes = computed(() => deeperScope(t('research.search.scope_bodies')))
const activeScopes = deeperScopeModel(() => store.inBodies, store.searchDeeper)
const searchLabel = computed(() =>
  t(store.inBodies ? 'research.research.filter.query_deep' : 'research.research.filter.query_labels'),
)
const searchHint = computed(() =>
  t(store.inBodies ? 'research.research.filter.query_hint' : 'research.research.filter.query_hint_labels'),
)
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="title"
      :loading="store.loading && !group && !ungrouped"
      back-to="/research/groups"
    >
      <!-- Описание полки — обычный текст: иконка в строке прозы читалась как случайный значок,
           а не как метка. Вид полки (иконка и цвет) остаётся там, где полка — объект: на её
           карточке в списке групп и на строке исследования. -->
      <template v-if="group || ungrouped" #description>
        {{ description }}
      </template>
      <template #actions>
        <VBtn variant="text" :disabled="store.loading" @click="load">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': store.loading }" /></template>
          {{ t('research.action.refresh') }}
        </VBtn>
      </template>
    </PageHeader>

    <SectionError v-if="error" :error="error" />
    <SectionError v-else-if="store.error" :error="store.error" />
    <!-- Поиск отдаётся списку слотом, как в реестре: он сам знает, где панели жить — в карточке
         таблицы под линейкой или отдельной карточкой над плитками. -->
    <!-- Пустой список под поиском означает не то же, что пустая полка: исследования на ней есть,
         просто ни одно не совпало — особенно при выключенных телах. -->
    <ResearchesList
      v-else
      :empty-text="t(store.query ? 'research.group.detail.empty_search' : 'research.group.detail.empty')"
    >
      <template #filters>
        <div class="filter-row">
          <SearchField
            v-model="queryInput"
            v-model:active-scopes="activeScopes"
            :scopes="searchScopes"
            :label="searchLabel"
            :hint="searchHint"
            :loading="store.loading"
          />
        </div>
      </template>
    </ResearchesList>
  </PageLayout>
</template>

<style scoped>
/* Отступ панели — на ней самой, как у сетки фильтров в реестре: карточку рисует список,
   и добавлять ей поля некуда. */
.filter-row {
  padding: 12px;
}

</style>
