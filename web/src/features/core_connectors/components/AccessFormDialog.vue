<script setup lang="ts">
// Форма подключения, собранная из паспорта коннектора: набор полей задаёт бэкенд, экран о
// конкретных сервисах ничего не знает. Редакторы полей — общие с настройками (дескрипторы
// одинаковые), поэтому секретное поле уже умеет вести себя правильно.
//
// Контракт секрета: приходит сентинел (заданный) или пустая строка (не задан). Не тронул —
// уходит тот же сентинел, и бэк оставляет прежнее значение. Стереть = очистить поле руками:
// пустое поле там, где значение было, уезжает в явный список `clear`.
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import AppDialog from '@/components/AppDialog.vue'
import SettingField from '@/components/settings/SettingField.vue'
import SwitchPanel from '@/components/SwitchPanel.vue'
import { errorText } from '@/api/errorText'
import type { FieldDescriptor, StrFieldDescriptor } from '@/shared/settings-fields'
import {
  createAccess,
  deleteAccess,
  fetchAccess,
  updateAccess,
  SECRET_UNCHANGED,
  type AccessPayload,
  type AccessRow,
  type ConnectorPassport,
} from '../api'

const open = defineModel<boolean>({ required: true })

const props = defineProps<{
  passport: ConnectorPassport
  access: AccessRow | null
}>()

const emit = defineEmits<{ saved: []; removed: [] }>()

const { t } = useI18n()

const fields = ref<FieldDescriptor[]>(props.passport.fields)
const values = ref<Record<string, unknown>>({})
const enabled = ref(true)
const saving = ref(false)
const removing = ref(false)
const error = ref<string | null>(null)

function isSecret(field: FieldDescriptor): boolean {
  return field.kind === 'str' && (field as StrFieldDescriptor).secret
}

function wasSet(field: FieldDescriptor): boolean {
  return field.kind === 'str' && Boolean((field as StrFieldDescriptor).is_set)
}

async function reload() {
  error.value = null
  enabled.value = props.access?.enabled ?? true
  if (props.access === null) {
    fields.value = props.passport.fields
    values.value = Object.fromEntries(props.passport.fields.map(f => [f.key, f.default]))
    return
  }
  const detail = await fetchAccess(props.access.id)
  fields.value = detail.fields.length ? detail.fields : props.passport.fields
  values.value = Object.fromEntries(
    fields.value.map(f => [f.key, detail.values[f.key] ?? f.default]),
  )
}

watch(open, async isOpen => {
  if (isOpen) await reload()
}, { immediate: true })

// Значения, которые реально меняются, плюс явный список стираемых: нетронутый секрет
// (сентинел) не едет вовсе, опустошённый — едет в `clear`.
const payload = computed<AccessPayload>(() => {
  const changed: Record<string, string> = {}
  const clear: string[] = []
  for (const field of fields.value) {
    const value = String(values.value[field.key] ?? '')
    if (!isSecret(field)) {
      changed[field.key] = value
      continue
    }
    if (value === SECRET_UNCHANGED) continue
    if (value === '') {
      if (wasSet(field)) clear.push(field.key)
      continue
    }
    changed[field.key] = value
  }
  return { enabled: enabled.value, values: changed, clear }
})

async function save() {
  saving.value = true
  error.value = null
  try {
    if (props.access === null) await createAccess(props.passport.service, payload.value)
    else await updateAccess(props.access.id, payload.value)
    open.value = false
    emit('saved')
  } catch (e) {
    error.value = errorText(e)
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (props.access === null) return
  removing.value = true
  try {
    await deleteAccess(props.access.id)
    open.value = false
    emit('removed')
  } catch (e) {
    error.value = errorText(e)
  } finally {
    removing.value = false
  }
}
</script>

<template>
  <AppDialog
    v-model="open"
    :title="t('core_connectors.form.title', { name: passport.name })"
    :description="passport.description"
    :close-disabled="saving"
  >
    <div class="access-form">
      <VAlert v-if="error" type="error" variant="tonal" density="compact">{{ error }}</VAlert>

      <SwitchPanel
        v-model="enabled"
        :title-on="t('core_connectors.form.enabled_on')"
        :title-off="t('core_connectors.form.enabled_off')"
        :description-on="t('core_connectors.form.enabled_on_hint')"
        :description-off="t('core_connectors.form.enabled_off_hint')"
      />

      <SettingField
        v-for="field in fields"
        :key="field.key"
        :field="field"
        :model-value="values[field.key]"
        :error="null"
        :saving="false"
        @update:model-value="values[field.key] = $event"
      />
    </div>

    <template #actions>
      <VBtn
        v-if="access"
        variant="text"
        color="error"
        :loading="removing"
        @click="remove"
      >
        {{ t('core_connectors.action.delete') }}
      </VBtn>
      <VSpacer />
      <VBtn variant="text" :disabled="saving" @click="open = false">
        {{ t('core_connectors.action.cancel') }}
      </VBtn>
      <VBtn variant="flat" color="primary" :loading="saving" @click="save">
        {{ t('core_connectors.action.save') }}
      </VBtn>
    </template>
  </AppDialog>
</template>

<style scoped>
.access-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
