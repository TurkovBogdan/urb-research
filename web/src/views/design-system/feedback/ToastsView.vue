<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'
import { clearToasts, pushToast, toasts, type ToastLevel } from '@/composables/useToasts'

const { t } = useI18n()

const levels: ToastLevel[] = ['success', 'info', 'warn', 'error']

const usageSnippet = `// Отказ запроса всплывает САМ: клиент API зовёт pushToast через errorText (api/client/internal.ts).
// Руками — только то, чего клиент не знает: успех операции и предупреждения интерфейса.
import { pushToast } from '@/composables/useToasts'

pushToast('Настройки сохранены', 'success')
pushToast('Поиск уже выполняется', 'warn')

// timeout: 0 — сообщение висит, пока его не закроют
pushToast('Сервер перезапускается…', 'info', 0)`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader
      :title="t('design-system.page.toasts.title')"
      :description="t('design-system.page.toasts.description')"
      back-to="/design-system"
    />

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.toasts.levels') }}</h6>
      <div class="ds-card">
        <div v-for="level in levels" :key="level" class="ds-row">
          <span class="ds-tag">{{ level }}</span>
          <div class="ds-controls">
            <VBtn
              variant="outlined"
              size="small"
              @click="pushToast(t(`design-system.section.toasts.sample.${level}`), level)"
            >
              {{ t('design-system.section.toasts.show') }}
            </VBtn>
          </div>
          <span class="ds-spec">pushToast(text, '{{ level }}')</span>
        </div>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.toasts.queue') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">queue</span>
          <div class="ds-controls">
            <VBtn
              variant="outlined"
              size="small"
              @click="levels.forEach((level, i) => pushToast(`${i + 1}. ${t(`design-system.section.toasts.sample.${level}`)}`, level))"
            >
              {{ t('design-system.section.toasts.burst') }}
            </VBtn>
            <VBtn variant="text" size="small" @click="clearToasts">
              {{ t('design-system.section.toasts.clear') }}
            </VBtn>
          </div>
          <span class="ds-spec">{{ toasts.length }} / 3</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">dedupe</span>
          <div class="ds-controls">
            <VBtn
              variant="outlined"
              size="small"
              @click="pushToast(t('design-system.section.toasts.sample.error'), 'error')"
            >
              {{ t('design-system.section.toasts.same') }}
            </VBtn>
          </div>
          <span class="ds-spec">{{ t('design-system.section.toasts.dedupe_note') }}</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">sticky</span>
          <div class="ds-controls">
            <VBtn
              variant="outlined"
              size="small"
              @click="pushToast(t('design-system.section.toasts.sample.sticky'), 'info', 0)"
            >
              {{ t('design-system.section.toasts.show') }}
            </VBtn>
          </div>
          <span class="ds-spec">timeout: 0</span>
        </div>
      </div>
    </section>

    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.toasts.usage') }}</h6>
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
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 100px 1fr 200px;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
}
.ds-row:last-child { border-bottom: none; }

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
}

.ds-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
