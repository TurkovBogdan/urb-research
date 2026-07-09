<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'

const colors = [
  { name: '--sidebar-bg',  label: 'Sidebar BG',  desc: 'sidebar background' },
  { name: '--bg',          label: 'Background',   desc: 'app background' },
  { name: '--surface',     label: 'Surface',      desc: 'cards, panels' },
  { name: '--surface-hi',  label: 'Surface Hi',   desc: 'hover state' },
  { name: '--surface-sunken', label: 'Surface Sunken', desc: 'recessed tray' },
  { name: '--input-bg',    label: 'Input BG',     desc: 'input field background' },
  { name: '--border',      label: 'Border',       desc: 'main borders' },
  { name: '--border-soft', label: 'Border Soft',  desc: 'soft dividers' },
  { name: '--border-sunken', label: 'Border Sunken', desc: 'sunken-tray border' },
  { name: '--text',        label: 'Text',         desc: 'primary text' },
  { name: '--text-muted',  label: 'Text Muted',   desc: 'secondary text' },
  { name: '--text-faint',  label: 'Text Faint',   desc: 'tags, specs' },
  { name: '--accent',      label: 'Accent',       desc: 'primary / #008890' },
  { name: '--accent-soft', label: 'Accent Soft',  desc: 'accent 10%' },
  { name: '--accent-mid',  label: 'Accent Mid',   desc: 'accent 25%' },
  { name: '--warn',         label: 'Warn',         desc: 'warning' },
  { name: '--warn-soft',    label: 'Warn Soft',    desc: 'warn 12%' },
  { name: '--error',        label: 'Error',        desc: 'error' },
  { name: '--error-soft',   label: 'Error Soft',   desc: 'error 12%' },
  { name: '--success',      label: 'Success',      desc: 'completed / green' },
  { name: '--success-soft', label: 'Success Soft', desc: 'success 12%' },
  { name: '--info',         label: 'Info',         desc: 'info / cyan' },
  { name: '--info-soft',    label: 'Info Soft',    desc: 'info 12%' },
]

const radii = [
  { name: '--radius',    label: 'radius',    px: '8px',  desc: 'cards, dropdowns' },
  { name: '--radius-sm', label: 'radius-sm', px: '6px',  desc: 'buttons, fields' },
]

const fonts = [
  { name: '--font',      label: 'font',      value: "'Onest', system-ui",    sample: 'The quick brown fox' },
  { name: '--font-mono', label: 'font-mono', value: "'JetBrains Mono', mono", sample: 'const x = 42;' },
]

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.tokens.title')" :description="t('design-system.page.tokens.description')" back-to="/design-system" />

    <!-- Colors -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.tokens.colors') }}</h6>
      <div class="colors-grid">
        <div v-for="c in colors" :key="c.name" class="color-card">
          <div class="color-swatch" :style="{ background: `var(${c.name})` }" />
          <div class="color-info">
            <span class="color-name">{{ c.name }}</span>
            <span class="color-label">{{ c.label }}</span>
            <span class="color-desc">{{ c.desc }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Radii -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.tokens.radii') }}</h6>
      <div class="tokens-row">
        <div v-for="r in radii" :key="r.name" class="radius-card">
          <div class="radius-box" :style="{ borderRadius: `var(${r.name})` }" />
          <div class="token-info">
            <span class="token-name">{{ r.name }}</span>
            <span class="token-value">{{ r.px }}</span>
            <span class="token-desc">{{ r.desc }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Fonts -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.tokens.fonts') }}</h6>
      <div class="ds-card">
        <div v-for="f in fonts" :key="f.name" class="font-row">
          <div class="font-sample" :style="{ fontFamily: `var(${f.name})` }">
            {{ f.sample }}
          </div>
          <div class="font-meta">
            <span class="token-name">{{ f.name }}</span>
            <span class="token-value">{{ f.value }}</span>
          </div>
        </div>
      </div>
    </section>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }
.ds-section { margin-bottom: 32px; }

/* ── Colors ─────────────────────────────────────────────── */
.colors-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}

.color-card {
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border-soft);
  background: var(--surface);
}

.color-swatch {
  height: 56px;
}

.color-info {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.color-name {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  line-height: 1.3;
}

.color-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.3;
}

.color-desc {
  font-size: 10px;
  color: var(--text-faint);
  line-height: 1.3;
}

/* ── Radii ──────────────────────────────────────────────── */
.tokens-row {
  display: flex;
  gap: 12px;
}

.radius-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  flex: 1;
}

.radius-box {
  width: 56px;
  height: 56px;
  background: var(--accent-soft);
  border: 2px solid var(--accent-mid);
  flex-shrink: 0;
}

/* ── Fonts ──────────────────────────────────────────────── */
.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.font-row {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
}

.font-sample {
  font-size: 18px;
  color: var(--text);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Shared token metadata ────────────────────────────── */
.token-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.font-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 220px;
}

.token-name {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent);
}

.token-value {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}

.token-desc {
  font-size: 11px;
  color: var(--text-faint);
}
</style>
