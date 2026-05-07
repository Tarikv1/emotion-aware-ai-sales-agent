# RAG-010 Reviewed Expansion Slice Design

## Context

RAG-009 accounted for all `95` RAG-004 sources and all `121` RAG-005 chunks while keeping runtime retrieval disabled. It identified four clean next-promotion candidates:

- `rag005-chunk-029` - Level 3 Executive Problem / PR Risk
- `rag005-chunk-030` - The "So What" Gap
- `rag005-chunk-031` - Deadline Qualification
- `rag005-chunk-036` - Cadence Detection

## Decision

RAG-010 promotes those four candidates into a second reviewed, project-owned paraphrase slice. It does not enable runtime retrieval, chunk import, embeddings, vector storage, LLM reranking, provider calls, NotebookLM calls, private customer data reads, or auto-promotion.

## Candidate Review Rules

RAG-010 rewrites each source candidate into bounded, vertical-agnostic product guidance:

- Operational-to-business impact questions are allowed when they do not exaggerate risk, invent PR/retention consequences, or pressure the buyer.
- "So what" follow-up questions are allowed when phrased as respectful impact clarification, not interrogation.
- Deadline/timing qualification is allowed when it discovers real buyer timing and does not manufacture urgency.
- Cadence detection is allowed only as advisory delivery/context guidance. Speech speed can suggest pacing or a gentle check-in, but it cannot infer hidden emotion, intent, urgency, or buyer truth.

## Output

RAG-010 produces:

- `scripts/rag_reviewed_expansion_slice.py`
- `scripts/run_rag_010_reviewed_expansion_slice.py`
- `scripts/validate_rag_010_reviewed_expansion_slice.py`
- `research/experiments/cases/rag-010-reviewed-expansion-slice.json`
- `research/experiments/generated/RAG-010-reviewed-expansion-slice/result.json`
- `research/experiments/generated/RAG-010-reviewed-expansion-slice/report.md`
- `docs/product/RAG_010_REVIEWED_EXPANSION_SLICE.md`

## Safety Boundary

All items stay `runtime_eligible_now: false` and `retrieval_eligible_now: false`. The artifact stores no source excerpt text and carries only reviewed paraphrases, source IDs, topic IDs, source titles, and guardrail notes. Runtime use still requires a later integration gate for campaign guardrail ordering, trace logging, no-match fallback, observability, and human review.
