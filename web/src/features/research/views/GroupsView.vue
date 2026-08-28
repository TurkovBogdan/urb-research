<script setup lang="ts">
import { computed, onActivated, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  IconCheck,
  IconCopy,
  IconDotsVertical,
  IconPencil,
  IconPlus,
  IconRefresh,
  IconSortAscending,
  IconSortDescending,
  IconTrash,
} from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import SectionError from '@/components/SectionError.vue'
import SearchField from '@/components/SearchField.vue'
import { useClipboard } from '@/composables/useClipboard'
import { deeperScope, deeperScopeModel } from '../search'
import { groupColorVars } from '../constants/groupColors'
import { GROUP_ICON_FALLBACK, groupIcon } from '../constants/groupIcons'
import GroupFormDialog from '../components/GroupFormDialog.vue'
import GroupDeleteDialog from '../components/GroupDeleteDialog.vue'
import { useGroupsStore } from '../stores/groups.store'
import { fmtDateTime } from '@/shared/utils/date'
import { GROUP_SORT_FIELDS, UNGROUPED_CODE, type GroupListRow, type GroupSortBy } from '../api'

const { t } = useI18n()
const store = useGroupsStore()

// Копируется код с префиксом (GROUP@…) — ровно в таком виде его понимают MCP-тулы, ради них
// кнопка и нужна: полка заводится руками, а сослаться на неё надо из переписки с агентом.
const { copy, isCopied } = useClipboard()

onActivated(store.load)

// Поиск идёт на бэк (тела зон и заметок до клиента не доходят), поэтому строка отложена —
// та же задержка, что и в реестре исследований.
const SEARCH_DEBOUNCE_MS = 350
const queryInput = ref(store.query)
let queryTimer: ReturnType<typeof setTimeout> | null = null

watch(queryInput, (value) => {
  if (queryTimer) clearTimeout(queryTimer)
  queryTimer = setTimeout(() => store.search(value ?? ''), SEARCH_DEBOUNCE_MS)
})

// Глубина поиска кнопкой в самом поле: она относится к этому запросу и ни к чему больше.
// Переключение перезапрашивает — сужение считается на бэке, до клиента тексты не доходят.
// Подпись поля следует за кнопкой и сама говорит, где сейчас ищем, — пояснения под полем
// поэтому нет: оно повторяло бы подпись другими словами.
const searchScopes = computed(() => deeperScope(t('research.search.scope_researches')))
const activeScopes = deeperScopeModel(() => store.inResearches, store.searchDeeper)
const searchLabel = computed(() =>
  t(store.inResearches ? 'research.group.search.label' : 'research.group.search.label_groups_only'),
)

const sortOptions = computed(() =>
  GROUP_SORT_FIELDS.map((field) => ({ title: t(`research.group.sort.by.${field}`), value: field })),
)

const selectSortBy = (field: GroupSortBy) => store.sort(field, store.sortDir)
const toggleSortDir = () => store.sort(store.sortBy, store.sortDir === 'desc' ? 'asc' : 'desc')

// Код приходит уже с типовым префиксом (GROUP@…) — он и есть сегмент адреса полки; у
// псевдо-полки «Без группы» хеш пустой, путь тот же. Кодировать код НЕЛЬЗЯ: `@` в пути
// разрешён (RFC 3986), а `%40` не совпадает с регуляркой маршрута `GROUP@.*` — адрес тогда
// уходит во вьюху исследования. Ссылка, а не обработчик клика: карточка обязана быть <a>,
// иначе нет ни средней кнопки, ни «открыть в новой вкладке».
const groupPath = (code: string) => `/research/researches/${code}`

const editing = ref<GroupListRow | null>(null)
const removing = ref<GroupListRow | null>(null)
const formOpen = ref(false)
const deleteOpen = ref(false)

// Создание и правка — одно окно: пустая карточка отличается от заполненной только тем,
// что группы у неё пока нет.
function create() {
  editing.value = null
  formOpen.value = true
}

function edit(group: GroupListRow) {
  editing.value = group
  formOpen.value = true
}

function remove(group: GroupListRow) {
  removing.value = group
  deleteOpen.value = true
}
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('research.group.list.title')"
      :description="t('research.group.list.description')"
    >
      <template #actions>
        <VBtn variant="text" :disabled="store.loading" @click="store.load">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': store.loading }" /></template>
          {{ t('research.action.refresh') }}
        </VBtn>
        <VBtn color="primary" variant="flat" @click="create">
          <template #prepend><IconPlus :size="16" /></template>
          {{ t('research.group.list.add') }}
        </VBtn>
      </template>
    </PageHeader>

    <!-- Панель поиска над полками: она их сужает, поэтому стоит отдельной карточкой сверху,
         а не внутри сетки. Видна и на пустой странице — но не пока полки грузятся. -->
    <VCard v-if="!store.loading && !store.error" variant="outlined" rounded="lg" class="filter-panel mb-3">
      <div class="filter-grid">
        <SearchField
          v-model="queryInput"
          v-model:active-scopes="activeScopes"
          :scopes="searchScopes"
          :label="searchLabel"
          :loading="store.searching"
        />
        <!-- Сортировка не сужает список, а переставляет его, поэтому стоит после поиска
             и отбита от него. Поле и направление — одна ручка (`.field-group`, живой пример
             на /design-system/selects): направление без поля ничего не значит. -->
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
      </div>
    </VCard>

    <div v-if="store.loading" class="group-grid">
      <VCard v-for="n in 3" :key="n" variant="flat" class="group-card skel-card">
        <VSkeletonLoader type="heading, text, text" />
      </VCard>
    </div>

    <SectionError v-else-if="store.error" :error="store.error" />

    <div v-else-if="store.isEmpty" class="groups-empty">
      {{ t('research.group.search.empty') }}
    </div>

    <div v-else class="group-grid">
      <!-- Цвет полки живёт на самой карточке: от него красится и плашка иконки, и обводка
           выделения (`.v-card--link` в main.scss берёт `--gc-ink`). -->
      <VCard
        v-for="group in store.visibleItems"
        :key="group.code"
        variant="flat"
        class="group-card color-tones"
        :style="groupColorVars(group.color)"
        :to="groupPath(group.code)"
      >
        <header class="group-card__header">
          <span class="group-card__icon">
            <component :is="groupIcon(group.icon)" :size="20" :stroke-width="1.6" />
          </span>
          <h3 class="group-card__title">{{ group.title }}</h3>

          <!-- Кнопки внутри ссылки-карточки: без остановки события клик уводил бы на полку. -->
          <VBtn
            icon
            variant="text"
            class="group-card__action"
            :title="isCopied(group.code) ? t('research.group.card.copied') : t('research.group.card.copy')"
            @click.stop.prevent="copy(group.code)"
          >
            <IconCheck
              v-if="isCopied(group.code)"
              :size="16"
              :stroke-width="1.6"
              class="group-card__action--done"
            />
            <IconCopy v-else :size="16" :stroke-width="1.6" />
          </VBtn>

          <VMenu location="bottom end" :offset="4">
            <template #activator="{ props: menu }">
              <VBtn
                v-bind="menu"
                icon
                variant="text"
                class="group-card__action group-card__action--last"
                :title="t('research.group.card.actions')"
                @click.stop.prevent
              >
                <IconDotsVertical :size="16" :stroke-width="1.6" />
              </VBtn>
            </template>

            <VList density="compact">
              <VListItem :prepend-icon="IconPencil" @click="edit(group)">
                <VListItemTitle>{{ t('common.action.edit') }}</VListItemTitle>
              </VListItem>
              <VListItem :prepend-icon="IconTrash" class="group-card__menu-danger" @click="remove(group)">
                <VListItemTitle>{{ t('research.group.card.delete') }}</VListItemTitle>
              </VListItem>
            </VList>
          </VMenu>
        </header>

        <p class="group-card__desc">{{ group.description }}</p>

        <!-- Дата рядом со счётчиком объясняет порядок по умолчанию: без неё карточки стояли бы
             в последовательности, причины которой на экране не видно. У пустой полки её нет —
             прочерк был бы шумом там, где отсутствие и есть ответ. -->
        <footer class="group-card__footer">
          <span class="group-card__count">{{ group.research_count }}</span>
          <span class="group-card__count-label">{{ t('research.group.card.researches') }}</span>
          <span v-if="group.research_updated_at" class="group-card__worked">
            {{ fmtDateTime(group.research_updated_at) }}
            <VTooltip activator="parent" location="top">
              {{ t('research.group.card.worked_at') }}
            </VTooltip>
          </span>
        </footer>
      </VCard>

      <!-- Полка, которой нет в БД: сюда попадает всё, что не разложено. Всегда последняя и
           приглушена — это не выбор пользователя, а остаток. Под поиском исчезает наравне с
           обычными: у неё тоже либо совпало что-то из лежащих на ней исследований, либо нет. -->
      <VCard
        v-if="store.ungroupedVisible"
        variant="flat"
        class="group-card group-card--auto"
        :to="groupPath(UNGROUPED_CODE)"
      >
        <header class="group-card__header">
          <span class="group-card__icon">
            <component :is="GROUP_ICON_FALLBACK" :size="20" :stroke-width="1.6" />
          </span>
          <h3 class="group-card__title">{{ t('research.group.ungrouped.title') }}</h3>
        </header>

        <p class="group-card__desc">{{ t('research.group.ungrouped.description') }}</p>

        <footer class="group-card__footer">
          <span class="group-card__count">{{ store.ungroupedCount }}</span>
          <span class="group-card__count-label">{{ t('research.group.card.researches') }}</span>
        </footer>
      </VCard>
    </div>

    <GroupFormDialog v-model="formOpen" :group="editing" @saved="store.load" />
    <GroupDeleteDialog
      v-model="deleteOpen"
      :group="removing"
      @deleted="store.load"
    />
  </PageLayout>
</template>

<style scoped>
/* Панель управления списком: те же 12px внутри, что у панелей фильтров в реестре и в источниках.
   Отступ несёт сетка внутри, карточке добавлять нечего. */
.filter-panel {
  overflow: hidden;
}

/* Выравнивание по ВЕРХУ, а не по центру, как в реестре исследований: у поля поиска под ним
   висит пояснение, поэтому оно выше соседей — по центру селект и кнопка уехали бы вниз. */
.filter-grid {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: start;
  padding: 12px;
}

/* Ширину держит поле; кнопка направления приросла к нему справа и в эту ширину не входит.
   Коробка самой кнопки — в утилите `.field-group__btn` (main.scss). */
.filter-grid__sort .v-select {
  width: 260px;
}

.groups-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  color: var(--text-muted);
  font-size: 13px;
}

.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px;
}

.skel-card { min-height: 132px; }
.skel-card :deep(.v-skeleton-loader) { width: 100%; padding: 0; }

.group-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  cursor: pointer;
  transition: background-color 120ms ease;
}

.group-card:hover { background: var(--surface-hi); }

/* Автоматическая полка отличается от настоящих: пунктир вместо заливки-плашки у иконки. */
.group-card--auto .group-card__icon {
  color: var(--text-muted);
  background: transparent;
  border: 1px dashed var(--border);
}

.group-card--auto .group-card__title { color: var(--text-muted); }

.group-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  /* Цвет полки, а без него — акцент: у псевдо-полки «Без группы» его и не может быть. */
  color: var(--gc-ink, var(--accent));
  background: var(--gc-fill, var(--accent-soft));
  flex: none;
}

.group-card__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
  line-height: 1.3;
  flex: 1;
  min-width: 0;
}

/* Коробка задана здесь, а не пропсами `size`/`density`: у иконочной кнопки Vuetify считает сторону
   как `--v-btn-height + 12px`, а density правит только высоту — обе ручки дают то прямоугольник,
   то размер крупнее исходного. Незаслоённое правило перебивает `@layer vuetify-components`
   (см. docs/frontend/vuetify-css-patterns), поэтому хватает обычного объявления.
   Крайняя правая утоплена вбок: иначе её кромка съезжает вправо от края текста. */
.group-card__action {
  width: 26px;
  min-width: 26px;
  height: 26px;
  color: var(--text-faint);
}

.group-card__action--last { margin-right: -4px; }

/* Отбивка шапки (10px) разделяет заголовок и кнопки, но между собой кнопки — одна группа
   управления, и та же величина рвала бы её надвое. */
.group-card__action + .group-card__action {
  margin-left: -6px;
}

.group-card__action:hover { color: var(--text); }

/* Отметка «скопировано» держится полторы секунды — цвет успеха отличает её от обычного ховера. */
.group-card__action--done { color: var(--success); }

.group-card__menu-danger :deep(.v-list-item-title) { color: var(--error); }
.group-card__menu-danger :deep(.v-list-item__prepend) { color: var(--error); }

/* Счётчик прижат к низу карточки — карточки в ряду выравниваются по нижней границе. */
.group-card__footer {
  display: flex;
  align-items: baseline;
  gap: 6px;
  border-top: 1px solid var(--border);
  padding-top: 12px;
  margin-top: auto;
}

.group-card__count {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  line-height: 1;
}

.group-card__count-label {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
}

/* Дата прижата к правому краю подвала: слева счётчик — то, сколько тут лежит, справа — когда
   этого касались; два ответа об одной полке, но о разном, и разводить их по краям читается
   быстрее, чем ставить в строку. */
.group-card__worked {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-faint);
}

/* Описание фиксировано на две строки: короткие резервируют высоту, длинные обрезаются
   многоточием — карточки в ряду выравниваются по высоте (как на /connectors). */
.group-card__desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  margin: -6px 0 0;
  min-height: calc(1.5em * 2);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
