<script setup lang="ts">
import { computed } from 'vue'
import type { DateTimeFieldDescriptor } from '@/features/settings/api'

const props = defineProps<{
  field: DateTimeFieldDescriptor
  modelValue: string
  error: string | null
  saving: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [string] }>()

// Бэк хранит naive-UTC ISO с секундами (2026-05-12T15:30:00),
// HTML `datetime-local` оперирует форматом без секунд и таймзоны.
// Стрипаем секунды для отображения, добавляем :00 на эмите.
const inputValue = computed(() =>
  props.modelValue ? props.modelValue.slice(0, 16) : '',
)

function onInput(v: string) {
  emit('update:modelValue', v.length >= 16 ? `${v}:00` : v)
}
</script>

<template>
  <VTextField
    :model-value="inputValue"
    type="datetime-local"
    :min="field.min ?? undefined"
    :max="field.max ?? undefined"
    :label="field.label"
    :error-messages="error ?? undefined"
    hide-details="auto"
    :loading="saving"
    variant="outlined"
    density="comfortable"
    @update:model-value="onInput"
  />
</template>
