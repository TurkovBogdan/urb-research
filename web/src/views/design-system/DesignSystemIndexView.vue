<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import {
  IconColorSwatch, IconTypography, IconLayout, IconClick,
  IconLayoutColumns, IconSelector, IconForms, IconCurrencyRubel,
  IconToggleRight, IconAdjustmentsHorizontal, IconLoader2, IconCircleDot,
  IconPageBreak, IconTable, IconTableRow, IconLayoutBottombar, IconCode, IconMarkdown,
  IconMessage2, IconCalendarTime, IconSeparator, IconWorld, IconChartLine,
  IconBoxMultiple, IconChartBar, IconChartPie, IconLayoutCards, IconDeviceMobile,
  IconAlertTriangle, IconLayoutKanban, IconArrowsHorizontal, IconTags,
  IconLayoutBottombarExpand, IconToggleLeft, IconPaperclip,
  IconMessages, IconMail, IconChevronDown, IconUsersGroup,
} from '@tabler/icons-vue'
import type { TablerIcon } from '@/shared/nav'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'

const { t, tm, rt } = useI18n()

// slug = route segment + i18n key under `design-system.index.page.<slug>`.
type Page = { slug: string; icon: TablerIcon }
type Group = { key: string; pages: Page[] }

const groups: Group[] = [
  {
    key: 'basics',
    pages: [
      { slug: 'tokens',     icon: IconColorSwatch },
      { slug: 'typography', icon: IconTypography },
      { slug: 'layout',     icon: IconLayout },
    ],
  },
  {
    key: 'responsive',
    pages: [
      { slug: 'breakpoints',  icon: IconDeviceMobile },
      { slug: 'action-panel', icon: IconLayoutBottombarExpand },
    ],
  },
  {
    key: 'controls',
    pages: [
      { slug: 'buttons',      icon: IconClick },
      { slug: 'button-group', icon: IconLayoutColumns },
      { slug: 'selects',      icon: IconSelector },
      { slug: 'inputs',       icon: IconForms },
      { slug: 'numbers',      icon: IconCurrencyRubel },
      { slug: 'toggle',       icon: IconToggleRight },
      { slug: 'sliders',      icon: IconAdjustmentsHorizontal },
      { slug: 'date-pickers', icon: IconCalendarTime },
    ],
  },
  {
    key: 'data',
    pages: [
      { slug: 'data-table',  icon: IconTable },
      { slug: 'table',       icon: IconTableRow },
      { slug: 'pagination',  icon: IconPageBreak },
      { slug: 'world-map',   icon: IconWorld },
    ],
  },
  {
    key: 'charts',
    pages: [
      { slug: 'line-chart', icon: IconChartLine },
      { slug: 'bar-chart',  icon: IconChartBar },
      { slug: 'pie-chart',  icon: IconChartPie },
    ],
  },
  {
    key: 'feedback',
    pages: [
      { slug: 'alerts',       icon: IconAlertTriangle },
      { slug: 'loaders',      icon: IconLoader2 },
      { slug: 'skeleton',     icon: IconBoxMultiple },
      { slug: 'status-badge', icon: IconCircleDot },
      { slug: 'chips',        icon: IconTags },
      { slug: 'switch-panel', icon: IconToggleLeft },
      { slug: 'dialogs',      icon: IconLayoutBottombar },
      { slug: 'tooltips',     icon: IconMessage2 },
    ],
  },
  {
    key: 'content',
    pages: [
      { slug: 'code-block', icon: IconCode },
      { slug: 'markdown',   icon: IconMarkdown },
      { slug: 'chat',       icon: IconMessages },
      { slug: 'message',    icon: IconMail },
    ],
  },
  {
    key: 'structure',
    pages: [
      { slug: 'cards',      icon: IconLayoutCards },
      { slug: 'dividers',   icon: IconSeparator },
      { slug: 'file-cards',   icon: IconPaperclip },
      { slug: 'spoiler',      icon: IconChevronDown },
      { slug: 'members-cell', icon: IconUsersGroup },
    ],
  },
  {
    key: 'interface',
    pages: [
      { slug: 'kanban',        icon: IconLayoutKanban },
      { slug: 'edge-scroller', icon: IconArrowsHorizontal },
    ],
  },
]

const pageLabel = (slug: string) => t(`design-system.index.page.${slug}.label`)
const pageTags = (slug: string) => tm(`design-system.index.page.${slug}.tags`) as unknown[]
const groupLabel = (key: string) => t(`design-system.index.group.${key}`)
</script>

<template>
  <PageLayout>
    <div class="ds-index">
      <PageHeader :title="t('design-system.index.title')" :description="t('design-system.index.description')" />

      <template v-for="(group, i) in groups" :key="group.key">
        <VDivider v-if="i > 0" class="ds-index__divider" />

        <div class="ds-index__group">
          <p class="ds-index__group-label">{{ groupLabel(group.key) }}</p>
          <div class="ds-index__grid">
            <VCard
              v-for="page in group.pages"
              :key="page.slug"
              variant="flat"
              link
              :to="`/design-system/${page.slug}`"
              class="ds-index__card"
            >
              <div class="ds-index__card-head">
                <component :is="page.icon" class="ds-index__icon" :size="20" :stroke-width="1.5" />
                <span class="ds-index__title">{{ pageLabel(page.slug) }}</span>
              </div>
              <div class="ds-index__tags">
                <span v-for="(tag, ti) in pageTags(page.slug)" :key="ti" class="ds-index__tag">{{ rt(tag as string) }}</span>
              </div>
            </VCard>
          </div>
        </div>
      </template>
    </div>
  </PageLayout>
</template>

<style scoped>
.ds-index {
  max-width: 900px;
}

.ds-index__divider {
  margin: 20px 0;
}

.ds-index__group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ds-index__group-label {
  margin: 0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.ds-index__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 10px;
}

/* surface / border / radius / hover / focus — глобальный дефолт .v-card + .v-card--link */
.ds-index__card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
}

.ds-index__card-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ds-index__icon {
  color: var(--accent);
  flex-shrink: 0;
}

.ds-index__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.3;
}

.ds-index__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ds-index__tag {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-faint);
  background: var(--input-bg);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  padding: 1px 6px;
  line-height: 18px;
}
</style>
