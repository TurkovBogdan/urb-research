<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconArrowLeft, IconArrowRight } from '@tabler/icons-vue'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import TablePaginationBar from '@/components/TablePaginationBar.vue'
import CodeBlock from '@/components/CodeBlock.vue'

const pageBasic = ref(3)
const pageDense = ref(1)
const pageLong = ref(7)
const pageRounded = ref(2)
const pageDisabled = ref(1)

const pageWithSize = ref(1)
const pageSize = ref(20)
const pageSizes = [10, 20, 50, 100]
const totalItems = 237
const pageCount = () => Math.max(1, Math.ceil(totalItems / pageSize.value))

const pageIcons = ref(2)

// TablePaginationBar — the standardized footer component. Drive its page/size
// from local state so the demo is fully interactive.
const barPage = ref(1)
const barSize = ref(50)
const barTotal = 1089
const barPageCount = () => Math.max(1, Math.ceil(barTotal / barSize.value))
function onBarSize(size: number) { barSize.value = size; barPage.value = 1 }

const usageSnippet = `<TablePaginationBar
  :page="store.page"
  :page-size="store.pageSize"
  :total="store.total"
  :page-count="store.pageCount"
  @update:page="onPageChange"
  @update:page-size="onPageSizeChange"
/>`

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.pagination.title')" :description="t('design-system.page.pagination.description')" back-to="/design-system" />

    <!-- Basic -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.pagination.basic') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <VPagination v-model="pageBasic" :length="7" :total-visible="5" />
          </div>
          <span class="ds-spec">:length="7" · :total-visible="5"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">long</span>
          <div class="ds-controls">
            <VPagination v-model="pageLong" :length="50" :total-visible="7" />
          </div>
          <span class="ds-spec">:length="50" · ellipsis</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">short</span>
          <div class="ds-controls">
            <VPagination v-model="pageBasic" :length="3" />
          </div>
          <span class="ds-spec">:length="3" — no ellipsis</span>
        </div>

      </div>
    </section>

    <!-- Density -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.pagination.density') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">compact</span>
          <div class="ds-controls">
            <VPagination v-model="pageDense" :length="10" :total-visible="5" density="compact" />
          </div>
          <span class="ds-spec">density="compact"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">comfortable</span>
          <div class="ds-controls">
            <VPagination v-model="pageDense" :length="10" :total-visible="5" density="comfortable" />
          </div>
          <span class="ds-spec">density="comfortable" — recommended</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">default</span>
          <div class="ds-controls">
            <VPagination v-model="pageDense" :length="10" :total-visible="5" density="default" />
          </div>
          <span class="ds-spec">density="default"</span>
        </div>

      </div>
    </section>

    <!-- Shape -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.pagination.shape') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">circle</span>
          <div class="ds-controls">
            <VPagination v-model="pageRounded" :length="7" :total-visible="5" rounded="circle" />
          </div>
          <span class="ds-spec">rounded="circle"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">rounded</span>
          <div class="ds-controls">
            <VPagination v-model="pageRounded" :length="7" :total-visible="5" rounded />
          </div>
          <span class="ds-spec">rounded</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">square</span>
          <div class="ds-controls">
            <VPagination v-model="pageRounded" :length="7" :total-visible="5" rounded="0" />
          </div>
          <span class="ds-spec">rounded="0"</span>
        </div>

      </div>
    </section>

    <!-- Arrow icons -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.pagination.arrowIcons') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">first/last</span>
          <div class="ds-controls">
            <VPagination
              v-model="pageIcons"
              :length="20"
              :total-visible="5"
              show-first-last-page
            />
          </div>
          <span class="ds-spec">show-first-last-page</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">custom</span>
          <div class="ds-controls">
            <VPagination
              v-model="pageIcons"
              :length="20"
              :total-visible="5"
              :prev-icon="IconArrowLeft"
              :next-icon="IconArrowRight"
            />
          </div>
          <span class="ds-spec">:prev-icon / :next-icon (Tabler)</span>
        </div>

      </div>
    </section>

    <!-- States -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.pagination.states') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">disabled</span>
          <div class="ds-controls">
            <VPagination v-model="pageDisabled" :length="7" :total-visible="5" disabled />
          </div>
          <span class="ds-spec">disabled</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">length=1</span>
          <div class="ds-controls">
            <VPagination v-model="pageDisabled" :length="1" />
          </div>
          <span class="ds-spec">single page</span>
        </div>

      </div>
    </section>

    <!-- Real-world scenario -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.pagination.pageSize') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">table</span>
          <div class="ds-controls ds-controls--pager">
            <span class="ds-meta">
              {{ (pageWithSize - 1) * pageSize + 1 }}–{{ Math.min(pageWithSize * pageSize, totalItems) }}
              of {{ totalItems }}
            </span>
            <VSpacer />
            <VSelect
              v-model="pageSize"
              :items="pageSizes"
              label="Per page"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 130px"
            />
            <VPagination
              v-model="pageWithSize"
              :length="pageCount()"
              :total-visible="5"
              density="comfortable"
            />
          </div>
          <span class="ds-spec">table bottom-bar pattern</span>
        </div>

      </div>
    </section>

    <!-- Standardized component -->
    <section class="ds-section">
      <h6 class="mb-1">{{ t('design-system.section.pagination.component') }}</h6>
      <p class="ds-note">{{ t('design-system.section.pagination.componentNote') }}</p>

      <VCard variant="outlined" rounded="lg" class="ds-bar-host">
        <div class="ds-bar-table">VDataTable …</div>
        <TablePaginationBar
          :page="barPage"
          :page-size="barSize"
          :total="barTotal"
          :page-count="barPageCount()"
          @update:page="barPage = $event"
          @update:page-size="onBarSize"
        />
      </VCard>

      <CodeBlock :code="usageSnippet" lang="vue" class="mt-3" />
    </section>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 1100px; }
.ds-section { margin-bottom: 28px; }

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 100px 1fr 220px;
  align-items: start;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
  &:last-child { border-bottom: none; }
  &.ds-row--center { align-items: center; }
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
  gap: 8px;
}

.ds-controls--pager {
  width: 100%;
  gap: 12px;
}

.ds-meta {
  font-size: 12px;
  color: var(--text-faint);
}

.ds-note {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 12px;
  max-width: 720px;
}

.ds-bar-host {
  overflow: hidden;
}

.ds-bar-table {
  padding: 24px 16px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-faint);
  text-align: center;
}
</style>
