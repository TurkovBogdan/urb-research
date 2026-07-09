---
name: feedback_never_checkout_dirty_shared_files
description: Never git checkout/restore a dirty file to undo a local mistake — the working tree carries uncommitted work from other tasks
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6163b521-8732-4ea9-b86e-d427d35ca100
---

Never run `git checkout`/`git restore`/`git stash` on a tracked file to undo your own bad edit. The working tree routinely carries **uncommitted** work from OTHER tasks (esp. shared files: `web/src/locales/**`, `AGENTS/**/INDEX.md`, `app/modules.py`). A checkout discards ALL of it, not just your change, and it is unrecoverable (unstaged → not in git, not in stash, IDE Local History often doesn't track these files, the committed SPA bundle predates recent work).

**Why:** on 2026-06-17 a scripted JSON edit reformatted `design-system/{en,ru}.json`; reverting it with `git checkout` wiped the uncommitted `spoiler` AND unrelated `message` i18n sections in both files. Recovery was partial (RU `message` had to be re-translated).

**How to apply:** undo a local edit by editing it back **by hand** (Edit tool), never with git. Combined with [[feedback_commit_protocol]] (never `git add -A`) and the edit-by-hand rule: treat any tracked file as if it holds someone else's unsaved work. If a revert seems unavoidable, first `git stash`-less: copy the current content aside, or `git diff <file>` to capture state, before touching it.
