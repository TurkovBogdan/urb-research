<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import CodeBlock from '@/components/CodeBlock.vue'

type Variant = 'minimal' | 'icon' | 'accent'

const variant = ref<Variant>('icon')
const lineNumbers = ref(false)

const { t } = useI18n()

const python = `def fetch_vacancies(status: str, limit: int = 50) -> list[Vacancy]:
    with session_scope() as session:
        return (
            session.query(Vacancy)
            .filter(Vacancy.status == status)
            .order_by(Vacancy.published_at.desc())
            .limit(limit)
            .all()
        )`

const samples: Record<string, string> = {
  json: `{
  "id": "hh-1234567",
  "title": "Python Backend Developer",
  "salary": { "from": 180000, "to": 250000, "currency": "RUR" },
  "experience": "between3And6",
  "schedule": "remote",
  "published_at": "2026-05-17T09:00:00+05:00"
}`,

  typescript: `interface BlockMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

async function completeSession(sessionId: number, text: string) {
  const { data } = await api.post<BlockMessage>(\`/sessions/\${sessionId}/complete\`, { text })
  return data
}`,

  bash: `#!/usr/bin/env bash
set -euo pipefail
pnpm --filter web build
python build.py --clean
echo "Done: dist/release/hh-support-agent"`,

  sql: `SELECT v.id, v.title, v.salary_from, c.name AS company_name
FROM hh_vacancy v
JOIN hh_company c ON c.id = v.company_id
WHERE v.status = 'active' AND v.salary_from >= 150000
ORDER BY v.published_at DESC
LIMIT 20;`,
}
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader :title="t('design-system.page.code-block.title')" :description="t('design-system.page.code-block.description')" back-to="/design-system" />

      <!-- Component props -->
      <VCard class="ds-card">
        <h6 class="ds-card__title">{{ t('design-system.section.code-block.props') }}</h6>
        <div class="ds-props">

          <div class="ds-row">
            <span class="ds-tag">variant</span>
            <div class="ds-controls">
              <VBtnToggle v-model="variant" mandatory divided density="compact">
                <VBtn value="minimal">Minimal</VBtn>
                <VBtn value="icon">Icon</VBtn>
                <VBtn value="accent">Accent</VBtn>
              </VBtnToggle>
            </div>
            <span class="ds-spec">header template</span>
          </div>

          <div class="ds-row ds-row--border">
            <span class="ds-tag">showLineNumbers</span>
            <div class="ds-controls">
              <VBtnToggle v-model="lineNumbers" mandatory divided density="compact">
                <VBtn :value="false">Off</VBtn>
                <VBtn :value="true">On</VBtn>
              </VBtnToggle>
            </div>
            <span class="ds-spec">default numbering</span>
          </div>

        </div>
      </VCard>

      <!-- Demo -->
      <VCard class="ds-card">
        <h6 class="ds-card__title">{{ t('design-system.section.code-block.demo') }}</h6>
        <CodeBlock
          :code="python"
          lang="python"
          :variant="variant"
          :show-line-numbers="lineNumbers"
        />
      </VCard>

      <!-- All variants -->
      <VCard class="ds-card">
        <h6 class="ds-card__title">{{ t('design-system.section.code-block.allVariants') }}</h6>
        <div class="variants">
          <div class="variant-item">
            <span class="ds-tag">minimal</span>
            <CodeBlock :code="python" lang="python" variant="minimal" />
          </div>
          <div class="variant-item">
            <span class="ds-tag">icon</span>
            <CodeBlock :code="python" lang="python" variant="icon" />
          </div>
          <div class="variant-item">
            <span class="ds-tag">accent</span>
            <CodeBlock :code="python" lang="python" variant="accent" />
          </div>
        </div>
      </VCard>

      <!-- Languages -->
      <VCard class="ds-card">
        <h6 class="ds-card__title">{{ t('design-system.section.code-block.languages') }}</h6>
        <div class="lang-grid">
          <div v-for="(code, lang) in samples" :key="lang" class="lang-item">
            <CodeBlock :code="code" :lang="lang" variant="icon" />
          </div>
        </div>
      </VCard>

    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 860px;
}

.ds-card {
  padding: 16px;
}

.ds-card__title {
  margin: 0 0 12px;
}

.ds-props {
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 140px 1fr 200px;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
}

.ds-row--border {
  border-top: 1px solid var(--border-soft);
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
  gap: 8px;
}

.variants {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.variant-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.variant-item .ds-tag {
  display: block;
}

.lang-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.lang-item {
  display: flex;
  flex-direction: column;
}
</style>
