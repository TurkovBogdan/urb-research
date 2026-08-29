<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconChevronRight } from '@tabler/icons-vue'

import DetailHead from '@/layout/components/DetailHead.vue'
import { useDetailRail } from '@/layout/detailRail'
import SectionError from '@/components/SectionError.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import { type NavSection } from '@/components/SectionNav.vue'
import InlineEditBlock from '@/components/InlineEditBlock.vue'
import type { HeadingAnchor } from '@/components/markdown/render'
import { useSettingsStore } from '@/stores/settings'
import { fmtDateTime, fmtRelative } from '@/shared/utils/date'

import BodySection from '../components/BodySection.vue'
import SourcesSection from '../components/SourcesSection.vue'
import TitleEditor from '../components/TitleEditor.vue'
import { useAreaDetailStore } from '../stores/area-detail.store'
import { useDetailReload } from '../useDetailReload'

const { t } = useI18n()
const router = useRouter()
const store = useAreaDetailStore()
const settings = useSettingsStore()

const go = (path: string) => router.push(path)

// На уровень выше зоны — исследование, которому она принадлежит. Пока зоны нет, подниматься
// некуда, кроме реестра: её код приезжает вместе с ней, и подпись выхода едет за адресом.
const parentPath = computed(() =>
  store.area ? `/research/researches/${store.area.research_code}` : '/research/researches',
)

const parentLabel = computed(() =>
  store.area ? t('research.back.research') : t('research.back.researches'),
)

// Якоря разделов: один источник для `id` на самом разделе и для ссылки в боковой навигации —
// разъехавшись, они дали бы ссылку в никуда. Первый якорь стоит на шапке: перемотка к первому
// пункту оглавления означает «вернуться к началу документа».
const SECTION = {
  top: 'area-top',
  task: 'area-task',
  body: 'area-body',
  queries: 'area-queries',
  documents: 'area-documents',
} as const

// Заголовки синтеза: размечает их сам рендерер markdown (проставляет `id` и отдаёт список),
// страница лишь принимает готовое.
const documentHeadings = ref<HeadingAnchor[]>([])

watch(() => store.area?.body, (body) => {
  if (!body) documentHeadings.value = []
})

const NAV_HEADING_MAX_LEVEL = 2

// Раздел прячется, только когда ищут: без поиска пустая карточка честно сообщает, что элементов
// нет, а под запросом она сказала бы неправду.
const sectionShown = computed(() => ({
  brief: !store.searching || store.briefMatches,
  task: (!store.searching || store.taskMatches) && task.value.length > 0,
  body: !store.searching || store.bodyMatches,
  queries: !store.searching || store.filteredQueries.length > 0,
  documents: !store.searching || store.filteredSources.length > 0,
}))

const documentNavShown = computed(() => settings.ui.documentNav && sectionShown.value.body)

const navSections = computed<NavSection[]>(() => [
  ...(sectionShown.value.brief
    ? [{ id: SECTION.top, label: t('research.area.detail.brief') }]
    : []),
  ...(sectionShown.value.task
    ? [{ id: SECTION.task, label: t('research.area.detail.task') }]
    : []),
  ...(sectionShown.value.body
    ? [{ id: SECTION.body, label: t('research.area.detail.body') }]
    : []),
  ...(documentNavShown.value
    ? documentHeadings.value
        .filter((heading) => heading.level <= NAV_HEADING_MAX_LEVEL && heading.text)
        .map((heading) => ({ id: heading.id, label: heading.text, depth: 1 }))
    : []),
  ...(sectionShown.value.queries
    ? [{ id: SECTION.queries, label: t('research.area.detail.queries'), count: store.filteredQueries.length }]
    : []),
  ...(sectionShown.value.documents
    ? [{ id: SECTION.documents, label: t('research.doc.section'), count: store.filteredSources.length }]
    : []),
])

// Столько принимает бэкенд (`AreaDescriptionBody` = ширина колонки): длиннее не отправляем.
// У зоны потолок свой и вчетверо ниже исследовательского — описание зоны это строка списка.
const DESCRIPTION_MAX = 512

// Правка описания на месте: черновик держит сам редактор, сохранение — стор. Закрывает правку
// удавшийся ответ, а не сама отправка: на отказе текст остаётся набранным.
const editingDescription = ref(false)

async function saveDescription(description: string) {
  if (await store.saveDescription(description)) editingDescription.value = false
}

watch(() => store.area?.code, () => { editingDescription.value = false })

// Точная дата отвечает «когда», относительная — «давно ли»; поодиночке каждая заставляет
// додумывать вторую.
const updatedAt = computed(() => {
  const value = store.area?.updated_at
  if (!value) return ''
  const relative = fmtRelative(value)
  return relative ? `${fmtDateTime(value)} (${relative})` : fmtDateTime(value)
})

// Постановка задачи области: что ищем, где границы, чего ждём. Пишет её MCP, поэтому здесь она
// только читается — в отличие от описания над ней.
const task = computed(() => {
  const area = store.area
  if (!area) return []
  return [
    { label: t('research.area.detail.objective'), text: area.objective },
    { label: t('research.area.detail.scope'), text: area.scope },
    { label: t('research.area.detail.expectations'), text: area.expectations },
  ].filter((field) => field.text)
})

const { reload } = useDetailReload(store.load)

// Колонку рисует общая рамка деталок — страница её только заполняет.
useDetailRail(() => ({
  parent: parentPath.value,
  label: parentLabel.value,
  appearance: true,
  sections: store.area ? navSections.value : [],
  search: store.area
    ? {
        label: t('research.area.detail.search'),
        value: store.search,
        update: (query: string) => { store.search = query },
        summary: store.searching
          ? t('research.area.detail.found', { n: store.matchCount })
          : '',
      }
    : undefined,
}))
</script>

<template>
  <div>
    <SectionError v-if="store.error" :error="store.error" />

    <template v-if="store.area">
      <DetailHead
        :id="SECTION.top"
        :code="store.area.code"
        :loading="store.loading"
        @refresh="reload"
      >
        <!-- Над именем — исследование, которому зона принадлежит: то же место, что занимает
             полка над именем исследования, и тот же ответ на вопрос «где я нахожусь». -->
        <template #above>
          <RouterLink :to="parentPath" class="parent-link">
            {{ store.area.research_title }}
          </RouterLink>
        </template>
        <TitleEditor
          variant="title"
          :heading="1"
          :title="store.area.title"
          :label="t('research.area.detail.title_label')"
          :saving="store.renaming"
          @save="store.rename"
        />
      </DetailHead>

      <!-- Вводное описание — своей карточкой, как у исследования: это ответ своими словами,
           отдельный от заполненной агентом постановки под ним. -->
      <VCard v-if="sectionShown.brief" variant="outlined" rounded="lg" class="brief-card">
        <VCardText>
          <InlineEditBlock
            v-model:editing="editingDescription"
            class="brief-desc"
            :value="store.area.description"
            :label="t('research.area.detail.description_label')"
            :empty="t('research.area.detail.no_description')"
            :maxlength="DESCRIPTION_MAX"
            :saving="store.describing"
            allow-empty
            @save="saveDescription"
          >
            <!-- Дата стоит в строке действий редактора и в правке тоже: «когда это менялось»
                 не перестаёт быть правдой оттого, что текст сейчас правят. -->
            <template #aside>
              <span class="meta-item">{{ t('research.field.updated_at') }}: {{ updatedAt }}</span>
            </template>
          </InlineEditBlock>
        </VCardText>
      </VCard>

      <TransitionGroup name="fragment" tag="div">
        <!-- Постановку правит не человек, а агент: карточка только читается. -->
        <section v-if="sectionShown.task" :key="SECTION.task" :id="SECTION.task">
          <SectionHeader :title="t('research.area.detail.task')" />
          <VCard variant="outlined" rounded="lg" class="mb-4">
            <VCardText class="task-card">
              <dl class="task-fields">
                <template v-for="field in task" :key="field.label">
                  <dt class="task-label">{{ field.label }}</dt>
                  <dd class="task-text">{{ field.text }}</dd>
                </template>
              </dl>
            </VCardText>
          </VCard>
        </section>

        <section v-if="sectionShown.body" :key="SECTION.body" :id="SECTION.body">
          <BodySection
            :title="t('research.area.detail.body')"
            :text="store.area.body"
            :empty="t('research.area.detail.no_body')"
            @headings="documentHeadings = $event"
          />
        </section>

        <section v-if="sectionShown.queries" :key="SECTION.queries" :id="SECTION.queries">
          <SectionHeader
            :title="t('research.area.detail.queries')"
            :count="store.filteredQueries.length"
          />
          <VCard v-if="store.filteredQueries.length" variant="outlined" rounded="lg" class="mb-4">
            <VList class="row-list">
              <template v-for="(q, i) in store.filteredQueries" :key="q.code">
                <VDivider v-if="i > 0" />
                <VListItem class="row-item" @click="go(`/research/queries/${q.code}`)">
                  <VListItemTitle class="row-title">{{ q.query }}</VListItemTitle>
                  <template #append><IconChevronRight :size="18" class="row-chevron" /></template>
                </VListItem>
              </template>
            </VList>
          </VCard>
          <VCard v-else variant="outlined" rounded="lg" class="mb-4">
            <VCardText class="empty text-medium-emphasis">
              {{ t('research.area.detail.no_queries') }}
            </VCardText>
          </VCard>
        </section>

        <section v-if="sectionShown.documents" :key="SECTION.documents" :id="SECTION.documents">
          <SourcesSection
            :items="store.filteredSources"
            :loading="store.loading"
            @reload="reload"
          />
        </section>
      </TransitionGroup>
    </template>
  </div>
</template>

<style scoped>
.brief-card {
  margin-bottom: 16px;
}

/* Та же метрика и тот же приглушённый тон, что у полки над именем исследования: строка над
   заголовком означает одно и то же на обеих страницах, и разными она читалась бы как разное. */
.parent-link {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: 12px;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.14s ease;
}

.parent-link:hover {
  color: var(--text);
}


/* Описание — такой же связный текст, как и синтез, поэтому и набирается зоной чтения. Класс на
   самом `p` обязателен — правило для голого `p` из main.scss лежит вне слоёв (та же причина
   описана в MarkdownRenderer). */
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

/* Постановка — такое же чтение, как основной текст, поэтому и воздуха ей столько же. */
.task-card {
  padding: 28px 16px;
}

.task-fields {
  margin: 0;
}

.task-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-faint);
  margin-bottom: 4px;
}

/* Типографика зоны чтения — та же, что у описания и основного текста: постановку читают
   абзацами, а не просматривают как подпись к полю. */
.task-text {
  margin: 0 0 20px;
  max-width: var(--reading-measure, 92ch);
  font-family: var(--font-reading);
  font-size: var(--reading-size, 14px);
  line-height: 1.7;
  color: var(--text);
  white-space: pre-wrap;
  text-wrap: pretty;
}

.task-text:last-child {
  margin-bottom: 0;
}

.row-item {
  cursor: pointer;
  transition: background 0.12s ease;
}

.row-item:hover {
  background: var(--surface-hi);
}

.row-title {
  font-weight: 500;
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

.empty {
  padding: 16px 0;
  text-align: center;
}

/* Появление и уход разделов при сужении поиска — те же величины, что и на исследовании. */
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

@media (prefers-reduced-motion: reduce) {
  .fragment-enter-active,
  .fragment-leave-active,
  .fragment-move {
    transition: none;
  }
}
</style>
