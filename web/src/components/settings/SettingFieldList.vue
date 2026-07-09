<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconPlus, IconX } from '@tabler/icons-vue'

const { t } = useI18n()

import type {
  FieldDescriptor,
  ListFieldDescriptor,
  ListItemDescriptor,
} from '@/features/settings/api'

import SettingFieldInt from './SettingFieldInt.vue'
import SettingFieldFloat from './SettingFieldFloat.vue'
import SettingFieldString from './SettingFieldString.vue'
import SettingFieldDate from './SettingFieldDate.vue'
import SettingFieldDateTime from './SettingFieldDateTime.vue'
import SettingFieldChoice from './SettingFieldChoice.vue'

const props = defineProps<{
  field: ListFieldDescriptor
  modelValue: unknown[]
  error: string | null
  saving: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [unknown[]] }>()

// Списки кинов в SettingFieldList отдельно — multichoice/list внутри списка
// бэк не отдаёт, остаётся 6 простых типов.
const itemEditors = {
  int: SettingFieldInt,
  float: SettingFieldFloat,
  str: SettingFieldString,
  date: SettingFieldDate,
  datetime: SettingFieldDateTime,
  choice: SettingFieldChoice,
} as const

// Item-дескриптор → полноценный field для соответствующего редактора.
// Label/description пустые — у элементов списка их не бывает.
function itemField(item: ListItemDescriptor): FieldDescriptor {
  return { ...item, key: '', label: '', description: '', default: null } as FieldDescriptor
}

function defaultItemValue(item: ListItemDescriptor): unknown {
  switch (item.kind) {
    case 'int':
    case 'float':
      return 0
    case 'str':
      return ''
    case 'date':
      return '1970-01-01'
    case 'datetime':
      return '1970-01-01T00:00:00'
    case 'choice':
      return item.options[0]?.code ?? ''
  }
}

const canAdd = computed(() =>
  props.field.max_items == null || props.modelValue.length < props.field.max_items,
)
const canRemove = computed(() => props.modelValue.length > props.field.min_items)

function onItemChange(i: number, value: unknown) {
  const next = props.modelValue.slice()
  next[i] = value
  emit('update:modelValue', next)
}

function onRemove(i: number) {
  if (!canRemove.value) return
  const next = props.modelValue.slice()
  next.splice(i, 1)
  emit('update:modelValue', next)
}

function onAdd() {
  if (!canAdd.value) return
  emit('update:modelValue', [...props.modelValue, defaultItemValue(props.field.item)])
}
</script>

<template>
  <div class="setting-field-list">
    <div class="setting-field-list__header">
      <div class="setting-field-list__label">{{ field.label }}</div>
    </div>

    <div
      v-for="(value, i) in modelValue"
      :key="i"
      class="setting-field-list__row"
    >
      <component
        :is="itemEditors[field.item.kind]"
        class="setting-field-list__editor"
        :field="itemField(field.item) as never"
        :model-value="value as never"
        :error="null"
        :saving="saving"
        @update:model-value="onItemChange(i, $event)"
      />
      <VBtn
        :icon="IconX"
        variant="text"
        size="small"
        density="comfortable"
        :disabled="!canRemove"
        @click="onRemove(i)"
      />
    </div>

    <div class="setting-field-list__footer">
      <VBtn
        :prepend-icon="IconPlus"
        variant="text"
        size="small"
        :disabled="!canAdd"
        @click="onAdd"
      >
        {{ t('common.action.add') }}
      </VBtn>
      <VAlert
        v-if="error"
        type="error"
        variant="tonal"
        density="compact"
        class="setting-field-list__error"
      >
        {{ error }}
      </VAlert>
    </div>
  </div>
</template>

<style scoped>
.setting-field-list__header {
  margin-bottom: 8px;
}
.setting-field-list__label {
  font-size: 14px;
  font-weight: 500;
}
.setting-field-list__row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
}
.setting-field-list__editor {
  flex: 1 1 0;
  min-width: 0;
}
.setting-field-list__footer {
  display: flex;
  align-items: center;
  gap: 12px;
}
.setting-field-list__error {
  flex: 1 1 0;
}
</style>
