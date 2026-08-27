<script setup lang="ts">
// Список реестра исследований — общий для страницы «Исследования» и для детали группы.
// Данные и пагинация берутся из общего стора: обе страницы показывают один и тот же список,
// отличаясь только тем, выставлен ли в сторе groupCode.
//
// Раскладок две — таблица и плитки, — и различаются они РОВНО отрисовкой строки: содержимое,
// действия, фильтры, постраничность и окна у них общие. Поэтому раскладка выбирается внутри
// одной карточки, а не отдельным компонентом на каждую: второй компонент означал бы два списка,
// расходящиеся при первом же новом действии.
//
// Карточка со всей обвязкой (фильтры → список → постраничность) — та же анатомия, что у таблицы
// источников (`DocumentsTable`). Фильтры приходят слотом, потому что владеет ими страница:
// у реестра они есть, у группы — нет (группа сама и есть фильтр).
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import TablePaginationBar from '@/components/TablePaginationBar.vue'
import { useSettingsStore } from '@/stores/settings'
import { fmtDateTime } from '@/shared/utils/date'

import ResearchGroupDialog from './ResearchGroupDialog.vue'
import ResearchDeleteDialog from './ResearchDeleteDialog.vue'
import ResearchRowActions from './ResearchRowActions.vue'
import { groupColorVars } from '../constants/groupColors'
import { groupIcon } from '../constants/groupIcons'
import { useGroupsStore } from '../stores/groups.store'
import { useResearchesStore } from '../stores/researches.store'
import { setResearchGroup, type ResearchListRow } from '../api'

const props = defineProps<{ emptyText?: string }>()

const { t } = useI18n()
const router = useRouter()
const store = useResearchesStore()
const settings = useSettingsStore()

const cards = computed(() => settings.lists.researchView === 'cards')
const emptyText = computed(() => props.emptyText ?? t('research.research.list.empty'))

const DESCRIPTION_MAX = 128
const truncate = (s: string, n: number) => (s.length > n ? s.slice(0, n) + '…' : s)

const headers = [
  { title: '', key: 'actions', sortable: false, width: 84 },
  { title: t('research.research.col.research'), key: 'title', sortable: false },
  { title: t('research.research.col.areas'), key: 'area_count', sortable: false, width: 96, align: 'end' as const },
  { title: t('research.research.col.queries'), key: 'query_count', sortable: false, width: 96, align: 'end' as const },
  { title: t('research.research.col.kept'), key: 'document_kept', sortable: false, width: 104, align: 'end' as const },
  { title: t('research.research.col.filtered'), key: 'document_filtered', sortable: false, width: 104, align: 'end' as const },
  { title: t('research.research.col.updated_at'), key: 'updated_at', sortable: false, width: 170 },
]

// Один сегмент на оба кода: RESEARCH@ открывает карточку исследования, GROUP@ — список группы
// (маршруты разведены префиксом, см. routes.ts).
const researchesPath = (code: string) => `/research/researches/${code}`

function openResearch(_: unknown, row: { item: ResearchListRow }) {
  router.push(researchesPath(row.item.code))
}

function openCode(code: string) {
  router.push(researchesPath(code))
}

function onPageChange(page: number) {
  store.page = page
  store.load()
}

function onPageSizeChange(size: number) {
  store.pageSize = size
  store.resetPage()
  store.load()
}

// ── Группа и удаление ─────────────────────────────────────────────────────────
// Строка, над которой открыто окно. Держим саму строку, а не код: окнам нужны и название, и
// счётчики, а перечитывать их ради уже показанных на экране данных незачем.
const groupTarget = ref<ResearchListRow | null>(null)
const groupDialog = ref(false)
const deleteTarget = ref<ResearchListRow | null>(null)
const deleteDialog = ref(false)
// Отвязка идёт без окна, поэтому у неё есть своё «в полёте» — иначе повторный клик по пункту
// отправил бы второй запрос.
const detaching = ref<string | null>(null)

const groupsStore = useGroupsStore()

function openGroupDialog(research: ResearchListRow) {
  groupTarget.value = research
  groupDialog.value = true
}

function openDeleteDialog(research: ResearchListRow) {
  deleteTarget.value = research
  deleteDialog.value = true
}

/** Отвязка обратима и выбора не требует — окна ей не нужно. */
async function detach(research: ResearchListRow) {
  if (detaching.value) return
  detaching.value = research.code
  try {
    await setResearchGroup(research.code, null)
    afterChange()
  } catch {
    // Отказ уже показан тостом (у пункта меню нет своего места под сообщение), а вся оставшаяся
    // реакция — оставить строку в прежней группе, что и происходит без перезагрузки списка.
  } finally {
    detaching.value = null
  }
}

// Группы держат счётчик исследований, поэтому их список устаревает вместе со списком строк.
function afterChange() {
  store.load()
  if (groupsStore.items.length) groupsStore.load()
}
</script>

<template>
  <div class="researches">
    <!-- ПЛИТКИ. Сетка лежит прямо на полотне страницы: плитка сама себе рамка, и общая карточка
         вокруг дала бы рамку в рамке. Поэтому фильтры получают СВОЮ панель сверху — иначе им
         не в чем было бы жить. У таблицы наоборот: строки рамок не имеют, и панель с ними в одной
         карточке (ниже). -->
    <template v-if="cards">
      <VCard v-if="$slots.filters" variant="outlined" rounded="lg" class="filter-panel mb-3">
        <slot name="filters" />
      </VCard>

      <!-- Загрузку и пустоту у таблицы рисовал `VDataTable`; сетке их нужно дать самой, и в
           карточке — на голом полотне сообщение висело бы без опоры. -->
      <VCard v-if="store.loading && !store.items.length" variant="outlined" rounded="lg">
        <div class="cards__state"><VProgressCircular indeterminate size="28" width="3" /></div>
      </VCard>
      <VCard v-else-if="!store.items.length" variant="outlined" rounded="lg">
        <div class="cards__state text-medium-emphasis">{{ emptyText }}</div>
      </VCard>

      <div v-else class="cards__grid">
        <VCard
          v-for="item in store.items"
          :key="item.code"
          variant="outlined"
          rounded="lg"
          class="card"
          @click="openCode(item.code)"
        >
          <div class="card__head">
            <h3 class="card__title">{{ item.title }}</h3>
            <ResearchRowActions
              :research="item"
              :detaching="detaching === item.code"
              @group="openGroupDialog(item)"
              @detach="detach(item)"
              @remove="openDeleteDialog(item)"
            />
          </div>

          <p v-if="item.description" class="card__desc">
            {{ truncate(item.description, DESCRIPTION_MAX) }}
          </p>

          <!-- Полка своей плашкой, как на карточке самой полки: иконка в цвете группы плюс имя.
               Без полки подвал несёт только дату — пустой плашки «без группы» тут не нужно, её
               отсутствие и есть ответ. -->
          <footer class="card__foot">
            <span
              v-if="item.group_code"
              class="card__group color-tones"
              :style="groupColorVars(item.group_color)"
            >
              <span class="card__group-icon">
                <component :is="groupIcon(item.group_icon)" :size="14" :stroke-width="1.7" />
              </span>
              {{ item.group_name }}
            </span>
            <span class="card__date">{{ fmtDateTime(item.updated_at) }}</span>
          </footer>
        </VCard>
      </div>

      <!-- Полоса на полотне: линейка ей не нужна, отделять себя от плиток нечем и не от чего. -->
      <TablePaginationBar
        :page="store.page"
        :page-size="store.pageSize"
        :total="store.total"
        :page-count="store.pageCount"
        :divider="false"
        @update:page="onPageChange"
        @update:page-size="onPageSizeChange"
      />
    </template>

    <!-- ТАБЛИЦА: фильтры, строки и постраничность — одна карточка, отбитые линейками. -->
    <VCard v-else variant="outlined" rounded="lg">
      <template v-if="$slots.filters">
        <slot name="filters" />
        <VDivider />
      </template>

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
        @click:row="openResearch"
      >
        <template #[`item.actions`]="{ item }">
          <ResearchRowActions
            :research="item"
            :detaching="detaching === item.code"
            @group="openGroupDialog(item)"
            @detach="detach(item)"
            @remove="openDeleteDialog(item)"
          />
        </template>

        <template #[`item.title`]="{ item }">
          <div class="topic-cell">{{ item.title }}</div>
          <div v-if="item.description" class="desc-cell">
            {{ truncate(item.description, DESCRIPTION_MAX) }}
          </div>
        </template>
        <template #[`item.area_count`]="{ item }">
          <span class="count-cell">{{ item.area_count }}</span>
        </template>
        <template #[`item.query_count`]="{ item }">
          <span class="count-cell">{{ item.query_count }}</span>
        </template>
        <template #[`item.document_kept`]="{ item }">
          <span class="count-cell count-cell--kept">{{ item.document_kept }}</span>
        </template>
        <template #[`item.document_filtered`]="{ item }">
          <span class="count-cell count-cell--filtered">{{ item.document_filtered }}</span>
        </template>
        <template #[`item.updated_at`]="{ item }">
          <span class="date-cell">{{ fmtDateTime(item.updated_at) }}</span>
        </template>
      </VDataTable>

      <TablePaginationBar
        :page="store.page"
        :page-size="store.pageSize"
        :total="store.total"
        :page-count="store.pageCount"
        @update:page="onPageChange"
        @update:page-size="onPageSizeChange"
      />
    </VCard>

    <ResearchGroupDialog
      v-model="groupDialog"
      :research="groupTarget"
      @saved="afterChange"
    />
    <ResearchDeleteDialog
      v-model="deleteDialog"
      :research="deleteTarget"
      @deleted="afterChange"
    />
  </div>
</template>

<style scoped>
/* ── Плитки ─────────────────────────────────────────────────────────────────── */

/* Панель фильтров отступ несёт сама (`.filter-grid`), карточке добавлять нечего. */
.filter-panel {
  overflow: hidden;
}

.cards__state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

/* Колонка не уже 300px — в неё должны помещаться четыре подписанных счётчика в один ряд.
   Отступов у сетки нет: она лежит на полотне страницы, а поля страницы дал `PageLayout`. */
.cards__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}

/* Плитка одной высоты с соседками по ряду, а дата и группа прижаты к её низу: иначе подвал
   гулял бы по вертикали от длины описания, и ряд читался бы как набор разных карточек. */
.card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  cursor: pointer;
  transition: border-color 0.12s ease, background 0.12s ease;
}

.card:hover {
  border-color: var(--border);
  background: var(--surface-hi);
}

/* Действия прижаты к правому краю и выровнены по ПЕРВОЙ строке названия: у длинного заголовка
   центрирование увело бы их в середину плитки. */
.card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.card__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text);
}

.card__desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--text-muted);
}

/* Подвал прижат к низу плитки: описание бывает и в строку, и в три, а ряд плиток должен
   заканчиваться одной линией. */
.card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--border-soft);
}

/* Полка названа иконкой в своём цвете + именем. Цвет несёт только иконка: именем он читался бы
   как выделение, а плашка на всё имя спорила бы с рамкой самой плитки. */
.card__group {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  font-size: 11px;
  color: var(--text-muted);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.card__group-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  flex: none;
  /* Цвет полки, а без него — акцент: тот же запасной путь, что у карточки самой полки. */
  color: var(--gc-ink, var(--accent));
  background: var(--gc-fill, var(--accent-soft));
}

.card__date {
  margin-left: auto;
  font-size: 11px;
  white-space: nowrap;
  color: var(--text-faint);
}

/* ── Таблица ────────────────────────────────────────────────────────────────── */

.topic-cell {
  font-weight: 500;
  line-height: 1.4;
}

.desc-cell {
  margin-top: 2px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.45;
}

.count-cell {
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.count-cell--kept {
  color: rgb(var(--v-theme-success));
}

.count-cell--filtered {
  color: var(--text-faint);
}

.date-cell {
  white-space: nowrap;
  color: var(--text-muted);
}
</style>
