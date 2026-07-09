<script setup lang="ts">
import { ref } from 'vue'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { IconRefresh } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'

// Interactive "loading → content" toggle
const loading = ref(true)

const { t } = useI18n()

function reload() {
  loading.value = true
  // simulate a request: show real content after 1.6s
  window.setTimeout(() => { loading.value = false }, 1600)
}
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader
      :title="t('design-system.page.skeleton.title')"
      :description="t('design-system.page.skeleton.description')"
      back-to="/design-system"
    />

    <!-- Basic types -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.skeleton.basicTypes') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">text</span>
          <div class="ds-controls ds-controls--block">
            <VSkeletonLoader type="text" />
          </div>
          <span class="ds-spec">single line</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">heading</span>
          <div class="ds-controls ds-controls--block">
            <VSkeletonLoader type="heading" />
          </div>
          <span class="ds-spec">heading</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">paragraph</span>
          <div class="ds-controls ds-controls--block">
            <VSkeletonLoader type="paragraph" />
          </div>
          <span class="ds-spec">3 text lines</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">avatar</span>
          <div class="ds-controls">
            <VSkeletonLoader type="avatar" />
          </div>
          <span class="ds-spec">round avatar</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">button</span>
          <div class="ds-controls">
            <VSkeletonLoader type="button" />
          </div>
          <span class="ds-spec">button</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">chip</span>
          <div class="ds-controls">
            <VSkeletonLoader type="chip" />
          </div>
          <span class="ds-spec">chip</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">image</span>
          <div class="ds-controls ds-controls--block">
            <VSkeletonLoader type="image" />
          </div>
          <span class="ds-spec">image / preview</span>
        </div>

      </div>
    </section>

    <!-- Composite presets -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.skeleton.presets') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">list-item-avatar</span>
          <div class="ds-controls ds-controls--block">
            <VSkeletonLoader type="list-item-avatar" />
          </div>
          <span class="ds-spec">list row with avatar</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">article</span>
          <div class="ds-controls ds-controls--block">
            <VSkeletonLoader type="article" />
          </div>
          <span class="ds-spec">heading + paragraph</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">card</span>
          <div class="ds-controls ds-controls--block">
            <VSkeletonLoader type="image, article" class="ds-skel-card" />
          </div>
          <span class="ds-spec">image + article</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">table-row</span>
          <div class="ds-controls ds-controls--block">
            <VSkeletonLoader type="table-row-divider@3" />
          </div>
          <span class="ds-spec">table rows ×3</span>
        </div>

      </div>
    </section>

    <!-- Custom set via the type string -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.skeleton.custom') }}</h6>
      <div class="ds-card">

        <div class="ds-row">
          <span class="ds-tag">list ×4</span>
          <div class="ds-controls ds-controls--block">
            <VSkeletonLoader type="list-item-two-line@4" />
          </div>
          <span class="ds-spec">@N — repeat N times</span>
        </div>

        <div class="ds-row">
          <span class="ds-tag">profile</span>
          <div class="ds-controls ds-controls--block">
            <VSkeletonLoader type="avatar, paragraph" />
          </div>
          <span class="ds-spec">comma = row / stack</span>
        </div>

      </div>
    </section>

    <!-- Interactive: loading → content -->
    <section class="ds-section">
      <div class="d-flex align-center justify-space-between mb-3">
        <h6 class="ma-0">{{ t('design-system.section.skeleton.loadingToContent') }}</h6>
        <VBtn size="small" variant="outlined" :prepend-icon="IconRefresh" @click="reload">
          Reload
        </VBtn>
      </div>
      <div class="ds-card ds-card--pad">
        <VSkeletonLoader :loading="loading" type="list-item-avatar-three-line@3">
          <div class="demo-list">
            <div v-for="n in 3" :key="n" class="demo-item">
              <div class="demo-avatar">{{ n }}</div>
              <div class="demo-text">
                <div class="demo-title">List item #{{ n }}</div>
                <div class="demo-sub">Real content that replaces the skeleton once the data has loaded.</div>
              </div>
            </div>
          </div>
        </VSkeletonLoader>
      </div>
      <p class="ds-note">
        <code>:loading="true"</code> renders the skeleton; once it becomes <code>false</code>, Vuetify shows the default slot content.
      </p>
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

  &--pad { padding: 8px; }
}

.ds-row {
  display: grid;
  grid-template-columns: 140px 1fr 200px;
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
  gap: 12px;

  &--block { display: block; }
}

/* Bone color/shimmer are set globally in main.scss.
   Here we only set width: otherwise inline-flex collapses full-width bones to 0. */
.ds-page :deep(.v-skeleton-loader) {
  width: 100%;
}

.ds-skel-card {
  max-width: 280px;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-note {
  margin: 10px 2px 0;
  font-size: 12px;
  color: var(--text-muted);

  code {
    font-family: var(--font-mono);
    font-size: 11px;
    background: var(--input-bg);
    border: 1px solid var(--border-soft);
    border-radius: var(--radius-sm);
    padding: 1px 5px;
  }
}

/* Real content for the interactive block */
.demo-list {
  display: flex;
  flex-direction: column;
}

.demo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
}

.demo-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
  font-size: 14px;
}

.demo-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.demo-sub {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
