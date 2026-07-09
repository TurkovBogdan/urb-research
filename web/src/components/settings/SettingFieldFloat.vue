<script setup lang="ts">
import type { FloatFieldDescriptor } from '@/features/settings/api'

defineProps<{
  field: FloatFieldDescriptor
  modelValue: number
  error: string | null
  saving: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [number] }>()

function onUpdate(v: number | null) {
  if (typeof v === 'number' && !Number.isNaN(v)) emit('update:modelValue', v)
}
</script>

<template>
  <VNumberInput
    :model-value="modelValue"
    :min="field.min ?? undefined"
    :max="field.max ?? undefined"
    :step="field.step"
    :precision="field.decimals"
    :label="field.label"
    :error-messages="error ?? undefined"
    hide-details="auto"
    :loading="saving"
    variant="outlined"
    density="comfortable"
    control-variant="stacked"
    @update:model-value="onUpdate"
  />
</template>
