<script setup lang="ts">
import { ref, watch, onActivated } from 'vue'
import { useI18n } from 'vue-i18n'
import { IconRefresh, IconServerBolt } from '@tabler/icons-vue'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import McpInfoPanel from '@/components/McpInfoPanel.vue'
import { serverIcon } from '@/shared/mcp_tool_icons'
import {
  listMcpServers,
  getMcpServer,
  type McpServerSummary,
  type McpServerDetail,
} from '../api'

defineOptions({ inheritAttrs: false })

const { t } = useI18n()

const servers   = ref<McpServerSummary[]>([])
const selected  = ref<string | null>(null)
const detail    = ref<McpServerDetail | null>(null)
const error     = ref('')
const loading   = ref(true)   // cold load of the server list
const detailLoading = ref(false)

async function loadList() {
  error.value = ''
  try {
    servers.value = await listMcpServers()
    // Keep the current selection if it still exists; otherwise pick the first.
    if (!selected.value || !servers.value.some(s => s.code === selected.value))
      selected.value = servers.value[0]?.code ?? null
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function loadDetail(code: string) {
  detailLoading.value = true
  error.value = ''
  try {
    detail.value = await getMcpServer(code)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
    detail.value = null
  } finally {
    detailLoading.value = false
  }
}

watch(selected, (code) => {
  if (code) void loadDetail(code)
  else detail.value = null
})

// Routed views live under a global <KeepAlive> (App.vue): onActivated fires on
// the first show too, so it alone covers first paint + every re-entry with a
// single load (onMounted would double-fire it on first mount).
onActivated(loadList)
</script>

<template>
  <PageLayout v-bind="$attrs">
    <PageHeader :title="t('core_mcp.page.title')" :description="t('core_mcp.page.description')">
      <template #actions>
        <VBtn variant="text" :disabled="loading" @click="loadList">
          <template #prepend><IconRefresh :size="16" /></template>
          {{ t('core_mcp.action.refresh') }}
        </VBtn>
      </template>
    </PageHeader>

    <VAlert v-if="error" type="error" variant="tonal" class="mb-3" :text="error" />

    <div v-if="loading" class="d-flex justify-center py-12">
      <VProgressCircular indeterminate />
    </div>

    <div v-else-if="servers.length === 0" class="mcp-empty">
      <IconServerBolt :size="32" stroke-width="1.5" />
      <span>{{ t('core_mcp.empty') }}</span>
    </div>

    <div v-else class="mcp-servers">
      <VCard variant="outlined" rounded="lg" class="mcp-servers__bar mb-3">
        <VSelect
          v-model="selected"
          :items="servers"
          item-title="code"
          item-value="code"
          :label="t('core_mcp.select.label')"
          density="comfortable"
          hide-details
          class="mcp-servers__select"
          :menu-props="{ contentClass: 'srv-menu' }"
        >
          <template v-if="selected" #prepend-inner>
            <VIcon :icon="serverIcon(selected)" size="16" class="srv-chip__icon" />
          </template>
          <template #item="{ props, item }">
            <VListItem v-bind="props" :title="item.code">
              <template #prepend>
                <VIcon :icon="serverIcon(item.code)" size="16" class="srv-chip__icon" />
              </template>
            </VListItem>
          </template>
        </VSelect>
      </VCard>

      <div class="mcp-servers__panel">
        <McpInfoPanel
          :loading="detailLoading && !detail"
          :server-name="detail?.name ?? selected"
          :version="detail?.version"
          :instructions="detail?.instructions"
          :connection-config="detail?.connection_config"
          :tools="detail?.tools ?? []"
        />
      </div>
    </div>
  </PageLayout>
</template>

<style scoped>
.mcp-servers {
  max-width: 860px;
}

.mcp-servers__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 12px;
}

.mcp-servers__select {
  flex: 1 1 240px;
  max-width: 360px;
}

.srv-chip__icon {
  color: var(--accent);
}

.mcp-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 64px 0;
  color: var(--text-muted);
  font-size: 13px;
}
</style>

<!-- Menu content is teleported out of the component root → un-scoped to reach it. -->
<style>
.srv-menu .v-list-item__spacer {
  width: 10px;
}
</style>
