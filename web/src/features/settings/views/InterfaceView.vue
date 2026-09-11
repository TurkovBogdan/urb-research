<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import SettingsGroup from '@/components/settings/SettingsGroup.vue'
import SwitchPanel from '@/components/SwitchPanel.vue'
import VSelectStepper from '@/components/VSelectStepper.vue'
import { useSettingsStore } from '@/stores/settings'
import { CODE_VARIANTS, type CodeVariantOption } from '@/constants/code'
import {
  DIAGRAM_ALIGNS,
  DIAGRAM_HEIGHTS,
  NO_DIAGRAM_HEIGHT,
  type DiagramAlignOption,
} from '@/constants/diagrams'
import {
  CODE_SIZES,
  DIAGRAM_FONTS,
  HEADING_FONTS,
  INTERFACE_FONTS,
  MONO_FONTS,
  NO_MEASURE,
  READING_FONTS,
  READING_MEASURES,
  READING_SIZES,
  READING_WEIGHTS,
  type FontOption,
} from '@/constants/fonts'
import { RESEARCH_LIST_VIEWS } from '@/constants/lists'
import { THEME_OPTIONS, type ThemeOption } from '@/constants/theme'

// Оформление приложения. В отличие от `/settings/modules` кнопки сохранения здесь нет: выбор
// применяется в тот же миг, а в базу (модуль `core_interface`) уезжает сам — пачкой, спустя
// полсекунды после последнего движения. Отсюда и отсутствие состояния «не сохранено».
//
// Разложены они всё же как настройки модулей — группами с пояснением, полем и подписью под ним,
// а тумблер стоит плашкой (`SwitchPanel`), той же, что рисует bool-поле схемы. Набор полей здесь
// известен на месте и разнороден, поэтому карточки написаны разметкой, а не собраны циклом по
// схеме: схема нужна там, где поля приходят с бэкенда.
const { t } = useI18n()
const settings = useSettingsStore()

// The sample is markdown and goes through the real renderer, so the preview is the reading
// zone itself rather than an imitation of it. It carries what the choices above are judged
// by — headings, running text with its inline constructions, a list — and stops there:
// tables, code, diagrams and the rest get preview zones of their own.
const PREVIEW = `# Заголовок первого уровня

Первый абзац идёт сразу под заголовком — по нему видно рисунок строчных, интерлиньяж и,
главное, длину строки, на которой глаз ещё уверенно находит начало следующей. Длина строки
влияет на скорость чтения сильнее, чем кегль, поэтому колонка ограничена по ширине, а
таблицы и блоки кода из этого ограничения выведены — их просматривают, а не читают подряд.

## Заголовок второго уровня

Второй абзац — чтобы стало видно расстояние между разделами и то, что отступ над заголовком
заметно больше отступа под ним: заголовок принадлежит тексту, который идёт следом. Внутри
строки встречаются \`inline-код\`, **жирное выделение**, *курсив* и [внешняя ссылка](https://example.com),
а ещё пилюля ссылки на сущность — RESEARCH@ef8a7d2f25.

### Заголовок третьего уровня

- маркированный список: первый пункт
- второй пункт, заметно длиннее первого, чтобы стало видно, как ложится перенос внутри пункта
  - вложенный пункт
`

// Блок кода судят не сам по себе, а рядом с текстом: абзацы вокруг показывают, насколько
// моноширинная гарнитура спорит с читательской по цвету и росту знака. Питон — потому что на
// нём в этих телах пишут чаще всего, и подсветка здесь такая же, как в настоящем документе.
//
// Блока два, и это разные вещи: в многострочном видно шапку, номера строк и длину строки на
// выбранном кегле, а однострочный рисуется командной плашкой — без шапки и с кнопкой копирования
// по наведению. Судить их порознь нельзя, поэтому оба стоят в примере.
const CODE_PREVIEW = `Короткий абзац перед блоком: по нему видно, как моноширинный набор стоит
рядом с текстом — не спорит ли он с ним по росту знака и насыщенности. Внутри строки тоже
встречается \`inline-код\`, и он набран той же гарнитурой, что и блок ниже.

\`\`\`python
def read(path: Path) -> str:
    """Блок кода: подсветка, номера строк и копирование."""
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"пустой файл: {path}")
    lines = [line.rstrip() for line in text.splitlines()]
    return "\\n".join(lines)
\`\`\`

Абзац между блоками — тот же текст, что и в теле документа: по нему видно, сколько воздуха
остаётся вокруг листинга и не съедает ли блок отбивку соседних абзацев.

\`\`\`bash
uv run pytest --module=core_interface
\`\`\`
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

function variantProps(option: CodeVariantOption) {
  return { subtitle: option.note }
}

const diagramHeightOptions = DIAGRAM_HEIGHTS.map((height) => ({
  title: height === NO_DIAGRAM_HEIGHT ? t('settings.interface.diagram.height.unlimited') : `${height} px`,
  value: height,
}))

const sizeOptions = READING_SIZES.map((size) => ({ title: `${size} px`, value: size }))

const codeSizeOptions = CODE_SIZES.map((size) => ({ title: `${size} px`, value: size }))

// Каждый вариант набран своим весом: увидеть насыщенность важнее, чем прочитать её номер.
const weightOptions = READING_WEIGHTS.map((weight) => ({
  title: String(weight),
  value: weight,
  props: { style: { fontWeight: weight } },
}))

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

    <div class="settings-list">
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
          <VSelectStepper
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
          <VSelectStepper
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
          <VSelectStepper
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
          <VSelectStepper
            v-model="settings.typography.readingWeight"
            :items="weightOptions"
            :chips="false"
            :label="t('settings.interface.weight.reading.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.weight.reading.description') }}</p>
        </div>

        <div class="setting">
          <VSelectStepper
            v-model="settings.typography.headingFont"
            :items="HEADING_FONTS"
            item-title="label"
            item-value="code"
            :item-props="optionProps"
            :chips="false"
            :label="t('settings.interface.font.heading.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.font.heading.description') }}</p>
        </div>

        <div class="setting">
          <VSelectStepper
            v-model="settings.typography.headingWeight"
            :items="weightOptions"
            :chips="false"
            :label="t('settings.interface.weight.heading.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.weight.heading.description') }}</p>
        </div>

        <div class="setting">
          <VSelectStepper
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

      <!-- Пример документа стоит сразу за настройками, которые на него ложатся: гарнитуру, кегль и
           ширину колонки выбирают по тому, как они читаются, а не по названию в списке. Применяется
           он на горячую — выбор уходит в зону чтения тем же мигом, что и во всё приложение. -->
      <VCard variant="outlined" rounded="lg">
        <VCardTitle class="text-h6">{{ t('settings.interface.preview.title') }}</VCardTitle>
        <VDivider />
        <VCardText>
          <MarkdownRenderer :text="PREVIEW" />
        </VCardText>
      </VCard>

      <SettingsGroup
        :title="t('settings.interface.group.code.title')"
        :description="t('settings.interface.group.code.description')"
      >
        <div class="setting">
          <VSelect
            v-model="settings.typography.codeVariant"
            :items="CODE_VARIANTS"
            item-title="label"
            item-value="code"
            :item-props="variantProps"
            :chips="false"
            :label="t('settings.interface.code.variant.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.code.variant.description') }}</p>
        </div>

        <div class="setting">
          <VSelectStepper
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
          <VSelectStepper
            v-model="settings.typography.codeSize"
            :items="codeSizeOptions"
            :chips="false"
            :label="t('settings.interface.size.code.label')"
            variant="outlined"
            density="comfortable"
            hide-details="auto"
          />
          <p class="setting__desc">{{ t('settings.interface.size.code.description') }}</p>
        </div>

        <SwitchPanel
          v-model="settings.typography.codeLineNumbers"
          :title="t('settings.interface.code.line_numbers.label')"
          :description="t('settings.interface.code.line_numbers.description')"
        />
      </SettingsGroup>

      <VCard variant="outlined" rounded="lg">
        <VCardTitle class="text-h6">{{ t('settings.interface.preview.title') }}</VCardTitle>
        <VDivider />
        <VCardText>
          <MarkdownRenderer :text="CODE_PREVIEW" />
        </VCardText>
      </VCard>

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
  </PageLayout>
</template>

<style scoped>
/* Та же раскладка, что у карточек модулей: карточка группы во всю ширину страницы, группы идут
   стопкой, а в колонки разложены поля внутри (утилита `.settings-columns`). */
.settings-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
