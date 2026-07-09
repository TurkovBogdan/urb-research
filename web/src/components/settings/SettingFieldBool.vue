<script setup lang="ts">
import type { BoolFieldDescriptor } from '@/features/settings/api'
import SwitchPanel from '@/components/SwitchPanel.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

defineProps<{
  field: BoolFieldDescriptor
  modelValue: boolean
  error: string | null
  saving: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [boolean] }>()
</script>

<template>
  <SwitchPanel
    :model-value="modelValue"
    :title="field.label"
    :disabled="saving"
    tone="transparent"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <MarkdownRenderer v-if="field.description" :text="field.description" compact />
  </SwitchPanel>
</template>

<style scoped>
:deep(.md-body) {
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-muted);
}
:deep(.md-body p) {
  margin: 0;
}
</style>
