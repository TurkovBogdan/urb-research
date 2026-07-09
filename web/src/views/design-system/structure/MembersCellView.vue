<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'
import MembersCell, { type MemberCellItem } from '@/components/MembersCell.vue'

const { t } = useI18n()

const team: MemberCellItem[] = [
  { label: 'Alice Doe',   sub: 'alice@acme.example' },
  { label: 'Bob Roe',     sub: 'bob@acme.example' },
  { label: 'Carol Smith', sub: 'carol@acme.example' },
]

const contacts: MemberCellItem[] = [
  { label: 'cameron.anderson@acme.example' },
  { label: 'charlotte.anderson@acme.example' },
  { label: 'jordan.bond@acme.example' },
  { label: 'dustin.stewart@acme.example' },
]

const single: MemberCellItem[] = [{ label: 'contact@acme.example' }]
const empty: MemberCellItem[] = []

const picked = ref<string>('—')
function onSelect(items: MemberCellItem[], index: number) {
  picked.value = items[index].label
}

const usageSnippet = `<script setup lang="ts">
import MembersCell, { type MemberCellItem } from '@/components/MembersCell.vue'

// Map your rows to items; the parent owns the action via @select(index).
const items: MemberCellItem[] = members.map(m => ({
  label: m.name || m.email,   // primary text (truncated in the cell)
  sub: m.email,               // secondary line in the popover (hidden if === label)
  disabled: !m.email,         // a non-filterable entry is not clickable
}))
<\/script>

<template>
  <MembersCell :items="items" @select="(i) => applyFilter(members[i])" />

  <!-- email column: monospace + italic empty label -->
  <MembersCell
    :items="emailItems"
    mono
    :empty-text="$t('...no_team')"
    empty-italic
    @select="(i) => applyFilter(emails[i])"
  />
<\/template>`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.members-cell.title')" :description="t('design-system.page.members-cell.description')" back-to="/design-system" />

    <!-- Basic: name + email, overflow popover -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.members-cell.basic') }}</h6>
      <div class="ds-host ds-host--narrow">
        <MembersCell :items="team" @select="(i) => onSelect(team, i)" />
      </div>
      <p class="ds-note">
        Shows the first member; the rest collapse behind a <code>+N</code> badge that opens a
        click-through popover. Each row emits <code>select(index)</code> — the parent owns the action.
      </p>
    </section>

    <!-- Mono (email columns) -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.members-cell.mono') }}</h6>
      <div class="ds-host ds-host--narrow">
        <MembersCell :items="contacts" mono @select="(i) => onSelect(contacts, i)" />
      </div>
      <p class="ds-note"><code>mono</code> — monospace labels for email/login columns.</p>
    </section>

    <!-- Empty states -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.members-cell.empty') }}</h6>
      <div class="ds-host ds-host--narrow ds-rows">
        <MembersCell :items="single" mono @select="(i) => onSelect(single, i)" />
        <MembersCell :items="empty" />
        <MembersCell :items="empty" :empty-text="t('design-system.section.members-cell.no_team')" empty-italic />
      </div>
      <p class="ds-note">
        One member → no badge. No members → <code>emptyText</code> (default <code>—</code>);
        <code>emptyItalic</code> renders a muted italic placeholder (e.g. «no team»).
      </p>
    </section>

    <!-- Last picked -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.members-cell.event') }}</h6>
      <div class="ds-host">
        <span class="ds-note ma-0">select → <code>{{ picked }}</code></span>
      </div>
    </section>

    <!-- Usage -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.members-cell.usage') }}</h6>
      <CodeBlock :code="usageSnippet" lang="vue" />
    </section>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }
.ds-section { margin-bottom: 28px; }

.ds-host {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 16px;
}

.ds-host--narrow { max-width: 320px; }

.ds-rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ds-note {
  margin: 8px 2px 0;
  font-size: 12px;
  color: var(--text-faint);
}

.ds-note code {
  font-family: var(--font-mono);
  font-size: 11px;
}
</style>
