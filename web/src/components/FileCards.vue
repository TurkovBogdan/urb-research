<script lang="ts">
/** One file to render as a card. Domain-agnostic — any feature maps its own rows to this.
 * Mirrors the displayable fields of a stored file (core_storage): name, mime, size,
 * safety verdict and the servable url. */
export interface FileCardItem {
  key: string | number
  filename: string | null
  // Declared MIME type; drives icon selection first, with the filename extension as fallback.
  mime: string | null
  size: number | null
  // Trust verdict driving the card colour + caption. Anything other than safe/warning
  // (incl. rejected / null) renders as the red "untrusted" state.
  safety: 'safe' | 'warning' | 'rejected' | null
  // Download link; a card with a url is a link, one without is inert.
  url: string | null
}
</script>

<script setup lang="ts">
/**
 * File cards — a self-contained, domain-agnostic list. Each item describes a file (name,
 * mime, size, trust verdict, optional download url); the row derives its icon from the
 * mime/extension and its colour + caption from the verdict: green/safe, yellow/warning,
 * red/untrusted. A row with a url is a download link; one without is inert. An optional
 * `title` renders a header (paperclip + title + count).
 *
 * Two presentations via `variant`:
 * - `card` (default) — floating cards (surface + shadow + padding); responsive grid, one
 *   column on narrow widths, two once there is room. Use where there is room to breathe.
 * - `list` — compact linear rows (no surface/shadow/padding box), always single column.
 *   Use in tight spaces like a sidebar.
 */
import { computed } from 'vue'
import { IconPaperclip, IconDownload } from '@tabler/icons-vue'
import { fileIcon, humanSize } from '@/shared/utils/file-icon'
import { mimeToName } from '@/shared/utils/mime-to-name'

const props = withDefaults(
  defineProps<{
    files: FileCardItem[]
    title?: string
    variant?: 'card' | 'list'
  }>(),
  { variant: 'card' },
)

const iconSize = computed(() => (props.variant === 'list' ? 18 : 22))

const items = computed(() => props.files ?? [])

type SafetyState = 'safe' | 'warning' | 'untrusted'

const SAFETY_LABEL: Record<SafetyState, string> = {
  safe: 'common.file_card.safe',
  warning: 'common.file_card.warning',
  untrusted: 'common.file_card.untrusted',
}

function safetyOf(file: FileCardItem): SafetyState {
  if (file.safety === 'safe') return 'safe'
  if (file.safety === 'warning') return 'warning'
  return 'untrusted'
}

function isDownloadable(file: FileCardItem): boolean {
  return !!file.url
}
</script>

<template>
  <section class="fc" :class="`fc--${variant}`">
    <div v-if="title" class="fc-head">
      <VIcon :icon="IconPaperclip" size="16" />
      <span>{{ title }}</span>
      <span class="fc-count">{{ items.length }}</span>
    </div>

    <div class="fc-grid">
      <template v-for="file in items" :key="file.key">
        <component
          :is="isDownloadable(file) ? 'a' : 'div'"
          class="fc-card"
          :class="[`fc-card--${safetyOf(file)}`, { 'fc-card--link': isDownloadable(file) }]"
          v-bind="isDownloadable(file)
            ? { href: file.url!, download: file.filename || '', target: '_blank', rel: 'noopener' }
            : {}"
        >
          <span class="fc-icon" :class="`fc-icon--${safetyOf(file)}`">
            <component :is="fileIcon(file.filename, file.mime)" :size="iconSize" stroke="1.6" />
          </span>
          <span class="fc-body">
            <span class="fc-name" :title="file.filename || ''">
              {{ file.filename || $t('common.file_card.fallback_name') }}
            </span>
            <span class="fc-meta">
              <span class="fc-safety" :class="`fc-safety--${safetyOf(file)}`">
                {{ $t(SAFETY_LABEL[safetyOf(file)]) }}
              </span>
              <template v-if="humanSize(file.size)"> · {{ humanSize(file.size) }}</template>
              <template v-if="mimeToName(file.mime, file.filename)"> · {{ mimeToName(file.mime, file.filename) }}</template>
            </span>
          </span>
          <VIcon v-if="isDownloadable(file)" :icon="IconDownload" size="18" class="fc-dl" />
        </component>
      </template>
    </div>
  </section>
</template>

<style scoped>
.fc-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.fc-count {
  display: inline-grid;
  place-items: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  font-size: 11px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: var(--text-muted);
}

.fc-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.fc-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  min-width: 0;
  text-decoration: none;
  color: inherit;
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06), 0 2px 10px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.15s ease, transform 0.15s ease;
}

.fc-card--link {
  cursor: pointer;
}

.fc-card--link:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.fc-card--link:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
}

.fc-icon {
  flex: none;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: grid;
  place-items: center;
}

.fc-icon--safe {
  color: rgb(var(--v-theme-success));
  background: rgba(var(--v-theme-success), 0.14);
}

.fc-icon--warning {
  color: rgb(var(--v-theme-warning));
  background: rgba(var(--v-theme-warning), 0.14);
}

.fc-icon--untrusted {
  color: rgb(var(--v-theme-error));
  background: rgba(var(--v-theme-error), 0.14);
}

.fc-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1 1 auto;
}

.fc-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fc-meta {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fc-safety--safe {
  color: rgb(var(--v-theme-success));
}

.fc-safety--warning {
  color: rgb(var(--v-theme-warning));
}

.fc-safety--untrusted {
  color: rgb(var(--v-theme-error));
}

.fc-dl {
  flex: none;
  color: var(--text-faint);
}

.fc-card--link:hover .fc-dl {
  color: rgb(var(--v-theme-primary));
}

@media (min-width: 600px) {
  .fc--card .fc-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

/* ── List variant — compact linear rows, no card chrome ─────────────── */

.fc--list .fc-grid {
  gap: 2px;
}

.fc--list .fc-card {
  gap: 10px;
  padding: 6px 6px;
  border-radius: 8px;
  background: transparent;
  box-shadow: none;
}

.fc--list .fc-card--link:hover {
  transform: none;
  box-shadow: none;
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.fc--list .fc-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
}

.fc--list .fc-name {
  font-size: 12px;
}

.fc--list .fc-meta {
  font-size: 11px;
}
</style>
