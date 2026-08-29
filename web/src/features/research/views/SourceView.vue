<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconExternalLink } from '@tabler/icons-vue'

import DetailHead from '@/layout/components/DetailHead.vue'
import { useDetailRail } from '@/layout/detailRail'
import SectionError from '@/components/SectionError.vue'
import { type NavSection } from '@/components/SectionNav.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import type { HeadingAnchor } from '@/components/markdown/render'
import { useSettingsStore } from '@/stores/settings'
import { fmtDateTime, fmtRelative } from '@/shared/utils/date'

import BodySection from '../components/BodySection.vue'
import { useSourceDetailStore } from '../stores/source-detail.store'
import { useDetailReload } from '../useDetailReload'
import { SOURCE_STATUS_COLOR } from '../labels'

const { t } = useI18n()
const store = useSourceDetailStore()
const settings = useSettingsStore()
const { reload } = useDetailReload(store.load)

// Источник лежит глубже всех, но на уровень выше него — одна зона, из поиска которой он пришёл.
// Дальше наверх ведёт уже её кнопка: за нажатие снимается один уровень.
const parentPath = computed(() =>
  store.source ? `/research/areas/${store.source.area_code}` : '/research/researches',
)

const parentLabel = computed(() =>
  store.source ? t('research.back.area') : t('research.back.researches'),
)

// Якоря разделов: один источник для `id` на самом разделе и для ссылки в боковой навигации.
const SECTION = {
  top: 'source-top',
  body: 'source-body',
} as const

const documentHeadings = ref<HeadingAnchor[]>([])

watch(() => store.source?.body, (body) => {
  if (!body) documentHeadings.value = []
})

const NAV_HEADING_MAX_LEVEL = 2

const sectionShown = computed(() => ({
  brief: !store.searching || store.briefMatches,
  body: !store.searching || store.bodyMatches,
}))

const documentNavShown = computed(() => settings.ui.documentNav && sectionShown.value.body)

const navSections = computed<NavSection[]>(() => [
  ...(sectionShown.value.brief
    ? [{ id: SECTION.top, label: t('research.source.detail.brief') }]
    : []),
  ...(sectionShown.value.body
    ? [{ id: SECTION.body, label: t('research.source.detail.body') }]
    : []),
  ...(documentNavShown.value
    ? documentHeadings.value
        .filter((heading) => heading.level <= NAV_HEADING_MAX_LEVEL && heading.text)
        .map((heading) => ({ id: heading.id, label: heading.text, depth: 1 }))
    : []),
])

// Точная дата отвечает «когда», относительная — «давно ли»; поодиночке каждая заставляет
// додумывать вторую.
const updatedAt = computed(() => {
  const value = store.source?.updated_at
  if (!value) return ''
  const relative = fmtRelative(value)
  return relative ? `${fmtDateTime(value)} (${relative})` : fmtDateTime(value)
})

// Балл без ответа «а это много?» заставляет вспоминать шкалу, поэтому рядом с числом стоит его
// полоса — та же, по которой источники фильтруют в таблице.
const relevanceBand = computed(() => {
  const relevance = store.source?.relevance
  if (relevance == null) return 'unrated'
  if (relevance >= 8) return 'high'
  if (relevance >= 4) return 'medium'
  return 'low'
})

// Разбор источника — то, ради чего его открывают вторым заходом: чем он оказался полезен
// (`summary`) и что с ним не так (`note`). Пишет разбор агент, поэтому здесь он только читается.
const review = computed(() => {
  const source = store.source
  if (!source) return []
  return [
    { label: t('research.source.detail.summary'), text: source.summary },
    { label: t('research.source.detail.note'), text: source.note },
  ].filter((field) => field.text)
})

// Колонку рисует общая рамка деталок — страница её только заполняет.
useDetailRail(() => ({
  parent: parentPath.value,
  label: parentLabel.value,
  appearance: true,
  sections: store.source ? navSections.value : [],
  search: store.source
    ? {
        label: t('research.source.detail.search'),
        value: store.search,
        update: (query: string) => { store.search = query },
        summary: store.searching
          ? t('research.source.detail.found', { n: store.matchCount })
          : '',
      }
    : undefined,
}))
</script>

<template>
  <div>
    <SectionError v-if="store.error" :error="store.error" />

    <template v-if="store.source">
      <DetailHead
        :id="SECTION.top"
        :code="store.source.code"
        :loading="store.loading"
        @refresh="reload"
      >
        <!-- Над именем — зона, из поиска которой источник пришёл: то же место и тот же ответ
             «где я нахожусь», что у полки над именем исследования. -->
        <template #above>
          <RouterLink :to="parentPath" class="parent-link">
            {{ store.source.area_title }}
          </RouterLink>
        </template>

        <!-- Ни имя, ни разбор источника не правятся: он не написан здесь, а найден — строка
             выдачи поиска. Меняет его только повтор получения материала (меню строки в
             таблице), поэтому правки на месте тут нет нигде. -->
        <h1 class="src-title">{{ store.source.title || store.source.url }}</h1>

        <!-- Переход на сам сайт — действие над объектом, поэтому стоит в ряду действий шапки,
             а не в карточке под ней. -->
        <template #actions>
          <VBtn
            v-if="store.source.url"
            variant="text"
            :href="store.source.url"
            target="_blank"
            rel="noopener noreferrer"
          >
            <template #prepend><IconExternalLink :size="16" /></template>
            {{ t('research.source.detail.open_source') }}
          </VBtn>
        </template>
      </DetailHead>

      <!-- Первая карточка отвечает на вопросы об источнике как о находке: что с ним сделали
           (статус), насколько он оказался нужен (балл), откуда он и когда получен, — и лишь
           затем идёт разбор словами. Адрес стоит здесь, а не под именем: он такой же ответ,
           как остальные, и в шапке отбирал бы ширину у названия. -->
      <VCard v-if="sectionShown.brief" variant="outlined" rounded="lg" class="brief-card">
        <VCardText class="src-card">
          <dl class="facts">
            <div class="fact">
              <dt class="fact__label">{{ t('research.doc.col.status') }}</dt>
              <dd class="fact__value">
                <StatusBadge :color="SOURCE_STATUS_COLOR[store.source.status]">
                  {{ t(`research.source.status.${store.source.status}`) }}
                </StatusBadge>
              </dd>
            </div>

            <div class="fact">
              <dt class="fact__label">{{ t('research.source.detail.relevance') }}</dt>
              <dd class="fact__value">
                <span v-if="store.source.relevance != null" class="relevance">
                  {{ store.source.relevance }}
                </span>
                <span class="fact__hint">{{ t(`research.doc.relevance.${relevanceBand}`) }}</span>
              </dd>
            </div>

            <div class="fact fact--wide">
              <dt class="fact__label">{{ t('research.source.detail.url') }}</dt>
              <dd class="fact__value">
                <a
                  v-if="store.source.url"
                  :href="store.source.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="src-url"
                >{{ store.source.url }}</a>
                <span v-else class="fact__hint">{{ t('research.source.detail.no_url') }}</span>
              </dd>
            </div>

            <div class="fact">
              <dt class="fact__label">{{ t('research.field.updated_at') }}</dt>
              <dd class="fact__value fact__value--muted">{{ updatedAt }}</dd>
            </div>
          </dl>

          <dl v-if="review.length" class="review">
            <template v-for="field in review" :key="field.label">
              <dt class="review__label">{{ field.label }}</dt>
              <dd class="review__text">{{ field.text }}</dd>
            </template>
          </dl>
        </VCardText>
      </VCard>

      <TransitionGroup name="fragment" tag="div">
        <section v-if="sectionShown.body" :key="SECTION.body" :id="SECTION.body">
          <BodySection
            :title="t('research.source.detail.body')"
            :text="store.source.body ?? ''"
            :empty="t('research.source.detail.no_body')"
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

/* Кегль тот же, что у имён остальных деталок. Правки на месте у него нет, поэтому и карандаша
   рядом не появляется. */
.src-title {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.3;
  text-wrap: pretty;
}

/* Та же метрика и тот же приглушённый тон, что у полки над именем исследования. */
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

/* Столько же воздуха, сколько у карточки текста: карточка источника читается вместе с ней. */
.src-card {
  padding: 28px 16px;
}

/* Короткие ответы — сеткой в две колонки: их читают глазами по столбцу подписей, а не строкой,
   в которой поля разной длины разъезжаются от источника к источнику. Адрес занимает ряд целиком —
   он единственный, кому не хватает половины. */
.facts {
  margin: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 24px;
}

@media (max-width: 719px) {
  .facts {
    grid-template-columns: minmax(0, 1fr);
  }
}

.fact {
  min-width: 0;
}

.fact--wide {
  grid-column: 1 / -1;
}

.fact__label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-faint);
  margin-bottom: 4px;
}

.fact__value {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-size: 13px;
  color: var(--text);
}

.fact__value--muted {
  color: var(--text-muted);
}

/* Полоса при балле — пояснение к числу, поэтому тише его. */
.fact__hint {
  font-size: 12px;
  color: var(--text-faint);
}

.relevance {
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--text);
}

.src-url {
  min-width: 0;
  color: var(--text-muted);
  text-decoration: none;
  word-break: break-all;
}

.src-url:hover {
  color: rgb(var(--v-theme-primary));
}

/* Разбор отбит от коротких ответов линией: там свойства находки, здесь слова о ней. */
.review {
  margin: 20px 0 0;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.review__label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-faint);
  margin-bottom: 4px;
}

/* Типографика зоны чтения — та же, что у материала под карточкой: разбор читают абзацами. */
.review__text {
  margin: 0 0 20px;
  max-width: var(--reading-measure, 92ch);
  font-family: var(--font-reading);
  font-size: var(--reading-size, 14px);
  line-height: 1.7;
  color: var(--text);
  white-space: pre-wrap;
  text-wrap: pretty;
}

.review__text:last-child {
  margin-bottom: 0;
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
