<script setup lang="ts">
import type { StrFieldDescriptor } from '@/features/settings/api'

// Секрет наружу не отдаётся: бэк присылает сентинел `NOT_CHANGED` (заданный токен)
// либо `""` (не задан). Поле держит присланное значение как есть — маскированное
// (не пусто, если задан). Не тронул → уходит обратно тем же сентинелом, и бэк
// (src/core/_settings/api.py) НЕ обновляет токен. Ввёл новое → сохраняется.
defineProps<{
  field: StrFieldDescriptor
  modelValue: string
  error: string | null
  saving: boolean
}>()

defineEmits<{ 'update:modelValue': [string] }>()
</script>

<template>
  <VTextField
    :model-value="modelValue"
    type="password"
    autocomplete="off"
    data-1p-ignore
    data-lpignore="true"
    :label="field.label"
    :error-messages="error ?? undefined"
    hide-details="auto"
    :loading="saving"
    variant="outlined"
    density="comfortable"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>
