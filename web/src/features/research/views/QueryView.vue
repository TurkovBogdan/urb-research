<script setup lang="ts">
import { onActivated, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconExternalLink } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'

import { useQueryDetailStore } from '../stores/query-detail.store'
import { SOURCE_STATUS_COLOR } from '../labels'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useQueryDetailStore()

function openSource(code: string) {
  router.push(`/research/sources/${code}`)
}

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
      :title="t('research.query.detail.title')"
      :loading="store.loading"
      back-to="/research/researches"
    />

    <VAlert v-if="store.error" type="error" variant="tonal" class="mb-3">
      {{ store.error }}
    </VAlert>

    <template v-if="store.query">
      <VCard variant="outlined" rounded="lg" class="mb-4">
        <VCardText>
          <div class="query-text">{{ store.query.query }}</div>
        </VCardText>
      </VCard>

      <h2 class="section-title">
        {{ t('research.query.detail.sources') }}
        <span class="count">{{ store.documents.length }}</span>
      </h2>

      <VCard v-if="store.documents.length" variant="outlined" rounded="lg">
        <VList lines="two" class="doc-list">
          <template v-for="(d, i) in store.documents" :key="d.code">
            <VDivider v-if="i > 0" />
            <VListItem
              class="doc-item"
              :class="{ 'doc-item--dim': d.status !== 'kept' }"
              @click="openSource(d.code)"
            >
              <VListItemTitle class="doc-title">{{ d.title || d.url }}</VListItemTitle>
              <VListItemSubtitle class="doc-url">{{ d.url }}</VListItemSubtitle>
              <div v-if="d.summary" class="doc-summary">{{ d.summary }}</div>
              <template #append>
                <div class="doc-append">
                  <StatusBadge :color="SOURCE_STATUS_COLOR[d.status]">
                    {{ t(`research.source.status.${d.status}`) }}
                  </StatusBadge>
                  <span v-if="d.relevance != null" class="relevance">{{ d.relevance }}</span>
                  <VBtn
                    v-if="d.url"
                    :href="d.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    icon
                    variant="text"
                    size="small"
                    :title="t('research.source.detail.open_source')"
                    @click.stop
                  >
                    <IconExternalLink :size="16" />
                  </VBtn>
                </div>
              </template>
            </VListItem>
          </template>
        </VList>
      </VCard>

      <VCard v-else variant="outlined" rounded="lg">
        <VCardText class="empty text-medium-emphasis">
          {{ t('research.query.detail.no_sources') }}
        </VCardText>
      </VCard>
    </template>
  </PageLayout>
</template>

<style scoped>
.query-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
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

.doc-item {
  cursor: pointer;
  transition: background 0.12s ease;
}

.doc-item:hover {
  background: var(--surface-hi);
}

.doc-item--dim {
  opacity: 0.65;
}

.doc-title {
  font-weight: 500;
}

.doc-url {
  color: var(--text-faint);
  font-size: 12px;
  word-break: break-all;
}

.doc-summary {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
}

.doc-append {
  display: flex;
  align-items: center;
  gap: 10px;
  align-self: center;
}

.relevance {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-faint);
}

.empty {
  padding: 16px 0;
  text-align: center;
}
</style>
