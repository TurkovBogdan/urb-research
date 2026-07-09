---
name: Qwen lineage (as of 2026-05)
description: Actual Qwen3.x release order and the user's local model pool — Qwen3.5/3.6 exist, do not regress to "only Qwen3-2507"
type: project
originSessionId: c9b77601-32ae-4140-94a1-033a80bdc20f
---
Qwen release lineage as of 2026-05:

- **Qwen3** — Apr 2025, base (0.6/1.7/4/8/14/32B dense + 30B-A3B / 235B-A22B MoE).
- **Qwen3-2507** — Jul 2025, split into `Instruct-2507` (non-thinking) and `Thinking-2507`; `enable_thinking` removed.
- **Qwen3.5** — Feb–Mar 2026. 397B-A17B MoE first, then dense 0.8/2/4/9B and MoE 27B / 35B-A3B / 122B-A10B. No 14B in 3.5.
- **Qwen3.6** — Apr 2026. Refinement: default `temperature=0.2` (vs Qwen3 0.7), less overthinking, tighter JSON. Sizes incl. **Qwen3.6-35B-A3B** (MoE) and **Qwen3.6-27B** (dense). HF: `Qwen/Qwen3.6-35B-A3B`.

User's local LM Studio pool (verified by screenshot 2026-05-13):
Qwen3.6 35B-A3B Q4_K_M (20.55 GB), Qwen3.6 27B Q4_K_M (16.28 GB), Qwen3.5 9B Q4_K_M (6.10 GB), Qwen3 14B Q4_K_M (8.38 GB), Qwen3 4B 2507 + Thinking 2507 (Q6_K, 3.08 GB), Qwen3 VL 4B Q8 (4.77 GB), Qwen2.5 Coder 14B Q6_K.

**Why:** in the local-LLM enrichment research I initially treated Qwen3.6 as non-existent ("3.6 не существует, опечатка"). User corrected with a screenshot. Lineage moves fast — by 2026 Q2 Qwen3.6 is the production-grade pick.

**How to apply:** when discussing local model choice, default to Qwen3.6-35B-A3B (MoE) as the primary candidate and Qwen3.6-27B as the dense fallback. Use Qwen3.6 sampling defaults (`temperature=0.2, top_p=0.9`), not Qwen3-era 0.7/0.8. Re-verify against the LM Studio catalog at implementation time — don't pin old model names.

Full research with version-specific bugs and pitfalls: `AGENTS/research/qwen-local-enrichment/INDEX.md`.
