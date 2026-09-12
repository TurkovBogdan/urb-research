<script setup lang="ts">
// Оформление документа под рукой у самого документа: те же группы, что «Оформление документа»,
// «Оформление блока кода» и «Схемы» на `/settings/interface`, полным составом, в том же порядке и
// теми же ручками — расходиться наборам нельзя, иначе одна и та же настройка живёт в двух местах
// с разным именем группы. Где варианты стоят по порядку (гарнитуры, кегли, вес, ширина), ручка —
// `VSelectStepper`: соседний перебирают подряд, сравнивая результат, и здесь это нужнее, чем на
// странице настроек, — сравнивают-то по живому тексту рядом.
//
// Подбирают их глазами по живому тексту, а не по образцу на странице настроек: кегль, длина
// строки и гарнитуры хороши или плохи ИМЕННО на этом теле. Настройка при этом одна и та же
// (`useSettingsStore`, источник истины — база через `synced`, localStorage под ним лишь кеш до
// первого кадра), поэтому выбор здесь виден и там. Подписи тоже общие: словарь настроек —
// их единственный дом.
//
// Описаний под полями здесь нет, в отличие от страницы настроек: в колонке шириной 320px они
// заняли бы больше места, чем сами поля, а объяснять выбор — дело страницы настроек.
import { useI18n } from 'vue-i18n'

import SwitchPanel from '@/components/SwitchPanel.vue'
import VSelectStepper from '@/components/VSelectStepper.vue'
import { useSettingsStore } from '@/stores/settings'
import { CODE_VARIANTS } from '@/constants/code'
import { DIAGRAM_ALIGNS, DIAGRAM_HEIGHTS, DIAGRAM_THEMES, NO_DIAGRAM_HEIGHT } from '@/constants/diagrams'
import {
  CODE_SIZES,
  DIAGRAM_FONTS,
  HEADING_FONTS,
  MONO_FONTS,
  NO_MEASURE,
  READING_FONTS,
  READING_MEASURES,
  READING_SIZES,
  READING_WEIGHTS,
  type FontOption,
} from '@/constants/fonts'

const { t } = useI18n()
const settings = useSettingsStore()

// Каждый пункт набран той гарнитурой, которую выбирает: имя семьи говорит меньше, чем её рисунок.
function optionProps(option: FontOption) {
  return { style: { fontFamily: option.stack } }
}

const sizeOptions = READING_SIZES.map((size) => ({ title: `${size} px`, value: size }))

const codeSizeOptions = CODE_SIZES.map((size) => ({ title: `${size} px`, value: size }))

// Тем же приёмом, что и гарнитуры: вариант набран своей насыщенностью, а не только назван числом.
const weightOptions = READING_WEIGHTS.map((weight) => ({
  title: String(weight),
  value: weight,
  props: { style: { fontWeight: weight } },
}))

const measureOptions = READING_MEASURES.map((measure) => ({
  title: measure === NO_MEASURE ? t('settings.interface.measure.reading.unlimited') : `${measure}ch`,
  value: measure,
}))

const diagramHeightOptions = DIAGRAM_HEIGHTS.map((height) => ({
  title: height === NO_DIAGRAM_HEIGHT ? t('settings.interface.diagram.height.unlimited') : `${height} px`,
  value: height,
}))
</script>

<template>
  <VCard variant="outlined" rounded="lg" class="doc-appearance">
    <div class="doc-appearance__fields scroll-y">
      <p class="doc-appearance__title">{{ t('settings.interface.group.document.title') }}</p>

      <VSelectStepper
        v-model="settings.typography.readingFont"
        :items="READING_FONTS"
        item-title="label"
        item-value="code"
        :item-props="optionProps"
        :chips="false"
        :label="t('settings.interface.font.reading.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <VSelectStepper
        v-model="settings.typography.readingSize"
        :items="sizeOptions"
        :chips="false"
        :label="t('settings.interface.size.reading.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <VSelectStepper
        v-model="settings.typography.readingWeight"
        :items="weightOptions"
        :chips="false"
        :label="t('settings.interface.weight.reading.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <VSelectStepper
        v-model="settings.typography.headingFont"
        :items="HEADING_FONTS"
        item-title="label"
        item-value="code"
        :item-props="optionProps"
        :chips="false"
        :label="t('settings.interface.font.heading.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <VSelectStepper
        v-model="settings.typography.headingWeight"
        :items="weightOptions"
        :chips="false"
        :label="t('settings.interface.weight.heading.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <VSelectStepper
        v-model="settings.typography.readingMeasure"
        :items="measureOptions"
        :chips="false"
        :label="t('settings.interface.measure.reading.label')"
        variant="outlined"
        density="compact"
        hide-details
      />

      <p class="doc-appearance__title">{{ t('settings.interface.group.code.title') }}</p>

      <VSelect
        v-model="settings.typography.codeVariant"
        :items="CODE_VARIANTS"
        item-title="label"
        item-value="code"
        :chips="false"
        :label="t('settings.interface.code.variant.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <VSelectStepper
        v-model="settings.typography.monoFont"
        :items="MONO_FONTS"
        item-title="label"
        item-value="code"
        :item-props="optionProps"
        :chips="false"
        :label="t('settings.interface.font.mono.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <VSelectStepper
        v-model="settings.typography.codeSize"
        :items="codeSizeOptions"
        :chips="false"
        :label="t('settings.interface.size.code.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <!-- Плашка без фона: рамку и отбивку ей даёт карточка, а своя обводка внутри списка полей
           читалась бы как вложенный блок. -->
      <SwitchPanel
        v-model="settings.typography.codeLineNumbers"
        tone="transparent"
        :title="t('settings.interface.code.line_numbers.label')"
      />

      <p class="doc-appearance__title">{{ t('settings.interface.group.diagram.title') }}</p>

      <VSelect
        v-model="settings.diagrams.theme"
        :items="DIAGRAM_THEMES"
        item-title="label"
        item-value="code"
        :chips="false"
        :label="t('settings.interface.diagram.theme.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <VSelect
        v-model="settings.diagrams.font"
        :items="DIAGRAM_FONTS"
        item-title="label"
        item-value="code"
        :item-props="optionProps"
        :chips="false"
        :label="t('settings.interface.font.diagram.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <VSelect
        v-model="settings.diagrams.align"
        :items="DIAGRAM_ALIGNS"
        item-title="label"
        item-value="code"
        :chips="false"
        :label="t('settings.interface.diagram.align.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
      <VSelect
        v-model="settings.diagrams.maxHeight"
        :items="diagramHeightOptions"
        :chips="false"
        :label="t('settings.interface.diagram.height.label')"
        variant="outlined"
        density="compact"
        hide-details
      />
    </div>
  </VCard>
</template>

<style scoped>
/* Карточка не ужимается соседями (`flex: none`), но и не растёт бесконечно: четырнадцать полей
   выше любой колонки, поэтому высота ограничена долей экрана, а лишнее прокручивается ВНУТРИ
   рамки. Без предела карточка выдавила бы оглавление под собой из колонки целиком. */
.doc-appearance {
  padding: 0;
  margin-bottom: 12px;
  display: flex;
  flex: none;
  max-height: 45vh;
  min-width: 0;
}

/* Отбивка принадлежит прокручиваемой полосе, а не карточке: иначе полоса прокрутки встала бы
   внутри отступа, в 12px от края рамки. */
.doc-appearance__fields {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 16px;
  padding: 12px;
  min-width: 0;
  min-height: 0;
}

/* Заголовок группы, а не раздела: колонка — не страница настроек, и подпись здесь лишь называет,
   чем управляют поля под ней. Первая стоит у края, у остальных над собой — воздух побольше
   межполевого, чтобы группы читались группами. */
.doc-appearance__title {
  margin: 0;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-faint);
}

.doc-appearance__title:not(:first-child) {
  margin-top: 8px;
}

/* Узкий экран: колонка перестаёт быть липкой и ложится над содержимым, делить с ней высоту экрана
   больше некому — предел снимается, и поля идут подряд. Прокрутка внутри карточки там была бы
   второй прокруткой на странице, которая и так прокручивается. */
@media (max-width: 1099px) {
  .doc-appearance {
    max-height: none;
  }
}
</style>
