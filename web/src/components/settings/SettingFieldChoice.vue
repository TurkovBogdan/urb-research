<script setup lang="ts">
import type { ChoiceFieldDescriptor } from '@/features/settings/api'

const props = defineProps<{
  field: ChoiceFieldDescriptor
  modelValue: string
  error: string | null
  saving: boolean
}>()

defineEmits<{ 'update:modelValue': [string] }>()
</script>

<template>
  <VSelect
    :model-value="modelValue"
    :items="field.options"
    item-value="code"
    item-title="label"
    :label="field.label"
    :error-messages="error ?? undefined"
    hide-details="auto"
    :loading="saving"
    variant="outlined"
    density="comfortable"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>
