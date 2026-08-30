<script setup lang="ts">
// Страница печати исследования: тот же документ, что и на деталке, но один на пустом листе — без
// колонки навигации, шапки, карточек и разделов со связанными элементами. Её открывает скрытый
// кадр (`printPage`) и печатает виртуальным принтером; заход по прямому адресу показывает ровно
// то же самое на экране — печатаемое видно до печати.
import { nextTick, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { errorText } from '@/api/errorText'
import { announcePrintFailure, announcePrintReady } from '@/shared/utils/print'
import { fmtDateTime } from '@/shared/utils/date'

import ResearchBody from '../components/ResearchBody.vue'
import { getResearch, type ResearchDetail } from '../api'

const route = useRoute()
const { t } = useI18n()

const research = ref<ResearchDetail | null>(null)
const error = ref('')

// Схема, которую ещё рисуют, помечена этим блоком: пока он на странице, документ неполон.
const DRAWING_DIAGRAM = '.diagram-loading'
const DRAWN_POLL_MS = 100
const DRAWN_TIMEOUT_MS = 20_000

// Печать не может идти по событию загрузки страницы: оно наступает задолго до того, как приедет
// исследование, разберётся markdown, нарисуются схемы и скачаются шрифты, — на лист лёг бы
// наполовину пустой документ.
async function whenDocumentDrawn(): Promise<void> {
  await nextTick()
  await document.fonts?.ready

  // Схема, которая не нарисовалась за отведённое время, печать не отменяет: рендерер сам роняет
  // такую обратно в блок кода, и лист с исходником лучше несостоявшейся печати.
  const deadline = Date.now() + DRAWN_TIMEOUT_MS
  while (document.querySelector(DRAWING_DIAGRAM) && Date.now() < deadline) {
    await new Promise((wake) => setTimeout(wake, DRAWN_POLL_MS))
  }
}

// Печатают на белую бумагу, а фоновые заливки браузер по умолчанию не печатает: под ночной темой
// на лист лёг бы светлый текст по белому. Поэтому страница печати всегда дневная — выбранная в
// приложении тема на неё не распространяется.
function forceLightScheme(): void {
  document.documentElement.dataset.theme = 'light'
}

// Имя сохранённого файла браузер берёт из заголовка документа: без этого PDF назывался бы общей
// подписью маршрута, одинаковой у всех исследований.
function nameDocument(title: string): void {
  document.title = title
}

onMounted(async () => {
  forceLightScheme()

  try {
    research.value = await getResearch(String(route.params.code))
  } catch (e) {
    error.value = errorText(e)
    announcePrintFailure(error.value)
    return
  }

  nameDocument(research.value.title)
  await whenDocumentDrawn()
  announcePrintReady()
})
</script>

<template>
  <div class="print-page">
    <article v-if="research" class="print-doc">
      <header class="print-doc__head">
        <h1 class="print-doc__title">{{ research.title }}</h1>
        <p v-if="research.description" class="print-doc__lead">{{ research.description }}</p>
        <p class="print-doc__meta">
          {{ research.code }} · {{ t('research.field.updated_at') }}:
          {{ fmtDateTime(research.updated_at) }}
        </p>
      </header>

      <ResearchBody v-if="research.body" :text="research.body" />
      <p v-else class="print-doc__meta">{{ t('research.research.detail.no_body') }}</p>
    </article>

    <p v-else-if="error" class="print-doc__error">{{ error }}</p>
  </div>
</template>

<style scoped>
/* На экране страница прокручивается сама: она стоит вне рамки страниц приложения, и зоны
   прокрутки, которую та обычно даёт, у неё нет. */
.print-page {
  height: 100%;
  overflow: auto;
  background: var(--bg);
}

/* Ширина листа A4 — она же и на экране: печатаемое должно быть видно ровно таким, каким уйдёт
   на принтер, а не в полную ширину окна. */
.print-doc {
  max-width: 794px;
  margin: 0 auto;
  padding: 32px 24px 64px;
  /* Мера строки принадлежит зоне чтения на экране, где окно шире листа; на листе колонку задаёт
     он сам, и оставленная мера обрезала бы текст по левой половине страницы. */
  --reading-measure: 100%;
}

.print-doc__head {
  margin-bottom: 28px;
}

.print-doc__title {
  font-family: var(--font-reading);
  font-size: 26px;
  line-height: 1.25;
  letter-spacing: -0.02em;
  margin: 0 0 10px;
}

.print-doc__lead {
  font-family: var(--font-reading);
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-muted);
  margin: 0 0 10px;
}

.print-doc__meta,
.print-doc__error {
  font-size: 11px;
  color: var(--text-faint);
  margin: 0;
}

/* Разрыв страницы посреди схемы, таблицы или блока кода делает обе половины нечитаемыми, а
   заголовок в подвале листа отрывает раздел от его первой строки. */
.print-doc :deep(:is(figure, .md-table-wrap, .md-code-slot)) {
  break-inside: avoid;
}
.print-doc :deep(:is(h1, h2, h3, h4, h5, h6)) {
  break-after: avoid;
}
</style>

<style>
/* Правила печати — без `scoped`: они снимают ограничения рамки приложения, а не оформляют саму
   страницу. Рамка держит содержимое в зоне фиксированной высоты со скрытым переполнением — на
   принтер из такой зоны уходит только первый лист. Утечь правилам некуда: этот адрес открывают
   в отдельном кадре, где документ состоит из одной этой страницы. */
@media print {
  html,
  body,
  .v-application,
  .v-application__wrap,
  .main-content,
  .print-page {
    height: auto !important;
    overflow: visible !important;
    background: #fff !important;
  }

  .print-doc {
    max-width: none;
    padding: 0;
  }

  /* Подсказки об управлении — часть экрана, а не документа: на листе «двойной клик — во весь
     экран» и кнопка копирования обещают то, чего у бумаги нет. */
  .print-doc .diagram__hint,
  .print-doc .code-block__actions,
  .print-doc .code-block__copy-float {
    display: none !important;
  }
}

@page {
  margin: 16mm 14mm;
}
</style>
