<script setup lang="ts">
// Confirmation before something irreversible. Generic on purpose: removals, revocations and
// transfers all deserve the same pause, and they should look identical when they ask for it.
//
// The dialog does NOT perform the action — it asks. The parent listens for `confirm`, runs the
// work, and closes by setting the model. That split is what lets the parent keep the dialog open
// on failure (with the error rendered where the user is looking) instead of it vanishing on click
// and leaving them to guess whether anything happened.
import { useI18n } from 'vue-i18n'
import AppDialog from './AppDialog.vue'

const open = defineModel<boolean>({ required: true })

withDefaults(defineProps<{
  title: string
  /** Body text. Use the default slot instead when it needs markup. */
  text?: string
  /** Label of the confirming button; defaults to a neutral "Confirm". */
  confirmLabel?: string
  /** `danger` paints the confirm button as destructive — the default for a removal. */
  tone?: 'danger' | 'primary'
  /** Work in flight: buttons lock and the dialog refuses to close behind the user's back. */
  loading?: boolean
}>(), {
  text: undefined,
  confirmLabel: undefined,
  tone: 'danger',
  loading: false,
})

const emit = defineEmits<{ (e: 'confirm'): void }>()

const { t } = useI18n()
</script>

<template>
  <!-- `rule=false`: спрашивающий текст ниже И ЕСТЬ описание, отделять его от заголовка нечем. -->
  <AppDialog
    v-model="open"
    :title="title"
    size="narrow"
    :rule="false"
    :persistent="loading"
    :close-disabled="loading"
  >
    <div class="cfm__text">
      <slot>{{ text }}</slot>
    </div>

    <template #actions>
      <VBtn variant="text" :disabled="loading" @click="open = false">
        {{ t('common.action.cancel') }}
      </VBtn>
      <VBtn
        :color="tone === 'danger' ? 'error' : 'primary'"
        variant="flat"
        :loading="loading"
        @click="emit('confirm')"
      >
        {{ confirmLabel ?? t('common.action.confirm') }}
      </VBtn>
    </template>
  </AppDialog>
</template>

<style scoped>
/* Отступы приносит тело окна; текст отвечает только за собственный набор. */
.cfm__text {
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-muted);
  overflow-wrap: anywhere;
}
</style>
