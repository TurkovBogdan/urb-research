<script setup lang="ts">
import { ref } from 'vue'
import CodeBlock from '@/components/CodeBlock.vue'
import { toolIcon } from '@/shared/mcp_tool_icons'

export interface McpToolInfo {
  name: string
  description: string | null
  input_schema: Record<string, unknown> | null
  output_schema: Record<string, unknown> | null
}

defineProps<{
  serverName?: string | null
  title?: string | null
  version?: string | null
  instructions?: string | null
  tools: McpToolInfo[]
  /** JSON-конфиг для копирования в клиент (Claude и пр.). */
  connectionConfig?: string | null
  connectionLang?: string
  /** Cold-load skeleton (no data yet). */
  loading?: boolean
}>()

const dialogOpen = ref(false)
const active     = ref<McpToolInfo | null>(null)

function open(tool: McpToolInfo) {
  active.value = tool
  dialogOpen.value = true
}
</script>

<template>
  <VCard variant="outlined" rounded="lg" class="mcp-panel">
    <!-- Cold-load skeleton mirroring the panel layout. -->
    <template v-if="loading">
      <header class="mcp-panel__head">
        <div class="mcp-panel__title-row">
          <VSkeletonLoader type="text" class="mcp-skel mcp-skel--name" />
          <VSkeletonLoader type="chip" class="mcp-skel mcp-skel--ver" />
        </div>
      </header>
      <section class="mcp-panel__section">
        <VSkeletonLoader type="text" class="mcp-skel mcp-skel--h" />
        <VSkeletonLoader type="paragraph" class="mcp-skel" />
      </section>
      <section class="mcp-panel__section">
        <VSkeletonLoader type="text" class="mcp-skel mcp-skel--h" />
        <VSkeletonLoader type="image" class="mcp-skel mcp-skel--code" />
      </section>
      <section class="mcp-panel__section">
        <VSkeletonLoader type="text" class="mcp-skel mcp-skel--h" />
        <div class="mcp-panel__tools">
          <div v-for="n in 8" :key="n" class="tool-row tool-row--skel">
            <VSkeletonLoader type="avatar" class="mcp-skel mcp-skel--ic" />
            <div class="tool-row__body">
              <VSkeletonLoader type="text" class="mcp-skel mcp-skel--tname" />
              <VSkeletonLoader type="text" class="mcp-skel mcp-skel--tdesc" />
            </div>
          </div>
        </div>
      </section>
    </template>

    <template v-else>
    <header v-if="serverName || title || version" class="mcp-panel__head">
      <div class="mcp-panel__title-row">
        <span v-if="serverName" class="mcp-panel__name">{{ serverName }}</span>
        <span v-if="title" class="mcp-panel__title">{{ title }}</span>
        <VChip v-if="version" size="x-small" variant="tonal" class="mcp-panel__version">
          v{{ version }}
        </VChip>
      </div>
    </header>

    <section v-if="instructions" class="mcp-panel__section">
      <h6 class="mcp-panel__section-title">{{ $t('common.mcp.description') }}</h6>
      <p class="mcp-panel__instructions">{{ instructions }}</p>
    </section>

    <section v-if="connectionConfig" class="mcp-panel__section">
      <h6 class="mcp-panel__section-title">{{ $t('common.mcp.connection') }}</h6>
      <CodeBlock :code="connectionConfig" :lang="connectionLang ?? 'json'" variant="accent" />
    </section>

    <section class="mcp-panel__section">
      <h6 class="mcp-panel__section-title">
        {{ $t('common.mcp.tools') }}
        <span class="mcp-panel__count">{{ tools.length }}</span>
      </h6>

      <div v-if="tools.length === 0" class="mcp-panel__empty">
        {{ $t('common.mcp.tools_empty') }}
      </div>

      <div v-else class="mcp-panel__tools">
        <button
          v-for="t in tools"
          :key="t.name"
          type="button"
          class="tool-row"
          @click="open(t)"
        >
          <VIcon :icon="toolIcon(t.name)" size="14" class="tool-icon" />
          <div class="tool-row__body">
            <span class="tool-row__name">{{ t.name }}</span>
            <span v-if="t.description" class="tool-row__desc">{{ t.description }}</span>
          </div>
        </button>
      </div>
    </section>
    </template>

    <VDialog v-model="dialogOpen" max-width="640" scrollable>
      <VCard v-if="active">
        <VCardTitle class="d-flex align-center ga-2">
          <VIcon :icon="toolIcon(active.name)" size="18" class="tool-icon" />
          <span class="cell-mono">{{ active.name }}</span>
          <VChip v-if="serverName" size="x-small" variant="tonal" class="ml-1">
            {{ serverName }}
          </VChip>
        </VCardTitle>
        <VDivider />
        <VCardText class="tool-dialog__body">
          <div v-if="active.description" class="tool-dialog__desc">
            {{ active.description }}
          </div>
          <div v-else class="tool-dialog__empty">{{ $t('common.mcp.no_description') }}</div>

          <div v-if="active.input_schema" class="tool-dialog__schema">
            <h6 class="mcp-panel__section-title">Input schema</h6>
            <CodeBlock
              :code="JSON.stringify(active.input_schema, null, 2)"
              lang="json"
              variant="minimal"
            />
          </div>

          <div v-if="active.output_schema" class="tool-dialog__schema">
            <h6 class="mcp-panel__section-title">Output schema</h6>
            <CodeBlock
              :code="JSON.stringify(active.output_schema, null, 2)"
              lang="json"
              variant="minimal"
            />
          </div>
        </VCardText>
        <VDivider />
        <VCardActions>
          <VSpacer />
          <VBtn variant="text" @click="dialogOpen = false">{{ $t('common.action.close') }}</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VCard>
</template>

<style scoped>
.mcp-panel {
  display: flex;
  flex-direction: column;
  background: var(--surface);
}

/* ── Loading skeleton ──────────────────────────────────────────────── */
/* Text bones size to the loader's width, so we pin the loader root widths. */
.mcp-skel { padding: 0; background: transparent; }
.mcp-skel--name { width: 160px; }
.mcp-skel--ver :deep(.v-skeleton-loader__chip) { width: 40px; height: 18px; margin: 0; }
.mcp-skel--h { width: 90px; margin-bottom: 10px; }
.mcp-skel--code :deep(.v-skeleton-loader__image) { height: 96px; border-radius: var(--radius-sm); }
.mcp-skel--ic :deep(.v-skeleton-loader__avatar) { width: 16px; height: 16px; margin: 2px 0 0; }
.mcp-skel--tname { width: 110px; }
.mcp-skel--tdesc { width: 90%; }

.tool-row--skel {
  cursor: default;
}
.tool-row--skel:hover {
  background: transparent;
}

.mcp-panel__head {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-soft);
}

.mcp-panel__title-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
}

.mcp-panel__name {
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.01em;
}

.mcp-panel__title {
  font-size: 13px;
  color: var(--text-faint);
}

.mcp-panel__version {
  font-family: var(--font-mono);
  align-self: center;
}

.mcp-panel__section {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-soft);

  &:last-child {
    border-bottom: none;
  }
}

.mcp-panel__section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 10px 0;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.mcp-panel__count {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
  padding: 1px 6px;
  background: var(--surface-hi);
  border: 1px solid var(--border-soft);
  border-radius: 999px;
  letter-spacing: 0;
  text-transform: none;
}

.mcp-panel__instructions {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--text);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.mcp-panel__empty {
  font-size: 12px;
  color: var(--text-muted);
  padding: 4px 0;
}

.mcp-panel__tools {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 4px 12px;
}

.tool-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color 0.1s ease;
  min-width: 0;
  text-align: left;
  background: transparent;
  border: none;
  font: inherit;
  color: inherit;
}

.tool-row:hover {
  background: var(--surface-hi);
}

.tool-row:focus-visible {
  outline: 1px solid var(--accent-mid);
  outline-offset: -1px;
}

.tool-icon {
  color: var(--accent);
  flex-shrink: 0;
  margin-top: 2px;
}

.tool-row__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1 1 0;
}

.tool-row__name {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tool-row__desc {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.4;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.cell-mono {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text);
}

.tool-dialog__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-top: 16px !important;
}

.tool-dialog__desc {
  font-size: 13px;
  line-height: 1.55;
  color: var(--text);
  white-space: pre-wrap;
}

.tool-dialog__empty {
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}

.tool-dialog__schema {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
