<script setup lang="ts">
// Удаление исследования. Каскад необратим и уносит всю наработку, поэтому окно не просто
// спрашивает «точно?», а перечисляет, чего именно человек лишится — счётчики у строки списка уже
// есть, и они здесь единственный честный ответ на «сколько там всего».
//
// Само окно (шапка, полоса кнопок, запрет закрытия во время запроса) — `ConfirmDialog`; оно
// спрашивает, а удаляет этот компонент, поэтому при отказе окно остаётся открытым с текстом
// ошибки на месте, а не исчезает, оставив человека гадать.
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { errorText } from '@/api/errorText'

import { deleteResearch, type ResearchListRow } from '../api'

const open = defineModel<boolean>({ required: true })

const props = defineProps<{ research: ResearchListRow | null }>()
const emit = defineEmits<{ deleted: [] }>()

const { t } = useI18n()

const busy = ref(false)
const error = ref<string | null>(null)

/** Пустое исследование сносится без перечня — перечислять нечего. */
const losses = computed(() => {
  const row = props.research
  if (!row) return []
  const sources = row.document_kept + row.document_filtered
  return [
    { key: 'areas', count: row.area_count },
    { key: 'queries', count: row.query_count },
    { key: 'sources', count: sources },
  ].filter((entry) => entry.count > 0)
})

watch(open, (isOpen) => {
  if (isOpen) error.value = null
})

async function remove() {
  if (!props.research) return
  busy.value = true
  error.value = null
  try {
    await deleteResearch(props.research.code, { report: false })
    open.value = false
    emit('deleted')
  } catch (e) {
    error.value = errorText(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <ConfirmDialog
    v-model="open"
    :title="t('research.research.delete.title')"
    :confirm-label="t('research.research.delete.submit')"
    :loading="busy"
    @confirm="remove"
  >
    <div class="research-delete">
      <p class="research-delete__text">
        {{ t('research.research.delete.text', { title: props.research?.title }) }}
      </p>

      <ul v-if="losses.length" class="research-delete__losses">
        <li v-for="loss in losses" :key="loss.key">
          {{ t(`research.research.delete.losses.${loss.key}`, { count: loss.count }) }}
        </li>
      </ul>

      <p class="research-delete__warning">{{ t('research.research.delete.warning') }}</p>

      <VAlert v-if="error" type="error" variant="tonal" density="compact">{{ error }}</VAlert>
    </div>
  </ConfirmDialog>
</template>

<style scoped>
.research-delete {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.research-delete__text {
  margin: 0;
}

/* Перечень потерь — список, а не строка через запятую: по нему считывают объём одним взглядом. */
.research-delete__losses {
  margin: 0;
  padding-left: 18px;
}

/* Предупреждение о необратимом — цветом отказа, но без иконки-алерта: это не сбой, а следствие
   выбора, и кричать им на человека, который его только рассматривает, незачем. */
.research-delete__warning {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--error);
}
</style>
