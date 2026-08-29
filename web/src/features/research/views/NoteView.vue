<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import DetailHead from '@/layout/components/DetailHead.vue'
import { useDetailRail } from '@/layout/detailRail'
import SectionError from '@/components/SectionError.vue'
import { type NavSection } from '@/components/SectionNav.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import InlineEditBlock from '@/components/InlineEditBlock.vue'
import type { HeadingAnchor } from '@/components/markdown/render'
import { useSettingsStore } from '@/stores/settings'
import { fmtDateTime, fmtRelative } from '@/shared/utils/date'

import BodySection from '../components/BodySection.vue'
import TitleEditor from '../components/TitleEditor.vue'
import { useNoteDetailStore } from '../stores/note-detail.store'
import { useDetailReload } from '../useDetailReload'
import { NOTE_KIND_COLOR } from '../labels'

const { t } = useI18n()
const store = useNoteDetailStore()
const settings = useSettingsStore()
const { reload } = useDetailReload(store.load)

// Заметка привязана только к исследованию — зоны у неё нет, поэтому уровень выше всегда один.
const parentPath = computed(() =>
  store.note ? `/research/researches/${store.note.research_code}` : '/research/researches',
)

const parentLabel = computed(() =>
  store.note ? t('research.back.research') : t('research.back.researches'),
)

// Якоря разделов: один источник для `id` на самом разделе и для ссылки в боковой навигации.
// Первый стоит на шапке: перемотка к первому пункту означает «вернуться к началу документа».
const SECTION = {
  top: 'note-top',
  body: 'note-body',
} as const

const documentHeadings = ref<HeadingAnchor[]>([])

watch(() => store.note?.body, (body) => {
  if (!body) documentHeadings.value = []
})

const NAV_HEADING_MAX_LEVEL = 2

// Раздел прячется, только когда ищут: без поиска пустая карточка честно сообщает, что текста
// нет, а под запросом она сказала бы неправду.
const sectionShown = computed(() => ({
  brief: !store.searching || store.briefMatches,
  body: !store.searching || store.bodyMatches,
}))

const documentNavShown = computed(() => settings.ui.documentNav && sectionShown.value.body)

const navSections = computed<NavSection[]>(() => [
  ...(sectionShown.value.brief
    ? [{ id: SECTION.top, label: t('research.note.detail.brief') }]
    : []),
  ...(sectionShown.value.body
    ? [{ id: SECTION.body, label: t('research.note.detail.body') }]
    : []),
  ...(documentNavShown.value
    ? documentHeadings.value
        .filter((heading) => heading.level <= NAV_HEADING_MAX_LEVEL && heading.text)
        .map((heading) => ({ id: heading.id, label: heading.text, depth: 1 }))
    : []),
])

// Столько принимает бэкенд (`NoteDescriptionBody` = ширина колонки): длиннее не отправляем.
const DESCRIPTION_MAX = 512

// Правка описания на месте: черновик держит сам редактор, сохранение — стор. Закрывает правку
// удавшийся ответ, а не сама отправка: на отказе текст остаётся набранным.
const editingDescription = ref(false)

async function saveDescription(description: string) {
  if (await store.saveDescription(description)) editingDescription.value = false
}

watch(() => store.note?.code, () => { editingDescription.value = false })

// Точная дата отвечает «когда», относительная — «давно ли»; поодиночке каждая заставляет
// додумывать вторую.
const updatedAt = computed(() => {
  const value = store.note?.updated_at
  if (!value) return ''
  const relative = fmtRelative(value)
  return relative ? `${fmtDateTime(value)} (${relative})` : fmtDateTime(value)
})

// Колонку рисует общая рамка деталок — страница её только заполняет.
useDetailRail(() => ({
  parent: parentPath.value,
  label: parentLabel.value,
  appearance: true,
  sections: store.note ? navSections.value : [],
  search: store.note
    ? {
        label: t('research.note.detail.search'),
        value: store.search,
        update: (query: string) => { store.search = query },
        summary: store.searching
          ? t('research.note.detail.found', { n: store.matchCount })
          : '',
      }
    : undefined,
}))
</script>

<template>
  <div>
    <SectionError v-if="store.error" :error="store.error" />

    <template v-if="store.note">
      <DetailHead
        :id="SECTION.top"
        :code="store.note.code"
        :loading="store.loading"
        @refresh="reload"
      >
        <!-- Над именем — исследование, которому заметка принадлежит: то же место и тот же
             ответ «где я нахожусь», что у полки над именем исследования. -->
        <template #above>
          <RouterLink :to="parentPath" class="parent-link">
            {{ store.note.research_title }}
          </RouterLink>
        </template>
        <!-- Вид стоит В строке имени: это свойство самой заметки, как и её название, а не место,
             где она лежит. -->
        <div class="note-title">
          <StatusBadge :color="NOTE_KIND_COLOR[store.note.kind]">
            {{ t(`research.note.kind.${store.note.kind}`) }}
          </StatusBadge>
          <TitleEditor
            variant="title"
            :heading="1"
            :title="store.note.title"
            :label="t('research.note.detail.title_label')"
            :saving="store.renaming"
            @save="store.rename"
          />
        </div>
      </DetailHead>

      <VCard v-if="sectionShown.brief" variant="outlined" rounded="lg" class="brief-card">
        <VCardText>
          <InlineEditBlock
            v-model:editing="editingDescription"
            class="brief-desc"
            :value="store.note.description"
            :label="t('research.note.detail.description_label')"
            :empty="t('research.note.detail.no_description')"
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
        <section v-if="sectionShown.body" :key="SECTION.body" :id="SECTION.body">
          <BodySection
            :title="t('research.note.detail.body')"
            :text="store.note.body"
            :empty="t('research.note.detail.no_body')"
            @headings="documentHeadings = $event"
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

/* Шильдик и имя — одна строка: правка имени открывается на месте, поэтому строке нужен и
   верхний край по центру шильдика, и вся оставшаяся ширина под само имя. */
.note-title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.note-title > :last-child {
  min-width: 0;
  flex: 1;
}

/* Та же метрика и тот же приглушённый тон, что у полки над именем исследования. */
.parent-link {
  min-width: 0;
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

/* Описание — такой же связный текст, как и тело заметки, поэтому и набирается зоной чтения.
   Класс на самом `p` обязателен — правило для голого `p` из main.scss лежит вне слоёв. */
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
   текста вокруг ей не годится. */
.meta-item {
  font-family: var(--font);
  font-size: 13px;
  color: var(--text-muted);
  white-space: nowrap;
}

/* Появление и уход разделов при сужении поиска — те же величины, что и на других деталках. */
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
