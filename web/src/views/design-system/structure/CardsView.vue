<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { ref } from 'vue'
import { IconDots, IconHeart, IconShare, IconRobot, IconChevronRight } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Click feedback for the clickable-card demo.
const clicks = ref(0)
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.cards.title')" :description="t('design-system.page.cards.description')" back-to="/design-system" />

    <!-- Variants -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.cards.variants') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">elevated</span>
          <div class="ds-demo">
            <VCard variant="elevated" class="demo-card">
              <VCardText>Elevated — shadow, no border. Default surface card.</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">variant="elevated"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">flat</span>
          <div class="ds-demo">
            <VCard variant="flat" class="demo-card">
              <VCardText>Flat — no shadow, no border. Sits flush on the page.</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">variant="flat"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">outlined</span>
          <div class="ds-demo">
            <VCard variant="outlined" class="demo-card">
              <VCardText>Outlined — 1px border, no shadow. The app default.</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">variant="outlined"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">tonal</span>
          <div class="ds-demo">
            <VCard variant="tonal" color="primary" class="demo-card">
              <VCardText>Tonal — soft tinted background derived from color.</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">variant="tonal" color="primary"</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">text</span>
          <div class="ds-demo">
            <VCard variant="text" class="demo-card">
              <VCardText>Text — transparent, no chrome. Grouping only.</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">variant="text"</span>
        </div>

      </div>
    </section>

    <!-- Structure -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.cards.structure') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">title + text</span>
          <div class="ds-demo">
            <VCard variant="outlined" class="demo-card">
              <VCardItem>
                <VCardTitle>Support agent</VCardTitle>
                <VCardSubtitle>v2.1 · active</VCardSubtitle>
              </VCardItem>
              <VCardText>VCardItem groups title and subtitle; VCardText holds the body copy.</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">VCardItem + VCardTitle + VCardSubtitle</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">prepend icon</span>
          <div class="ds-demo">
            <VCard variant="outlined" class="demo-card">
              <VCardItem>
                <template #prepend><IconRobot :size="22" class="demo-icon" /></template>
                <VCardTitle>Dispatch task</VCardTitle>
                <VCardSubtitle>cron · every minute</VCardSubtitle>
                <template #append><IconDots :size="18" class="demo-icon" /></template>
              </VCardItem>
            </VCard>
          </div>
          <span class="ds-spec">#prepend / #append slots</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">actions</span>
          <div class="ds-demo">
            <VCard variant="outlined" class="demo-card">
              <VCardItem><VCardTitle>Confirm run</VCardTitle></VCardItem>
              <VCardText>Trigger a manual run of this task now.</VCardText>
              <VCardActions>
                <VSpacer />
                <VBtn variant="text" size="small">Cancel</VBtn>
                <VBtn variant="tonal" color="primary" size="small">Run</VBtn>
              </VCardActions>
            </VCard>
          </div>
          <span class="ds-spec">VCardActions — footer button row</span>
        </div>

      </div>
    </section>

    <!-- Rounded & elevation -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.cards.rounded') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">rounded</span>
          <div class="ds-demo ds-demo--h">
            <VCard variant="outlined" rounded="0" class="demo-card demo-card--sm">
              <VCardText class="demo-mini">rounded="0"</VCardText>
            </VCard>
            <VCard variant="outlined" rounded="lg" class="demo-card demo-card--sm">
              <VCardText class="demo-mini">rounded="lg"</VCardText>
            </VCard>
            <VCard variant="outlined" rounded="xl" class="demo-card demo-card--sm">
              <VCardText class="demo-mini">rounded="xl"</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">rounded="0 | lg | xl"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">elevation</span>
          <div class="ds-demo ds-demo--h">
            <VCard :elevation="2" class="demo-card demo-card--sm">
              <VCardText class="demo-mini">2</VCardText>
            </VCard>
            <VCard :elevation="6" class="demo-card demo-card--sm">
              <VCardText class="demo-mini">6</VCardText>
            </VCard>
            <VCard :elevation="12" class="demo-card demo-card--sm">
              <VCardText class="demo-mini">12</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">:elevation="2 | 6 | 12"</span>
        </div>

      </div>
    </section>

    <!-- States -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.cards.states') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">loading</span>
          <div class="ds-demo">
            <VCard variant="outlined" loading class="demo-card">
              <VCardText>Loading shows an indeterminate progress bar at the top edge.</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">loading</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">disabled</span>
          <div class="ds-demo">
            <VCard variant="outlined" disabled class="demo-card">
              <VCardText>Disabled dims the card and blocks interaction.</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">disabled</span>
        </div>

      </div>
    </section>

    <!-- Clickable -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.cards.clickable') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">link</span>
          <div class="ds-demo">
            <VCard variant="outlined" link class="demo-card">
              <VCardText>link — pointer cursor; the whole card is the click target. Hover highlights the accent border.</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">link</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">hover</span>
          <div class="ds-demo">
            <VCard variant="outlined" hover class="demo-card">
              <VCardText>hover — highlights the accent border on mouse-over (flat, no shadow).</VCardText>
            </VCard>
          </div>
          <span class="ds-spec">hover</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">link + hover</span>
          <div class="ds-demo">
            <VCard variant="outlined" link hover class="demo-card" @click="clicks++">
              <VCardItem>
                <template #prepend><IconRobot :size="22" class="demo-icon" /></template>
                <VCardTitle>Support agent</VCardTitle>
                <VCardSubtitle>v2.1 · 3 sessions</VCardSubtitle>
                <template #append><IconChevronRight :size="18" class="demo-icon" /></template>
              </VCardItem>
            </VCard>
            <p class="click-feedback">Clicked: {{ clicks }}</p>
          </div>
          <span class="ds-spec">link hover @click</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">to / href</span>
          <div class="ds-demo">
            <VCard variant="outlined" link to="/design-system" class="demo-card">
              <VCardItem>
                <VCardTitle>Back to design system</VCardTitle>
                <VCardSubtitle>link + to → router navigation</VCardSubtitle>
                <template #append><IconChevronRight :size="18" class="demo-icon" /></template>
              </VCardItem>
            </VCard>
          </div>
          <span class="ds-spec">link to="/…" (or href)</span>
        </div>

      </div>
    </section>

    <!-- Usage examples -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.cards.usage') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">stat</span>
          <div class="ds-demo ds-demo--h">
            <VCard variant="outlined" class="demo-card demo-card--sm">
              <VCardText>
                <div class="stat__value">1 284</div>
                <div class="stat__label">Conversations</div>
              </VCardText>
            </VCard>
            <VCard variant="outlined" class="demo-card demo-card--sm">
              <VCardText>
                <div class="stat__value stat__value--accent">12</div>
                <div class="stat__label">Running tasks</div>
              </VCardText>
            </VCard>
          </div>
          <span class="ds-spec">KPI / metric tiles</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">media</span>
          <div class="ds-demo">
            <VCard variant="outlined" class="demo-card" max-width="320">
              <div class="media-banner"><IconRobot :size="40" /></div>
              <VCardItem>
                <VCardTitle>Agent report</VCardTitle>
                <VCardSubtitle>Generated 2026-06-05</VCardSubtitle>
              </VCardItem>
              <VCardText>Weekly digest of tagged conversations and lead status shifts.</VCardText>
              <VCardActions>
                <VBtn variant="text" size="small"><template #prepend><IconHeart :size="16" /></template>Save</VBtn>
                <VBtn variant="text" size="small"><template #prepend><IconShare :size="16" /></template>Share</VBtn>
              </VCardActions>
            </VCard>
          </div>
          <span class="ds-spec">media + body + actions</span>
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

.ds-demo {
  display: flex;
  flex-direction: column;
  gap: 8px;
  &.ds-demo--h {
    flex-direction: row;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
  }
}

.demo-card { max-width: 360px; }
.demo-card--sm { width: 120px; flex: 0 0 auto; }

.demo-mini {
  font-family: var(--font-mono);
  font-size: 12px;
  text-align: center;
}

.demo-icon { color: var(--text-faint); }

.click-feedback {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
}

/* Stat tile */
.stat__value {
  font-size: 24px;
  font-weight: 600;
  font-family: var(--font-mono);
  color: var(--text);
  line-height: 1;
}
.stat__value--accent { color: var(--accent); }
.stat__label {
  margin-top: 4px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-faint);
}

/* Media banner */
.media-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 96px;
  background: var(--accent-soft);
  color: var(--accent);
}
</style>
