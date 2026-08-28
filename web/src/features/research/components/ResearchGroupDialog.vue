<script setup lang="ts">
// Группа исследования: привязать её или сменить на другую. Одно окно на оба случая — поле у них
// одно и то же, различается только заголовок; отдельное окно ради заголовка означало бы две
// формы, расходящиеся при первой же правке.
//
// Отвязка сюда не входит: там нечего выбирать, и ради неё окно не открывают (пункт меню
// отвязывает сразу).
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppDialog from '@/components/AppDialog.vue'
import { errorText } from '@/api/errorText'

import GroupSelect from './GroupSelect.vue'
import { setResearchGroup, type ResearchListRow } from '../api'

const open = defineModel<boolean>({ required: true })

const props = defineProps<{ research: ResearchListRow | null }>()
const emit = defineEmits<{ saved: [] }>()

const { t } = useI18n()

const groupCode = ref<string | null>(null)
const saving = ref(false)
const error = ref<string | null>(null)

const filing = computed(() => !props.research?.group_code)

/** Выбор ничего не меняет, пока это та же группа, — сохранять нечего. */
const unchanged = computed(() => groupCode.value === (props.research?.group_code ?? null))

watch(open, (isOpen) => {
  if (!isOpen) return
  groupCode.value = props.research?.group_code ?? null
  error.value = null
})

async function save() {
  if (!props.research || !groupCode.value || unchanged.value) return
  saving.value = true
  error.value = null
  try {
    // `report: false` — отказ показываем ЗДЕСЬ, рядом с кнопкой: окно остаётся открытым с
    // выбранной группой, а тост увёл бы сообщение из поля зрения.
    await setResearchGroup(props.research.code, groupCode.value, { report: false })
    open.value = false
    emit('saved')
  } catch (e) {
    error.value = errorText(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AppDialog
    v-model="open"
    :title="filing ? t('research.research.group.file_title') : t('research.research.group.move_title')"
    :description="props.research?.title"
    size="narrow"
    :persistent="saving"
    :close-disabled="saving"
  >
    <div class="research-group">
      <!-- Полки, их вид и загрузку держит сам `GroupSelect`: окну остаётся значение. -->
      <GroupSelect
        v-model="groupCode"
        :label="t('research.research.group.field')"
        autofocus
      />

      <VAlert v-if="error" type="error" variant="tonal" density="compact">{{ error }}</VAlert>
    </div>

    <template #actions>
      <VBtn variant="text" :disabled="saving" @click="open = false">
        {{ t('common.action.cancel') }}
      </VBtn>
      <VBtn
        color="primary"
        variant="flat"
        :loading="saving"
        :disabled="!groupCode || unchanged"
        @click="save"
      >
        {{ t('common.action.save') }}
      </VBtn>
    </template>
  </AppDialog>
</template>

<style scoped>
.research-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
