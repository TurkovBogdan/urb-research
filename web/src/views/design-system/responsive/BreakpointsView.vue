<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDisplay } from 'vuetify'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'

const { t } = useI18n()

// Live, reactive viewport state straight from Vuetify. `name` is the active
// breakpoint key; `mobile` reflects our `mobileBreakpoint: 'md'` override.
const { name, width, mobile, mobileBreakpoint } = useDisplay()

type Bp = { name: string; range: string; color: string }

// Vuetify default thresholds (mobile-first width windows). Each gets a distinct
// hue so the live panel visibly recolours as the viewport crosses a boundary.
const breakpoints: Bp[] = [
  { name: 'xs',  range: '< 600',       color: '#F95053' },
  { name: 'sm',  range: '600 – 959',   color: '#D88000' },
  { name: 'md',  range: '960 – 1279',  color: '#4caf50' },
  { name: 'lg',  range: '1280 – 1919', color: '#008890' },
  { name: 'xl',  range: '1920 – 2559', color: '#7C5CFF' },
  { name: 'xxl', range: '≥ 2560',      color: '#C026D3' },
]

const activeColor = computed(
  () => breakpoints.find(b => b.name === name.value)?.color ?? '#008890',
)
const device = (key: string) => t(`design-system.section.breakpoints.device.${key}`)
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader
      :title="t('design-system.page.breakpoints.title')"
      :description="t('design-system.page.breakpoints.description')"
      back-to="/design-system"
    />

    <!-- Live indicator — recolours and relabels as the window resizes -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.breakpoints.current') }}</h6>
      <div class="bp-live" :style="{ '--bp-color': activeColor }">
        <div class="bp-live__badge">{{ name }}</div>
        <div class="bp-live__meta">
          <div class="bp-live__width">
            {{ width }}<span class="bp-live__unit">px</span>
          </div>
          <div
            class="bp-live__chrome"
            :class="mobile ? 'is-mobile' : 'is-desktop'"
          >
            {{ mobile
              ? t('design-system.section.breakpoints.mobileChrome')
              : t('design-system.section.breakpoints.desktopChrome') }}
          </div>
        </div>
      </div>
    </section>

    <!-- Reference scale — every breakpoint with the mobile cutoff marked -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.breakpoints.scale') }}</h6>
      <div class="bp-scale">
        <template v-for="(b, i) in breakpoints" :key="b.name">
          <!-- Mobile chrome switches below `md` — mark the boundary it sits on -->
          <div
            v-if="b.name === mobileBreakpoint"
            class="bp-scale__threshold"
            :title="t('design-system.section.breakpoints.mobileThreshold')"
          >
            <span class="bp-scale__threshold-label">
              {{ t('design-system.section.breakpoints.mobileThreshold') }}
            </span>
          </div>

          <div
            class="bp-scale__item"
            :class="{ 'is-active': b.name === name }"
            :style="{ '--c': b.color }"
          >
            <span class="bp-scale__bar" />
            <span class="bp-scale__name">{{ b.name }}</span>
            <span class="bp-scale__range">{{ b.range }}</span>
            <span class="bp-scale__device">{{ device(b.name) }}</span>
          </div>

          <span v-if="i < breakpoints.length - 1" class="bp-scale__sep" />
        </template>
      </div>

      <p class="bp-note">{{ t('design-system.section.breakpoints.note') }}</p>
    </section>
  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }
.ds-section { margin-bottom: 32px; }

/* ── Live indicator ─────────────────────────────────────── */
.bp-live {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px 28px;
  border-radius: var(--radius);
  border: 1px solid var(--bp-color);
  background: color-mix(in srgb, var(--bp-color) 10%, var(--surface));
  transition: background 0.25s ease, border-color 0.25s ease;
}

.bp-live__badge {
  flex-shrink: 0;
  min-width: 88px;
  padding: 12px 16px;
  text-align: center;
  font-family: var(--font-mono);
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
  color: #fff;
  background: var(--bp-color);
  border-radius: var(--radius-sm);
  transition: background 0.25s ease;
}

.bp-live__meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bp-live__width {
  font-family: var(--font-mono);
  font-size: 24px;
  font-weight: 600;
  color: var(--text);
  line-height: 1;
}

.bp-live__unit {
  font-size: 14px;
  color: var(--text-faint);
  margin-left: 2px;
}

.bp-live__chrome {
  align-self: flex-start;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
}

.bp-live__chrome.is-mobile {
  color: var(--warn);
  background: var(--warn-soft);
}

.bp-live__chrome.is-desktop {
  color: var(--accent);
  background: var(--accent-soft);
}

/* ── Reference scale ────────────────────────────────────── */
.bp-scale {
  display: flex;
  align-items: stretch;
  gap: 0;
}

.bp-scale__item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid transparent;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.bp-scale__item.is-active {
  background: color-mix(in srgb, var(--c) 10%, var(--surface));
  border-color: var(--c);
}

.bp-scale__bar {
  height: 4px;
  border-radius: 2px;
  background: var(--c);
}

.bp-scale__name {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
}

.bp-scale__range {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.bp-scale__device {
  font-size: 11px;
  color: var(--text-faint);
  line-height: 1.3;
}

.bp-scale__sep { width: 6px; flex-shrink: 0; }

/* Mobile-cutoff marker sitting on the `md` boundary */
.bp-scale__threshold {
  position: relative;
  width: 2px;
  flex-shrink: 0;
  margin: 0 10px;
  background: repeating-linear-gradient(
    to bottom,
    var(--warn) 0 5px,
    transparent 5px 10px
  );
}

.bp-scale__threshold-label {
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font-size: 10px;
  font-weight: 600;
  color: var(--warn);
  background: var(--warn-soft);
  border-radius: 999px;
  padding: 2px 8px;
}

.bp-note {
  margin: 14px 0 0;
  font-size: 12px;
  color: var(--text-faint);
  line-height: 1.5;
}
</style>
