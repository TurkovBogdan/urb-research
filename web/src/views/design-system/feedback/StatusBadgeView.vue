<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.status-badge.title')" :description="t('design-system.page.status-badge.description')" back-to="/design-system" />

    <!-- Colors -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.status-badge.colors') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">accent</span>
          <div class="ds-controls">
            <StatusBadge color="accent">Active</StatusBadge>
            <StatusBadge color="accent">Running</StatusBadge>
            <StatusBadge color="accent">Enabled</StatusBadge>
          </div>
          <span class="ds-spec">color="accent"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">success</span>
          <div class="ds-controls">
            <StatusBadge color="success">Finished</StatusBadge>
            <StatusBadge color="success">Completed</StatusBadge>
            <StatusBadge color="success">ok</StatusBadge>
          </div>
          <span class="ds-spec">color="success"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">error</span>
          <div class="ds-controls">
            <StatusBadge color="error">Error</StatusBadge>
            <StatusBadge color="error">Failed</StatusBadge>
          </div>
          <span class="ds-spec">color="error"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">warn</span>
          <div class="ds-controls">
            <StatusBadge color="warn">Warning</StatusBadge>
            <StatusBadge color="warn">Caution</StatusBadge>
          </div>
          <span class="ds-spec">color="warn"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">muted</span>
          <div class="ds-controls">
            <StatusBadge color="muted">Disabled</StatusBadge>
            <StatusBadge color="muted">Off</StatusBadge>
            <StatusBadge>no color</StatusBadge>
          </div>
          <span class="ds-spec">color="muted" · default</span>
        </div>

      </div>
    </section>

    <!-- pulse -->
    <section class="ds-section">
      <h6 class="mb-3">Pulse</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">:pulse</span>
          <div class="ds-controls">
            <StatusBadge color="accent" :pulse="true">Active</StatusBadge>
            <StatusBadge color="accent">Active</StatusBadge>
          </div>
          <span class="ds-spec">:pulse="true" — dot glow</span>
        </div>

      </div>
    </section>

    <!-- Status mapping -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.status-badge.mapping') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">session</span>
          <div class="ds-controls">
            <StatusBadge color="accent" :pulse="true">active</StatusBadge>
            <StatusBadge color="success">completed</StatusBadge>
            <StatusBadge color="error">failed</StatusBadge>
          </div>
          <span class="ds-spec">agent session statuses</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">agent</span>
          <div class="ds-controls">
            <StatusBadge color="accent">Enabled</StatusBadge>
            <StatusBadge color="muted">Disabled</StatusBadge>
          </div>
          <span class="ds-spec">agent status</span>
        </div>

      </div>
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
  align-items: start;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
  &.ds-row--center { align-items: center; }
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
</style>
