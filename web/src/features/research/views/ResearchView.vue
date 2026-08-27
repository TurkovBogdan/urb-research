<script setup lang="ts">
import { computed, onActivated, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { IconCheck, IconChevronRight, IconCopy, IconRefresh, IconSearch } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import SectionError from '@/components/SectionError.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import SectionNav, { type NavSection } from '@/components/SectionNav.vue'
import type { HeadingAnchor } from '@/components/markdown/render'
import { useClipboard } from '@/composables/useClipboard'
import { useSettingsStore } from '@/stores/settings'
import { fmtDateTime, fmtRelative } from '@/shared/utils/date'

import ResearchBody from '../components/ResearchBody.vue'
import DocumentsTable from '../components/DocumentsTable.vue'
import TitleEditor from '../components/TitleEditor.vue'
import { groupColorVars } from '../constants/groupColors'
import { groupIcon } from '../constants/groupIcons'
import { useResearchDetailStore } from '../stores/research-detail.store'
import { useSourcesRefetch } from '../useSourcesRefetch'
import { refetchResearchDocuments } from '../api'
import { NOTE_KIND_COLOR } from '../labels'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useResearchDetailStore()
const settings = useSettingsStore()
const { copy, isCopied } = useClipboard()

const go = (path: string) => router.push(path)

// Куда возвращает шапка при прямом заходе (ссылка, перезагрузка): по истории идти некуда.
const RESEARCHES_PATH = '/research/researches'

// Якоря разделов: один источник для `id` на самом разделе и для ссылки в боковой навигации —
// разъехавшись, они дали бы ссылку в никуда.
const SECTION = {
  brief: 'research-brief',
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
    ? [{ id: SECTION.brief, label: t('research.research.detail.brief') }]
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
    ? [{ id: SECTION.documents, label: t('research.research.detail.documents'), count: store.filteredSources.length }]
    : []),
])

// Точная дата отвечает «когда», относительная — «давно ли»; поодиночке каждая заставляет
// додумывать вторую.
const updatedAt = computed(() => {
  const value = store.research?.updated_at
  if (!value) return ''
  const relative = fmtRelative(value)
  return relative ? `${fmtDateTime(value)} (${relative})` : fmtDateTime(value)
})

// KeepAlive wraps all routed views (App.vue), so reload on every activation, and on an
// in-place param change while active — otherwise a cached instance shows stale data.
function reload() {
  const code = route.params.code
  if (typeof code === 'string' && code) store.load(code)
}
onActivated(reload)
watch(() => route.params.code, reload)

// Повтор получения материала: ручка уровня исследования чинит все его источники без материала.
// Код берём из загруженного исследования, а не из адреса, — он приходит уже нормализованным.
const { refetchingAll, refetchingCode, refetchAllSources, refetchOneSource } = useSourcesRefetch(
  () => refetchResearchDocuments(store.research?.code ?? ''),
  reload,
)
</script>

<template>
  <PageLayout>
    <!-- Стандартная шапка страницы, как у всех остальных: возврат, название, действия.
         Название себя же и правит — пока данных нет, слот не рисуется и работает плейсхолдер. -->
    <PageHeader
      :title="store.research?.title || t('research.research.detail.title')"
      :loading="store.loading"
      :back-to="RESEARCHES_PATH"
    >
      <template v-if="store.research" #title>
        <TitleEditor
          variant="title"
          :heading="1"
          :title="store.research.title"
          :label="t('research.research.detail.title_label')"
          :saving="store.renaming"
          @save="store.rename"
        />
      </template>

      <template #actions>
        <VBtn variant="text" :disabled="store.loading" @click="reload">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': store.loading }" /></template>
          {{ t('research.action.refresh') }}
        </VBtn>
        <VBtn v-if="store.research" variant="text" @click="copy(store.research.code)">
          <template #prepend>
            <IconCheck v-if="isCopied(store.research.code)" :size="16" :stroke-width="1.6" />
            <IconCopy v-else :size="16" :stroke-width="1.6" />
          </template>
          {{ isCopied(store.research.code) ? t('research.action.copied') : t('research.action.copy') }}
        </VBtn>
      </template>
    </PageHeader>

    <SectionError v-if="store.error" :error="store.error" />

    <!-- Двенадцать колонок: три под липкую навигацию по разделам, девять под содержимое. Обе
         колонки — дети одной сетки и начинаются с одной строки, поэтому верх плашки сам встаёт
         вровень с первым разделом. -->
    <div v-if="!store.error" class="detail-grid">
      <!-- Левая колонка целиком липкая: поиск и оглавление держатся вместе, иначе первый уехал бы
           вверх, а второе осталось — и они разъехались бы на полэкрана. -->
      <div class="detail-grid__rail">
        <!-- Полка над колонкой, а не в карточке поиска: она отвечает не «что искать», а «где это
             лежит», и на полотне читается как надпись над разделом, а не как часть инструмента.
             Без полки строки нет вовсе — её отсутствие и есть ответ. -->
        <p v-if="store.research?.group_code" class="rail-group color-tones" :style="groupColorVars(store.research.group_color)">
          <component :is="groupIcon(store.research.group_icon)" :size="14" :stroke-width="1.7" class="rail-group__icon" />
          {{ store.research.group_name }}
        </p>

        <!-- Карточка ждёт данных вместе с остальным: имя и выход со страницы теперь несёт шапка,
             и держать пустую рамку на время загрузки больше незачем. -->
        <VCard v-if="store.research" variant="outlined" rounded="lg" class="rail-tools">
          <VTextField
            v-model="store.search"
            :label="t('research.research.detail.search')"
            :prepend-inner-icon="IconSearch"
            variant="outlined"
            density="comfortable"
            hide-details
            clearable
          />
          <!-- Пока догоняющая половина в пути, счётчик — промежуточный: говорим об этом, иначе
               дорисовавшиеся фрагменты выглядели бы как самопроизвольная перестановка. -->
          <p v-if="store.searching" class="rail-tools__summary">
            {{ t('research.research.detail.found', { n: store.matchCount }) }}
            <span v-if="store.deepSearching" class="rail-tools__pending">
              <VProgressCircular indeterminate size="11" width="2" />
              {{ t('research.research.detail.searching') }}
            </span>
          </p>
        </VCard>

        <SectionNav v-if="store.research" :sections="navSections" />
      </div>

      <!-- Разделы появляются и уходят по мере сужения поиска, поэтому переход, а не мгновенная
           подмена: иначе страница дёргается, и непонятно, что именно изменилось. Своё условие,
           потому что колонка слева переживает загрузку, а содержимое ждёт данных. -->
      <TransitionGroup
        v-if="store.research"
        name="fragment"
        tag="div"
        class="detail-grid__main"
      >
        <section v-if="sectionShown.brief" :key="SECTION.brief" :id="SECTION.brief">
          <SectionHeader :title="t('research.research.detail.brief')" />
          <VCard variant="outlined" rounded="lg" class="mb-4">
            <VCardText>
              <p v-if="store.research.description" class="brief-desc">
                {{ store.research.description }}
              </p>
              <div class="meta-row">
                <span class="meta-item">
                  {{ t('research.field.updated_at') }}: {{ updatedAt }}
                </span>
              </div>
            </VCardText>
          </VCard>
        </section>

        <section v-if="sectionShown.body" :key="SECTION.body" :id="SECTION.body">
          <SectionHeader :title="t('research.research.detail.body')" />
          <VCard variant="outlined" rounded="lg" class="mb-4">
            <VCardText>
              <ResearchBody
                v-if="store.research.body"
                :text="store.research.body"
                @headings="documentHeadings = $event"
              />
              <div v-else class="empty text-medium-emphasis">
                {{ t('research.research.detail.no_body') }}
              </div>
            </VCardText>
          </VCard>
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
          <SectionHeader
            :title="t('research.research.detail.documents')"
            :count="store.filteredSources.length"
          />
          <DocumentsTable
            :items="store.filteredSources"
            :loading="store.loading"
            :refetching-all="refetchingAll"
            :refetching-code="refetchingCode"
            @refetch-all="refetchAllSources"
            @refetch-one="refetchOneSource"
          />
        </section>
      </TransitionGroup>
    </div>
  </PageLayout>
</template>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 0 24px;
  align-items: start;
}

/* Три трека под колонку с поиском и оглавлением: ей нужна ширина под подпись, а не под текст.
   Отбивка сверху повторяет ту, с которой начинается заголовок первого раздела
   (`SectionHeader` даёт 4px) — без неё колонка ровно на столько же выше содержимого.
   Липкость на всей колонке, а не на оглавлении: иначе поиск уехал бы вверх без него. */
.detail-grid__rail {
  grid-column: span 3;
  min-width: 0;
  margin-top: 4px;
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: calc(100vh - 132px);
}

.rail-tools {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: none;
}

/* Полка над колонкой: плашка того же вида, что на карточке исследования в списке — иконка в цвете
   группы плюс имя. Отступ снизу тот же, что у сетки колонки (12px), поэтому строка читается как
   надпись над карточкой, а не как оторванный элемент. */
.rail-group {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  min-width: 0;
  font-size: 12px;
  color: var(--text-muted);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* Цвет несёт иконка, а не имя: тон выбран под плашку и текстом читался бы хуже подписи.
   Без цвета — акцент, как везде, где полка нарисована. */
.rail-group__icon {
  color: var(--gc-ink, var(--accent));
  flex: none;
}

.rail-tools__summary {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
}

/* Догоняющая половина поиска: строкой рядом со счётчиком, а не отдельным местом — она уточняет
   именно его число. */
.rail-tools__pending {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-left: 6px;
  color: var(--text-faint);
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

/* min-width: 0 обязателен: без него таблица источников с длинными url раздувает свой трек,
   и вся сетка уезжает за экран. */
.detail-grid__main {
  grid-column: span 9;
  min-width: 0;
}

/* На узком экране отдельная колонка под навигацию — уже не запас, а отнятое у текста место:
   обе встают в полную ширину друг под другом (в строку оглавление перестраивается само). */
@media (max-width: 1099px) {
  .detail-grid__rail,
  .detail-grid__main {
    grid-column: 1 / -1;
  }

  .detail-grid__rail {
    position: static;
    max-height: none;
    margin-bottom: 12px;
  }
}

/* Описание — такой же связный текст, как и основное тело, поэтому и набирается зоной чтения:
   те же семейство, кегль, интерлиньяж и предел длины строки, что у `.md-body`. Класс на самом
   `p` обязателен — правило для голого `p` из main.scss лежит вне слоёв, наследованием его не
   перебить (та же причина описана в MarkdownRenderer). */
.brief-desc {
  margin: 0 0 12px;
  max-width: var(--reading-measure, 92ch);
  font-family: var(--font-reading);
  font-size: var(--reading-size, 14px);
  line-height: 1.7;
  color: var(--text);
  text-wrap: pretty;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.meta-item {
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
