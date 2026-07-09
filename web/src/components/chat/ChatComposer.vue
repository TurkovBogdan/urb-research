<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { IconSend, IconX } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'
import type { TablerIcon } from '@/shared/nav'

interface QuickReply {
  label: string
  text: string
}

const props = withDefaults(defineProps<{
  modelValue?: string
  placeholder?: string
  disabled?: boolean
  quickReplies?: QuickReply[]
  submitIcon?: TablerIcon
  // Editor mode: keep the text after submit instead of clearing — for editing a standing value
  // (e.g. a per-contact instruction) rather than sending a fresh message.
  clearOnSend?: boolean
  // Show a secondary cancel button next to submit (e.g. to discard an in-progress edit).
  cancelable?: boolean
  width?: number
}>(), {
  modelValue: '',
  quickReplies: () => [],
  submitIcon: () => IconSend,
  clearOnSend: true,
  cancelable: false,
  width: 840,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  send: [value: string]
  cancel: []
}>()

const { t } = useI18n()

const rootEl = ref<HTMLElement | null>(null)

// A direct v-model on the field is required for VTextarea's auto-grow to recalculate height;
// the external v-model is mirrored through watchers rather than a controlled :model-value binding.
const draft = ref(props.modelValue)
watch(draft, (value) => emit('update:modelValue', value))
watch(() => props.modelValue, (value) => { if (value !== draft.value) draft.value = value })

const canSend = () => !props.disabled && draft.value.trim().length > 0

function textareaEl(): HTMLTextAreaElement | null {
  return rootEl.value?.querySelector('textarea.v-field__input:not(.v-textarea__sizer)') ?? null
}

function focus() {
  const field = textareaEl()
  field?.focus()
  field?.setSelectionRange(field.value.length, field.value.length)
}

defineExpose({ focus })

// A quick reply drops its full canned text into the draft at the caret (keeping anything already
// typed), then restores focus with the caret after the inserted text so the agent can keep editing.
function applyQuickReply(reply: QuickReply) {
  const field = textareaEl()
  const start = field?.selectionStart ?? draft.value.length
  const end = field?.selectionEnd ?? draft.value.length
  draft.value = draft.value.slice(0, start) + reply.text + draft.value.slice(end)
  const caret = start + reply.text.length
  nextTick(() => {
    const next = textareaEl()
    next?.focus()
    next?.setSelectionRange(caret, caret)
  })
}

function submit() {
  if (!canSend()) return
  emit('send', draft.value.trim())
  if (props.clearOnSend) draft.value = ''
}

function cancel() {
  draft.value = ''
  emit('cancel')
}

// Enter sends, Shift+Enter inserts a newline — the standard chat composer convention.
function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submit()
  }
}
</script>

<template>
  <div ref="rootEl" class="chat-composer" :style="{ '--chat-composer-width': `${props.width}px` }">
    <div class="chat-composer__inner">
      <VTextarea
        v-model="draft"
        :placeholder="placeholder ?? t('common.chat.composer.placeholder')"
        :disabled="disabled"
        auto-grow
        rows="1"
        max-rows="6"
        variant="solo-filled"
        density="comfortable"
        hide-details
        flat
        class="chat-composer__field"
        @keydown="onKeydown"
      />

      <VBtn
        v-if="cancelable"
        :icon="IconX"
        variant="tonal"
        :disabled="disabled || draft.trim().length === 0"
        class="chat-composer__cancel"
        :aria-label="t('common.chat.composer.cancel')"
        @click="cancel"
      />

      <VBtn
        :icon="submitIcon"
        color="primary"
        variant="flat"
        :disabled="!canSend()"
        class="chat-composer__send"
        :aria-label="t('common.chat.composer.send')"
        @click="submit"
      />
    </div>

    <div v-if="quickReplies.length" class="chat-composer__quick">
      <VChip
        v-for="(reply, i) in quickReplies"
        :key="i"
        size="small"
        variant="tonal"
        :disabled="disabled"
        @click="applyQuickReply(reply)"
      >
        {{ reply.label }}
      </VChip>
    </div>
  </div>
</template>

<style scoped>
.chat-composer {
  /* Single-row height of the solo-filled comfortable field — the send button squares to it so
     the two read as one control at rest; the button keeps this size, aligned to the field's
     bottom edge, as the textarea grows. */
  --composer-control-height: 48px;
  --chat-composer-gutter: 24px;
  padding: 12px max(var(--chat-composer-gutter), calc((100% - var(--chat-composer-width, 840px)) / 2));
  background: var(--surface);
}

.chat-composer__inner {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.chat-composer__field {
  flex: 1 1 0;
  min-width: 0;
}

/* Vuetify measures the auto-grow height into --v-textarea-control-height, but the app's global
   density rules pin .v-field__input to a fixed min-height (unlayered CSS beats Vuetify's @layer),
   so the field never grows past one row. Re-honor the measured height here, scoped to the composer.
   The :not(.v-textarea__sizer) is critical: the hidden sizer Vuetify measures is also a
   .v-field__input — flooring its min-height would stop its scrollHeight from shrinking, so the
   height would ratchet up and never come back down. Leave the sizer free to grow AND shrink. */
.chat-composer :deep(.v-textarea .v-field__input:not(.v-textarea__sizer)) {
  min-height: var(--v-textarea-control-height);
}

.chat-composer__quick {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.chat-composer__quick .v-chip {
  cursor: pointer;
}

/* Square the buttons to the single-row field height; the flex row aligns them to the field's
   bottom edge, so they sit on the last line as the textarea grows. Radius mirrors the field. */
.chat-composer__send,
.chat-composer__cancel {
  flex-shrink: 0;
  width: var(--composer-control-height);
  height: var(--composer-control-height);
  min-width: var(--composer-control-height);
  border-radius: 8px;
}
</style>
