<script setup lang="ts">
// Деталь полки: карточка группы + тот же список исследований, что и в реестре, но
// суженный до этой полки. Адрес — /research/researches/GROUP@<code>: сегмент общий с
// карточкой исследования, маршруты разведены по префиксу кода (см. routes.ts).
//
// Пустой хеш (GROUP@) — псевдо-полка «Без группы»: строки в БД у неё нет, поэтому за карточкой
// не ходим, а заголовок и описание берём из словаря. Список при этом фильтруется тем же
// параметром — бэк понимает пустой код как «только не разложенные».
import { computed, onActivated, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconRefresh } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import SectionError from '@/components/SectionError.vue'

import ResearchesList from '../components/ResearchesList.vue'
import { groupColorVars } from '../constants/groupColors'
import { GROUP_ICON_FALLBACK, groupIcon } from '../constants/groupIcons'
import { useResearchesStore } from '../stores/researches.store'
import { getGroup, UNGROUPED_CODE, type GroupRow } from '../api'

const { t } = useI18n()
const route = useRoute()
const store = useResearchesStore()

const group = ref<GroupRow | null>(null)
const error = ref<unknown>(null)

const groupCode = computed(() => {
  const code = route.params.code
  return typeof code === 'string' ? code : ''
})

const ungrouped = computed(() => groupCode.value === UNGROUPED_CODE)

const title = computed(() => (
  ungrouped.value ? t('research.group.ungrouped.title') : group.value?.title ?? t('research.group.detail.title')
))

const description = computed(() => (
  ungrouped.value
    ? t('research.group.ungrouped.description')
    : group.value?.description || t('research.group.detail.description')
))

const icon = computed(() => (
  ungrouped.value || !group.value ? GROUP_ICON_FALLBACK : groupIcon(group.value.icon)
))

async function load() {
  error.value = null
  if (store.groupCode !== groupCode.value) {
    store.groupCode = groupCode.value
    store.resetPage()
  }
  if (ungrouped.value) {
    group.value = null
  } else {
    try {
      // Отказ показывает сама страница (SectionError) — тост дублировал бы его.
      group.value = await getGroup(groupCode.value, { report: false })
    } catch (e) {
      group.value = null
      error.value = e
      return
    }
  }
  await store.load()
}

// KeepAlive держит вьюху живой между визитами — перезагружаем и на активации,
// и на смене кода в адресе, иначе показали бы предыдущую полку.
onActivated(load)
watch(groupCode, load)
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="title"
      :loading="store.loading && !group && !ungrouped"
      back-to="/research/groups"
    >
      <template v-if="group || ungrouped" #description>
        <span class="group-desc color-tones" :style="groupColorVars(group?.color)">
          <component :is="icon" :size="14" :stroke-width="1.7" class="group-desc__icon" />
          {{ description }}
        </span>
      </template>
      <template #actions>
        <VBtn variant="text" :disabled="store.loading" @click="load">
          <template #prepend><IconRefresh :size="16" :class="{ 'icon-spin': store.loading }" /></template>
          {{ t('research.action.refresh') }}
        </VBtn>
      </template>
    </PageHeader>

    <SectionError v-if="error" :error="error" />
    <SectionError v-else-if="store.error" :error="store.error" />
    <ResearchesList v-else :empty-text="t('research.group.detail.empty')" />
  </PageLayout>
</template>

<style scoped>
/* Иконка полки идёт в строку с её описанием — выравниваем по высоте прописной буквы. */
.group-desc {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

/* Цвет несёт иконка, а не строка описания: тон выбран под плашку, и текстом он читался бы
   хуже подписи. Без цвета — акцент, как у псевдо-полки «Без группы». */
.group-desc__icon {
  color: var(--gc-ink, var(--accent));
}
</style>
