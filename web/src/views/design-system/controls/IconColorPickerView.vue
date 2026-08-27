<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import IconColorPicker from '@/components/IconColorPicker.vue'
// Демо идёт на настоящих наборах — палитре и иконках полок research: выдуманные списки
// показывали бы раскладку на данных, которых в приложении нет.
import { groupColorNames, groupColorVars } from '@/features/research/constants/groupColors'
import { groupIcon, groupIconNames } from '@/features/research/constants/groupIcons'

const { t } = useI18n()

const icons = groupIconNames()
const colors = groupColorNames()

const icon = ref<string | null>('flask')
const color = ref<string | null>('teal')

const optionalIcon = ref<string | null>(null)
const optionalColor = ref<string | null>(null)

// Что уходит наружу, в этих же кавычках: имя — строка, «не выбрано» — `null`, и на витрине
// разница между ними должна быть видна, а не додумываться по пустому месту.
function modelLiteral(value: string | null): string {
  return value === null ? 'null' : `'${value}'`
}
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader
      :title="t('design-system.page.icon-color-picker.title')"
      :description="t('design-system.page.icon-color-picker.description')"
      back-to="/design-system"
    />

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.icon-color-picker.basic') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">default</span>
          <div class="ds-controls ds-controls--stack">
            <IconColorPicker
              v-model:icon="icon"
              v-model:color="color"
              :icons="icons"
              :colors="colors"
              :resolve-icon="groupIcon"
              :resolve-color="groupColorVars"
            />
            <p class="ds-value">icon = {{ modelLiteral(icon) }} · color = {{ modelLiteral(color) }}</p>
          </div>
          <span class="ds-spec">v-model:icon, v-model:color</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">clearable</span>
          <div class="ds-controls ds-controls--stack">
            <IconColorPicker
              v-model:icon="optionalIcon"
              v-model:color="optionalColor"
              :icons="icons"
              :colors="colors"
              :resolve-icon="groupIcon"
              :resolve-color="groupColorVars"
              :height="140"
              clearable
            />
            <p class="ds-value">
              icon = {{ modelLiteral(optionalIcon) }} · color = {{ modelLiteral(optionalColor) }}
            </p>
          </div>
          <span class="ds-spec">clearable, :height="140"</span>
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

/* Панель занимает всю ширину ячейки: сетки плиток считают колонки от неё. */
.ds-controls--stack {
  display: block;
}

/* Живое значение модели под панелью — тем же моноширинным набором, что подписи пропов справа:
   и то и другое читается как код, а не как текст интерфейса. */
.ds-value {
  margin: 8px 0 0;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}
</style>
