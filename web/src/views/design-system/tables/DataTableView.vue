<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

type Status = 'running' | 'success' | 'error'

interface Run {
  id: number
  name: string
  status: Status
  started: string
  duration: string
  error?: string
}

const runs: Run[] = [
  { id: 12, name: 'Collect vacancies', status: 'success', started: '06.05.2026 10:12', duration: '2m 14s' },
  { id: 13, name: 'Parse pages',       status: 'running', started: '06.05.2026 11:00', duration: '—'      },
  { id: 14, name: 'Send responses',    status: 'error',   started: '06.05.2026 09:45', duration: '0m 03s', error: 'Connection timeout' },
  { id: 15, name: 'Update resume',     status: 'success', started: '06.05.2026 08:30', duration: '0m 47s' },
  { id: 16, name: 'Check statuses',    status: 'success', started: '05.05.2026 23:10', duration: '1m 02s' },
]

const STATUS_COLOR: Record<Status, string> = { running: 'info', success: 'success', error: 'error' }

const headers = [
  { title: '#',        key: 'id',       width: 60  },
  { title: 'Task',     key: 'name'               },
  { title: 'Status',   key: 'status',   width: 120 },
  { title: 'Started',  key: 'started'            },
  { title: 'Duration', key: 'duration', width: 140 },
]

const headersWithError = [
  ...headers,
  { title: 'Error', key: 'error' },
]

const page = ref(1)
const pageSize = ref(10)
const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.data-table.title')" :description="t('design-system.page.data-table.description')" back-to="/design-system" />

    <!-- Basic -->
    <section class="ds-section">
      <p class="ds-label">comfortable · hover · hide-default-footer</p>
      <VCard variant="outlined" rounded="lg">
        <VDataTable
          :headers="headers"
          :items="runs"
          :items-per-page="-1"
          density="comfortable"
          hide-default-footer
          hover
        >
          <template #item.id="{ item }">
            <span class="mono">{{ item.id }}</span>
          </template>
          <template #item.status="{ item }">
            <VChip :color="STATUS_COLOR[item.status]" size="small" variant="tonal">
              {{ item.status }}
            </VChip>
          </template>
          <template #item.duration="{ item }">
            <span class="mono">{{ item.duration }}</span>
          </template>
        </VDataTable>
      </VCard>
    </section>

    <!-- Density -->
    <section class="ds-section">
      <p class="ds-label">density</p>
      <div class="two-col">
        <div>
          <p class="ds-sublabel">comfortable</p>
          <VCard variant="outlined" rounded="lg">
            <VDataTable :headers="headers" :items="runs.slice(0, 3)" :items-per-page="-1"
              density="comfortable" hide-default-footer hover>
              <template #item.status="{ item }">
                <VChip :color="STATUS_COLOR[item.status]" size="small" variant="tonal">{{ item.status }}</VChip>
              </template>
            </VDataTable>
          </VCard>
        </div>
        <div>
          <p class="ds-sublabel">compact</p>
          <VCard variant="outlined" rounded="lg">
            <VDataTable :headers="headers" :items="runs.slice(0, 3)" :items-per-page="-1"
              density="compact" hide-default-footer hover>
              <template #item.status="{ item }">
                <VChip :color="STATUS_COLOR[item.status]" size="x-small" variant="tonal">{{ item.status }}</VChip>
              </template>
            </VDataTable>
          </VCard>
        </div>
      </div>
    </section>

    <!-- States -->
    <section class="ds-section">
      <p class="ds-label">states</p>
      <div class="two-col">
        <div>
          <p class="ds-sublabel">loading</p>
          <VCard variant="outlined" rounded="lg">
            <VDataTable :headers="headers" :items="[]" :items-per-page="-1"
              density="comfortable" hide-default-footer :loading="true" />
          </VCard>
        </div>
        <div>
          <p class="ds-sublabel">empty</p>
          <VCard variant="outlined" rounded="lg">
            <VDataTable :headers="headers" :items="[]" :items-per-page="-1"
              density="comfortable" hide-default-footer no-data-text="No data" />
          </VCard>
        </div>
      </div>
    </section>

    <!-- Custom cells -->
    <section class="ds-section">
      <p class="ds-label">custom slots — chips, mono, error text</p>
      <VCard variant="outlined" rounded="lg">
        <VDataTable
          :headers="headersWithError"
          :items="runs"
          :items-per-page="-1"
          density="comfortable"
          hide-default-footer
          hover
        >
          <template #item.id="{ item }">
            <span class="mono">{{ item.id }}</span>
          </template>
          <template #item.status="{ item }">
            <VChip :color="STATUS_COLOR[item.status]" size="small" variant="tonal">
              {{ item.status }}
            </VChip>
          </template>
          <template #item.duration="{ item }">
            <span class="mono">{{ item.duration }}</span>
          </template>
          <template #item.error="{ item }">
            <span class="text-error text-caption">{{ item.error ?? '' }}</span>
          </template>
        </VDataTable>
      </VCard>
    </section>

    <!-- Pagination -->
    <section class="ds-section">
      <p class="ds-label">with pagination — VPagination + page size select in a single bar</p>
      <VCard variant="outlined" rounded="lg">
        <VDataTable
          :headers="headers"
          :items="runs"
          :items-per-page="-1"
          density="comfortable"
          hide-default-footer
          hover
        >
          <template #item.id="{ item }">
            <span class="mono">{{ item.id }}</span>
          </template>
          <template #item.status="{ item }">
            <VChip :color="STATUS_COLOR[item.status]" size="small" variant="tonal">
              {{ item.status }}
            </VChip>
          </template>
          <template #item.duration="{ item }">
            <span class="mono">{{ item.duration }}</span>
          </template>
        </VDataTable>
        <VDivider />
        <div class="pagination-bar">
          <span class="mono" style="font-size: 11px; color: var(--text-faint)">1–5 of 5</span>
          <VSpacer />
          <VSelect
            v-model="pageSize"
            :items="[10, 25, 50]"
            label="Per page"
            density="compact"
            variant="outlined"
            hide-details
            style="max-width: 130px"
          />
          <VPagination v-model="page" :length="3" :total-visible="5" density="comfortable" />
        </div>
      </VCard>
    </section>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 960px; }
.ds-section { margin-bottom: 32px; }

.ds-label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  margin-bottom: 8px;
}

.ds-sublabel {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-faint);
  margin-bottom: 6px;
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.pagination-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
}

.mono {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}
</style>
