<script setup lang="ts">
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconExternalLink } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import { fmtDateTime } from '@/shared/utils/date'

import { usePageDetailStore } from '../stores/page-detail.store'
import { PAGE_STATUS_COLOR } from '../labels'

const { t } = useI18n()
const route = useRoute()
const store = usePageDetailStore()

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
      :title="t('web_search.page.detail.title')"
      :loading="store.loading"
      back-to="/web-search/pages"
    />

    <VAlert v-if="store.error" type="error" variant="tonal" class="mb-3">
      {{ store.error }}
    </VAlert>

    <template v-if="store.page">
      <VCard variant="outlined" rounded="lg" class="mb-3">
        <VCardText>
          <div v-if="store.page.title" class="page-title">{{ store.page.title }}</div>
          <div class="url-row">
            <a :href="store.page.url" target="_blank" rel="noopener noreferrer" class="url-link">
              {{ store.page.url }}
              <IconExternalLink :size="14" />
            </a>
          </div>
          <div class="meta-row">
            <StatusBadge :color="PAGE_STATUS_COLOR[store.page.status]">
              {{ t(`web_search.page.status.${store.page.status}`) }}
            </StatusBadge>
            <span v-if="store.page.domain" class="meta-item">{{ store.page.domain }}</span>
            <span v-if="store.page.fetched_at" class="meta-item">
              {{ t('web_search.page.field.fetched_at') }}: {{ fmtDateTime(store.page.fetched_at) }}
            </span>
            <span v-if="store.page.error" class="meta-item meta-item--error">
              {{ store.page.error }}
            </span>
          </div>
        </VCardText>
      </VCard>

      <VCard variant="outlined" rounded="lg">
        <VCardText>
          <MarkdownRenderer v-if="store.page.body" :text="store.page.body" />
          <div v-else class="no-content text-medium-emphasis">
            {{ t('web_search.page.detail.no_content') }}
          </div>
        </VCardText>
      </VCard>
    </template>
  </PageLayout>
</template>

<style scoped>
.page-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.url-row {
  margin-bottom: 12px;
}

.url-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--accent);
  word-break: break-all;
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

.meta-item--error {
  color: var(--error);
}

.no-content {
  padding: 24px 0;
  text-align: center;
}
</style>
