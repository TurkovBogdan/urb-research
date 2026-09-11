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
import { useSettingsStore } from '@/stores/settings'
import { fmtDateTime, fmtRelative } from '@/shared/utils/date'

import GroupHeading from './GroupHeading.vue'
import ResearchShelfMark from './ResearchShelfMark.vue'
import ResearchCard from './ResearchCard.vue'
import ResearchGroupDialog from './ResearchGroupDialog.vue'
import ResearchRenameDialog from './ResearchRenameDialog.vue'
import ResearchDeleteDialog from './ResearchDeleteDialog.vue'
import ResearchRowActions from './ResearchRowActions.vue'
import { useGroupsStore } from '../stores/groups.store'
import { useResearchesStore } from '../stores/researches.store'
import { resolveResearchSortBy, setResearchGroup, type ResearchListRow, type SortDir } from '../api'

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


// Заголовки кликабельны, и порядок считает бэк: ключ колонки — это ключ его белого списка
// (`RESEARCH_SORT_FIELDS`), а не поле строки. Раскладку плиток это не касается — там порядок
// по-прежнему выбирают полем сортировки в панели фильтров.
// Свободное место окна забирает название: остальные колонки — числа и дата, им сверх своего
// содержимого прибавить нечего. При фиксированной раскладке (`table-layout: fixed`, см. стили)
// `width: 100%` у одной колонки и значит «весь остаток сюда».
const GREEDY_COLUMN_WIDTH = '100%'

// Ниже этого названию с описанием тесно: обрезаться начинают уже короткие строки. Нижнюю границу
// держит вся таблица целиком (её `min-width` ниже), а не колонка: жадная колонка отдаёт место
// первой, и порог, объявленный на ней самой, ничего бы не значил.
const TITLE_MIN_WIDTH = 340

const headers = [
  { title: '', key: 'actions', sortable: false, width: 70 },
  { title: t('research.research.col.research'), key: 'title', sortable: true, width: GREEDY_COLUMN_WIDTH },
  { title: t('research.research.col.areas'), key: 'area_count', sortable: true, width: 96 },
  { title: t('research.research.col.queries'), key: 'query_count', sortable: true, width: 104 },
  { title: t('research.research.col.sources'), key: 'document_count', sortable: true, width: 150 },
  { title: t('research.research.col.updated_at'), key: 'updated_at', sortable: true, width: 170 },
  { title: t('research.research.col.created_at'), key: 'created_at', sortable: true, width: 170 },
]

// Ширина, у́же которой таблица не сжимается, а начинает прокручиваться: сумма объявленных колонок,
// где за жадную считается её порог. Считается по самим заголовкам, чтобы новая колонка не забыла
// попасть в эту сумму.
const tableMinWidth = `${headers.reduce(
  (total, header) => total + (typeof header.width === 'number' ? header.width : TITLE_MIN_WIDTH),
  0,
)}px`

interface SortItem { key: string; order: SortDir }

const tableSortBy = computed(() => [{ key: store.sortBy, order: store.sortDir }])

function onUpdateSortBy(value: SortItem[]) {
  const first = value[0]
  if (!first) return
  store.sortBy = resolveResearchSortBy(first.key)
  store.sortDir = first.order
  store.resetPage()
  store.load()
}

// Один сегмент на оба кода: RESEARCH@ открывает карточку исследования, GROUP@ — список группы
// (маршруты разведены префиксом, см. routes.ts).
const researchesPath = (code: string) => `/research/researches/${code}`

function openResearch(_: unknown, row: { item: ResearchListRow }) {
  router.push(researchesPath(row.item.code))
}

function openCode(code: string) {
  router.push(researchesPath(code))
}

// Метка полки сужает выдачу до этой полки — тем же фильтром, что и выбор в панели: она попадает
// в чипы активных фильтров, снимается оттуда же и складывается с уже набранным поиском.
function filterByShelf(code: string) {
  store.groupFilter = code
  store.resetPage()
  store.load()
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
        :sort-by="tableSortBy"
        must-sort
        item-value="code"
        density="comfortable"
        hover
        hide-default-footer
        :no-data-text="emptyText"
        @click:row="openResearch"
        @update:sort-by="onUpdateSortBy"
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

        <!-- Полка стоит меткой в начале той же ячейки, а не своей колонкой: колонка отдавала
             имени полки место, сравнимое с местом самого исследования, а различать их достаточно
             по паре «иконка + цвет» — она и так узнаётся так везде. Имя полки остаётся во
             всплывающей подписи, ссылка ведёт на её список. -->
        <template #[`item.title`]="{ item }">
          <div class="topic">
            <ResearchShelfMark
              :research="item"
              :filterable="store.groupCode === null"
              @filter="filterByShelf"
            />
            <!-- Название — первая линия, описание — вторая, и каждое занимает РОВНО одну: что не
                 поместилось по ширине, обрезается многоточием. Так у всех строк реестра одна
                 высота, и список читается сверху вниз, а не разъезжается по длине названий. -->
            <div class="topic__text" :title="item.title">
              <div class="topic-cell">{{ item.title }}</div>
              <div v-if="item.description" class="desc-cell">{{ item.description }}</div>
            </div>
          </div>
        </template>
        <template #[`item.area_count`]="{ item }">
          <span class="count-cell">{{ item.area_count }}</span>
        </template>
        <template #[`item.query_count`]="{ item }">
          <span class="count-cell">{{ item.query_count }}</span>
        </template>
        <!-- Источники одной колонкой: всего — то, по чему колонка сортируется, а за разделителем
             разбор этого числа на принятые и отсеянные. Подписи разбора живут в подсказках:
             в строке они соревновались бы за внимание с самим числом. -->
        <template #[`item.document_count`]="{ item }">
          <span class="sources-cell">
            <span class="count-cell">{{ item.document_count }}</span>
            <span class="sources-cell__divider" aria-hidden="true"></span>
            <span class="count-cell count-cell--kept" :title="t('research.research.col.kept')">
              {{ item.document_kept }}
            </span>
            <span class="count-cell count-cell--filtered" :title="t('research.research.col.filtered')">
              {{ item.document_filtered }}
            </span>
            <span class="count-cell count-cell--error" :title="t('research.research.col.errored')">
              {{ item.document_error }}
            </span>
          </span>
        </template>
        <!-- Дата и давность парой, как в остальных таблицах проекта: точное время отвечает
             «когда именно», подпись под ним — «давно ли», и второй ответ читается без счёта. -->
        <template #[`item.updated_at`]="{ item }">
          <div class="date-cell">{{ fmtDateTime(item.updated_at) }}</div>
          <div class="date-rel">{{ fmtRelative(item.updated_at) }}</div>
        </template>
        <template #[`item.created_at`]="{ item }">
          <div class="date-cell">{{ fmtDateTime(item.created_at) }}</div>
          <div class="date-rel">{{ fmtRelative(item.created_at) }}</div>
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

/* Колонки берут объявленную ширину и НЕ растут под содержимым. Иначе `nowrap` у названия и
   описания делал колонку шириной с самое длинное описание: на живых данных это 5000px и
   прокрутка во весь экран — обрезать по многоточию было бы уже нечего. Нижняя граница — у
   таблицы, а не у колонки: у́же неё таблица не сжимается, а прокручивается. */
.researches :deep(.v-table__wrapper > table) {
  table-layout: fixed;
  min-width: v-bind(tableMinWidth);
}

/* Колонка действий — служебный жёлоб, а не данные: двух кнопок ей достаточно, и правая отбивка
   ядра отрывала их от названия шириной с саму пару. Снять надо и её, и ширину в `headers`:
   при `table-layout: auto` колонка считается по содержимому, но объявленная ширина работает
   нижней границей — одной правки из двух колонка не замечает. */
.researches :deep(thead th:first-child),
.researches :deep(tbody td:first-child) {
  padding-right: 0;
}

/* Метка полки открывает ячейку, текст идёт за ней. Растягивается она по всей высоте текста
   (`stretch`), а не стоит значком у первой строки: полка — свойство всего исследования, и полем
   во всю высоту она читается как поле строки, а не как приписка к названию. */
.topic {
  display: flex;
  align-items: stretch;
  gap: 12px;
  min-width: 0;
}

.topic__text {
  flex: 1;
  min-width: 0;
}

/* Обе линии не переносятся и обрезаются многоточием — отсюда и одинаковая высота у всех строк. */
.topic-cell,
.desc-cell {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

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

/* Разбор идёт после числа-итога и держится тише него: сначала читается «сколько всего». */
.sources-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.sources-cell__divider {
  width: 1px;
  height: 12px;
  background: var(--border);
}

.count-cell--kept {
  color: var(--success);
  opacity: 0.75;
}

.count-cell--filtered {
  color: var(--text-faint);
}

.count-cell--error {
  color: var(--error);
  opacity: 0.75;
}

.date-cell {
  white-space: nowrap;
  color: var(--text-muted);
}

.date-rel {
  white-space: nowrap;
  font-size: 12px;
  color: var(--text-faint);
}
</style>
