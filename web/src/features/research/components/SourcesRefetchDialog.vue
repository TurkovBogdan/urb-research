<script setup lang="ts">
// Массовый повтор получения материала: сначала план, потом прогон кусками.
//
// Работа считается СТРАНИЦАМИ, а не источниками: страница дедуплицирована между исследованиями,
// одна её загрузка чинит всю родню разом. План приходит уже свёрнутым, поэтому окно просто
// режет его на куски по `chunk_size` и шлёт их ПО ОДНОМУ — два куска в полёте удвоили бы
// нагрузку на движок получения мимо его настройки параллелизма.
//
// Окно ведёт прогон само, а не отдаёт его стору: ни одна его величина (план, счётчики, отметки
// строк) не переживает закрытия и никому снаружи не нужна.
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconAlertTriangle, IconCheck } from '@tabler/icons-vue'

import AppDialog from '@/components/AppDialog.vue'
import { errorText } from '@/api/errorText'

import { listUnfetched, refetchSources, type SourcesLevel, type UnfetchedPlan } from '../api'

const open = defineModel<boolean>({ required: true })

const props = defineProps<{ level: SourcesLevel; code: string }>()

/** Материал доехал — разделу пора перечитать источники. */
const emit = defineEmits<{ done: [] }>()

const { t } = useI18n()

const plan = ref<UnfetchedPlan | null>(null)
const loading = ref(false)
const planError = ref<string | null>(null)

const running = ref(false)
const stopped = ref(false)
const runError = ref<string | null>(null)

type PageOutcome = 'fetched' | 'failed'

const outcomes = ref(new Map<string, PageOutcome>())

const pages = computed(() => plan.value?.pages ?? [])
const settled = computed(() => outcomes.value.size)
const fetched = computed(
  () => [...outcomes.value.values()].filter((outcome) => outcome === 'fetched').length,
)
const failed = computed(() => settled.value - fetched.value)
const progress = computed(() => (pages.value.length ? (settled.value / pages.value.length) * 100 : 0))

async function loadPlan() {
  loading.value = true
  planError.value = null
  outcomes.value = new Map()
  runError.value = null
  try {
    plan.value = await listUnfetched(props.level, props.code, { report: false })
  } catch (e) {
    plan.value = null
    planError.value = errorText(e)
  } finally {
    loading.value = false
  }
}

// Строка отвечает за себя: её новый статус и есть итог. Кода, который бэк не вернул, больше нет —
// для человека это такой же «материала нет», как и повторный отказ движка.
function remember(chunk: string[], statuses: Map<string, string>) {
  for (const code of chunk) {
    outcomes.value.set(code, statuses.get(code) === 'pending' ? 'fetched' : 'failed')
  }
}

async function run() {
  const queue = pages.value.map((page) => page.code)
  const size = Math.max(1, plan.value?.chunk_size ?? 1)
  running.value = true
  stopped.value = false
  runError.value = null
  outcomes.value = new Map()
  try {
    for (let at = 0; at < queue.length && !stopped.value; at += size) {
      const chunk = queue.slice(at, at + size)
      const rows = await refetchSources(chunk, { report: false })
      remember(chunk, new Map(rows.map((row) => [row.code, row.status])))
    }
  } catch (e) {
    // Отказ куска останавливает прогон целиком: он один на всех (движок выключен, бэк лёг), и
    // следующий кусок повторил бы его с тем же исходом.
    runError.value = errorText(e)
  } finally {
    running.value = false
    if (settled.value > 0) emit('done')
  }
}

// Закрытое окно прогон не отменяет на бэке — текущий кусок доигрывает, — но следующий не уходит.
watch(open, (isOpen) => {
  if (isOpen) loadPlan()
  else stopped.value = true
})
</script>

<template>
  <AppDialog
    v-model="open"
    :title="t('research.doc.bulk.title')"
    size="wide"
    scrollable
    :close-disabled="running"
  >
    <div v-if="loading" class="bulk__state">{{ t('research.doc.bulk.loading') }}</div>

    <VAlert v-else-if="planError" type="error" variant="tonal" density="compact">
      {{ planError }}
    </VAlert>

    <div v-else-if="!pages.length" class="bulk__state">{{ t('research.doc.bulk.empty') }}</div>

    <template v-else>
      <p class="bulk__summary">
        {{ t('research.doc.bulk.summary', {
          pages: pages.length,
          sources: plan?.sources_total ?? 0,
        }) }}
      </p>

      <div v-if="settled || running" class="bulk__progress">
        <VProgressLinear :model-value="progress" color="primary" height="6" rounded />
        <div class="bulk__counters">
          <span>{{ t('research.doc.bulk.progress', { done: settled, total: pages.length }) }}</span>
          <span class="bulk__counter--ok">{{ t('research.doc.bulk.fetched', { n: fetched }) }}</span>
          <span class="bulk__counter--bad">{{ t('research.doc.bulk.failed', { n: failed }) }}</span>
        </div>
      </div>

      <VAlert v-if="runError" type="error" variant="tonal" density="compact" class="mb-2">
        {{ runError }}
      </VAlert>

      <VList class="bulk__list" density="compact">
        <VListItem v-for="page in pages" :key="page.code" class="bulk__item">
          <VListItemTitle class="bulk__title">{{ page.title || page.url }}</VListItemTitle>
          <VListItemSubtitle class="bulk__url">{{ page.url }}</VListItemSubtitle>

          <template #append>
            <div class="bulk__mark">
              <span v-if="page.sources > 1" class="bulk__shared">
                {{ t('research.doc.bulk.shared', { n: page.sources }) }}
              </span>
              <IconCheck
                v-if="outcomes.get(page.code) === 'fetched'"
                :size="16"
                class="bulk__mark--ok"
              />
              <IconAlertTriangle
                v-else-if="outcomes.get(page.code) === 'failed'"
                :size="16"
                class="bulk__mark--bad"
              />
              <span v-else class="bulk__reason">{{ page.error }}</span>
            </div>
          </template>
        </VListItem>
      </VList>
    </template>

    <template #actions>
      <VBtn v-if="running" variant="text" @click="stopped = true">
        {{ t('research.doc.bulk.stop') }}
      </VBtn>
      <VBtn v-else variant="text" @click="open = false">{{ t('common.action.close') }}</VBtn>
      <VBtn
        color="primary"
        variant="flat"
        :loading="running"
        :disabled="loading || !pages.length"
        @click="run"
      >
        {{ t('research.doc.bulk.start') }}
      </VBtn>
    </template>
  </AppDialog>
</template>

<style scoped>
.bulk__state {
  padding: 8px 0;
  color: var(--text-muted);
}

.bulk__summary {
  margin: 0 0 12px;
  color: var(--text);
}

.bulk__progress {
  margin-bottom: 12px;
}

.bulk__counters {
  display: flex;
  gap: 16px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-muted);
}

.bulk__counter--ok { color: var(--success); }
.bulk__counter--bad { color: var(--error); }

/* Список страниц — на полное окно: прокручивает его тело (`scrollable`), своей рамки не заводим. */
.bulk__list {
  background: transparent;
}

.bulk__item {
  padding-inline: 0;
}

.bulk__title {
  font-size: 13px;
  font-weight: 500;
}

.bulk__url {
  font-size: 12px;
  color: var(--text-faint);
}

.bulk__mark {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Причина отказа набрана моноширинным: это код движка (`ConnectError`, `empty`), а не фраза. */
.bulk__reason {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
}

/* Сколько источников ждёт эту страницу — только когда их больше одного: «1» ничего не добавляет. */
.bulk__shared {
  font-size: 11px;
  color: var(--text-muted);
}

.bulk__mark--ok { color: var(--success); }
.bulk__mark--bad { color: var(--error); }
</style>
