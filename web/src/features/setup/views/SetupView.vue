<script setup lang="ts">
import { onActivated, reactive, ref } from 'vue'
import { IconRefresh, IconDeviceFloppy } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { getSetup, applySetup, isBackendUp, type SetupGroup, type SetupField } from '../api'

const groups = ref<SetupGroup[]>([])
// Локальная working-copy: { ENV_KEY: строковое значение }.
const values = reactive<Record<string, string>>({})

const loading = ref(true)
const error = ref<string | null>(null)
const applying = ref(false)
const restarting = ref(false)

async function load() {
  loading.value = true
  error.value = null
  try {
    const payload = await getSetup()
    groups.value = payload.groups
    for (const group of payload.groups)
      for (const field of group.fields) values[field.key] = field.value
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

onActivated(load)

// Видимость реактивна от выбора в форме: postgres-поля скрыты при sqlite и наоборот.
function visibleFields(group: SetupGroup): SetupField[] {
  return group.fields.filter(
    (f) => !f.visible_when || values[f.visible_when.key] === f.visible_when.equals,
  )
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

async function waitForRestart() {
  await sleep(1000)
  for (let attempt = 0; attempt < 30; attempt++) {
    if (await isBackendUp()) {
      window.location.reload()
      return
    }
    await sleep(1000)
  }
  restarting.value = false
  error.value = 'Сервер не вернулся за 30 секунд — проверьте процесс вручную.'
}

async function apply() {
  applying.value = true
  error.value = null
  try {
    await applySetup({ ...values })
    applying.value = false
    restarting.value = true
    await waitForRestart()
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
    applying.value = false
  }
}
</script>

<template>
  <PageLayout>
    <PageHeader
      title="Настройка сервера"
      description="Базовые параметры сервера: база данных, адрес и порты, фоновые задачи. После сохранения сервер перезапустится."
    >
      <template #actions>
        <VBtn variant="text" :disabled="loading || applying || restarting" @click="load">
          <template #prepend><IconRefresh :size="16" /></template>
          Обновить
        </VBtn>
        <VBtn
          color="primary"
          :loading="applying"
          :disabled="restarting"
          @click="apply"
        >
          <template #prepend><IconDeviceFloppy :size="18" /></template>
          Сохранить и перезапустить
        </VBtn>
      </template>
    </PageHeader>

    <div v-if="loading" class="d-flex justify-center py-12">
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

    <VAlert v-if="restarting" type="info" variant="tonal" class="mb-4">
      <div class="d-flex align-center ga-3">
        <VProgressCircular indeterminate size="20" width="2" />
        Сервер перезапускается с новой конфигурацией…
      </div>
    </VAlert>

    <template v-if="!loading">
      <div class="d-flex flex-column ga-4">
        <VCard
          v-for="group in groups"
          :key="group.group"
          variant="outlined"
          rounded="lg"
        >
          <VCardTitle class="text-h6">{{ group.group }}</VCardTitle>
          <VDivider />
          <VCardText class="d-flex flex-column ga-4">
            <div
              v-for="field in visibleFields(group)"
              :key="field.key"
              class="d-flex flex-column"
            >
              <VSelect
                v-if="field.type === 'choice'"
                v-model="values[field.key]"
                :items="field.choices"
                :label="field.label"
                :disabled="applying || restarting"
                density="comfortable"
                hide-details
              />
              <VSwitch
                v-else-if="field.type === 'bool'"
                :model-value="values[field.key] === 'true'"
                :label="field.label"
                :disabled="applying || restarting"
                color="primary"
                density="comfortable"
                hide-details
                @update:model-value="values[field.key] = String($event)"
              />
              <VTextField
                v-else
                v-model="values[field.key]"
                :label="field.label"
                :type="field.type === 'int' ? 'number' : field.secret ? 'password' : 'text'"
                :disabled="applying || restarting"
                density="comfortable"
                hide-details
              />
              <span
                v-if="field.description"
                class="text-caption text-medium-emphasis mt-1"
              >
                {{ field.description }}
              </span>
            </div>
          </VCardText>
        </VCard>
      </div>
    </template>
  </PageLayout>
</template>
