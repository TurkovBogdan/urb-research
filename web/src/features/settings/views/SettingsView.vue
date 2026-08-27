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
  type FieldDescriptor,
  type ModulePayload,
} from '../api'

/** Блок полей на экране: либо со своей подписью, либо во главе с тумблером. */
interface FieldBlock {
  key: string
  /** Подпись блока. Пусто, когда её роль исполняет тумблер в шапке. */
  caption: string
  /** Bool-поле, поднятое в шапку блока: остальные поля читаются как его содержимое. */
  header: FieldDescriptor | null
  fields: FieldDescriptor[]
}

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

// Условие видимости считается по ТЕКУЩЕЙ форме, а не по сохранённому: выключил сервис — его ключ
// уходит сразу, не дожидаясь сохранения. Скрытое поле не стирается и вернётся вместе с условием.
function visible(module: string, field: FieldDescriptor): boolean {
  const condition = field.visible_when
  return condition === null || values[module]?.[condition.key] === condition.equals
}

// Поля одной группы идут в схеме подряд, поэтому блок закрывается на первом же поле с другой
// группой — сортировать и раскладывать по словарю не нужно, порядок схемы и есть порядок экрана.
function splitByGroup(fields: FieldDescriptor[]): FieldDescriptor[][] {
  const blocks: FieldDescriptor[][] = []
  for (const field of fields) {
    const sameGroupAsPrevious = blocks.length > 0 && blocks[blocks.length - 1][0].group === field.group
    if (sameGroupAsPrevious) blocks[blocks.length - 1].push(field)
    else blocks.push([field])
  }
  return blocks
}

// Тумблер во главе группы («Включить Tavily») сам называет блок, поэтому подпись при нём не
// рисуется — иначе название сервиса стояло бы дважды подряд.
function toBlock(module: string, group: FieldDescriptor[]): FieldBlock {
  const [first, ...rest] = group
  const headed = first.group !== '' && first.kind === 'bool'
  return {
    key: `${first.group}:${first.key}`,
    caption: headed ? '' : first.group,
    header: headed ? first : null,
    fields: (headed ? rest : group).filter((f) => visible(module, f)),
  }
}

const moduleBlocks = computed(() =>
  localizedModules.value.map((m) => ({
    ...m,
    blocks: splitByGroup(m.fields)
      .map((group) => toBlock(m.module, group))
      // Группа, где скрыто всё и нет тумблера, не должна оставлять пустую рамку.
      .filter((b) => b.header !== null || b.fields.length > 0),
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

    <div v-if="!loading" class="modules-grid">
      <VCard
        v-for="m in moduleBlocks"
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
          <div
            v-for="b in m.blocks"
            :key="b.key"
            class="field-block"
            :class="{ 'field-block--headed': b.header }"
          >
            <div v-if="b.caption" class="field-block__caption">{{ b.caption }}</div>

            <SettingField
              v-if="b.header"
              :field="b.header"
              :model-value="values[m.module]?.[b.header.key]"
              :error="fieldErrors[m.module]?.[b.header.key] ?? null"
              :saving="saving"
              @update:model-value="onChange(m.module, b.header.key, $event)"
            />

            <div v-if="b.fields.length" class="field-block__fields">
              <SettingField
                v-for="f in b.fields"
                :key="f.key"
                :field="f"
                :model-value="values[m.module]?.[f.key]"
                :error="fieldErrors[m.module]?.[f.key] ?? null"
                :saving="saving"
                @update:model-value="onChange(m.module, f.key, $event)"
              />
            </div>
          </div>
        </VCardText>
      </VCard>
    </div>
  </PageLayout>
</template>

<style scoped>
/* Раскладка та же, что у «Настройки сервера»: колонки с потолком ширины и высотой по
   содержимому. `minmax(320, 440)` — поле ввода шире ~440px читается хуже, лишнюю ширину отдаём
   соседней колонке; на типовой ширине контента (~930px) встают две колонки.
   `align-items: start` — карточка ровно по своему содержимому: у модулей число полей разное,
   и без него короткая карточка тянулась бы до высоты «Сервисов» с их девятью ключами. */
.modules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 440px));
  align-items: start;
  justify-content: start;
  gap: 16px;
}

/* Одна колонка на узком экране — иначе поля сжимаются до нечитаемых. */
@media (max-width: 700px) {
  .modules-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

/* Блок = группа полей схемы. Внутри поля стоят теснее, чем блоки между собой: расстояние и есть
   то, чем группировка читается, отдельной рамки для этого не нужно. */
.field-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-block__fields {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Поля под тумблером — его содержимое, а не соседи: сдвиг и линейка слева показывают, что ключ
   принадлежит именно этому сервису и уедет вместе с ним. Сдвиг равен ширине переключателя, чтобы
   поля вставали под текстом плашки, а не под её краем. */
.field-block--headed .field-block__fields {
  margin-left: 14px;
  padding-left: 14px;
  border-left: 1px solid var(--border-soft);
}

.field-block__caption {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-muted);
}

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
