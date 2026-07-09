<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageLayout from '@/layout/templates/PageLayout.vue'
import PageHeader from '@/layout/components/PageHeader.vue'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

const compact = ref(false)

const sampleFull = `# First-level heading

A regular paragraph with **bold text**, *italic* and \`inline code\`.

## Unordered list

- Develop and maintain backend services in Python
- Design REST APIs and integrate with external systems
- Review code, take part in architectural decisions
- Nested item:
  - Sub-item A
  - Sub-item B

## Ordered list

1. Write tests
2. Run CI
3. Ship to production

## Requirements

### Must have

- 3+ years of experience with Python 3.10+
- FastAPI / SQLAlchemy / PostgreSQL
- Understanding of asyncio and the event loop

### Nice to have

- Experience with queues (Celery, RabbitMQ, Redis)
- Knowledge of Docker and Kubernetes

## Code block

\`\`\`python
async def list_vacancies(status: str, limit: int = 50) -> list[Vacancy]:
    async with session_scope() as s:
        result = await s.execute(
            select(Vacancy).where(Vacancy.status == status).limit(limit)
        )
        return list(result.scalars())
\`\`\`

## Quote

> We are looking for a specialist ready to work in a fast-changing environment
> and not afraid of technical challenges.

---

Small text at the end of the paragraph. Links are filtered by DOMPurify and shown as plain text.`

const sampleVacancy = `Requirements:
- 2+ years of experience as a Python Backend Developer
- Knowledge of Django or FastAPI
- Understanding of SOLID principles and clean code
- Experience with relational databases (PostgreSQL preferred)

What we offer:
- Remote work, 5/2 schedule
- Health insurance from the first month
- Corporate training and conferences at the company's expense
- Choice of equipment (Mac/Linux)

We offer interesting tasks, honest feedback and no bureaucracy.`

const editable = ref(sampleVacancy)
const { t } = useI18n()
</script>

<template>
  <PageLayout>
    <div class="ds-page">
      <PageHeader
        :title="t('design-system.page.markdown.title')"
        :description="t('design-system.page.markdown.description')"
        back-to="/design-system"
      />

      <!-- Props -->
      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.markdown.props') }}</h6>
        <div class="ds-card">
          <div class="ds-row">
            <span class="ds-tag">compact</span>
            <div class="ds-controls">
              <VBtnToggle v-model="compact" mandatory divided density="compact">
                <VBtn :value="false">false</VBtn>
                <VBtn :value="true">true</VBtn>
              </VBtnToggle>
            </div>
            <span class="ds-spec">reduces font-size and spacing</span>
          </div>
        </div>
      </section>

      <!-- Live editor -->
      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.markdown.liveEditor') }}</h6>
        <div class="live-grid">
          <div class="live-pane">
            <span class="ds-tag mb-2">Markdown</span>
            <VTextarea
              v-model="editable"
              variant="outlined"
              density="compact"
              rows="14"
              hide-details
              style="font-family: var(--font-mono); font-size: 12px"
            />
          </div>
          <div class="live-pane">
            <span class="ds-tag mb-2">Result</span>
            <div class="preview-box">
              <MarkdownRenderer :text="editable" :compact="compact" />
            </div>
          </div>
        </div>
      </section>

      <!-- Full demo -->
      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.markdown.fullDemo') }}</h6>
        <div class="preview-box">
          <MarkdownRenderer :text="sampleFull" :compact="compact" />
        </div>
      </section>

      <!-- Typical content -->
      <section class="ds-section">
        <h6 class="mb-3">{{ t('design-system.section.markdown.jobContent') }}</h6>
        <div class="preview-box preview-box--narrow">
          <MarkdownRenderer :text="sampleVacancy" :compact="compact" />
        </div>
      </section>

    </div>
  </PageLayout>
</template>

<style scoped>
.ds-page {
  max-width: 960px;
}

.ds-section {
  margin-bottom: 32px;
}

.ds-card {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  overflow: hidden;
}

.ds-row {
  display: grid;
  grid-template-columns: 120px 1fr 240px;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
}

.ds-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-faint);
  display: block;
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

/* ── Live editor ──────────────────────────────────────────── */

.live-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

.live-pane {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ── Preview boxes ────────────────────────────────────────── */

.preview-box {
  background: var(--surface);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius);
  padding: 20px 24px;
}

.preview-box--narrow {
  max-width: 580px;
}
</style>
