<script setup lang="ts">
import { onActivated, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconExternalLink } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

import { useSourceDetailStore } from '../stores/source-detail.store'
import { SOURCE_STATUS_COLOR } from '../labels'

const { t } = useI18n()
const route = useRoute()
const store = useSourceDetailStore()

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
      :title="t('research.source.detail.title')"
      :loading="store.loading"
      back-to="/research/researches"
    />

    <VAlert v-if="store.error" type="error" variant="tonal" class="mb-3">
      {{ store.error }}
    </VAlert>

    <template v-if="store.source">
      <VCard variant="outlined" rounded="lg" class="mb-3">
        <VCardText>
          <div class="src-title">{{ store.source.title || store.source.url }}</div>
          <div v-if="store.source.url" class="src-url">{{ store.source.url }}</div>

          <div class="meta-row">
            <StatusBadge :color="SOURCE_STATUS_COLOR[store.source.status]">
              {{ t(`research.source.status.${store.source.status}`) }}
            </StatusBadge>
            <span v-if="store.source.relevance != null" class="meta-item">
              {{ t('research.source.detail.relevance') }}:
              <span class="relevance">{{ store.source.relevance }}</span>
            </span>
            <VBtn
              v-if="store.source.url"
              :href="store.source.url"
              target="_blank"
              rel="noopener noreferrer"
              size="small"
              variant="tonal"
            >
              {{ t('research.source.detail.open_source') }}
              <IconExternalLink :size="15" class="ms-1" />
            </VBtn>
          </div>

          <div v-if="store.source.summary" class="src-summary">{{ store.source.summary }}</div>
          <div v-if="store.source.note" class="src-note">
            {{ t('research.source.detail.note') }}: {{ store.source.note }}
          </div>
        </VCardText>
      </VCard>

      <VCard variant="outlined" rounded="lg">
        <VCardText>
          <MarkdownRenderer v-if="store.source.body" :text="store.source.body" />
          <div v-else class="no-content text-medium-emphasis">
            {{ t('research.source.detail.no_body') }}
          </div>
        </VCardText>
      </VCard>
    </template>
  </PageLayout>
</template>

<style scoped>
.src-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.src-url {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-faint);
  word-break: break-all;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
}

.meta-item {
  font-size: 13px;
  color: var(--text-muted);
  white-space: nowrap;
}

.relevance {
  font-family: var(--font-mono);
  color: var(--text-faint);
}

.src-summary {
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}

.src-note {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
}

.no-content {
  padding: 24px 0;
  text-align: center;
}
</style>
