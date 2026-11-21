<script setup lang="ts">
// Подключения коннектора, собранные из паспорта: набор полей задаёт бэкенд, экран о
// конкретных сервисах ничего не знает. Редакторы полей — общие с настройками (дескрипторы
// одинаковые), поэтому секретное поле уже умеет вести себя правильно.
//
// Подключений у коннектора бывает несколько (скрейпер напрямую и через VPN): сверху —
// переключатель между ними и вход «добавить», ниже — форма выбранного. Модули ходят через
// первое, если в их настройках не выбрано другое; выделять его здесь незачем.
//
// Контракт секрета: приходит сентинел (заданный) или пустая строка (не задан). Не тронул —
// уходит тот же сентинел, и бэк оставляет прежнее значение. Стереть = очистить поле руками:
// пустое поле там, где значение было, уезжает в явный список `clear`.
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconPlus } from '@tabler/icons-vue'

import AppDialog from '@/components/AppDialog.vue'
import SettingField from '@/components/settings/SettingField.vue'
import SwitchPanel from '@/components/SwitchPanel.vue'
import { errorText } from '@/api/errorText'
import { pushToast } from '@/composables/useToasts'
import type { FieldDescriptor, StrFieldDescriptor } from '@/shared/settings-fields'
import { useConnectionLabels } from '../labels'
import {
  checkAccess,
  createAccess,
  deleteAccess,
  fetchAccess,
  updateAccess,
  SECRET_UNCHANGED,
  type AccessPayload,
  type AccessRow,
  type ConnectorPassport,
} from '../api'

const NEW_CONNECTION = 'new'
type Selection = number | typeof NEW_CONNECTION

const open = defineModel<boolean>({ required: true })

const props = defineProps<{
  passport: ConnectorPassport
  // Подключения этого коннектора в порядке заведения; пусто — сервис ещё не подключён.
  accesses: AccessRow[]
}>()

const emit = defineEmits<{ saved: []; removed: [] }>()

const { t } = useI18n()
const { connectionLabel } = useConnectionLabels()

const selected = ref<Selection>(NEW_CONNECTION)
const fields = ref<FieldDescriptor[]>(props.passport.fields)
const values = ref<Record<string, unknown>>({})
const title = ref('')
const enabled = ref(true)
const saving = ref(false)
const removing = ref(false)
const checking = ref(false)
const error = ref<string | null>(null)

const current = computed<AccessRow | null>(
  () => props.accesses.find(access => access.id === selected.value) ?? null,
)

function isSecret(field: FieldDescriptor): boolean {
  return field.kind === 'str' && (field as StrFieldDescriptor).secret
}

function wasSet(field: FieldDescriptor): boolean {
  return field.kind === 'str' && Boolean((field as StrFieldDescriptor).is_set)
}

function initialSelection(): Selection {
  return props.accesses[0]?.id ?? NEW_CONNECTION
}

async function select(selection: Selection) {
  selected.value = selection
  error.value = null
  const access = current.value
  title.value = access?.title ?? ''
  enabled.value = access?.enabled ?? true
  if (access === null) {
    fields.value = props.passport.fields
    values.value = Object.fromEntries(props.passport.fields.map(f => [f.key, f.default]))
    return
  }
  const detail = await fetchAccess(access.id)
  fields.value = detail.fields.length ? detail.fields : props.passport.fields
  values.value = Object.fromEntries(
    fields.value.map(f => [f.key, detail.values[f.key] ?? f.default]),
  )
}

watch(open, async isOpen => {
  if (isOpen) await select(initialSelection())
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
  return {
    title: title.value.trim(),
    enabled: enabled.value,
    values: changed,
    clear,
  }
})

async function save() {
  saving.value = true
  error.value = null
  try {
    if (current.value === null) await createAccess(props.passport.service, payload.value)
    else await updateAccess(current.value.id, payload.value)
    open.value = false
    emit('saved')
  } catch (e) {
    error.value = errorText(e)
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (current.value === null) return
  removing.value = true
  try {
    await deleteAccess(current.value.id)
    open.value = false
    emit('removed')
  } catch (e) {
    error.value = errorText(e)
  } finally {
    removing.value = false
  }
}

// Проверяется сохранённое подключение, а не правки в форме: проба идёт через бэк по записи.
async function check() {
  const access = current.value
  if (access === null) return
  checking.value = true
  const subject = `${props.passport.name} · ${connectionLabel(access, props.accesses)}`
  try {
    const result = await checkAccess(access.id)
    const outcome = result.ok
      ? t('core_connectors.check.ok', { ms: result.latency_ms ?? 0 })
      : (result.error ?? t('core_connectors.check.failed'))
    pushToast(`${subject}: ${outcome}`, result.ok ? 'success' : 'error')
  } catch (e) {
    pushToast(`${subject}: ${errorText(e)}`, 'error')
  } finally {
    checking.value = false
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

      <VBtnToggle
        v-if="accesses.length"
        :model-value="selected"
        mandatory
        variant="outlined"
        divided
        density="compact"
        class="connections"
        @update:model-value="select"
      >
        <VBtn v-for="access in accesses" :key="access.id" :value="access.id" size="small">
          {{ connectionLabel(access, accesses) }}
        </VBtn>
        <VBtn :value="NEW_CONNECTION" size="small">
          <IconPlus :size="14" class="connections__add" />
          {{ t('core_connectors.connection.add') }}
        </VBtn>
      </VBtnToggle>

      <VTextField
        v-model="title"
        :label="t('core_connectors.form.connection_title.label')"
        :placeholder="t('core_connectors.form.connection_title.placeholder')"
        :maxlength="96"
        hide-details="auto"
      />

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
        v-if="current"
        variant="text"
        color="error"
        :loading="removing"
        @click="remove"
      >
        {{ t('core_connectors.action.delete') }}
      </VBtn>
      <VBtn v-if="current" variant="text" :loading="checking" @click="check">
        {{ t('core_connectors.action.check') }}
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

/* Подключений может стать больше, чем влезает в строку: переключатель переносится, а не
   уезжает за край окна. */
.connections {
  flex-wrap: wrap;
  height: auto;
  align-self: flex-start;
}

.connections__add { margin-right: 4px; }
</style>
