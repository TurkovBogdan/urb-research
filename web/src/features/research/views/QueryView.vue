<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { IconExternalLink } from '@tabler/icons-vue'

import DetailHead from '@/layout/components/DetailHead.vue'
import { useDetailRail } from '@/layout/detailRail'
import SectionError from '@/components/SectionError.vue'
import SectionHeader from '@/components/SectionHeader.vue'
import StatusBadge from '@/components/StatusBadge.vue'

import { useQueryDetailStore } from '../stores/query-detail.store'
import { useDetailReload } from '../useDetailReload'
import { SOURCE_STATUS_COLOR } from '../labels'

const { t } = useI18n()
const router = useRouter()
const store = useQueryDetailStore()
const { reload } = useDetailReload(store.load)

// Поиск принадлежит зоне: на уровень выше — она. Выше зоны лежит исследование, но туда ведёт уже
// её собственная кнопка — путь наверх проходится по одному уровню за нажатие.
const parentPath = computed(() =>
  store.query ? `/research/areas/${store.query.area_code}` : '/research/researches',
)

const parentLabel = computed(() =>
  store.query ? t('research.back.area') : t('research.back.researches'),
)

function openSource(code: string) {
  router.push(`/research/sources/${code}`)
}

// Колонку рисует общая рамка деталок — страница её только заполняет. Ни поиска, ни оглавления
// у поиска нет: на странице один раздел, и искать в списке ссылок нечего.
useDetailRail(() => ({
  parent: parentPath.value,
  label: parentLabel.value,
}))
</script>

<template>
  <div>
    <SectionError v-if="store.error" :error="store.error" />

    <template v-if="store.query">
      <!-- Имя поиска — сам запрос: другого у него нет, и в карточке он читался бы вложением,
           а не заголовком страницы. -->
      <DetailHead :code="store.query.code" :loading="store.loading" @refresh="reload">
        <h1 class="query-text">{{ store.query.query }}</h1>
      </DetailHead>

      <SectionHeader :title="t('research.query.detail.sources')" :count="store.documents.length" />

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
  </div>
</template>

<style scoped>
.query-text {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.3;
  text-wrap: pretty;
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
