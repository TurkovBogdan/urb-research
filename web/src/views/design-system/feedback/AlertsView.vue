<script setup lang="ts">
import { ref } from 'vue'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'
import { IconAlertTriangle, IconEye } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Closable demo — clicking the close button hides it; reset to show again.
const showClosable = ref(true)

const usageSnippet = `<!-- Text + action on one line, button wraps below on narrow widths -->
<VAlert color="warning" variant="tonal" density="compact" :icon="IconAlertTriangle">
  <div class="alert-action">
    <span class="alert-action__text">Images &amp; links hidden for tracking protection.</span>
    <VBtn size="small" variant="flat" color="warning" :prepend-icon="IconEye"
          class="alert-action__btn">Show content</VBtn>
  </div>
</VAlert>

<style scoped>
.alert-action { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 12px; }
.alert-action__text { flex: 1 1 auto; min-width: 0; }
.alert-action__btn { margin-left: auto; flex-shrink: 0; }
</style>`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.alerts.title')" :description="t('design-system.page.alerts.description')" back-to="/design-system" />

    <!-- Types -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.alerts.types') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">success</span>
          <div class="ds-controls">
            <VAlert type="success" variant="tonal" :text="t('design-system.section.alerts.sample.success')" />
          </div>
          <span class="ds-spec">type="success"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">info</span>
          <div class="ds-controls">
            <VAlert type="info" variant="tonal" :text="t('design-system.section.alerts.sample.info')" />
          </div>
          <span class="ds-spec">type="info"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">warning</span>
          <div class="ds-controls">
            <VAlert type="warning" variant="tonal" :text="t('design-system.section.alerts.sample.warning')" />
          </div>
          <span class="ds-spec">type="warning"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">error</span>
          <div class="ds-controls">
            <VAlert type="error" variant="tonal" :text="t('design-system.section.alerts.sample.error')" />
          </div>
          <span class="ds-spec">type="error"</span>
        </div>

      </div>
      <p class="ds-note">{{ t('design-system.section.alerts.iconNote') }}</p>
    </section>

    <!-- Variants -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.alerts.variants') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">tonal</span>
          <div class="ds-controls">
            <VAlert type="warning" variant="tonal" :text="t('design-system.section.alerts.sample.warning')" />
          </div>
          <span class="ds-spec">variant="tonal" · default</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">outlined</span>
          <div class="ds-controls">
            <VAlert type="warning" variant="outlined" :text="t('design-system.section.alerts.sample.warning')" />
          </div>
          <span class="ds-spec">variant="outlined"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">flat</span>
          <div class="ds-controls">
            <VAlert type="warning" variant="flat" :text="t('design-system.section.alerts.sample.warning')" />
          </div>
          <span class="ds-spec">variant="flat"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">text</span>
          <div class="ds-controls">
            <VAlert type="warning" variant="text" :text="t('design-system.section.alerts.sample.warning')" />
          </div>
          <span class="ds-spec">variant="text"</span>
        </div>

      </div>
    </section>

    <!-- Density & title -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.alerts.density') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <VAlert type="info" variant="tonal" :text="t('design-system.section.alerts.sample.info')" />
          </div>
          <span class="ds-spec">density default</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">compact</span>
          <div class="ds-controls">
            <VAlert type="info" variant="tonal" density="compact" :text="t('design-system.section.alerts.sample.info')" />
          </div>
          <span class="ds-spec">density="compact"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">title</span>
          <div class="ds-controls">
            <VAlert
              type="info"
              variant="tonal"
              :title="t('design-system.section.alerts.sample.title')"
              :text="t('design-system.section.alerts.sample.info')"
            />
          </div>
          <span class="ds-spec">title="…"</span>
        </div>

      </div>
    </section>

    <!-- Closable -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.alerts.closable') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">closable</span>
          <div class="ds-controls ds-controls--col">
            <VAlert
              v-if="showClosable"
              type="warning"
              variant="tonal"
              closable
              :text="t('design-system.section.alerts.sample.warning')"
              @click:close="showClosable = false"
            />
            <VBtn v-else size="small" variant="text" @click="showClosable = true">
              {{ t('design-system.section.alerts.reset') }}
            </VBtn>
          </div>
          <span class="ds-spec">closable · @click:close</span>
        </div>

      </div>
    </section>

    <!-- With action (mail anti-tracking pattern) -->
    <section class="ds-section">
      <h6 class="mb-1">{{ t('design-system.section.alerts.action') }}</h6>
      <p class="ds-note">{{ t('design-system.section.alerts.actionNote') }}</p>

      <VAlert color="warning" variant="tonal" density="compact" :icon="IconAlertTriangle">
        <div class="alert-action">
          <span class="alert-action__text">{{ t('design-system.section.alerts.sample.tracking') }}</span>
          <VBtn
            size="small"
            variant="flat"
            color="warning"
            :prepend-icon="IconEye"
            class="alert-action__btn"
          >
            {{ t('design-system.section.alerts.showContent') }}
          </VBtn>
        </div>
      </VAlert>

      <CodeBlock :code="usageSnippet" lang="vue" class="mt-3" />
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
  &:last-child { border-bottom: none; }
}

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
.ds-controls > * { flex: 1 1 auto; }
.ds-controls--col { flex-direction: column; align-items: flex-start; }

.ds-note {
  font-size: 12.5px;
  color: var(--text-muted);
  margin: 10px 2px 0;
}

/* Canonical "text + action" layout — button wraps below the text on narrow widths. */
.alert-action {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 12px;
}
.alert-action__text { flex: 1 1 auto; min-width: 0; }
.alert-action__btn { margin-left: auto; flex-shrink: 0; }
</style>
