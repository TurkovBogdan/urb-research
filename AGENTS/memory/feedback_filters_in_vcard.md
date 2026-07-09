---
name: feedback_filters_in_vcard
description: Filter bars/panels on list pages must always be wrapped in a VCard
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1a1636c0-9902-4a09-b895-fe58fae41417
---

Filters (search/select/toggle bars on any list/index page) are ALWAYS placed inside a `VCard`, never bare.

**Why:** consistent visual grouping across the app — a filter region reads as one panel.

**How to apply:** wrap the filter controls in `<VCard variant="outlined" rounded="lg" class="filter-panel mb-3">` with inner `padding: 12px` (the established convention — see `web/src/features/agents/views/ModelsView.vue` filter-panel/filter-grid). Layout the controls inside (flex row or grid). Applied to `core_mcp` McpServersView server/format bar.
