<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const scrollModes = [
  {
    value: 'y',
    label: 'scroll: y',
    desc: 'Vertical scrolling. Default for most pages.',
    use: 'Tasks, lists, forms',
  },
  {
    value: 'x',
    label: 'scroll: x',
    desc: 'Horizontal scrolling. Fixed-height content wider than the screen.',
    use: 'Wide tables, kanban',
  },
  {
    value: 'both',
    label: 'scroll: both',
    desc: 'Scrolling in both directions.',
    use: 'Editors, diagrams, maps',
  },
  {
    value: 'none',
    label: 'scroll: none',
    desc: 'No scrolling. Content manages overflow on its own.',
    use: 'Tables with fixed-header, split-view',
  },
]

const paddingModes = [
  {
    value: 'true',
    label: 'padding: true',
    desc: 'Default. PageLayout adds pa-6 to the content area.',
    use: 'Any standard pages',
  },
  {
    value: 'false',
    label: 'padding: false',
    desc: 'Content flush to the edges. The page manages spacing itself.',
    use: 'Full-bleed tables, custom layout',
  },
]

const routeExample = `// routes.ts
{
  path: '/tasks/:module/:code',
  component: () => import('./views/TaskRunsView.vue'),
  props: true,
  meta: { scroll: 'none', padding: false },
}`

const viewExample = `// TaskRunsView.vue — scroll: none, padding: false
<template>
  <PageLayout>
    <div class="d-flex flex-column h-100 pa-6">
      <PageHeader ... />
      <VCard class="flex-grow-1 min-h-0">
        <VDataTable fixed-header height="100%" ... />
      </VCard>
      <div class="pagination-row">...</div>
    </div>
  </PageLayout>
</template>`

const defaultExample = `// routes.ts — standard page
{
  path: '/tasks',
  component: () => import('./views/TasksView.vue'),
  meta: { scroll: 'y' },   // padding: true — by default
}`

const pageLayoutSource = `// PageLayout.vue — what it does
const contentClass = computed(() => [
  'page-layout__content',
  scrollClass(route.meta.scroll),   // 'scroll-y' | 'scroll-x' | ...
  // .page-layout__content--padded — padding via --page-layout-pad
  // (24px, 16px below md); see styles/layout.scss
  route.meta.padding !== false ? 'page-layout__content--padded' : '',
])`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.layout.title')" :description="t('design-system.page.layout.description')" back-to="/design-system" />

    <!-- Structure -->
    <section class="ds-section">
      <h6 class="mb-4">{{ t('design-system.section.layout.structure') }}</h6>
      <div class="ds-card">
        <div class="layout-diagram">
          <div class="ld-app">
            <div class="ld-label">App.vue — VMain</div>
            <div class="ld-page-layout">
              <div class="ld-label">PageLayout</div>
              <div class="ld-toolbar">
                <span class="ld-slot">#toolbar</span>
                <small>flex-shrink-0 · visibility via layout.showTopBar</small>
              </div>
              <div class="ld-content">
                <span class="ld-slot">#default</span>
                <small>flex-grow-1 · <strong>scroll + padding from route.meta</strong></small>
              </div>
              <div class="ld-footer">
                <span class="ld-slot">#footer</span>
                <small>flex-shrink-0 · visibility via layout.showBottomBar</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- scroll -->
    <section class="ds-section">
      <h6 class="mb-4">meta.scroll</h6>
      <div class="ds-card">
        <div v-for="m in scrollModes" :key="m.value" class="ds-row">
          <code class="ds-code">{{ m.label }}</code>
          <div class="ds-row-body">
            <p>{{ m.desc }}</p>
            <small>{{ m.use }}</small>
          </div>
          <div class="scroll-demo" :class="`scroll-demo--${m.value}`">
            <div class="scroll-demo__inner" />
          </div>
        </div>
      </div>
    </section>

    <!-- padding -->
    <section class="ds-section">
      <h6 class="mb-4">meta.padding</h6>
      <div class="ds-card">
        <div v-for="m in paddingModes" :key="m.value" class="ds-row">
          <code class="ds-code">{{ m.label }}</code>
          <div class="ds-row-body">
            <p>{{ m.desc }}</p>
            <small>{{ m.use }}</small>
          </div>
          <div class="padding-demo" :class="m.value === 'true' ? 'padding-demo--on' : 'padding-demo--off'">
            <div class="padding-demo__inner" />
          </div>
        </div>
      </div>
    </section>

    <!-- Examples -->
    <section class="ds-section">
      <h6 class="mb-4">{{ t('design-system.section.layout.examples') }}</h6>
      <div class="ds-card ds-card--examples">

        <div class="example-block">
          <div class="example-label">Standard page</div>
          <pre>{{ defaultExample }}</pre>
        </div>

        <div class="example-block">
          <div class="example-label">Page with a full-height table</div>
          <pre>{{ routeExample }}</pre>
          <pre>{{ viewExample }}</pre>
        </div>

        <div class="example-block">
          <div class="example-label">How PageLayout applies the parameters</div>
          <pre>{{ pageLayoutSource }}</pre>
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

/* Diagram */
.layout-diagram {
  padding: 20px;
}

.ld-app {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 12px;
  background: var(--bg);
}

.ld-page-layout {
  border: 1px dashed var(--accent-mid);
  border-radius: var(--radius-sm);
  margin-top: 8px;
  overflow: hidden;
}

.ld-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  padding: 4px 10px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.ld-toolbar,
.ld-content,
.ld-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-top: 1px solid var(--border-soft);
}

.ld-content {
  background: var(--legacy-accent-tint-05);
  border-color: var(--accent-mid);
  min-height: 56px;
}

.ld-slot {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid var(--accent-mid);
  border-radius: 4px;
  padding: 1px 7px;
  flex-shrink: 0;
}

/* Rows */
.ds-row {
  display: grid;
  grid-template-columns: 160px 1fr 100px;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
}

.ds-code {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--accent);
  background: var(--accent-soft);
  border: 1px solid var(--accent-mid);
  border-radius: 4px;
  padding: 2px 7px;
  white-space: nowrap;
}

.ds-row-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* Scroll demo */
.scroll-demo {
  width: 88px;
  height: 52px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
}

.scroll-demo__inner {
  position: absolute;
  background: linear-gradient(135deg, var(--accent-soft) 0%, transparent 100%);
  border: 1px solid var(--accent-mid);
  border-radius: 3px;
}

.scroll-demo--y   .scroll-demo__inner { width: calc(100% - 8px); height: 120%; top: 4px; left: 4px; }
.scroll-demo--x   .scroll-demo__inner { width: 160%; height: calc(100% - 8px); top: 4px; left: 4px; }
.scroll-demo--both .scroll-demo__inner { width: 160%; height: 150%; top: 4px; left: 4px; }
.scroll-demo--none .scroll-demo__inner { width: calc(100% - 8px); height: calc(100% - 8px); top: 4px; left: 4px; }

/* Scroll indicators */
.scroll-demo--y::after,
.scroll-demo--x::after,
.scroll-demo--both::after,
.scroll-demo--both::before {
  content: '';
  position: absolute;
  background: var(--accent);
  border-radius: 3px;
  opacity: 0.5;
}
.scroll-demo--y::after   { right: 2px; top: 20%; height: 40%; width: 3px; }
.scroll-demo--x::after   { bottom: 2px; left: 20%; width: 40%; height: 3px; }
.scroll-demo--both::after  { right: 2px; top: 20%; height: 40%; width: 3px; }
.scroll-demo--both::before { bottom: 2px; left: 20%; width: 40%; height: 3px; }

/* Padding demo */
.padding-demo {
  width: 88px;
  height: 52px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.padding-demo__inner {
  background: var(--accent-soft);
  border: 1px solid var(--accent-mid);
  border-radius: 3px;
}

.padding-demo--on  .padding-demo__inner { width: 60%; height: 55%; }
.padding-demo--off .padding-demo__inner { width: 90%; height: 85%; border-radius: 0; }

/* Examples */
.ds-card--examples {
  display: flex;
  flex-direction: column;
}

.example-block {
  padding: 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.example-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-faint);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 4px;
}
</style>
