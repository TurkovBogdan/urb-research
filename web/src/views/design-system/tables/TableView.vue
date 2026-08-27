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

const page = ref(1)
const pageSize = ref(10)
const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.table.title')" :description="t('design-system.page.table.description')" back-to="/design-system" />

    <!-- Basic -->
    <section class="ds-section">
      <p class="ds-label">comfortable · hover — native thead/tbody markup</p>
      <VCard variant="outlined" rounded="lg">
        <VTable density="comfortable" hover>
          <thead>
            <tr>
              <th style="width: 60px">#</th>
              <th>Task</th>
              <th style="width: 120px">Status</th>
              <th>Started</th>
              <th style="width: 140px">Duration</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in runs" :key="run.id">
              <td><span class="mono">{{ run.id }}</span></td>
              <td>{{ run.name }}</td>
              <td>
                <VChip :color="STATUS_COLOR[run.status]" size="small" variant="tonal">{{ run.status }}</VChip>
              </td>
              <td>{{ run.started }}</td>
              <td><span class="mono">{{ run.duration }}</span></td>
            </tr>
          </tbody>
        </VTable>
      </VCard>
    </section>

    <!-- Density -->
    <section class="ds-section">
      <p class="ds-label">density</p>
      <div class="two-col">
        <div>
          <p class="ds-sublabel">comfortable</p>
          <VCard variant="outlined" rounded="lg">
            <VTable density="comfortable" hover>
              <thead>
                <tr><th style="width: 60px">#</th><th>Task</th><th style="width: 120px">Status</th></tr>
              </thead>
              <tbody>
                <tr v-for="run in runs.slice(0, 3)" :key="run.id">
                  <td><span class="mono">{{ run.id }}</span></td>
                  <td>{{ run.name }}</td>
                  <td><VChip :color="STATUS_COLOR[run.status]" size="small" variant="tonal">{{ run.status }}</VChip></td>
                </tr>
              </tbody>
            </VTable>
          </VCard>
        </div>
        <div>
          <p class="ds-sublabel">compact</p>
          <VCard variant="outlined" rounded="lg">
            <VTable density="compact" hover>
              <thead>
                <tr><th style="width: 60px">#</th><th>Task</th><th style="width: 120px">Status</th></tr>
              </thead>
              <tbody>
                <tr v-for="run in runs.slice(0, 3)" :key="run.id">
                  <td><span class="mono">{{ run.id }}</span></td>
                  <td>{{ run.name }}</td>
                  <td><VChip :color="STATUS_COLOR[run.status]" size="x-small" variant="tonal">{{ run.status }}</VChip></td>
                </tr>
              </tbody>
            </VTable>
          </VCard>
        </div>
      </div>
    </section>

    <!-- States -->
    <section class="ds-section">
      <p class="ds-label">states — loading / empty composed by hand (no built-in props)</p>
      <div class="two-col">
        <div>
          <p class="ds-sublabel">loading</p>
          <VCard variant="outlined" rounded="lg">
            <VTable density="comfortable">
              <thead>
                <tr><th style="width: 60px">#</th><th>Task</th><th style="width: 120px">Status</th></tr>
              </thead>
            </VTable>
            <VProgressLinear indeterminate />
          </VCard>
        </div>
        <div>
          <p class="ds-sublabel">empty</p>
          <VCard variant="outlined" rounded="lg">
            <VTable density="comfortable">
              <thead>
                <tr><th style="width: 60px">#</th><th>Task</th><th style="width: 120px">Status</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td colspan="3" class="text-center text-medium-emphasis py-4">No data</td>
                </tr>
              </tbody>
            </VTable>
          </VCard>
        </div>
      </div>
    </section>

    <!-- Custom cells -->
    <section class="ds-section">
      <p class="ds-label">custom cells — chips, mono, error text</p>
      <VCard variant="outlined" rounded="lg">
        <VTable density="comfortable" hover>
          <thead>
            <tr>
              <th style="width: 60px">#</th>
              <th>Task</th>
              <th style="width: 120px">Status</th>
              <th>Started</th>
              <th style="width: 140px">Duration</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in runs" :key="run.id">
              <td><span class="mono">{{ run.id }}</span></td>
              <td>{{ run.name }}</td>
              <td><VChip :color="STATUS_COLOR[run.status]" size="small" variant="tonal">{{ run.status }}</VChip></td>
              <td>{{ run.started }}</td>
              <td><span class="mono">{{ run.duration }}</span></td>
              <td><span class="text-error text-caption">{{ run.error ?? '' }}</span></td>
            </tr>
          </tbody>
        </VTable>
      </VCard>
    </section>

    <!-- Pagination -->
    <section class="ds-section">
      <p class="ds-label">with pagination — VPagination + page size select in a single bar</p>
      <VCard variant="outlined" rounded="lg">
        <VTable density="comfortable" hover>
          <thead>
            <tr>
              <th style="width: 60px">#</th>
              <th>Task</th>
              <th style="width: 120px">Status</th>
              <th>Started</th>
              <th style="width: 140px">Duration</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in runs" :key="run.id">
              <td><span class="mono">{{ run.id }}</span></td>
              <td>{{ run.name }}</td>
              <td><VChip :color="STATUS_COLOR[run.status]" size="small" variant="tonal">{{ run.status }}</VChip></td>
              <td>{{ run.started }}</td>
              <td><span class="mono">{{ run.duration }}</span></td>
            </tr>
          </tbody>
        </VTable>
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
