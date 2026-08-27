<script setup lang="ts">
import { onActivated, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconChevronRight } from '@tabler/icons-vue'

import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import SectionError from '@/components/SectionError.vue'
import SectionHeader from '@/components/SectionHeader.vue'

import ResearchBody from '../components/ResearchBody.vue'
import DocumentsTable from '../components/DocumentsTable.vue'
import TitleEditor from '../components/TitleEditor.vue'
import { useAreaDetailStore } from '../stores/area-detail.store'
import { useSourcesRefetch } from '../useSourcesRefetch'
import { refetchAreaDocuments } from '../api'

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

// Повтор получения материала: ручка уровня зоны чинит источники её поисков.
const { refetchingAll, refetchingCode, refetchAllSources, refetchOneSource } = useSourcesRefetch(
  () => refetchAreaDocuments(store.area?.code ?? ''),
  reload,
)
</script>

<template>
  <PageLayout>
    <PageHeader
      :title="t('research.area.detail.title')"
      :loading="store.loading"
      back-to="/research/researches"
    />

    <SectionError v-if="store.error" :error="store.error" />

    <template v-if="store.area">
      <VCard variant="outlined" rounded="lg" class="mb-3">
        <VCardText>
          <TitleEditor
            class="area-title"
            :title="store.area.title"
            :label="t('research.area.detail.title_label')"
            :saving="store.renaming"
            @save="store.rename"
          />
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

      <SectionHeader :title="t('research.area.detail.body')" />
      <VCard variant="outlined" rounded="lg" class="mb-4">
        <VCardText>
          <ResearchBody v-if="store.area.body" :text="store.area.body" />
          <div v-else class="empty text-medium-emphasis">
            {{ t('research.area.detail.no_body') }}
          </div>
        </VCardText>
      </VCard>

      <SectionHeader :title="t('research.area.detail.queries')" :count="store.queries.length" />
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

      <SectionHeader :title="t('research.area.detail.documents')" />
      <DocumentsTable
        :items="store.sources"
        :loading="store.loading"
        :refetching-all="refetchingAll"
        :refetching-code="refetchingCode"
        @refetch-all="refetchAllSources"
        @refetch-one="refetchOneSource"
      />
    </template>
  </PageLayout>
</template>

<style scoped>
/* Кегль строки редактора задаётся его же токенами: подменять `font-size` снаружи нельзя —
   на нём держится равная высота покоя и правки. */
.area-title {
  --ile-size: 16px;
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
