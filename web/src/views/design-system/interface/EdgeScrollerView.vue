<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import EdgeScroller from '@/layout/components/EdgeScroller.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Demo data — a wide table (nowrap cells) to force horizontal scroll, the same
// EdgeScroller that powers the kanban board, here wrapping a <table>.
const headers = ['Module', 'Owner', 'Status', 'Version', 'Migrations', 'Tests', 'Coverage', 'Last run', 'MCP server', 'Routes', 'RSS (MB)', 'Notes']
const rows = [
  ['core_users', 'BT', 'active', '1.4.0', 'cu03', 208, '98%', '2026-06-07 09:12', '—', 11, 132, 'auth + sessions + tokens'],
  ['conversation_insights', 'AK', 'active', '0.17.2', 'ci08', 122, '95%', '2026-06-07 08:41', 'scm-conversation-insights', 14, 141, 'tagging axes redesign'],
  ['conversations', 'BT', 'active', '2.1.0', 'c11', 161, '93%', '2026-06-06 22:03', 'scm-conversations', 9, 138, 'chunked rebuild'],
  ['intercom', 'MS', 'active', '1.0.3', 'i06', 95, '90%', '2026-06-06 19:55', '—', 7, 140, 'HTTP-bound full import'],
  ['mail_sync', 'MS', 'active', '0.9.1', '—', 88, '91%', '2026-06-06 18:20', 'mail-sync', 6, 139, 'ThreadBuilder rebuild'],
  ['twenty', 'BT', 'beta', '0.4.0', '—', 41, '84%', '2026-06-05 14:10', '—', 5, 136, 'companies + people only'],
  ['llm_providers', 'AK', 'active', '3.4.1', 'l1m0', 352, '96%', '2026-06-07 07:30', 'llm-providers', 13, 145, 'MCP client + registry'],
  ['core_geo', 'MS', 'active', '0.8.0', 'cg02', 36, '89%', '2026-06-04 11:48', '—', 3, 134, 'timezones pending'],
]
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader :title="t('design-system.page.edge-scroller.title')" :description="t('design-system.page.edge-scroller.description')" back-to="/design-system" />

      <section class="ds-section">
        <h6 class="mb-1">{{ t('design-system.section.edge-scroller.title') }}</h6>
        <p class="ds-note">{{ t('design-system.section.edge-scroller.note') }}</p>

        <EdgeScroller bleed>
          <table class="demo-table">
            <thead>
              <tr>
                <th v-for="h in headers" :key="h">{{ h }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in rows" :key="ri">
                <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
              </tr>
            </tbody>
          </table>
        </EdgeScroller>
      </section>
    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 100%; }
.ds-section { margin-bottom: 28px; }

.ds-note {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--text-faint);
  max-width: 720px;
}

.demo-table {
  border-collapse: collapse;
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.demo-table th,
.demo-table td {
  white-space: nowrap;
  text-align: left;
  padding: 10px 16px;
  font-size: 13px;
  border-bottom: 1px solid var(--border-soft);
}

.demo-table th {
  font-weight: 600;
  color: var(--text-faint);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: var(--surface-hi);
}

.demo-table tbody tr:last-child td {
  border-bottom: none;
}

.demo-table td {
  color: var(--text);
}
</style>
