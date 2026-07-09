<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.typography.title')" :description="t('design-system.page.typography.description')" back-to="/design-system" />

    <!-- Headings -->
    <section class="ds-section">
      <h6 class="mb-4">{{ t('design-system.section.typography.headings') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">h1</span>
          <h1>Display heading</h1>
          <span class="ds-spec">28px / 700 / −0.02em</span>
        </div>
        <div class="ds-row">
          <span class="ds-tag">h2</span>
          <h2>Section heading</h2>
          <span class="ds-spec">20px / 600 / −0.01em</span>
        </div>
        <div class="ds-row">
          <span class="ds-tag">h3</span>
          <h3>Card heading</h3>
          <span class="ds-spec">16px / 600</span>
        </div>
        <div class="ds-row">
          <span class="ds-tag">h4</span>
          <h4>Block subheading</h4>
          <span class="ds-spec">14px / 600</span>
        </div>
        <div class="ds-row">
          <span class="ds-tag">h5</span>
          <h5>Field label</h5>
          <span class="ds-spec">13px / 600</span>
        </div>
        <div class="ds-row">
          <span class="ds-tag">h6</span>
          <h6>SECTION TITLE</h6>
          <span class="ds-spec">11px / 600 / +0.07em / uppercase / faint</span>
        </div>
      </div>
    </section>

    <!-- Text -->
    <section class="ds-section">
      <h6 class="mb-4">{{ t('design-system.section.typography.text') }}</h6>
      <div class="ds-card">
        <div class="ds-row ds-row--top">
          <span class="ds-tag">p</span>
          <p>Primary interface text. Used for descriptions, hints, and card content. Size 13px with a 1.6 line height for comfortable readability.</p>
          <span class="ds-spec">13px / 400 / 1.6lh</span>
        </div>
        <div class="ds-row">
          <span class="ds-tag">small</span>
          <small>Meta information, timestamps, counters, secondary captions</small>
          <span class="ds-spec">12px / 400 / muted</span>
        </div>
      </div>
    </section>

    <!-- Code -->
    <section class="ds-section">
      <h6 class="mb-4">{{ t('design-system.section.typography.code') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">code</span>
          <p>Task identifier <code>hh.apply_to_vacancies</code> or the <code>session_token</code> key</p>
          <span class="ds-spec">12px / mono / accent</span>
        </div>
        <div class="ds-row ds-row--top">
          <span class="ds-tag">pre</span>
          <pre>GET /api/v1/hh/vacancies
{ "status": "running", "ttl": 60 }</pre>
          <span class="ds-spec">12px / mono / block</span>
        </div>
      </div>
    </section>

    <!-- Links -->
    <section class="ds-section">
      <h6 class="mb-4">{{ t('design-system.section.typography.links') }}</h6>
      <div class="ds-card">
        <div class="ds-row">
          <span class="ds-tag">a</span>
          <p><a href="#">Link to a page</a> — accent color, underline on hover</p>
          <span class="ds-spec">accent / underline:hover</span>
        </div>
      </div>
    </section>

    <!-- Fonts -->
    <section class="ds-section">
      <h6 class="mb-4">{{ t('design-system.section.typography.families') }}</h6>
      <div class="ds-card">
        <div class="ds-row ds-row--top">
          <span class="ds-tag">—font</span>
          <div class="ds-font-preview">
            Onest — ABCDEFGHIJKLM abcdefghijklm 0123456789
          </div>
          <span class="ds-spec">'Onest', system-ui</span>
        </div>
        <div class="ds-row ds-row--top">
          <span class="ds-tag">—font-mono</span>
          <div class="ds-font-preview ds-font-preview--mono">
            JetBrains Mono — ABCDEF abcdef 0123456789
          </div>
          <span class="ds-spec">'JetBrains Mono'</span>
        </div>
      </div>
    </section>
  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page {
  max-width: 860px;
}

.ds-section {
  margin-bottom: 28px;
}

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 110px 1fr 220px;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
  &.ds-row--top { align-items: start; }
}

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  flex-shrink: 0;
}

.ds-spec {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  text-align: right;
  flex-shrink: 0;
}

.ds-font-preview {
  font-family: var(--font);
  font-size: 18px;
  font-weight: 500;
  color: var(--text);
  line-height: 1.4;
}

.ds-font-preview--mono {
  font-family: var(--font-mono);
  font-weight: 400;
  font-size: 16px;
}
</style>
