<script setup lang="ts">
import { onActivated, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconChevronRight } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'

import ResearchBody from '../components/ResearchBody.vue'
import DocumentsTable from '../components/DocumentsTable.vue'
import { useAreaDetailStore } from '../stores/area-detail.store'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useAreaDetailStore()

const go = (path: string) => router.push(path)

// KeepAlive-safe reload (see ResearchView).
function reload() {
  const code = route.params.code
  if (typeof code === 'string' && code) store.load(code)
}
onActivated(reload)
watch(() => route.params.code, reload)
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('research.area.detail.title')"
      :loading="store.loading"
      back-to="/research/researches"
    />

    <VAlert v-if="store.error" type="error" variant="tonal" class="mb-3">
      {{ store.error }}
    </VAlert>

    <template v-if="store.area">
      <VCard variant="outlined" rounded="lg" class="mb-3">
        <VCardText>
          <div class="area-title">{{ store.area.title }}</div>
          <div v-if="store.area.description" class="area-desc">{{ store.area.description }}</div>
        </VCardText>
      </VCard>

      <VCard
        v-if="store.area.objective || store.area.scope || store.area.expectations"
        variant="outlined"
        rounded="lg"
        class="mb-4 brief-card"
      >
        <VCardText>
          <div v-if="store.area.objective" class="brief-block">
            <div class="brief-label">{{ t('research.area.detail.objective') }}</div>
            <div class="brief-text">{{ store.area.objective }}</div>
          </div>
          <div v-if="store.area.scope" class="brief-block">
            <div class="brief-label">{{ t('research.area.detail.scope') }}</div>
            <div class="brief-text">{{ store.area.scope }}</div>
          </div>
          <div v-if="store.area.expectations" class="brief-block">
            <div class="brief-label">{{ t('research.area.detail.expectations') }}</div>
            <div class="brief-text">{{ store.area.expectations }}</div>
          </div>
        </VCardText>
      </VCard>

      <h2 class="section-title">{{ t('research.area.detail.body') }}</h2>
      <VCard variant="outlined" rounded="lg" class="mb-4">
        <VCardText>
          <ResearchBody v-if="store.area.body" :text="store.area.body" />
          <div v-else class="empty text-medium-emphasis">
            {{ t('research.area.detail.no_body') }}
          </div>
        </VCardText>
      </VCard>

      <h2 class="section-title">
        {{ t('research.area.detail.queries') }}
        <span class="count">{{ store.queries.length }}</span>
      </h2>
      <VCard v-if="store.queries.length" variant="outlined" rounded="lg" class="mb-4">
        <VList class="row-list">
          <template v-for="(q, i) in store.queries" :key="q.code">
            <VDivider v-if="i > 0" />
            <VListItem class="row-item" @click="go(`/research/queries/${q.code}`)">
              <VListItemTitle class="row-title">{{ q.query }}</VListItemTitle>
              <template #append><IconChevronRight :size="18" class="row-chevron" /></template>
            </VListItem>
          </template>
        </VList>
      </VCard>
      <VCard v-else variant="outlined" rounded="lg" class="mb-4">
        <VCardText class="empty text-medium-emphasis">{{ t('research.area.detail.no_queries') }}</VCardText>
      </VCard>

      <h2 class="section-title">{{ t('research.area.detail.documents') }}</h2>
      <DocumentsTable scope="area" :code="store.area.code" />
    </template>
  </PageLayout>
</template>

<style scoped>
.area-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.area-desc {
  margin-top: 6px;
  font-size: 14px;
  color: var(--text-muted);
}

.brief-block + .brief-block {
  margin-top: 14px;
}

.brief-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-faint);
  margin-bottom: 3px;
}

.brief-text {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.55;
  white-space: pre-wrap;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  margin: 4px 0 10px;
}

.section-title .count {
  font-size: 12px;
  color: var(--text-faint);
  font-weight: 500;
}

.row-item {
  cursor: pointer;
  transition: background 0.12s ease;
}

.row-item:hover {
  background: var(--surface-hi);
}

.row-title {
  font-weight: 500;
}

.row-chevron {
  color: var(--text-faint);
  flex: none;
  transition: color 0.12s ease, transform 0.12s ease;
}

.row-item:hover .row-chevron {
  color: rgb(var(--v-theme-primary));
  transform: translateX(2px);
}

.empty {
  padding: 16px 0;
  text-align: center;
}
</style>
