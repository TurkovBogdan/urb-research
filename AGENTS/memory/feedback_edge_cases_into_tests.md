---
name: feedback_edge_cases_into_tests
description: Every strange/edge case found during audits must become a fixture + test; expand the test set after each fix iteration.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 98d9ce38-4234-44e2-b91b-2281e22a1862
---

When auditing/fixing (esp. content_parser email-splitting), capture **every strange or edge case** —
real defects AND accepted limitations AND deferred design cases — as a corpus fixture + a regression
test, and **expand the test set after each iteration of edits**. Do not just fix-and-move-on.

**Why:** the user explicitly asked ("Важно добавлять подобные сценарии к тестовому набору, расширяй его
после каждой итерации правок. Всё странное в тесты"). It prevents silent regressions (several were
introduced and only caught a round later) and pins documented limitations so a future change is flagged.

**How to apply:**
- After each fix: save the real message body to `dev/bench/content_parser/for-test/<threadid>-<msgid>.txt`
  and add a test (fixture-backed via the `for_test` fixture) asserting the new behavior.
- Also pin **accepted limitations** and **deferred** cases in `tests/.../test_limitations.py` documenting
  CURRENT behavior (e.g. top-quote-with-trailing-reply kept whole, no data loss) — so the design fix is caught.
- Add a sharp **unit test** for anything a fixture can't reproduce (e.g. CRLF: `read_text` strips `\r`, so
  the CRLF guard lives in a unit test that builds the body with explicit `\r\n`).
- Re-run the module suite + a signature-count regression check on the bench every iteration.
See [[content_parser_audit_campaign]].
