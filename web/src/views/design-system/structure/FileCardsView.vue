<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'
import FileCards, { type FileCardItem } from '@/components/FileCards.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const mixed: FileCardItem[] = [
  { key: 1, filename: 'Invoice-2001321.pdf', mime: 'application/pdf', size: 188_416, safety: 'safe', url: '#' },
  { key: 2, filename: 'quarterly-report.xlsx', mime: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', size: 1_398_101, safety: 'safe', url: '#' },
  { key: 3, filename: 'archive.zip', mime: 'application/zip', size: 10_485_760, safety: 'warning', url: '#' },
  { key: 4, filename: 'untitled.exe', mime: 'application/octet-stream', size: 524_288, safety: 'rejected', url: null },
]

const byState: FileCardItem[] = [
  { key: 'safe', filename: 'contract.docx', mime: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', size: 84_992, safety: 'safe', url: '#' },
  { key: 'warning', filename: 'macros.zip', mime: 'application/zip', size: 2_097_152, safety: 'warning', url: '#' },
  { key: 'untrusted', filename: 'payload.scr', mime: 'application/octet-stream', size: 65_536, safety: 'rejected', url: null },
]

const kinds: FileCardItem[] = [
  { key: 'pdf', filename: 'doc.pdf', mime: 'application/pdf', size: 120_000, safety: 'safe', url: '#' },
  { key: 'img', filename: 'photo.png', mime: 'image/png', size: 240_000, safety: 'safe', url: '#' },
  { key: 'sheet', filename: 'data.csv', mime: 'text/csv', size: 8_000, safety: 'safe', url: '#' },
  { key: 'slides', filename: 'deck.pptx', mime: 'application/vnd.openxmlformats-officedocument.presentationml.presentation', size: 980_000, safety: 'safe', url: '#' },
  { key: 'cal', filename: 'meeting.ics', mime: 'text/calendar', size: 2_400, safety: 'safe', url: '#' },
  { key: 'other', filename: 'notes', mime: null, size: 512, safety: 'safe', url: '#' },
]

const usageSnippet = `<script setup lang="ts">
import FileCards, { type FileCardItem } from '@/components/FileCards.vue'

const files: FileCardItem[] = [
  { key: 1, filename: 'invoice.pdf', mime: 'application/pdf', size: 188416, safety: 'safe', url: '/storage/...' },
  { key: 2, filename: 'archive.zip', mime: 'application/zip', size: 10485760, safety: 'warning', url: '/storage/...' },
  { key: 3, filename: 'payload.exe', mime: 'application/octet-stream', size: 65536, safety: 'rejected', url: null },
]
<\/script>

<template>
  <FileCards :files="files" title="Attachments" />
<\/template>`
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.file-cards.title')" :description="t('design-system.page.file-cards.description')" back-to="/design-system" />

    <!-- With a header -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.file-cards.withHeader') }}</h6>
      <div class="ds-host">
        <FileCards :files="mixed" :title="'Attachments'" />
      </div>
      <p class="ds-note">title — optional header (paperclip + label + count).</p>
    </section>

    <!-- States -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.file-cards.states') }}</h6>
      <div class="ds-host">
        <FileCards :files="byState" />
      </div>
      <p class="ds-note">
        safety: <code>safe</code> → green, <code>warning</code> → yellow,
        <code>rejected</code>/<code>null</code> → red "untrusted". A url makes the card a
        download link; without it the card is inert.
      </p>
    </section>

    <!-- File kinds -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.file-cards.kinds') }}</h6>
      <div class="ds-host">
        <FileCards :files="kinds" />
      </div>
      <p class="ds-note">The glyph is derived from the filename extension.</p>
    </section>

    <!-- List variant -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.file-cards.list') }}</h6>
      <div class="ds-host ds-host--narrow">
        <FileCards :files="mixed" variant="list" title="Attachments" />
      </div>
      <p class="ds-note">
        <code>variant="list"</code> — compact linear rows, no surface/shadow/padding box,
        always single column. For tight spaces like a sidebar.
      </p>
    </section>

    <!-- Usage -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.file-cards.usage') }}</h6>
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

.ds-host--narrow {
  max-width: 320px;
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
