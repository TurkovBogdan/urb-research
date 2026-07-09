<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { IconUser, IconSettings, IconBell } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.dividers.title')" :description="t('design-system.page.dividers.description')" back-to="/design-system" />

    <!-- Horizontal -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.dividers.horizontal') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">default</span>
          <div class="ds-demo ds-demo--v">
            <span class="ds-text">Top block</span>
            <VDivider />
            <span class="ds-text">Bottom block</span>
          </div>
          <span class="ds-spec">&lt;VDivider /&gt;</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">thickness</span>
          <div class="ds-demo ds-demo--v">
            <span class="ds-text">Block A</span>
            <VDivider :thickness="2" />
            <span class="ds-text">Block B</span>
          </div>
          <span class="ds-spec">:thickness="2"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">custom color</span>
          <div class="ds-demo ds-demo--v">
            <span class="ds-text">Section 1</span>
            <VDivider class="divider-accent" />
            <span class="ds-text">Section 2</span>
          </div>
          <span class="ds-spec">style="border-color: var(--accent)"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">opacity</span>
          <div class="ds-demo ds-demo--v">
            <span class="ds-text">Block above</span>
            <VDivider :opacity="0.3" />
            <span class="ds-text">Block below</span>
          </div>
          <span class="ds-spec">:opacity="0.3"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">inset</span>
          <div class="ds-demo ds-demo--v">
            <span class="ds-text">Offset item</span>
            <VDivider inset />
            <span class="ds-text">Offset item</span>
          </div>
          <span class="ds-spec">inset — 72px left offset</span>
        </div>

      </div>
    </section>

    <!-- Vertical -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.dividers.vertical') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">vertical</span>
          <div class="ds-demo ds-demo--h">
            <span class="ds-text">Left</span>
            <VDivider vertical />
            <span class="ds-text">Right</span>
          </div>
          <span class="ds-spec">vertical</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">thickness</span>
          <div class="ds-demo ds-demo--h">
            <span class="ds-text">A</span>
            <VDivider vertical :thickness="2" />
            <span class="ds-text">B</span>
            <VDivider vertical :thickness="2" />
            <span class="ds-text">C</span>
          </div>
          <span class="ds-spec">vertical :thickness="2"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">in buttons</span>
          <div class="ds-demo ds-demo--h">
            <VBtn variant="text" size="small">Action 1</VBtn>
            <VDivider vertical style="height: 20px;" />
            <VBtn variant="text" size="small">Action 2</VBtn>
            <VDivider vertical style="height: 20px;" />
            <VBtn variant="text" size="small">Action 3</VBtn>
          </div>
          <span class="ds-spec">between inline elements</span>
        </div>

      </div>
    </section>

    <!-- Usage examples -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.dividers.usage') }}</h6>
      <div class="ds-card">

        <!-- Card with sections -->
        <div class="ds-row">
          <span class="ds-tag">card</span>
          <div class="ds-demo">
            <div class="ex-card">
              <div class="ex-card__section">
                <p class="ex-card__label">General info</p>
                <p class="ex-card__value">Support agent v2.1</p>
              </div>
              <VDivider />
              <div class="ex-card__section">
                <p class="ex-card__label">Status</p>
                <p class="ex-card__value">Active · 3 sessions</p>
              </div>
              <VDivider />
              <div class="ex-card__section">
                <p class="ex-card__label">Last run</p>
                <p class="ex-card__value">2026-05-25 14:22</p>
              </div>
            </div>
          </div>
          <span class="ds-spec">separates card sections</span>
        </div>

        <!-- List with dividers -->
        <div class="ds-row">
          <span class="ds-tag">list</span>
          <div class="ds-demo">
            <VList density="compact" class="ex-list">
              <VListItem>
                <template #prepend><IconUser :size="18" class="ex-list__icon" /></template>
                <VListItemTitle>User</VListItemTitle>
              </VListItem>
              <VDivider inset />
              <VListItem>
                <template #prepend><IconSettings :size="18" class="ex-list__icon" /></template>
                <VListItemTitle>Settings</VListItemTitle>
              </VListItem>
              <VDivider inset />
              <VListItem>
                <template #prepend><IconBell :size="18" class="ex-list__icon" /></template>
                <VListItemTitle>Notifications</VListItemTitle>
              </VListItem>
            </VList>
          </div>
          <span class="ds-spec">inset in VList with icons</span>
        </div>

        <!-- Toolbar / header -->
        <div class="ds-row ds-row--center">
          <span class="ds-tag">toolbar</span>
          <div class="ds-demo ds-demo--h ex-toolbar">
            <span class="ex-toolbar__title">Agents</span>
            <VDivider vertical style="height: 20px;" />
            <span class="ex-toolbar__sub">12 active</span>
            <div style="flex: 1" />
            <VBtn size="small" variant="tonal">Create</VBtn>
            <VDivider vertical style="height: 20px;" />
            <VBtn size="small" variant="text" icon><IconSettings :size="16" /></VBtn>
          </div>
          <span class="ds-spec">separates toolbar groups</span>
        </div>

        <!-- Form with field groups -->
        <div class="ds-row">
          <span class="ds-tag">form</span>
          <div class="ds-demo ds-demo--v">
            <p class="ex-section-title">General</p>
            <div class="ex-form-row">
              <VTextField label="Name" density="compact" hide-details style="max-width: 200px;" />
              <VTextField label="Email" density="compact" hide-details style="max-width: 200px;" />
            </div>
            <VDivider />
            <p class="ex-section-title">Access settings</p>
            <div class="ex-form-row">
              <VSelect label="Role" density="compact" hide-details :items="['Administrator', 'Operator']" style="max-width: 200px;" />
            </div>
          </div>
          <span class="ds-spec">between form field groups</span>
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
  grid-template-columns: 100px 1fr 220px;
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

.ds-text {
  font-size: 13px;
  color: var(--text-muted);
  padding: 4px 0;
}

/* Custom color: main.scss overrides border-color via !important,
   so a more specific selector is needed for a custom color */
:deep(.divider-accent) { border-color: var(--accent) !important; }

.ds-demo {
  display: flex;
  flex-direction: column;
  gap: 0;
  &.ds-demo--h {
    flex-direction: row;
    align-items: center;
    gap: 8px;
  }
  &.ds-demo--v {
    gap: 0;
  }
}

/* Card */
.ex-card {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  overflow: hidden;
  max-width: 280px;
}
.ex-card__section {
  padding: 10px 14px;
}
.ex-card__label {
  margin: 0 0 2px;
  font-size: 11px;
  color: var(--text-faint);
}
.ex-card__value {
  margin: 0;
  font-size: 13px;
  color: var(--text);
}

/* List */
.ex-list {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  max-width: 260px;
}
.ex-list__icon {
  color: var(--text-faint);
}

/* Toolbar */
.ex-toolbar {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  padding: 6px 12px;
  width: 100%;
}
.ex-toolbar__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}
.ex-toolbar__sub {
  font-size: 12px;
  color: var(--text-faint);
}

/* Form */
.ex-section-title {
  margin: 8px 0 8px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-faint);
}
.ex-form-row {
  display: flex;
  gap: 12px;
  padding-bottom: 12px;
}
</style>
