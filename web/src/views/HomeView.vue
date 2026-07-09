<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import {
  IconServerBolt,
  IconWorldSearch,
  IconSitemap,
  IconTelescope,
  IconNotes,
  IconArrowNarrowRight,
} from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'

const { t } = useI18n()

const flowSteps = [
  { key: 'research', icon: IconTelescope },
  { key: 'area', icon: IconSitemap },
  { key: 'query', icon: IconWorldSearch },
  { key: 'source', icon: IconServerBolt },
  { key: 'note', icon: IconNotes },
] as const

const capabilities = [
  { key: 'mcp', icon: IconServerBolt },
  { key: 'search', icon: IconWorldSearch },
  { key: 'structure', icon: IconSitemap },
  { key: 'result', icon: IconTelescope },
] as const
</script>

<template>
  <PageLayout>
    <div class="home">
      <div class="home__hero">
        <span class="home__badge">{{ t('common.home.badge') }}</span>
        <div class="home__brand">
          <span class="home__glyph">◈</span>
          <h1 class="home__title">{{ t('common.home.title') }}</h1>
        </div>
        <p class="home__lead">{{ t('common.home.lead') }}</p>
      </div>

      <div class="home__flow">
        <div class="home__flow-title">{{ t('common.home.flow.title') }}</div>
        <div class="home__flow-track">
          <template v-for="(step, i) in flowSteps" :key="step.key">
            <div class="home__flow-step">
              <component :is="step.icon" class="home__flow-icon" :size="20" stroke="1.5" />
              <span class="home__flow-label">{{ t(`common.home.flow.steps.${step.key}`) }}</span>
            </div>
            <IconArrowNarrowRight
              v-if="i < flowSteps.length - 1"
              class="home__flow-arrow"
              :size="18"
              stroke="1.5"
            />
          </template>
        </div>
      </div>

      <div class="home__grid">
        <div v-for="cap in capabilities" :key="cap.key" class="home__card">
          <component :is="cap.icon" class="home__card-icon" :size="24" stroke="1.5" />
          <h2 class="home__card-title">{{ t(`common.home.capabilities.${cap.key}.title`) }}</h2>
          <p class="home__card-text">{{ t(`common.home.capabilities.${cap.key}.text`) }}</p>
        </div>
      </div>

      <p class="home__hint">{{ t('common.home.hint') }}</p>
    </div>
  </PageLayout>
</template>

<style scoped>
.home {
  max-width: 880px;
  margin: 0 auto;
  padding: 24px 0 8px;
}

.home__hero {
  text-align: center;
  margin-bottom: 32px;
}

.home__badge {
  display: inline-block;
  padding: 4px 12px;
  border: 1px solid var(--border-soft);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: var(--accent);
  background: var(--accent-soft);
}

.home__brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 18px;
}

.home__glyph {
  font-size: 34px;
  color: var(--accent);
  line-height: 1;
}

.home__title {
  margin: 0;
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--text);
}

.home__lead {
  margin: 16px auto 0;
  max-width: 660px;
  font-size: 15px;
  line-height: 1.65;
  color: var(--text-muted);
}

.home__flow {
  margin-bottom: 32px;
  padding: 18px 20px;
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
}

.home__flow-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-faint);
  margin-bottom: 14px;
}

.home__flow-track {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  flex-wrap: wrap;
}

.home__flow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 4px;
}

.home__flow-icon {
  color: var(--accent);
}

.home__flow-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
}

.home__flow-arrow {
  color: var(--text-faint);
  flex-shrink: 0;
}

.home__grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.home__card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  padding: 20px;
  transition: border-color 0.15s ease;
}

.home__card:hover {
  border-color: var(--accent-mid);
}

.home__card-icon {
  color: var(--accent);
}

.home__card-title {
  margin: 12px 0 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.home__card-text {
  margin: 6px 0 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-muted);
}

.home__hint {
  margin: 28px 0 0;
  text-align: center;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-muted);
}

@media (max-width: 720px) {
  .home__grid {
    grid-template-columns: 1fr;
  }

  .home__flow-track {
    justify-content: center;
  }
}
</style>
