<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import SettingsGroup from '@/components/settings/SettingsGroup.vue'
import SwitchPanel from '@/components/SwitchPanel.vue'
import { useSettingsStore } from '@/stores/settings'
import {
  DIAGRAM_ALIGNS,
  DIAGRAM_HEIGHTS,
  NO_DIAGRAM_HEIGHT,
  type DiagramAlignOption,
} from '@/constants/diagrams'
import {
  DIAGRAM_FONTS,
  INTERFACE_FONTS,
  MONO_FONTS,
  NO_MEASURE,
  READING_FONTS,
  READING_MEASURES,
  READING_SIZES,
  type FontOption,
} from '@/constants/fonts'
import { RESEARCH_LIST_VIEWS } from '@/constants/lists'
import { THEME_OPTIONS, type ThemeOption } from '@/constants/theme'

// Client-side appearance settings. Unlike /settings/modules these never reach the
// backend: they live in localStorage and apply as they are picked, so the page has no
// save button and no dirty state.
//
// Разложены они всё же как настройки модулей — группами с пояснением, полем и подписью под ним,
// а тумблер стоит плашкой (`SwitchPanel`), той же, что рисует bool-поле схемы. Набор полей здесь
// известен на месте и разнороден, поэтому карточки написаны разметкой, а не собраны циклом по
// схеме: схема нужна там, где поля приходят с бэкенда.
const { t } = useI18n()
const settings = useSettingsStore()

// The sample is markdown and goes through the real renderer, so the preview is the reading
// zone itself rather than an imitation of it. It carries one of every construction a body
// actually uses — that is what makes the choice above judgeable: a family that looks fine in
// a paragraph can fall apart in a dense table or next to monospace.
const PREVIEW = `# Заголовок первого уровня

Первый абзац идёт сразу под заголовком — по нему видно рисунок строчных, интерлиньяж и,
главное, длину строки, на которой глаз ещё уверенно находит начало следующей. Длина строки
влияет на скорость чтения сильнее, чем кегль, поэтому колонка ограничена по ширине, а
таблицы и блоки кода из этого ограничения выведены — их просматривают, а не читают подряд.

## Заголовок второго уровня

Второй абзац — чтобы стало видно расстояние между разделами и то, что отступ над заголовком
заметно больше отступа под ним: заголовок принадлежит тексту, который идёт следом. Внутри
строки встречаются \`inline-код\`, **жирное выделение**, *курсив* и [внешняя ссылка](https://example.com),
а ещё пилюля ссылки на сущность — RESEARCH@ef8a7d2f258de68b188bda.

### Заголовок третьего уровня

- маркированный список: первый пункт
- второй пункт, заметно длиннее первого, чтобы стало видно, как ложится перенос внутри пункта
  - вложенный пункт
- третий пункт

1. нумерованный список
2. второй пункт

- [x] выполненный пункт чек-листа
- [ ] невыполненный пункт

> Цитата отбивается линейкой и воздухом, без курсива: в этих телах она бывает длиной
> в абзац, а курсив на такой длине читается заметно медленнее.

| Параметр | Значение | Комментарий |
|---|---|---|
| Кегль текста | 16 px | нижняя граница для чтения подряд |
| Интерлиньяж | 1.7 | абзацам нужно больше воздуха, чем строкам интерфейса |
| Длина строки | 92ch | таблицы и код в это ограничение не входят |

\`\`\`python
def read(text: str, *, size: int = 16) -> str:
    """Блок кода: подсветка, номера строк и копирование."""
    return text.strip()
\`\`\`

Схема идёт в теле тем же блоком, что и код, и набрана своей гарнитурой — подписи внутри
блоков живут в тесных коробках, и семья, хорошая в абзаце, там может не поместиться.

\`\`\`mermaid
graph LR
  A[Запрос агента] --> B{Схема поддержана?}
  B -->|да| C[Рендер SVG]
  B -->|нет| D[Блок кода]
\`\`\`

---

Последний абзац после разделителя — самый широкий интервал в теле.
`

// Each option previews itself: the row is set in the family it selects, which tells more
// than its name does, and the note says what the family is for.
function optionProps(option: FontOption) {
  return { subtitle: option.note, style: { fontFamily: option.stack } }
}

function themeProps(option: ThemeOption) {
  return { subtitle: option.note }
}

function alignProps(option: DiagramAlignOption) {
  return { subtitle: option.note }
}

const diagramHeightOptions = DIAGRAM_HEIGHTS.map((height) => ({
  title: height === NO_DIAGRAM_HEIGHT ? t('settings.interface.diagram.height.unlimited') : `${height} px`,
  value: height,
}))

const sizeOptions = READING_SIZES.map((size) => ({ title: `${size} px`, value: size }))

const measureOptions = READING_MEASURES.map((measure) => ({
  title: measure === NO_MEASURE ? t('settings.interface.measure.reading.unlimited') : `${measure}ch`,
  value: measure,
}))

// Реестр показывает выбранную раскладку и без захода сюда — тем же переключателем на своей
// странице; здесь она названа полностью, там стоит парой иконок.
const researchViewOptions = RESEARCH_LIST_VIEWS.map((view) => ({
  title: t(view.label),
  value: view.code,
  props: { prependIcon: view.icon },
}))
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('settings.interface.page.title')"
      :description="t('settings.interface.page.description')"
    />

    <div class="settings-grid">
      <SettingsGroup
        :title="t('settings.interface.group.app.title')"
        :description="t('settings.interface.group.app.description')"
      >
        <div class="setting">
          <VSelect
            v-model="settings.appearance.theme"
            :items="THEME_OPTIONS"
            item-title="label"
            item-value="code"
            :item-props="themeProps"
            :chips="false"
            :label="t('settings.interface.theme.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.theme.description') }}</p>
        </div>

        <div class="setting">
          <VSelect
            v-model="settings.typography.interfaceFont"
            :items="INTERFACE_FONTS"
            item-title="label"
            item-value="code"
            :item-props="optionProps"
            :chips="false"
            :label="t('settings.interface.font.interface.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.font.interface.description') }}</p>
        </div>

        <div class="setting">
          <VSelect
            v-model="settings.lists.researchView"
            :items="researchViewOptions"
            :chips="false"
            :label="t('settings.interface.list.research.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.list.research.description') }}</p>
        </div>

        <SwitchPanel
          v-model="settings.ui.documentNav"
          :title="t('settings.interface.nav.document.label')"
          :description="t('settings.interface.nav.document.description')"
        />
      </SettingsGroup>

      <SettingsGroup
        :title="t('settings.interface.group.document.title')"
        :description="t('settings.interface.group.document.description')"
      >
        <div class="setting">
          <VSelect
            v-model="settings.typography.readingFont"
            :items="READING_FONTS"
            item-title="label"
            item-value="code"
            :item-props="optionProps"
            :chips="false"
            :label="t('settings.interface.font.reading.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.font.reading.description') }}</p>
        </div>

        <div class="setting">
          <VSelect
            v-model="settings.typography.readingSize"
            :items="sizeOptions"
            :chips="false"
            :label="t('settings.interface.size.reading.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.size.reading.description') }}</p>
        </div>

        <div class="setting">
          <VSelect
            v-model="settings.typography.monoFont"
            :items="MONO_FONTS"
            item-title="label"
            item-value="code"
            :item-props="optionProps"
            :chips="false"
            :label="t('settings.interface.font.mono.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.font.mono.description') }}</p>
        </div>

        <div class="setting">
          <VSelect
            v-model="settings.typography.readingMeasure"
            :items="measureOptions"
            :chips="false"
            :label="t('settings.interface.measure.reading.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.measure.reading.description') }}</p>
        </div>

      </SettingsGroup>

      <SettingsGroup
        :title="t('settings.interface.group.diagram.title')"
        :description="t('settings.interface.group.diagram.description')"
      >
        <div class="setting">
          <VSelect
            v-model="settings.diagrams.font"
            :items="DIAGRAM_FONTS"
            item-title="label"
            item-value="code"
            :item-props="optionProps"
            :chips="false"
            :label="t('settings.interface.font.diagram.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.font.diagram.description') }}</p>
        </div>

        <div class="setting">
          <VSelect
            v-model="settings.diagrams.align"
            :items="DIAGRAM_ALIGNS"
            item-title="label"
            item-value="code"
            :item-props="alignProps"
            :chips="false"
            :label="t('settings.interface.diagram.align.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.diagram.align.description') }}</p>
        </div>

        <div class="setting">
          <VSelect
            v-model="settings.diagrams.maxHeight"
            :items="diagramHeightOptions"
            :chips="false"
            :label="t('settings.interface.diagram.height.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.diagram.height.description') }}</p>
        </div>
      </SettingsGroup>
    </div>

    <!-- Предпросмотр вне сетки: он не настройка, а то, на что настройки применяются, и читать его
         надо на полной ширине — колонка группы уже ограничения зоны чтения. -->
    <VCard variant="outlined" rounded="lg" class="mt-4">
      <VCardTitle class="text-h6">{{ t('settings.interface.preview.title') }}</VCardTitle>
      <VDivider />
      <VCardText>
        <MarkdownRenderer :text="PREVIEW" />
      </VCardText>
    </VCard>
  </PageLayout>
</template>

<style scoped>
/* Та же сетка, что у карточек модулей: колонки с потолком ширины и высотой по содержимому —
   поле ввода шире ~440px читается хуже, а группы тут разной длины. */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 440px));
  align-items: start;
  justify-content: start;
  gap: 16px;
}

@media (max-width: 700px) {
  .settings-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

/* Подпись под полем, а не подсказкой Vuetify: у настроек модулей описание живёт отдельной
   строкой под полем, и клиентские настройки не должны выглядеть другим сортом настроек. */
.setting {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.setting__desc {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-muted);
}
</style>
