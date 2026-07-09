<script setup lang="ts">
import { computed } from 'vue'
import type { DateFieldDescriptor } from '@/features/settings/api'

const props = defineProps<{
  field: DateFieldDescriptor
  modelValue: string
  error: string | null
  saving: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [string] }>()

function parseDate(iso: string | null): Date | null {
  if (!iso) return null
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d, 12)
}

function formatDate(date: Date | null): string {
  if (!date) return ''
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const dateModel = computed({
  get: () => parseDate(props.modelValue),
  set: (v: Date | null) => emit('update:modelValue', formatDate(v)),
})
</script>

<template>
  <VDateInput
    v-model="dateModel"
    :min="field.min ?? undefined"
    :max="field.max ?? undefined"
    :label="field.label"
    :error-messages="error ?? undefined"
    hide-details="auto"
    :loading="saving"
    variant="outlined"
    density="comfortable"
  />
</template>
