<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import IconPicker from '@/components/IconPicker.vue'
// Демо идёт на настоящем наборе — палитре полок research (120 кодов): выдуманный список
// показывал бы прокрутку и поиск на данных, которых в приложении нет.
import { groupIcon, groupIconNames } from '@/features/research/constants/groupIcons'

const { t } = useI18n()

const icons = groupIconNames()

const picked = ref<string>('flask')
const empty = ref<string | null>(null)
const short = ref<string>('folder')
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader
      :title="t('design-system.page.icon-picker.title')"
      :description="t('design-system.page.icon-picker.description')"
      back-to="/design-system"
    />

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.icon-picker.basic') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">default</span>
          <div class="ds-controls ds-controls--stack">
            <IconPicker v-model="picked" :icons="icons" :resolve="groupIcon" />
          </div>
          <span class="ds-spec">v-model, :icons, :resolve</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">empty</span>
          <div class="ds-controls ds-controls--stack">
            <IconPicker v-model="empty" :icons="icons" :resolve="groupIcon" />
          </div>
          <span class="ds-spec">v-model=null</span>
        </div>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.icon-picker.height') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">height</span>
          <div class="ds-controls ds-controls--stack">
            <IconPicker v-model="short" :icons="icons" :resolve="groupIcon" :height="120" />
          </div>
          <span class="ds-spec">:height="120"</span>
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
  gap: 4px 16px;
}

/* Пикер занимает всю ширину ячейки: сетка плиток считает колонки от неё. */
.ds-controls--stack {
  display: block;
}
</style>
