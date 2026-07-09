<script setup lang="ts">
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import { IconInfoCircle, IconHelp, IconAlertTriangle } from '@tabler/icons-vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <PageLayout>
  <div class="ds-page">
    <PageHeader :title="t('design-system.page.tooltips.title')" :description="t('design-system.page.tooltips.description')" back-to="/design-system" />

    <!-- Basic -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.tooltips.basic') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">text</span>
          <div class="ds-controls">
            <VTooltip text="Simple tooltip" location="top">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="tonal" size="small">Hover me</VBtn>
              </template>
            </VTooltip>
            <VTooltip text="Action button" location="top">
              <template #activator="{ props }">
                <VBtn v-bind="props" color="primary" size="small">Primary</VBtn>
              </template>
            </VTooltip>
          </div>
          <span class="ds-spec">text="..." location="top"</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">on icon</span>
          <div class="ds-controls">
            <VTooltip text="Information" location="top">
              <template #activator="{ props }">
                <VBtn v-bind="props" icon variant="text" size="small">
                  <IconInfoCircle :size="18" />
                </VBtn>
              </template>
            </VTooltip>
            <VTooltip text="Help" location="top">
              <template #activator="{ props }">
                <VBtn v-bind="props" icon variant="text" size="small">
                  <IconHelp :size="18" />
                </VBtn>
              </template>
            </VTooltip>
            <VTooltip text="Warning: this action cannot be undone" location="top">
              <template #activator="{ props }">
                <VBtn v-bind="props" icon variant="text" size="small" color="warn">
                  <IconAlertTriangle :size="18" />
                </VBtn>
              </template>
            </VTooltip>
          </div>
          <span class="ds-spec">tooltip on an icon</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">on text</span>
          <div class="ds-controls">
            <VTooltip text="Session ID: 7f3c-4a9e" location="top">
              <template #activator="{ props }">
                <span v-bind="props" class="ds-hint">hover over me</span>
              </template>
            </VTooltip>
          </div>
          <span class="ds-spec">activator is a span</span>
        </div>

      </div>
    </section>

    <!-- Placement -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.tooltips.placement') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">location</span>
          <div class="ds-controls">
            <VTooltip text="top" location="top">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="outlined" size="small">top</VBtn>
              </template>
            </VTooltip>
            <VTooltip text="bottom" location="bottom">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="outlined" size="small">bottom</VBtn>
              </template>
            </VTooltip>
            <VTooltip text="start" location="start">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="outlined" size="small">start</VBtn>
              </template>
            </VTooltip>
            <VTooltip text="end" location="end">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="outlined" size="small">end</VBtn>
              </template>
            </VTooltip>
          </div>
          <span class="ds-spec">top · bottom · start · end</span>
        </div>

      </div>
    </section>

    <!-- Multiline -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.tooltips.multiline') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">\n</span>
          <div class="ds-controls">
            <VTooltip location="top">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="tonal" size="small">Line breaks</VBtn>
              </template>
              <div class="ds-tip">
                <div>First line of the tooltip</div>
                <div>Second line of the tooltip</div>
                <div>And one more</div>
              </div>
            </VTooltip>
          </div>
          <span class="ds-spec">default slot instead of text</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">paragraph</span>
          <div class="ds-controls">
            <VTooltip location="top" max-width="320">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="tonal" size="small">Long text</VBtn>
              </template>
              <div class="ds-tip">
                A long tooltip that wraps to a fixed width: we set max-width="320",
                and the text wraps naturally. Used to describe form fields and
                complex operations.
              </div>
            </VTooltip>
          </div>
          <span class="ds-spec">max-width="320"</span>
        </div>

      </div>
    </section>

    <!-- Structured -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.tooltips.structured') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">title</span>
          <div class="ds-controls">
            <VTooltip location="top" max-width="320">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="tonal" size="small">Title + text</VBtn>
              </template>
              <div class="ds-tip">
                <div class="ds-tip__title">Run task</div>
                <div class="ds-tip__divider" />
                <div>Queues the task in the scheduler and runs it on the next tick.</div>
              </div>
            </VTooltip>
          </div>
          <span class="ds-spec">title + divider + text</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">key/value</span>
          <div class="ds-controls">
            <VTooltip location="top" max-width="360">
              <template #activator="{ props }">
                <span v-bind="props" class="ds-hint">session #42</span>
              </template>
              <div class="ds-tip">
                <div class="ds-tip__title">Session #42</div>
                <div class="ds-tip__divider" />
                <dl class="ds-tip__kv">
                  <dt>ID</dt><dd>7f3c-4a9e-2b11</dd>
                  <dt>Status</dt><dd>active</dd>
                  <dt>Agent</dt><dd>support-agent</dd>
                  <dt>Created</dt><dd>2026-05-24 14:02</dd>
                </dl>
              </div>
            </VTooltip>
          </div>
          <span class="ds-spec">dl with metadata</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">sections</span>
          <div class="ds-controls">
            <VTooltip location="top" max-width="380">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="tonal" size="small">Several sections</VBtn>
              </template>
              <div class="ds-tip">
                <div class="ds-tip__title">Agent budget</div>
                <div class="ds-tip__divider" />
                <div class="ds-tip__row">
                  <span class="ds-tip__label">Used</span>
                  <span class="ds-tip__value">12.4k / 50k tokens</span>
                </div>
                <div class="ds-tip__row">
                  <span class="ds-tip__label">Cost</span>
                  <span class="ds-tip__value">$0.084</span>
                </div>
                <div class="ds-tip__divider" />
                <div class="ds-tip__muted">Resets daily at 00:00 UTC</div>
              </div>
            </VTooltip>
          </div>
          <span class="ds-spec">title · rows · footer</span>
        </div>

        <div class="ds-row ds-row--center">
          <span class="ds-tag">code</span>
          <div class="ds-controls">
            <VTooltip location="top" max-width="420">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="tonal" size="small">With code</VBtn>
              </template>
              <div class="ds-tip">
                <div class="ds-tip__title">Validation error</div>
                <div class="ds-tip__divider" />
                <div>The <code class="ds-tip__code">model</code> field is required when <code class="ds-tip__code">provider</code> is set.</div>
                <div class="ds-tip__divider" />
                <pre class="ds-tip__pre">ValidationError:
  provider: openai
  model: null  ← required</pre>
              </div>
            </VTooltip>
          </div>
          <span class="ds-spec">inline code + pre</span>
        </div>

      </div>
    </section>

    <!-- Delays -->
    <section class="ds-section">
      <h6 class="mb-3">{{ t('design-system.section.tooltips.delays') }}</h6>
      <div class="ds-card">

        <div class="ds-row ds-row--center">
          <span class="ds-tag">delay</span>
          <div class="ds-controls">
            <VTooltip text="No delay" location="top">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="outlined" size="small">0 ms</VBtn>
              </template>
            </VTooltip>
            <VTooltip text="Opens after 500 ms" location="top" :open-delay="500">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="outlined" size="small">500 ms</VBtn>
              </template>
            </VTooltip>
            <VTooltip text="Closes 800 ms after leaving" location="top" :close-delay="800">
              <template #activator="{ props }">
                <VBtn v-bind="props" variant="outlined" size="small">close 800 ms</VBtn>
              </template>
            </VTooltip>
          </div>
          <span class="ds-spec">:open-delay · :close-delay</span>
        </div>

      </div>
    </section>

  </div>
  </PageLayout>
</template>

<style scoped>
.ds-page { max-width: 860px; }
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

.ds-hint {
  border-bottom: 1px dashed var(--text-faint);
  cursor: help;
  font-size: 13px;
}

.ds-tip {
  font-size: 12px;
  line-height: 1.45;
}
.ds-tip__title {
  font-weight: 600;
  font-size: 12px;
}
.ds-tip__divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.18);
  margin: 6px 0;
}
.ds-tip__kv {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2px 12px;
  margin: 0;
}
.ds-tip__kv dt {
  color: rgba(255, 255, 255, 0.7);
  font-size: 11px;
}
.ds-tip__kv dd {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 11px;
}
.ds-tip__row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.ds-tip__label {
  color: rgba(255, 255, 255, 0.7);
}
.ds-tip__value {
  font-family: var(--font-mono);
}
.ds-tip__muted {
  color: rgba(255, 255, 255, 0.6);
  font-size: 11px;
}
.ds-tip__code {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 1px 4px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.12);
}
.ds-tip__pre {
  font-family: var(--font-mono);
  font-size: 11px;
  margin: 0;
  padding: 6px 8px;
  background: rgba(0, 0, 0, 0.25);
  border-radius: 4px;
  white-space: pre;
  overflow-x: auto;
}
</style>
