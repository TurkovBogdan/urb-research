<script setup lang="ts">
import { computed, onActivated, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconRotate, IconDeviceFloppy } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import SettingField from '@/components/settings/SettingField.vue'
import { useSettingText } from '../settingText'
import {
  listModules,
  putValue,
  type ModulePayload,
} from '../api'

const { t } = useI18n()
const { localizeField } = useSettingText()

// Названия модулей в шапке карточек. Если ключа нет — показываем как есть.
const MODULE_LABELS: Record<string, string> = {
  hh: 'Headhunter',
  core_connectors: 'Сервисы',
  web_search: 'Веб-поиск',
}

const modules = ref<ModulePayload[]>([])
const loading = ref(true)
const refreshing = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
// values — редактируемая копия; saved — снимок с сервера для детекции изменений.
const values = reactive<Record<string, Record<string, unknown>>>({})
const saved = reactive<Record<string, Record<string, unknown>>>({})
// Ошибки валидации по конкретному полю (заполняются на сохранении).
const fieldErrors = reactive<Record<string, Record<string, string | null>>>({})

function moduleLabel(name: string): string {
  return MODULE_LABELS[name] ?? name
}

// Field label/description are backend-owned; translate them at render time so the
// switch is live. Re-runs on locale change (localizeField reads the reactive locale).
const localizedModules = computed(() =>
  modules.value.map((m) => ({
    ...m,
    fields: m.fields.map((f) => localizeField(m.module, f)),
  })),
)

function changed(module: string, key: string): boolean {
  return JSON.stringify(values[module]?.[key]) !== JSON.stringify(saved[module]?.[key])
}

function snapshot(module: string, serverValues: Record<string, unknown>) {
  values[module] = { ...serverValues }
  saved[module] = { ...serverValues }
  fieldErrors[module] = {}
}

async function load() {
  refreshing.value = true
  error.value = null
  try {
    const list = await listModules()
    modules.value = list
    for (const m of list) snapshot(m.module, m.values)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    refreshing.value = false
  }
}

onActivated(async () => {
  await load()
  loading.value = false
})

function onChange(module: string, key: string, value: unknown) {
  values[module] = { ...values[module], [key]: value }
  fieldErrors[module][key] = null
}

// Единая кнопка «Сохранить»: пишем ВСЕ изменённые поля. Введённое значение остаётся
// в поле (снимок двигаем на него), страницу НЕ перечитываем — иначе секрет пришёл бы
// сентинелом и «стёр» бы только что введённый токен из поля. Свежий сентинел придёт
// уже при следующем открытии страницы.
async function saveAll() {
  saving.value = true
  error.value = null
  let hadError = false
  for (const m of modules.value) {
    for (const f of m.fields) {
      if (!changed(m.module, f.key)) continue
      try {
        await putValue(m.module, f.key, values[m.module][f.key])
        saved[m.module][f.key] = values[m.module][f.key]
        fieldErrors[m.module][f.key] = null
      } catch (e) {
        hadError = true
        fieldErrors[m.module][f.key] = e instanceof Error ? e.message : String(e)
      }
    }
  }
  saving.value = false
  if (hadError) error.value = t('settings.error.save_failed')
}
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('settings.page.title')"
      :description="t('settings.page.description')"
    >
      <template #actions>
        <VBtn
          variant="text"
          :disabled="refreshing || saving"
          @click="load"
        >
          <template #prepend><IconRotate :size="16" :class="{ 'icon-spin': refreshing }" /></template>
          {{ t('settings.action.discard') }}
        </VBtn>
        <VBtn
          color="primary"
          :loading="saving"
          @click="saveAll"
        >
          <template #prepend><IconDeviceFloppy :size="18" /></template>
          {{ t('settings.action.save') }}
        </VBtn>
      </template>
    </PageHeader>

    <div v-if="loading" class="d-flex justify-center align-center py-12">
      <VProgressCircular indeterminate size="32" width="2" />
    </div>

    <VAlert
      v-if="error"
      type="error"
      variant="tonal"
      closable
      class="mb-4"
      @click:close="error = null"
    >
      {{ error }}
    </VAlert>

    <div v-if="!loading" class="d-flex flex-column ga-4">
      <VCard
        v-for="m in localizedModules"
        :key="m.module"
        variant="outlined"
        rounded="lg"
      >
        <VCardTitle class="text-h6">{{ moduleLabel(m.module) }}</VCardTitle>
        <div v-if="m.description" class="module-desc">
          <MarkdownRenderer :text="m.description" compact />
        </div>
        <VDivider />
        <VCardText v-if="m.fields.length === 0" class="text-medium-emphasis">
          {{ t('settings.module.no_fields') }}
        </VCardText>
        <VCardText v-else class="d-flex flex-column ga-6">
          <SettingField
            v-for="f in m.fields"
            :key="f.key"
            :field="f"
            :model-value="values[m.module]?.[f.key]"
            :error="fieldErrors[m.module]?.[f.key] ?? null"
            :saving="saving"
            @update:model-value="onChange(m.module, f.key, $event)"
          />
        </VCardText>
      </VCard>
    </div>
  </PageLayout>
</template>

<style scoped>
.module-desc {
  padding: 0 16px 16px;
}
.module-desc :deep(.md-body) {
  font-size: 13px;
  line-height: 1.4;
  color: var(--text-muted);
}
.module-desc :deep(.md-body p) {
  margin: 0;
}
</style>
