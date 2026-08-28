<script setup lang="ts">
// Удаление полки. Пустую сносим вопросом; у непустой сначала решается судьба исследований —
// снять с полки / перевесить на другую / удалить вместе с содержимым.
//
// Выбор обязателен и не имеет «безопасного умолчания по клику»: удаление исследований необратимо,
// поэтому выбранным открывается самый мягкий вариант (снять), а не тот, что был в прошлый раз.
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppDialog from '@/components/AppDialog.vue'
import { errorText } from '@/api/errorText'

import GroupSelect from './GroupSelect.vue'
import { deleteGroup, type GroupListRow, type ResearchesAction } from '../api'

const open = defineModel<boolean>({ required: true })

const props = defineProps<{ group: GroupListRow | null }>()
const emit = defineEmits<{ deleted: [] }>()

const { t } = useI18n()

const action = ref<ResearchesAction>('detach')
const moveTo = ref<string | null>(null)
const busy = ref(false)
const error = ref<string | null>(null)

const hasResearches = computed(() => (props.group?.research_count ?? 0) > 0)

const blocked = computed(() => action.value === 'move' && !moveTo.value)

watch(open, (isOpen) => {
  if (!isOpen) return
  action.value = 'detach'
  moveTo.value = null
  error.value = null
})

async function remove() {
  if (!props.group || blocked.value) return
  busy.value = true
  error.value = null
  try {
    // Отказ показываем в окне, а не тостом: человек смотрит сюда и здесь же решает, что делать.
    await deleteGroup(
      props.group.code,
      hasResearches.value ? { researches: action.value, move_to: moveTo.value } : undefined,
      { report: false },
    )
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
  <AppDialog
    v-model="open"
    :title="t('research.group.delete.title')"
    :description="props.group?.title"
    size="narrow"
    :persistent="busy"
    :close-disabled="busy"
  >
    <div class="group-delete">
      <p class="group-delete__text">
        {{ hasResearches
          ? t('research.group.delete.with_researches', { count: props.group?.research_count })
          : t('research.group.delete.empty') }}
      </p>

      <VRadioGroup v-if="hasResearches" v-model="action" hide-details density="compact">
        <VRadio :label="t('research.group.delete.action.detach')" value="detach" />
        <VRadio :label="t('research.group.delete.action.move')" value="move" />
        <VRadio :label="t('research.group.delete.action.delete')" value="delete" />
      </VRadioGroup>

      <!-- Удаляемая полка из списка исключена: перевесить на неё нельзя. -->
      <GroupSelect
        v-if="hasResearches && action === 'move'"
        v-model="moveTo"
        :label="t('research.group.delete.move_to')"
        :exclude="props.group?.code"
      />

      <p v-if="hasResearches && action === 'delete'" class="group-delete__warning">
        {{ t('research.group.delete.warning') }}
      </p>

      <VAlert v-if="error" type="error" variant="tonal" density="compact">{{ error }}</VAlert>
    </div>

    <template #actions>
      <VBtn variant="text" :disabled="busy" @click="open = false">
        {{ t('common.action.cancel') }}
      </VBtn>
      <VBtn color="error" variant="flat" :loading="busy" :disabled="blocked" @click="remove">
        {{ t('research.group.delete.submit') }}
      </VBtn>
    </template>
  </AppDialog>
</template>

<style scoped>
.group-delete {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.group-delete__text {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-muted);
}

/* Предупреждение о необратимом — цветом отказа, но без иконки-алерта: это не сбой, а следствие
   выбора, и кричать им на человека, который его только рассматривает, незачем. */
.group-delete__warning {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--error);
}
</style>
