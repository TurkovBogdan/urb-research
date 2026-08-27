<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import ColorPicker from '@/components/ColorPicker.vue'
// Демо идёт на настоящем наборе — палитре полок research: выдуманный список показывал бы
// раскладку на цветах, которых в приложении нет.
import { groupColorNames, groupColorVars } from '@/features/research/constants/groupColors'
import { groupIcon } from '@/features/research/constants/groupIcons'

const { t } = useI18n()

const colors = groupColorNames()

const picked = ref<string | null>('teal')
const optional = ref<string | null>(null)
const large = ref<string | null>('rose')

// Что уходит наружу, в этих же кавычках: имя — строка, «без цвета» — `null`, и на витрине
// разница между ними должна быть видна, а не додумываться по пустому месту.
function modelLiteral(value: string | null): string {
  return value === null ? 'null' : `'${value}'`
}
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader
      :title="t('design-system.page.color-picker.title')"
      :description="t('design-system.page.color-picker.description')"
      back-to="/design-system"
    />

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.color-picker.basic') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">default</span>
          <div class="ds-controls ds-controls--stack">
            <ColorPicker v-model="picked" :colors="colors" :resolve="groupColorVars" />
            <p class="ds-value">picked = {{ modelLiteral(picked) }}</p>
          </div>
          <span class="ds-spec">v-model, :colors, :resolve</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">clearable</span>
          <div class="ds-controls ds-controls--stack">
            <ColorPicker v-model="optional" :colors="colors" :resolve="groupColorVars" clearable />
            <p class="ds-value">optional = {{ modelLiteral(optional) }}</p>
          </div>
          <span class="ds-spec">clearable</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">size</span>
          <div class="ds-controls ds-controls--stack">
            <ColorPicker v-model="large" :colors="colors" :resolve="groupColorVars" :size="48" />
            <p class="ds-value">large = {{ modelLiteral(large) }}</p>
          </div>
          <span class="ds-spec">:size="48"</span>
        </div>
      </div>
    </section>

    <!-- Ради чего набор и заведён: то же имя красит плашку иконки полки. Показываем плашку рядом
         с пикером, потому что выбор оценивают по ней, а не по самой плитке. -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.color-picker.plate') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">plate</span>
          <div class="ds-controls">
            <span v-for="name in colors" :key="name" class="ds-plate color-tones" :style="groupColorVars(name)">
              <component :is="groupIcon('flask')" :size="18" :stroke-width="1.6" />
            </span>
          </div>
          <span class="ds-spec">groupColorVars(name)</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">unset</span>
          <div class="ds-controls">
            <span class="ds-plate color-tones" :style="groupColorVars(null)">
              <component :is="groupIcon('flask')" :size="18" :stroke-width="1.6" />
            </span>
          </div>
          <span class="ds-spec">groupColorVars(null) → accent</span>
        </div>
      </div>
    </section>
  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }

.ds-section { margin-bottom: 28px; }

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 100px 1fr 200px;
  align-items: start;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
}

.ds-row:last-child { border-bottom: none; }

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  padding-top: 10px;
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
  padding-top: 10px;
}

.ds-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

/* Пикер занимает всю ширину ячейки: сетка плиток считает колонки от неё. */
.ds-controls--stack {
  display: block;
}

/* Живое значение модели под пикером — тем же моноширинным набором, что подписи пропов справа:
   и то и другое читается как код, а не как текст интерфейса. */
.ds-value {
  margin: 8px 0 0;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

/* Та же плашка, что на карточке полки, — цвет берётся из вар, а не задаётся здесь. */
.ds-plate {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 7px;
  color: var(--gc-ink);
  background: var(--gc-fill);
}
</style>
