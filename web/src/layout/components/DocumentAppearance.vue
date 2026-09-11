<script setup lang="ts">
// Оформление документа под рукой у самого документа: те же настройки, что в группах «Оформление
// документа» и «Схемы» на `/settings/interface`, но в колонке страницы, которую читают.
//
// Подбирают их глазами по живому тексту, а не по образцу на странице настроек: кегль и длина
// строки хороши или плохи ИМЕННО на этом теле. Настройки те же самые (`useSettingsStore`,
// localStorage), поэтому выбор здесь виден и там — это одна настройка в двух местах, а не две.
// Подписи тоже общие: словарь настроек — их единственный дом.
import { useI18n } from 'vue-i18n'

import { useSettingsStore } from '@/stores/settings'
import { DIAGRAM_ALIGNS, DIAGRAM_HEIGHTS, NO_DIAGRAM_HEIGHT } from '@/constants/diagrams'
import {
  DIAGRAM_FONTS,
  MONO_FONTS,
  NO_MEASURE,
  READING_FONTS,
  READING_MEASURES,
  READING_SIZES,
  type FontOption,
} from '@/constants/fonts'

const { t } = useI18n()
const settings = useSettingsStore()

// Каждый пункт набран той гарнитурой, которую выбирает: имя семьи говорит меньше, чем её рисунок.
function optionProps(option: FontOption) {
  return { style: { fontFamily: option.stack } }
}

const sizeOptions = READING_SIZES.map((size) => ({ title: `${size} px`, value: size }))

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
    <p class="doc-appearance__title">{{ t('settings.interface.group.document.title') }}</p>

    <VSelect
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
    <VSelect
      v-model="settings.typography.readingSize"
      :items="sizeOptions"
      :chips="false"
      :label="t('settings.interface.size.reading.label')"
      variant="outlined"
      density="compact"
      hide-details
    />
    <VSelect
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
    <VSelect
      v-model="settings.typography.readingMeasure"
      :items="measureOptions"
      :chips="false"
      :label="t('settings.interface.measure.reading.label')"
      variant="outlined"
      density="compact"
      hide-details
    />
    <p class="doc-appearance__title">{{ t('settings.interface.group.diagram.title') }}</p>

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
  </VCard>
</template>

<style scoped>
/* Карточка не ужимается: колонка — flex, и без этого её поля сдавливались бы под доступную
   высоту, а `VCard` режет то, что не влезло. Место под себя она отнимает у оглавления ниже —
   оно умеет прокручиваться, а поля настроек нет. */
.doc-appearance {
  padding: 12px;
  margin-bottom: 12px;
  display: flex;
  flex: none;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

/* Заголовок карточки, а не заголовок раздела: колонка — не страница настроек, и подпись здесь
   лишь называет, чем управляют четыре поля под ней. */
.doc-appearance__title {
  margin: 0;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-faint);
}
</style>
