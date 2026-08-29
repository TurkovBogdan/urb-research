<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { IconChevronRight, IconFolderPlus, IconFolderX } from '@tabler/icons-vue'

import DetailHead from '@/layout/components/DetailHead.vue'
import { useDetailRail } from '@/layout/detailRail'
import StatusBadge from '@/components/StatusBadge.vue'
import SectionError from '@/components/SectionError.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import { type NavSection } from '@/components/SectionNav.vue'
import InlineEditBlock from '@/components/InlineEditBlock.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import type { HeadingAnchor } from '@/components/markdown/render'
import { errorText } from '@/api/errorText'
import { useSettingsStore } from '@/stores/settings'
import { fmtDateTime, fmtRelative } from '@/shared/utils/date'

import BodySection from '../components/BodySection.vue'
import SourcesSection from '../components/SourcesSection.vue'
import TitleEditor from '../components/TitleEditor.vue'
import GroupLink from '../components/GroupLink.vue'
import ResearchGroupDialog from '../components/ResearchGroupDialog.vue'
import { useResearchDetailStore } from '../stores/research-detail.store'
import { useDetailReload } from '../useDetailReload'
import { UNGROUPED_CODE, setResearchGroup } from '../api'
import { NOTE_KIND_COLOR } from '../labels'

const { t } = useI18n()
const router = useRouter()
const store = useResearchDetailStore()
const settings = useSettingsStore()

const go = (path: string) => router.push(path)

// Выше исследования только реестр.
const PARENT_PATH = '/research/researches'

// Якоря разделов: один источник для `id` на самом разделе и для ссылки в боковой навигации —
// разъехавшись, они дали бы ссылку в никуда.
//
// Первый якорь стоит на шапке, а не на карточке описания: перемотка к первому пункту оглавления
// означает «вернуться к началу документа», и оставленное над кадром имя исследования читалось бы
// как обрезанная страница.
const SECTION = {
  top: 'research-top',
  body: 'research-body',
  areas: 'research-areas',
  notes: 'research-notes',
  documents: 'research-documents',
} as const

// Заголовки основного документа: размечает их сам рендерер markdown (проставляет `id` и
// отдаёт список), страница лишь принимает готовое.
const documentHeadings = ref<HeadingAnchor[]>([])

// Пустое тело не рендерится вовсе, значит и события с заголовками не будет — чистим сами,
// иначе от предыдущего исследования осталось бы чужое оглавление.
watch(() => store.research?.body, (body) => {
  if (!body) documentHeadings.value = []
})

// Показываем верхний ярус структуры документа. Третий уровень в реальных телах даёт ещё
// два десятка строк — оглавление перестало бы обозримо помещаться рядом с текстом.
const NAV_HEADING_MAX_LEVEL = 2

// Раздел прячется, только когда ищут: без поиска пустая карточка честно сообщает, что элементов
// нет, а под запросом она сказала бы неправду. Описание и основной документ — такие же документы
// исследования, поэтому подчиняются тому же правилу.
const sectionShown = computed(() => ({
  brief: !store.searching || store.briefMatches,
  body: !store.searching || store.bodyMatches,
  areas: !store.searching || store.filteredAreas.length > 0,
  notes: !store.searching || store.filteredNotes.length > 0,
  documents: !store.searching || store.filteredSources.length > 0,
}))

// Оглавление документа — необязательная часть навигации (настройка интерфейса) и бессмысленная,
// когда сам документ скрыт поиском.
const documentNavShown = computed(
  () => settings.ui.documentNav && sectionShown.value.body,
)

const navSections = computed<NavSection[]>(() => [
  ...(sectionShown.value.brief
    ? [{ id: SECTION.top, label: t('research.research.detail.brief') }]
    : []),
  ...(sectionShown.value.body
    ? [{ id: SECTION.body, label: t('research.research.detail.body') }]
    : []),
  ...(documentNavShown.value
    ? documentHeadings.value
        .filter((heading) => heading.level <= NAV_HEADING_MAX_LEVEL && heading.text)
        .map((heading) => ({ id: heading.id, label: heading.text, depth: 1 }))
    : []),
  ...(sectionShown.value.areas
    ? [{ id: SECTION.areas, label: t('research.research.detail.areas'), count: store.filteredAreas.length }]
    : []),
  ...(sectionShown.value.notes
    ? [{ id: SECTION.notes, label: t('research.research.detail.notes'), count: store.filteredNotes.length }]
    : []),
  ...(sectionShown.value.documents
    ? [{ id: SECTION.documents, label: t('research.doc.section'), count: store.filteredSources.length }]
    : []),
])

// Столько принимает бэкенд (`ResearchDescriptionBody` = ширина колонки): длиннее не отправляем.
const DESCRIPTION_MAX = 2048

// Правка описания на месте: черновик держит сам редактор, сохранение — стор. Закрывает правку
// удавшийся ответ, а не сама отправка: на отказе текст остаётся набранным, то есть человек
// попадает ровно туда, откуда повторит попытку.
const editingDescription = ref(false)

// Смена полки — то же окно, что и в реестре: вопрос один, и вторая форма разошлась бы с первой
// при первой же правке. Ответ применяем перечитыванием страницы — полка стоит на ней в двух
// местах, и оба берут её из тех же данных.
const groupDialog = ref(false)

// Отвязка обратима, но незаметна: пропадает только строка полки над названием, и промахнувшийся
// по соседнему пункту меню узнаёт об этом не сразу. Поэтому спрашиваем — тем же окном, что и в
// реестре. Отказ показываем в самом окне: тост увёл бы сообщение из поля зрения, а по открытому
// окну видно, что полка осталась.
const detachDialog = ref(false)
const detaching = ref(false)
const detachError = ref<string | null>(null)

async function detachGroup() {
  const research = store.research
  if (!research || detaching.value) return

  detaching.value = true
  detachError.value = null
  try {
    await setResearchGroup(research.code, null, { report: false })
    detachDialog.value = false
    await reload()
  } catch (e) {
    detachError.value = errorText(e)
  } finally {
    detaching.value = false
  }
}

async function saveDescription(description: string) {
  if (await store.saveDescription(description)) editingDescription.value = false
}

// Уход со страницы и переход на другое исследование закрывают правку: открытое поле с чужим
// текстом пережило бы смену данных под собой.
watch(() => store.research?.code, () => { editingDescription.value = false })

// Полка над названием есть всегда: не разложенное исследование лежит на полке-остатке «Без
// группы» — это ответ, а не его отсутствие, и ведёт он туда же, куда её карточка в реестре полок.
const shelf = computed(() => {
  const research = store.research
  if (!research) return null
  if (research.group_code) {
    return {
      code: research.group_code,
      name: research.group_name,
      icon: research.group_icon,
      color: research.group_color,
      plain: false,
    }
  }
  return {
    code: UNGROUPED_CODE,
    name: t('research.group.ungrouped.title'),
    icon: '',
    color: '',
    plain: true,
  }
})

// Точная дата отвечает «когда», относительная — «давно ли»; поодиночке каждая заставляет
// додумывать вторую.
const updatedAt = computed(() => {
  const value = store.research?.updated_at
  if (!value) return ''
  const relative = fmtRelative(value)
  return relative ? `${fmtDateTime(value)} (${relative})` : fmtDateTime(value)
})

const { reload } = useDetailReload(store.load)

// Колонку рисует общая рамка деталок — страница её только заполняет.
useDetailRail(() => ({
  parent: PARENT_PATH,
  label: t('research.back.researches'),
  appearance: true,
  sections: store.research ? navSections.value : [],
  search: store.research
    ? {
        label: t('research.research.detail.search'),
        value: store.search,
        update: (query: string) => { store.search = query },
        summary: store.searching
          ? t('research.research.detail.found', { n: store.matchCount })
          : '',
        pending: store.deepSearching ? t('research.research.detail.searching') : '',
      }
    : undefined,
}))
</script>

<template>
  <div>
    <SectionError v-if="store.error" :error="store.error" />

    <template v-if="!store.error">
      <!-- Полка и имя — не карточка, а заголовок страницы: рамка вокруг них сделала бы имя ещё
           одним блоком содержимого наравне с описанием и телом, тогда как оно надписано НАД всем
           этим. Шапка стоит вне TransitionGroup — имя принадлежит артефакту и не исчезает, когда
           поиск прячет разделы. -->
      <DetailHead
        v-if="store.research"
        :id="SECTION.top"
        :code="store.research.code"
        :loading="store.loading"
        @refresh="reload"
      >
        <template #above>
          <GroupLink v-if="shelf" v-bind="shelf" />
        </template>
        <TitleEditor
          variant="title"
          :heading="1"
          :title="store.research.title"
          :label="t('research.research.detail.title_label')"
          :saving="store.renaming"
          @save="store.rename"
        />

        <!-- Раскладка по полкам — единственное, что делают с исследованием помимо чтения и правки
             текстов, и делают редко: отсюда меню, а не пара кнопок в шапке. Отвязки нет, когда
             отвязывать не от чего. -->
        <template #more>
          <VListItem :prepend-icon="IconFolderPlus" @click="groupDialog = true">
            <VListItemTitle>
              {{ store.research.group_code
                ? t('research.research.action.move_group')
                : t('research.research.action.set_group') }}
            </VListItemTitle>
          </VListItem>
          <VListItem
            v-if="store.research.group_code"
            :prepend-icon="IconFolderX"
            @click="detachDialog = true"
          >
            <VListItemTitle>{{ t('research.research.action.unset_group') }}</VListItemTitle>
          </VListItem>
        </template>
      </DetailHead>

      <!-- Правка НА МЕСТЕ описания: поля не видно, редактируемым становится сам текст — тем же
           способом, что и имя в шапке. Открывает её ссылка ниже или двойной клик по тексту. -->
      <VCard
        v-if="store.research && sectionShown.brief"
        variant="outlined"
        rounded="lg"
        class="brief-card"
      >
        <VCardText>
          <InlineEditBlock
            v-model:editing="editingDescription"
            class="brief-desc"
            :value="store.research.description"
            :label="t('research.research.detail.description_label')"
            :empty="t('research.research.detail.no_description')"
            :maxlength="DESCRIPTION_MAX"
            :saving="store.describing"
            allow-empty
            @save="saveDescription"
          >
            <!-- Дата стоит в строке действий редактора и в правке тоже: «когда это менялось»
                 не перестаёт быть правдой оттого, что текст сейчас правят. -->
            <template #aside>
              <span class="meta-item">
                {{ t('research.field.updated_at') }}: {{ updatedAt }}
              </span>
            </template>
          </InlineEditBlock>
        </VCardText>
      </VCard>

      <!-- Разделы появляются и уходят по мере сужения поиска, поэтому переход, а не мгновенная
           подмена: иначе страница дёргается, и непонятно, что именно изменилось. Своё условие,
           потому что колонка слева переживает загрузку, а содержимое ждёт данных. -->
      <TransitionGroup
        v-if="store.research"
        name="fragment"
        tag="div"
      >

        <section v-if="sectionShown.body" :key="SECTION.body" :id="SECTION.body">
          <BodySection
            :title="t('research.research.detail.body')"
            :text="store.research.body"
            :empty="t('research.research.detail.no_body')"
            @headings="documentHeadings = $event"
          />
        </section>

        <!-- Под активным поиском раздел без совпадений скрывается целиком: пустая карточка с
             «зон пока нет» соврала бы — зоны есть, просто не про это. -->
        <section v-if="sectionShown.areas" :key="SECTION.areas" :id="SECTION.areas">
          <SectionHeader :title="t('research.research.detail.areas')" :count="store.filteredAreas.length" />
          <VCard v-if="store.filteredAreas.length" variant="outlined" rounded="lg" class="mb-4">
            <VList class="row-list">
              <template v-for="(a, i) in store.filteredAreas" :key="a.code">
                <VDivider v-if="i > 0" />
                <VListItem class="row-item" @click="go(`/research/areas/${a.code}`)">
                  <VListItemTitle class="row-title">{{ a.title }}</VListItemTitle>
                  <VListItemSubtitle v-if="a.description" class="row-sub">
                    {{ a.description }}
                  </VListItemSubtitle>
                  <template #append><IconChevronRight :size="18" class="row-chevron" /></template>
                </VListItem>
              </template>
            </VList>
          </VCard>
          <VCard v-else variant="outlined" rounded="lg" class="mb-4">
            <VCardText class="empty text-medium-emphasis">{{ t('research.research.detail.no_areas') }}</VCardText>
          </VCard>
        </section>

        <section v-if="sectionShown.notes" :key="SECTION.notes" :id="SECTION.notes">
          <SectionHeader :title="t('research.research.detail.notes')" :count="store.filteredNotes.length" />
          <TransitionGroup
            v-if="store.filteredNotes.length"
            name="fragment"
            tag="div"
            class="note-grid mb-4"
          >
            <VCard
              v-for="note in store.filteredNotes"
              :key="note.code"
              variant="outlined"
              rounded="lg"
              class="note-card"
              :to="`/research/notes/${note.code}`"
            >
              <header class="note-card__header">
                <h3 class="note-card__title">{{ note.title }}</h3>
                <StatusBadge :color="NOTE_KIND_COLOR[note.kind]">
                  {{ t(`research.note.kind.${note.kind}`) }}
                </StatusBadge>
              </header>
              <p class="note-card__desc">{{ note.description }}</p>
              <footer class="note-card__footer">{{ fmtDateTime(note.updated_at) }}</footer>
            </VCard>
          </TransitionGroup>
          <VCard v-else variant="outlined" rounded="lg" class="mb-4">
            <VCardText class="empty text-medium-emphasis">{{ t('research.research.detail.no_notes') }}</VCardText>
          </VCard>
        </section>

        <section v-if="sectionShown.documents" :key="SECTION.documents" :id="SECTION.documents">
          <!-- Без ручки «перекачать всё сломанное»: на уровне исследования это сотни строк, и по
               итогу прогона не видно, что именно чинили. Действие осталось уровнем ниже, у зоны. -->
          <SourcesSection
            :items="store.filteredSources"
            :loading="store.loading"
            @reload="reload"
          />
        </section>
      </TransitionGroup>
    </template>

    <ResearchGroupDialog v-model="groupDialog" :research="store.research" @saved="reload" />

    <ConfirmDialog
      v-model="detachDialog"
      :title="t('research.research.detach.title')"
      :confirm-label="t('research.research.action.unset_group')"
      tone="primary"
      :loading="detaching"
      @confirm="detachGroup"
    >
      {{ t('research.research.detach.text', {
        title: store.research?.title ?? '',
        group: store.research?.group_name ?? '',
      }) }}
      <VAlert v-if="detachError" type="error" variant="tonal" density="compact" class="mt-3">
        {{ detachError }}
      </VAlert>
    </ConfirmDialog>
  </div>
</template>

<style scoped>
.brief-card {
  margin-bottom: 16px;
}

/* Появление и уход фрагментов при сужении поиска. Уход быстрее прихода: исчезновение — это
   ответ на уже набранную букву, а появление должно успеть попасть в глаза.
   `fragment-move` двигает оставшиеся соседи, поэтому список не перескакивает, а сходится. */
.fragment-enter-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.fragment-leave-active {
  transition: opacity 0.13s ease, transform 0.13s ease;
}

.fragment-move {
  transition: transform 0.22s ease;
}

.fragment-enter-from,
.fragment-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

/* Движение здесь — служебное, а не смысловое: кому оно мешает, тот его отключил в системе. */
@media (prefers-reduced-motion: reduce) {
  .fragment-enter-active,
  .fragment-leave-active,
  .fragment-move {
    transition: none;
  }
}

/* Описание — такой же связный текст, как и основное тело, поэтому и набирается зоной чтения:
   те же семейство, кегль, интерлиньяж и предел длины строки, что у `.md-body`. Класс на самом
   `p` обязателен — правило для голого `p` из main.scss лежит вне слоёв, наследованием его не
   перебить (та же причина описана в MarkdownRenderer). */
.brief-desc {
  margin: 0;
  max-width: var(--reading-measure, 92ch);
  font-family: var(--font-reading);
  font-size: var(--reading-size, 14px);
  line-height: 1.7;
  color: var(--text);
  text-wrap: pretty;
}

/* Дата в строке действий редактора: гарнитура интерфейсная, поэтому наследование от читательского
   текста вокруг ей не годится — задаётся тем же способом, что и подписи ссылок рядом. */
.meta-item {
  font-family: var(--font);
  font-size: 13px;
  color: var(--text-muted);
  white-space: nowrap;
}

/* Ровно две колонки, как просили: заметки — соседи одного уровня, и переменное их число в ряду
   читалось бы как разная важность. */
.note-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 719px) {
  .note-grid {
    grid-template-columns: 1fr;
  }
}

.note-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
}

.note-card:hover {
  background: var(--surface-hi);
}

.note-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.note-card__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--text);
  text-wrap: balance;
}

/* Описание фиксировано на три строки, а дата прижата к низу (`margin-top: auto`) — так соседи
   по ряду выравниваются и по тексту, и по нижней кромке независимо от длины описания. */
.note-card__desc {
  margin: 0;
  min-height: calc(1.5em * 3);
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-muted);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.note-card__footer {
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid var(--border);
  font-size: 12px;
  color: var(--text-faint);
}

.row-item {
  cursor: pointer;
  transition: background 0.12s ease;
}

.row-item:hover {
  background: var(--surface-hi);
}

.row-append {
  display: flex;
  align-items: center;
  gap: 10px;
}

.row-chevron {
  color: var(--text-faint);
  flex: none;
  transition: color 0.12s ease, transform 0.12s ease;
}

.row-item:hover .row-chevron {
  color: rgb(var(--v-theme-primary));
  transform: translateX(2px);
}

.row-title {
  font-weight: 500;
}

.row-sub {
  color: var(--text-muted);
  font-size: 13px;
}

.empty {
  padding: 16px 0;
  text-align: center;
}
</style>
