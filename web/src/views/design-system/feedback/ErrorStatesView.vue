<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import ErrorState from '@/components/ErrorState.vue'
import SectionError from '@/components/SectionError.vue'
import CodeBlock from '@/components/CodeBlock.vue'
import { ApiError } from '@/api/client/internal'
import { ERROR_KINDS, type ErrorKind } from '@/constants/errors'

const { t } = useI18n()

// Экраны показываются ПО ОДНОМУ через переключатель, а не все сразу: каждый забирает фокус на
// свой заголовок при монтировании, и четыре штуки на странице дрались бы за него.
const kinds = Object.keys(ERROR_KINDS) as ErrorKind[]
const kind = ref<ErrorKind>('not-found')
const spec = computed(() => ERROR_KINDS[kind.value])

const missing = new ApiError(404, { error: 'Исследование не найдено' })
const failed = new ApiError(500, { error: 'Внутренняя ошибка сервера' })
const offline = new ApiError(0, { error: 'Network error', code: 'network' })

const usageSnippet = `// Экран вместо содержимого — ставит клиент API, перехватчик рендера или обработчик навигации.
// Адрес НЕ меняется: уход на отдельный /403 стёр бы то, что человек открывал.
import { setShellError } from '@/composables/useShellError'
setShellError('failure')

// Отказ чтения раздела — на месте содержимого, шелл и меню остаются
<SectionError v-if="store.error" :error="store.error" />

// Отказ операции — всплывает сам, из клиента API. Показывает форма сама → report: false
await internalApi.post('/web-search/queries', body, { report: false })`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader
      :title="t('design-system.page.error-states.title')"
      :description="t('design-system.page.error-states.description')"
      back-to="/design-system"
    />

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.error-states.rule') }}</h6>
      <div class="ds-card ds-card--padded">
        <p class="ds-note">{{ t('design-system.section.error-states.rule_note') }}</p>
        <table class="ds-table">
          <thead>
            <tr>
              <th>{{ t('design-system.section.error-states.col.case') }}</th>
              <th>{{ t('design-system.section.error-states.col.form') }}</th>
              <th>{{ t('design-system.section.error-states.col.who') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in ['route', 'entity', 'forbidden', 'operation', 'failure', 'offline', 'chunk']" :key="row">
              <td>{{ t(`design-system.section.error-states.rules.${row}.case`) }}</td>
              <td>{{ t(`design-system.section.error-states.rules.${row}.form`) }}</td>
              <td class="ds-mono">{{ t(`design-system.section.error-states.rules.${row}.who`) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.error-states.screens') }}</h6>
      <div class="ds-card ds-card--padded">
        <VBtnToggle v-model="kind" mandatory density="compact" variant="outlined" class="mb-4">
          <VBtn v-for="k in kinds" :key="k" :value="k" size="small">{{ k }}</VBtn>
        </VBtnToggle>

        <div class="ds-frame">
          <ErrorState
            :key="kind"
            :icon="spec.icon"
            :code="spec.code"
            :title="t(`common.errors.${spec.key}.title`)"
            :description="t(`common.errors.${spec.key}.description`)"
            :actions="spec.actions"
          />
        </div>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.error-states.section') }}</h6>
      <div class="ds-card ds-card--padded">
        <p class="ds-note">{{ t('design-system.section.error-states.section_note') }}</p>
        <div class="ds-frame ds-frame--short"><SectionError :error="missing" /></div>
        <div class="ds-frame ds-frame--short"><SectionError :error="failed" /></div>
        <div class="ds-frame ds-frame--short"><SectionError :error="offline" /></div>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.error-states.usage') }}</h6>
      <CodeBlock :code="usageSnippet" lang="ts" />
    </section>
  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }
.ds-section { margin-bottom: 28px; }

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
}
.ds-card--padded { padding: 16px; }

.ds-note {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--text-muted);
}

/* Рамка вокруг демонстрации: экран отказа рассчитан на всю зону содержимого, и без границы
   непонятно, где он начинается. */
.ds-frame {
  border: 1px dashed var(--border-soft);
  border-radius: var(--radius-sm);
  min-height: 360px;
  display: flex;
}
.ds-frame--short {
  min-height: 0;
  margin-bottom: 12px;
}
.ds-frame--short:last-child { margin-bottom: 0; }
.ds-frame > * { flex: 1; }

.ds-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.ds-table th {
  text-align: left;
  padding: 6px 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-faint);
  border-bottom: 1px solid var(--border-soft);
}
.ds-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-soft);
  color: var(--text);
  vertical-align: top;
}
.ds-table tr:last-child td { border-bottom: none; }
.ds-mono {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}
</style>
