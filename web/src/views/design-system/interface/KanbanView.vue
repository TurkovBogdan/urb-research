<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import KanbanBoard from '@/components/kanban/KanbanBoard.vue'
import KanbanColumn from '@/components/kanban/KanbanColumn.vue'
import KanbanCard, { type KanbanTag } from '@/components/kanban/KanbanCard.vue'
import { IconPlus } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Demo data — a task pipeline board. Static literals (design showcase, not wired to a store).
type Card = {
  id: string
  title: string
  tags: KanbanTag[]
  /** Optional body — rendered as paragraphs in the card's default slot. */
  body?: string[]
  comments?: number
  attachments?: number
  assignee: string
}
type Column = { id: string; title: string; tone: string; cards: Card[] }

const columns: Column[] = [
  {
    id: 'backlog',
    title: 'Backlog',
    tone: 'var(--text-faint)',
    cards: [
      { id: 'b1', title: 'Audit llm_providers dead code paths', tags: [{ label: 'audit' }], comments: 2, assignee: 'BT' },
      { id: 'b2', title: 'Per-server MCP admin-only gating', tags: [{ label: 'mcp', tone: 'accent' }, { label: 'security', tone: 'warn' }], body: [
        'Each MCP server should be gated to admins, not just authenticated users — the design exists from the surface task.',
        'Reuse the token resolver: the verifier maps a bearer token to an AccessToken whose scope carries the user group.',
        'Mount-time validation rejects a server whose required group is unknown, so misconfig fails fast at boot.',
        'Tests cover the verifier (pure) plus in-memory client CRUD per server to confirm the gate holds end to end.',
      ], assignee: 'AK' },
      { id: 'b3', title: 'Twenty import — completion checkpoint', tags: [{ label: 'import' }], attachments: 1, assignee: 'BT' },
      { id: 'b4', title: 'core_geo timezones (zone1970.tab)', tags: [{ label: 'core_geo' }], assignee: 'MS' },
    ],
  },
  {
    id: 'progress',
    title: 'In progress',
    tone: 'rgb(var(--v-theme-primary))',
    cards: [
      { id: 'p1', title: 'Conversation insights — result schema redesign', tags: [{ label: 'schema', tone: 'accent' }, { label: 'migration', tone: 'warn' }], body: [
        'Rename and extend the result axes to self-explanatory names so reports read without a legend.',
        'Split the generated is_open flag from chat_status via a STORED computed column — single source, indexable, no desync.',
        'Add a separate chat_result axis for clean report aggregates instead of folding states into chat_status.',
        'Migration ci08 drops and recreates the table (the data is derived); a full re-tag then runs via an AGENT_VERSION bump.',
      ], comments: 6, attachments: 2, assignee: 'BT' },
      { id: 'p2', title: 'Mobile filter slot experiment', tags: [{ label: 'frontend' }], comments: 1, assignee: 'AK' },
    ],
  },
  {
    id: 'review',
    title: 'Review',
    tone: 'rgb(var(--v-theme-warning))',
    cards: [
      { id: 'r1', title: 'nginx side of MCP streaming', tags: [{ label: 'ops' }, { label: 'nginx', tone: 'warn' }], body: [
        'Dedicated location /mcp/ for the Streamable-HTTP sub-app, mounted inside the backend process.',
        'MCP streams over SSE, so nginx default buffering breaks it — the block turns proxy_buffering off.',
        'proxy_pass keeps no trailing slash: the app owns the /mcp/<code> prefix, and stripping it 404s.',
        'Leave /internal and /api buffered; only /mcp opts out, plus longer read/send timeouts for long streams.',
      ], comments: 3, assignee: 'MS' },
      { id: 'r2', title: 'Per-user MCP bearer tokens', tags: [{ label: 'auth', tone: 'accent' }], comments: 4, attachments: 1, assignee: 'BT' },
    ],
  },
  {
    id: 'done',
    title: 'Done',
    tone: 'rgb(var(--v-theme-success))',
    cards: [
      { id: 'd1', title: 'MCP connection config — force https', tags: [{ label: 'mcp', tone: 'accent' }], assignee: 'BT' },
      { id: 'd2', title: 'Password change + strict policy', tags: [{ label: 'core_users' }, { label: 'done', tone: 'ok' }], comments: 5, assignee: 'AK' },
      { id: 'd3', title: 'Mobile navigation — responsive sidebar', tags: [{ label: 'frontend' }], assignee: 'MS' },
    ],
  },
]
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader :title="t('design-system.page.kanban.title')" :description="t('design-system.page.kanban.description')" back-to="/design-system" />

      <section class="ds-section">
        <h6 class="mb-1">{{ t('design-system.section.kanban.title') }}</h6>
        <p class="ds-note">{{ t('design-system.section.kanban.note') }}</p>

        <KanbanBoard bleed>
          <KanbanColumn
            v-for="col in columns"
            :key="col.id"
            :title="col.title"
            :count="col.cards.length"
            :tone="col.tone"
            :add-label="t('design-system.section.kanban.addCard')"
          >
            <template #actions>
              <VBtn icon variant="text" size="x-small" density="comfortable">
                <IconPlus :size="16" />
              </VBtn>
            </template>

            <KanbanCard
              v-for="card in col.cards"
              :key="card.id"
              :title="card.title"
              :tags="card.tags"
              :comments="card.comments"
              :attachments="card.attachments"
              :assignee="card.assignee"
              :menu="col.id !== 'done'"
            >
              <p v-for="(para, pi) in card.body" :key="pi" class="kanban-card-text">{{ para }}</p>
            </KanbanCard>
          </KanbanColumn>
        </KanbanBoard>
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

/* Paragraph text inside a card (demo of the card default slot). */
.kanban-card-text {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--text-muted);
}
.kanban-card-text + .kanban-card-text {
  margin-top: 8px;
}
</style>
