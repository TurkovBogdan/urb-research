<script setup lang="ts">
import { computed } from 'vue'
import type { StrFieldDescriptor } from '@/features/settings/api'

const props = defineProps<{
  field: StrFieldDescriptor
  modelValue: string
  error: string | null
  saving: boolean
}>()

defineEmits<{ 'update:modelValue': [string] }>()

const isMultiline = computed(() => props.field.lines > 1)
</script>

<template>
  <VTextarea
    v-if="isMultiline"
    :model-value="modelValue"
    :rows="field.lines"
    :maxlength="field.max_length ?? undefined"
    :counter="field.max_length != null ? true : undefined"
    :label="field.label"
    :error-messages="error ?? undefined"
    hide-details="auto"
    :loading="saving"
    variant="outlined"
    density="comfortable"
    auto-grow
    @update:model-value="$emit('update:modelValue', $event)"
  />
  <VTextField
    v-else
    :model-value="modelValue"
    :maxlength="field.max_length ?? undefined"
    :counter="field.max_length != null ? true : undefined"
    :label="field.label"
    :error-messages="error ?? undefined"
    hide-details="auto"
    :loading="saving"
    variant="outlined"
    density="comfortable"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>
