<script setup lang="ts">
// Список реестра исследований — общий для страницы «Исследования» и для детали группы.
// Данные и пагинация берутся из общего стора: обе страницы показывают один и тот же список,
// отличаясь только тем, выставлен ли в сторе groupCode.
//
// Раскладки две — таблица и плитки по полкам, — и различаются они РОВНО отрисовкой строк:
// содержимое, действия, фильтры, постраничность и окна у них общие. Поэтому раскладка
// выбирается внутри одной карточки, а не отдельным компонентом на каждую: второй компонент
// означал бы два списка, расходящиеся при первом же новом действии.
//
// Карточка со всей обвязкой (фильтры → список → постраничность) — та же анатомия, что у таблицы
// источников (`DocumentsTable`). Фильтры приходят слотом, потому что владеет ими страница:
// у реестра они есть, у группы — нет (группа сама и есть фильтр).
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import TablePaginationBar from '@/components/TablePaginationBar.vue'
import { errorText } from '@/api/errorText'
import { RESEARCH_PAGE_SIZES } from '@/constants/lists'
import { useSettingsStore } from '@/stores/settings'
import { fmtDateTime } from '@/shared/utils/date'

import GroupHeading from './GroupHeading.vue'
import ResearchCard from './ResearchCard.vue'
import ResearchGroupDialog from './ResearchGroupDialog.vue'
import ResearchRenameDialog from './ResearchRenameDialog.vue'
import ResearchDeleteDialog from './ResearchDeleteDialog.vue'
import ResearchRowActions from './ResearchRowActions.vue'
import { useGroupsStore } from '../stores/groups.store'
import { useResearchesStore } from '../stores/researches.store'
import { setResearchGroup, type ResearchListRow } from '../api'

const props = defineProps<{ emptyText?: string }>()

const { t } = useI18n()
const router = useRouter()
const store = useResearchesStore()
const settings = useSettingsStore()

// Разложить по полкам можно только реестр: на странице самой полки все плитки принадлежат ей
// одной, и раздел повторял бы заголовок страницы. Там те же плитки идут общим потоком.
const tiled = computed(() => settings.lists.researchView === 'grouped')
const sectioned = computed(() => tiled.value && store.groupCode === null)
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

// ── Разделы полок ─────────────────────────────────────────────────────────────
// Порядок разделов задаёт панель: полка встаёт туда, где в отсортированном списке встретилось
// первое её исследование, — то есть разделы упорядочены тем же полем, что и сам список.
// Внутри раздела порядок свой и всегда один: свежие сверху.
//
// Раскладываем ТУ ЖЕ страницу выдачи, что показывают остальные раскладки: постраничность общая,
// и раздел здесь означает «эти исследования на текущей странице», а не всю полку целиком.
interface ResearchSection {
  /** Пустая строка — не разложенные: у псевдо-полки кода нет. */
  code: string
  title: string
  icon: string
  color: string
  items: ResearchListRow[]
}

// Даты приходят в SQL-формате (`YYYY-MM-DD HH:MM:SS`) — он сортируется как строка.
const byUpdatedAtDesc = (a: ResearchListRow, b: ResearchListRow) =>
  b.updated_at.localeCompare(a.updated_at)

const sections = computed<ResearchSection[]>(() => {
  const byGroup = new Map<string, ResearchSection>()
  for (const item of store.items) {
    const code = item.group_code ?? ''
    let section = byGroup.get(code)
    if (!section) {
      section = {
        code,
        title: code ? item.group_name : t('research.group.ungrouped.title'),
        icon: item.group_icon,
        color: item.group_color,
        items: [],
      }
      byGroup.set(code, section)
    }
    section.items.push(item)
  }
  for (const section of byGroup.values()) section.items.sort(byUpdatedAtDesc)
  return [...byGroup.values()]
})

function onPageChange(page: number) {
  store.page = page
  store.load()
}

function onPageSizeChange(size: number) {
  store.pageSize = size
  store.resetPage()
  store.load()
}

// ── Переименование, группа и удаление ─────────────────────────────────────────
// Строка, над которой открыто окно. Держим саму строку, а не код: окнам нужны и название, и
// счётчики, а перечитывать их ради уже показанных на экране данных незачем.
const renameTarget = ref<ResearchListRow | null>(null)
const renameDialog = ref(false)
const groupTarget = ref<ResearchListRow | null>(null)
const groupDialog = ref(false)
const deleteTarget = ref<ResearchListRow | null>(null)
const deleteDialog = ref(false)
const detachTarget = ref<ResearchListRow | null>(null)
const detachDialog = ref(false)
const detaching = ref(false)
// Отказ показываем в самом окне, рядом с кнопкой: тост увёл бы сообщение из поля зрения,
// а окно остаётся открытым — видно, что полка не снята.
const detachError = ref<string | null>(null)

const groupsStore = useGroupsStore()

function openRenameDialog(research: ResearchListRow) {
  renameTarget.value = research
  renameDialog.value = true
}

function openGroupDialog(research: ResearchListRow) {
  groupTarget.value = research
  groupDialog.value = true
}

function openDeleteDialog(research: ResearchListRow) {
  deleteTarget.value = research
  deleteDialog.value = true
}

// Отвязка обратима, но незаметна: строка просто уезжает из полки, и промахнувшийся по соседнему
// пункту меню узнаёт об этом, только заметив пропажу. Поэтому спрашиваем.
function openDetachDialog(research: ResearchListRow) {
  detachTarget.value = research
  detachError.value = null
  detachDialog.value = true
}

async function detach() {
  const research = detachTarget.value
  if (!research || detaching.value) return
  detaching.value = true
  detachError.value = null
  try {
    await setResearchGroup(research.code, null, { report: false })
    detachDialog.value = false
    afterChange()
  } catch (e) {
    detachError.value = errorText(e)
  } finally {
    detaching.value = false
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
    <template v-if="tiled">
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

      <!-- Разложенные по полкам: те же плитки, но каждая полка — свой раздел под заголовком.
           Плашка полки внутри плитки при этом убрана: раздел её уже назвал. -->
      <div v-else-if="sectioned" class="sections">
        <section v-for="section in sections" :key="section.code" class="sections__item">
          <GroupHeading
            :title="section.title"
            :icon="section.icon"
            :color="section.color"
            :ungrouped="!section.code"
          />
          <div class="cards__grid">
            <ResearchCard
              v-for="item in section.items"
              :key="item.code"
              :research="item"
              :with-group="false"
              @open="openCode(item.code)"
              @rename="openRenameDialog(item)"
              @group="openGroupDialog(item)"
              @detach="openDetachDialog(item)"
              @remove="openDeleteDialog(item)"
            />
          </div>
        </section>
      </div>

      <!-- Страница одной полки: разделов нет, потому что полка тут одна — те же плитки общим
           потоком. -->
      <div v-else class="cards__grid">
        <ResearchCard
          v-for="item in store.items"
          :key="item.code"
          :research="item"
          @open="openCode(item.code)"
          @rename="openRenameDialog(item)"
          @group="openGroupDialog(item)"
          @detach="openDetachDialog(item)"
          @remove="openDeleteDialog(item)"
        />
      </div>

      <!-- Постраничность в своей карточке — зеркало панели фильтров сверху: обе не часть сетки,
           а управление ею, и на голом полотне висели бы без опоры. Линейка внутри не нужна:
           карточка и есть граница, отделять полосу больше не от чего. -->
      <VCard variant="outlined" rounded="lg" class="mt-3">
        <TablePaginationBar
          :page="store.page"
          :page-size="store.pageSize"
          :total="store.total"
          :page-count="store.pageCount"
          :page-sizes="RESEARCH_PAGE_SIZES"
          :divider="false"
          @update:page="onPageChange"
          @update:page-size="onPageSizeChange"
        />
      </VCard>
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
            @rename="openRenameDialog(item)"
            @group="openGroupDialog(item)"
            @detach="openDetachDialog(item)"
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
        :page-sizes="RESEARCH_PAGE_SIZES"
        @update:page="onPageChange"
        @update:page-size="onPageSizeChange"
      />
    </VCard>

    <!-- Переименование не трогает ни полки, ни счётчики — списку хватает своей перезагрузки. -->
    <ResearchRenameDialog
      v-model="renameDialog"
      :research="renameTarget"
      @saved="store.load()"
    />
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
    <ConfirmDialog
      v-model="detachDialog"
      :title="t('research.research.detach.title')"
      :confirm-label="t('research.research.action.unset_group')"
      tone="primary"
      :loading="detaching"
      @confirm="detach"
    >
      {{ t('research.research.detach.text', {
        title: detachTarget?.title ?? '',
        group: detachTarget?.group_name ?? '',
      }) }}
      <VAlert v-if="detachError" type="error" variant="tonal" density="compact" class="mt-3">
        {{ detachError }}
      </VAlert>
    </ConfirmDialog>
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

/* Колонка не уже 300px — на этой ширине подвал плитки ещё держит плашку полки и дату одной
   строкой. Отступов у сетки нет: она лежит на полотне страницы, а поля страницы дал `PageLayout`.

   Сверху колонки ограничены числом: на широком мониторе `auto-fill` набирал пятую и шестую, и
   плитка вырождалась в узкую полоску, где название переносится на четыре строки. Потолок задан
   не медиазапросом, а нижней границей самой дорожки — «не уже доли ряда»: пока ряд узкий,
   работает пол в 300px и колонок становится 3, 2, 1, а как только доля ряда его перерастает,
   ширина дорожки упирается в неё, и больше `--cards-max-columns` штук уже не помещается. */
.cards__grid {
  --cards-gap: 12px;
  --cards-max-columns: 4;
  --cards-min-column: 300px;
  --cards-column-share: calc(
    (100% - (var(--cards-max-columns) - 1) * var(--cards-gap)) / var(--cards-max-columns)
  );

  display: grid;
  grid-template-columns: repeat(
    auto-fill,
    minmax(max(var(--cards-min-column), var(--cards-column-share)), 1fr)
  );
  gap: var(--cards-gap);
}

/* Разделы полок отбиты друг от друга сильнее, чем плитки внутри раздела: расстояние и есть
   граница раздела, а заголовок с линейкой лишь называет его. */
.sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.sections__item {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
