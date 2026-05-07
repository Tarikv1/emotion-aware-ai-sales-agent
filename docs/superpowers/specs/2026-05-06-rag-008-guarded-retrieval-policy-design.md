# RAG-008 Guarded Retrieval Policy Design

## Objective

Create the first executable retrieval-policy checkpoint after RAG-007 without enabling runtime retrieval.

RAG-008 tests whether reviewed RAG-007 knowledge can be selected, cited, and blocked safely in a dry-run packet. It does not import chunks into runtime memory and does not let the live sales agent query RAG.

## Current Context

RAG-007 produced `9` manually reviewed, project-owned paraphrased knowledge items:

- `5` response-wording items.
- `4` voice-delivery items.
- `9` manual quote clearances.
- `0` auto-promoted chunks.

Every RAG-007 item still has `runtime_eligible_now: false` and `retrieval_eligible_now: false`. RAG-008 must preserve that boundary while proving a future retrieval layer can be constrained.

## Recommended Approach

Build a local deterministic dry-run retrieval packet.

RAG-008 reads only `research/experiments/generated/RAG-007-reviewed-first-slice/result.json` and a small synthetic case file. It matches synthetic queries to reviewed RAG-007 items using transparent token matching and explicit lane filters. It emits candidate retrieval packets with source IDs and guardrail notes, but every packet remains non-runtime.

No embeddings, provider calls, LLM calls, NotebookLM API calls, private data, source excerpts, or runtime memory writes are allowed.

## Components

- `scripts/rag_guarded_retrieval_policy.py`: pure local retrieval-policy builder.
- `scripts/run_rag_008_guarded_retrieval_policy.py`: CLI runner with project-root and private-path guards.
- `scripts/validate_rag_008_guarded_retrieval_policy.py`: validator that creates fixtures, runs the builder/runner, and checks boundary behavior.
- `research/experiments/cases/rag-008-guarded-retrieval-policy.json`: synthetic query and blocking cases.
- `research/experiments/generated/RAG-008-guarded-retrieval-policy/result.json`: official dry-run output.
- `research/experiments/generated/RAG-008-guarded-retrieval-policy/report.md`: human-readable report.
- `docs/product/RAG_008_GUARDED_RETRIEVAL_POLICY.md`: product checkpoint doc.
- `docs/product/COMMANDS.md`, `scripts/check_setup.py`, `docs/thesis/ROADMAP.md`, and `docs/thesis/METHODOLOGY_LOG.md`: wiring and thesis traceability.

## Retrieval Rules

Each query case contains:

- `case_id`
- `query`
- `lane_filter`: `response_wording`, `voice_delivery`, or `any`
- `context_flags`: synthetic flags such as `ordinary_objection`, `broad_question`, `tone_uncertainty`, `customer_refusal`, `protected_script`, `human_escalation`, `pressure_sensitive`, and `private_data_requested`
- `expected_behavior`: `retrieve` or `block`

For retrieve cases, RAG-008 may return at most `3` candidate items. Every returned item must include:

- `knowledge_id`
- `lane`
- `source_chunk_ids`
- `source_ids`
- `project_rule`
- `guardrail_notes`
- `match_reasons`
- `citation_trace`
- `runtime_use_allowed: false`

For blocked cases, RAG-008 must return no items and must record a concrete `block_reason`.

## Blocking Rules

Retrieval must be blocked when any of these context flags are true:

- `customer_refusal`
- `do_not_call`
- `protected_script`
- `required_disclosure`
- `human_escalation`
- `pressure_sensitive`
- `private_data_requested`

These rules model campaign guardrails remaining authoritative. RAG can suggest communication style only after campaign/compliance/refusal boundaries allow freeform guidance.

## Voice/Prosody Boundary

Voice-delivery retrieval is advisory only. It can propose delivery metadata or review hints, but it cannot change protected words, infer hidden emotion with certainty, or override explicit customer intent.

The tone-mismatch case must retrieve the uncertainty/clarification item only when the case is low-pressure and not blocked. The output must preserve the wording that tone is a weak uncertainty signal, not emotion certainty.

## Output Boundaries

The result summary and boundaries must include:

- `runtime_retrieval_enabled: false`
- `retrieval_used_in_runtime: false`
- `chunk_import_enabled: false`
- `auto_promote_allowed: false`
- `provider_calls_made: false`
- `notebooklm_api_used: false`
- `private_customer_data_used: false`
- `reads_data_private: false`
- `source_excerpt_text_stored: false`
- `only_reviewed_rag007_used: true`

## Validation Requirements

The validator must prove:

- Only RAG-007 knowledge IDs appear in retrieval outputs.
- Retrieve cases produce bounded, cited candidate packets.
- Blocked cases produce no retrieved items.
- Runtime retrieval and chunk import stay disabled.
- Voice/prosody items stay advisory.
- No source excerpt text, private data, provider call, NotebookLM API call, or API key is used.
- The runner rejects inputs or outputs under `data/private` and `data/private-restricted`.
- The product remains vertical-agnostic.

## Non-Goals

- No vector database.
- No embeddings.
- No LLM reranking.
- No runtime sales-agent integration.
- No customer transcript ingestion.
- No private data reads.
- No automatic promotion of more chunks.

## Approval State

Tarik approved this dry-run approach in chat on 2026-05-06. Implementation can proceed with a validator-first workflow.
