<script setup lang="ts">
// Переименование исследования из списка. На карточке исследования название правится на месте
// (`TitleEditor`), но в списке править нечего — строка не форма, — поэтому здесь окно: тот же
// набор действий, что у группы и удаления, и держит их всех список.
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppDialog from '@/components/AppDialog.vue'
import { errorText } from '@/api/errorText'

import { renameResearch, type ResearchListRow } from '../api'

/** Столько принимает бэкенд (`TitleBody`): длиннее не отправляем вовсе. */
const MAX_LENGTH = 128

const open = defineModel<boolean>({ required: true })

const props = defineProps<{ research: ResearchListRow | null }>()
const emit = defineEmits<{ saved: [] }>()

const { t } = useI18n()

const title = ref('')
const saving = ref(false)
const error = ref<string | null>(null)

const trimmed = computed(() => title.value.trim())
const submittable = computed(() => !!trimmed.value && trimmed.value !== props.research?.title)

watch(open, (isOpen) => {
  if (!isOpen) return
  title.value = props.research?.title ?? ''
  error.value = null
})

async function save() {
  if (!props.research || !submittable.value) return
  saving.value = true
  error.value = null
  try {
    // `report: false` — отказ показываем ЗДЕСЬ, рядом с кнопкой: окно остаётся открытым с
    // набранным названием, а тост увёл бы сообщение из поля зрения.
    await renameResearch(props.research.code, trimmed.value, { report: false })
    open.value = false
    emit('saved')
  } catch (e) {
    error.value = errorText(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AppDialog
    v-model="open"
    :title="t('research.research.rename.title')"
    size="narrow"
    :persistent="saving"
    :close-disabled="saving"
  >
    <div class="research-rename">
      <VTextField
        v-model="title"
        :label="t('research.research.rename.field')"
        :maxlength="MAX_LENGTH"
        :disabled="saving"
        variant="outlined"
        density="comfortable"
        hide-details
        autofocus
        @keyup.enter="save"
      />

      <VAlert v-if="error" type="error" variant="tonal" density="compact">{{ error }}</VAlert>
    </div>

    <template #actions>
      <VBtn variant="text" :disabled="saving" @click="open = false">
        {{ t('common.action.cancel') }}
      </VBtn>
      <VBtn
        color="primary"
        variant="flat"
        :loading="saving"
        :disabled="!submittable"
        @click="save"
      >
        {{ t('common.action.save') }}
      </VBtn>
    </template>
  </AppDialog>
</template>

<style scoped>
.research-rename {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
