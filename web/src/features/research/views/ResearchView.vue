<script setup lang="ts">
import { onActivated, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { IconChevronRight } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import { fmtDateTime } from '@/shared/utils/date'

import ResearchBody from '../components/ResearchBody.vue'
import DocumentsTable from '../components/DocumentsTable.vue'
import { useResearchDetailStore } from '../stores/research-detail.store'
import { NOTE_KIND_COLOR } from '../labels'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useResearchDetailStore()

const go = (path: string) => router.push(path)

// KeepAlive wraps all routed views (App.vue), so reload on every activation, and on an
// in-place param change while active — otherwise a cached instance shows stale data.
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
      :title="t('research.research.detail.title')"
      :loading="store.loading"
      back-to="/research/researches"
    />

    <VAlert v-if="store.error" type="error" variant="tonal" class="mb-3">
      {{ store.error }}
    </VAlert>

    <template v-if="store.research">
      <VCard variant="outlined" rounded="lg" class="mb-3">
        <VCardText>
          <div class="topic-text">{{ store.research.title }}</div>
          <div v-if="store.research.description" class="desc-text">
            {{ store.research.description }}
          </div>
          <div class="meta-row">
            <span class="meta-item">
              {{ t('research.field.updated_at') }}: {{ fmtDateTime(store.research.updated_at) }}
            </span>
          </div>
        </VCardText>
      </VCard>

      <h2 class="section-title">{{ t('research.research.detail.body') }}</h2>
      <VCard variant="outlined" rounded="lg" class="mb-4">
        <VCardText>
          <ResearchBody v-if="store.research.body" :text="store.research.body" />
          <div v-else class="empty text-medium-emphasis">
            {{ t('research.research.detail.no_body') }}
          </div>
        </VCardText>
      </VCard>

      <h2 class="section-title">
        {{ t('research.research.detail.areas') }}
        <span class="count">{{ store.areas.length }}</span>
      </h2>
      <VCard v-if="store.areas.length" variant="outlined" rounded="lg" class="mb-4">
        <VList class="row-list">
          <template v-for="(a, i) in store.areas" :key="a.code">
            <VDivider v-if="i > 0" />
            <VListItem class="row-item" @click="go(`/research/areas/${a.code}`)">
              <VListItemTitle class="row-title">{{ a.title }}</VListItemTitle>
              <VListItemSubtitle v-if="a.description" class="row-sub">
                {{ a.description }}
              </VListItemSubtitle>
              <template #append><IconChevronRight :size="18" class="row-chevron" /></template>
            </VListItem>
          </template>
        </VList>
      </VCard>
      <VCard v-else variant="outlined" rounded="lg" class="mb-4">
        <VCardText class="empty text-medium-emphasis">{{ t('research.research.detail.no_areas') }}</VCardText>
      </VCard>

      <h2 class="section-title">
        {{ t('research.research.detail.queries') }}
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
        <VCardText class="empty text-medium-emphasis">{{ t('research.research.detail.no_queries') }}</VCardText>
      </VCard>

      <h2 class="section-title">{{ t('research.research.detail.documents') }}</h2>
      <div class="mb-4">
        <DocumentsTable scope="research" :code="store.research.code" />
      </div>

      <h2 class="section-title">
        {{ t('research.research.detail.notes') }}
        <span class="count">{{ store.notes.length }}</span>
      </h2>
      <VCard v-if="store.notes.length" variant="outlined" rounded="lg">
        <VList class="row-list">
          <template v-for="(n, i) in store.notes" :key="n.code">
            <VDivider v-if="i > 0" />
            <VListItem class="row-item" @click="go(`/research/notes/${n.code}`)">
              <VListItemTitle class="row-title">{{ n.title }}</VListItemTitle>
              <VListItemSubtitle v-if="n.description" class="row-sub">
                {{ n.description }}
              </VListItemSubtitle>
              <template #append>
                <div class="row-append">
                  <StatusBadge :color="NOTE_KIND_COLOR[n.kind]">
                    {{ t(`research.note.kind.${n.kind}`) }}
                  </StatusBadge>
                  <IconChevronRight :size="18" class="row-chevron" />
                </div>
              </template>
            </VListItem>
          </template>
        </VList>
      </VCard>
      <VCard v-else variant="outlined" rounded="lg">
        <VCardText class="empty text-medium-emphasis">{{ t('research.research.detail.no_notes') }}</VCardText>
      </VCard>
    </template>
  </PageLayout>
</template>

<style scoped>
.topic-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
}

.desc-text {
  font-size: 14px;
  color: var(--text-muted);
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

.row-append {
  display: flex;
  align-items: center;
  gap: 10px;
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

.row-title {
  font-weight: 500;
}

.row-sub {
  color: var(--text-muted);
  font-size: 13px;
}

.empty {
  padding: 16px 0;
  text-align: center;
}
</style>
