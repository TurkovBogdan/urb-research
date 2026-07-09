<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { fmtDateTime } from '@/shared/utils/date'

import { useQueryDetailStore } from '../stores/query-detail.store'
import { PAGE_STATUS_COLOR, QUERY_STATUS_COLOR } from '../labels'
import type { PageStatus, QueryResultView } from '../api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useQueryDetailStore()

function resultTitle(r: QueryResultView): string {
  return r.page_title ? r.page_title : r.page_url
}

function resultSnippet(r: QueryResultView): string | null {
  return r.summary ? r.summary : null
}

const paramsText = computed(() => {
  const params = store.query?.params
  return params && Object.keys(params).length ? JSON.stringify(params, null, 2) : null
})

function openPage(code: string) {
  router.push(`/web-search/pages/${encodeURIComponent(code)}`)
}

watch(
  () => route.params.code,
  (code) => {
    if (typeof code === 'string' && code) store.load(code)
  },
  { immediate: true },
)
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('web_search.query.detail.title')"
      :loading="store.loading"
      back-to="/web-search/queries"
    />

    <VAlert v-if="store.error" type="error" variant="tonal" class="mb-3">
      {{ store.error }}
    </VAlert>

    <template v-if="store.query">
      <VCard variant="outlined" rounded="lg" class="mb-3">
        <VCardText>
          <div class="request-text">{{ store.query.query }}</div>
          <div class="meta-row">
            <StatusBadge :color="QUERY_STATUS_COLOR[store.query.status]">
              {{ t(`web_search.query.status.${store.query.status}`) }}
            </StatusBadge>
            <span class="meta-item">{{ t('web_search.query.field.search_engine') }}: <b>{{ store.query.search_engine }}</b></span>
            <span class="meta-item">{{ t('web_search.query.field.fetch_engine') }}: <b>{{ store.query.fetch_engine }}</b></span>
            <span class="meta-item">{{ t('web_search.query.field.created_at') }}: {{ fmtDateTime(store.query.created_at) }}</span>
            <span v-if="store.query.finished_at" class="meta-item">
              {{ t('web_search.query.field.finished_at') }}: {{ fmtDateTime(store.query.finished_at) }}
            </span>
          </div>
          <pre v-if="paramsText" class="params">{{ paramsText }}</pre>
        </VCardText>
      </VCard>

      <h2 class="section-title">
        {{ t('web_search.query.detail.results') }}
        <span class="count">{{ store.results.length }}</span>
      </h2>

      <VCard v-if="store.results.length" variant="outlined" rounded="lg">
        <VList lines="two" class="result-list">
          <template v-for="(r, i) in store.results" :key="r.page_code">
            <VDivider v-if="i > 0" />
            <VListItem class="result-item" @click="openPage(r.page_code)">
              <template #prepend>
                <span class="rank">{{ r.rank ?? i + 1 }}</span>
              </template>
              <VListItemTitle class="result-title">{{ resultTitle(r) }}</VListItemTitle>
              <VListItemSubtitle class="result-url">{{ r.page_url }}</VListItemSubtitle>
              <div v-if="resultSnippet(r)" class="result-snippet">{{ resultSnippet(r) }}</div>
              <template #append>
                <div class="result-append">
                  <StatusBadge :color="PAGE_STATUS_COLOR[r.page_status as PageStatus]">
                    {{ t(`web_search.page.status.${r.page_status}`) }}
                  </StatusBadge>
                  <span v-if="r.score != null" class="score">{{ r.score.toFixed(2) }}</span>
                </div>
              </template>
            </VListItem>
          </template>
        </VList>
      </VCard>

      <VCard v-else variant="outlined" rounded="lg">
        <VCardText class="text-medium-emphasis">{{ t('web_search.query.detail.no_results') }}</VCardText>
      </VCard>
    </template>
  </PageLayout>
</template>

<style scoped>
.request-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.meta-item {
  font-size: 13px;
  color: var(--text-muted);
  white-space: nowrap;
}

.params {
  margin-top: 14px;
  padding: 10px 12px;
  background: var(--surface-hi);
  border: 1px solid var(--border-soft);
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
  overflow-x: auto;
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

.result-item {
  cursor: pointer;
}

.rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--surface-hi);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  margin-right: 6px;
}

.result-title {
  font-weight: 500;
}

.result-url {
  color: var(--accent);
  font-size: 12px;
}

.result-snippet {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-append {
  display: flex;
  align-items: center;
  gap: 10px;
}

.score {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-faint);
}
</style>
