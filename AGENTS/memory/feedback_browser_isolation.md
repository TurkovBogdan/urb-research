---
name: feedback-browser-isolation
description: "Never drive the user's working browser — take a separate dedicated browser instance under control before any page interaction"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e8faae31-62b6-4f68-a862-bc19c50368b5
---

Never open/navigate/resize tabs in the browser the user is actively working in (2026-06-10: agent-driven page switching disrupted the user's parallel work).

**Why:** the user runs their own tasks in their main browser; an agent flipping pages there destroys their workflow.

**How to apply:** before ANY browser interaction, call `list_connected_browsers` and `select_browser` to take a dedicated instance (or create tabs only via `tabs_create_mcp` in that instance); never reuse the user's active window/tabs. Related: [[responsive-testing-process]] (pop the MCP tab into its own window before resizing).
