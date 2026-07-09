<script setup lang="ts">
import { computed } from 'vue'
import type { FieldDescriptor } from '@/features/settings/api'

import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import SettingFieldInt from './SettingFieldInt.vue'
import SettingFieldFloat from './SettingFieldFloat.vue'
import SettingFieldBool from './SettingFieldBool.vue'
import SettingFieldString from './SettingFieldString.vue'
import SettingFieldSecret from './SettingFieldSecret.vue'
import SettingFieldDate from './SettingFieldDate.vue'
import SettingFieldDateTime from './SettingFieldDateTime.vue'
import SettingFieldChoice from './SettingFieldChoice.vue'
import SettingFieldMultiChoice from './SettingFieldMultiChoice.vue'
import SettingFieldList from './SettingFieldList.vue'

const props = defineProps<{
  field: FieldDescriptor
  modelValue: unknown
  error: string | null
  saving: boolean
}>()

defineEmits<{ 'update:modelValue': [unknown] }>()

const editors = {
  int: SettingFieldInt,
  float: SettingFieldFloat,
  bool: SettingFieldBool,
  str: SettingFieldString,
  date: SettingFieldDate,
  datetime: SettingFieldDateTime,
  choice: SettingFieldChoice,
  multichoice: SettingFieldMultiChoice,
  list: SettingFieldList,
} as const

// Секретная строка сохраняется вручную (кнопка) — свой редактор вместо автосейва.
const editor = computed(() =>
  props.field.kind === 'str' && props.field.secret
    ? SettingFieldSecret
    : editors[props.field.kind],
)

// Bool-поле рисует описание внутри плашки-переключателя (сгруппировано с заголовком),
// поэтому общая подпись снизу для него не нужна.
const descriptionBelow = computed(
  () => Boolean(props.field.description) && props.field.kind !== 'bool',
)
</script>

<template>
  <div class="setting-field">
    <component
      :is="editor"
      :field="field as never"
      :model-value="modelValue as never"
      :error="error"
      :saving="saving"
      @update:model-value="$emit('update:modelValue', $event)"
    />
    <!-- Descriptions render as Markdown so a field caption can carry links (e.g. the
         service token page for a connector API key). Single home for every field kind. -->
    <div v-if="descriptionBelow" class="setting-field__desc">
      <MarkdownRenderer :text="field.description" compact />
    </div>
  </div>
</template>

<style scoped>
.setting-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.setting-field__desc :deep(.md-body) {
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-muted);
}
.setting-field__desc :deep(.md-body p) {
  margin: 0;
}
</style>
