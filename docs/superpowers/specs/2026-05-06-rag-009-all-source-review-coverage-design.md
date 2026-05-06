# RAG-009 All-Source Review Coverage Design

## Objective

Before runtime retrieval, cover the full RAG source universe with a review gate.

RAG-009 should account for every source candidate and chunk candidate created by RAG-003 through RAG-006, then separate safe promotion candidates from items that still need source mapping, topic mapping, quote clearance, rejection, or later review. It does not make every chunk retrievable and does not enable runtime RAG.

## Current Context

The current RAG pipeline has broad intake coverage but only a small reviewed first slice:

- RAG-003: `11` imported reports cover `10 / 10` active RAG topics.
- RAG-004: `95` metadata-only source candidates require human metadata review.
- RAG-005: `121` chunk candidates exist; `58` are source-mapped, `63` still need source mapping, `8` need topic-mapping review, and `80` contain source-excerpt references that require quote review.
- RAG-006: review queues exist for source mapping, topic mapping, quote review, and first-slice candidates; `0` chunks are auto-promoted.
- RAG-007: only `9` manually reviewed knowledge items are promoted into the first reviewed slice.
- RAG-008: a dry-run retrieval policy can query only those `9` reviewed items, while runtime retrieval remains disabled.

Tarik's direction is to include all sources before runtime retrieval. That means all sources and chunks need explicit review coverage, not automatic runtime eligibility.

## Recommended Approach

Build a local all-source review coverage gate.

RAG-009 reads the existing RAG-004, RAG-005, RAG-006, and RAG-007 artifacts. It produces a complete coverage matrix and promotion ledger that says where every source and every chunk currently stands:

- already reviewed in RAG-007
- eligible for next manual promotion review
- blocked until source mapping
- blocked until topic mapping
- blocked until quote clearance
- rejected for safety/product reasons
- deferred for later topic expansion

No embeddings, vector DB, provider calls, LLM calls, NotebookLM API calls, private data, source excerpt text storage, or runtime integration are allowed.

## Components

- `scripts/rag_all_source_review_coverage.py`: local coverage builder.
- `scripts/run_rag_009_all_source_review_coverage.py`: CLI runner with project-root and private-path guards.
- `scripts/validate_rag_009_all_source_review_coverage.py`: validator that checks coverage completeness and safety boundaries.
- `research/experiments/cases/rag-009-all-source-review-coverage.json`: configuration for review lanes, promotion criteria, rejection criteria, and output limits.
- `research/experiments/generated/RAG-009-all-source-review-coverage/result.json`: machine-readable review coverage output.
- `research/experiments/generated/RAG-009-all-source-review-coverage/report.md`: human-readable review report.
- `docs/product/RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md`: product checkpoint doc.
- `docs/product/COMMANDS.md`, `scripts/check_setup.py`, `docs/thesis/ROADMAP.md`, and `docs/thesis/METHODOLOGY_LOG.md`: wiring and thesis traceability.

## Coverage Model

RAG-009 should create these top-level collections:

- `source_coverage`: one row per RAG-004 source candidate.
- `chunk_coverage`: one row per RAG-005 chunk candidate.
- `review_queues`: grouped source-mapping, topic-mapping, quote-clearance, safety-review, and deferred-review queues.
- `promotion_ledger`: reviewed, candidate, blocked, rejected, and deferred chunk statuses.
- `next_promotion_candidates`: a bounded set of clean candidates for the next manual review slice.

Every RAG-005 chunk ID must appear exactly once in `chunk_coverage`. Every RAG-004 source ID must appear exactly once in `source_coverage`.

## Promotion Criteria

A chunk can enter `next_promotion_candidates` only if it meets all of these conditions:

- has stable source IDs from the RAG-004 manifest
- has approved RAG topic IDs or no topic-mapping review flag
- has no unresolved source-excerpt dependency
- has no secret-like text flag
- has no pressure, manipulation, protected-attribute, false-certainty, or compliance-risk flag
- can be represented as project-owned paraphrased knowledge with source IDs and chunk IDs
- stays vertical-agnostic or is clearly campaign-configurable
- preserves campaign guardrails, consent handling, protected scripts, required disclosures, and human escalation

RAG-009 may identify candidates. It must not promote them into runtime retrieval.

## Blocking And Rejection Criteria

RAG-009 must block or reject chunks that contain or require:

- unresolved source mapping
- unresolved topic mapping
- source excerpt text or quote dependency without manual clearance
- pressure tactics
- sensitive demographic personalization
- hidden-emotion certainty claims
- compliance, legal, medical, financial, or regulated-claim risk
- protected script rewriting
- customer refusal or do-not-call override behavior
- private/customer data

Blocked means "could become eligible after review." Rejected means "should not be promoted unless Tarik explicitly reverses the decision."

## Voice/Prosody Boundary

Voice and prosody chunks can be included in the all-source review coverage, but they remain advisory. They may guide delivery metadata, listening rubrics, or later TTS phrasing review, but they cannot:

- infer hidden emotion with certainty
- override explicit customer words
- alter protected scripts, disclosures, compliance text, handoff text, or refusal handling
- imitate a source speaker identity, accent, or theatrical style
- become runtime personalization without later review

Tone mismatch should remain a weak uncertainty signal that can justify a gentle clarification only in unblocked contexts.

## Output Boundaries

The result summary and boundaries must include:

- `runtime_retrieval_enabled: false`
- `retrieval_used_in_runtime: false`
- `chunk_import_enabled: false`
- `auto_promoted_chunk_count: 0`
- `provider_calls_made: false`
- `notebooklm_api_used: false`
- `private_customer_data_used: false`
- `reads_data_private: false`
- `source_excerpt_text_stored: false`
- `all_rag004_sources_accounted_for: true`
- `all_rag005_chunks_accounted_for: true`

## Validation Requirements

The validator must prove:

- Every RAG-004 source candidate appears exactly once.
- Every RAG-005 chunk candidate appears exactly once.
- RAG-007 reviewed items remain recognized as reviewed, not duplicated as new candidates.
- Unmapped chunks remain blocked until source mapping is resolved.
- Topic-review chunks remain blocked until topic mapping is resolved.
- Quote-dependent chunks remain blocked until manual quote clearance is recorded.
- Rejected chunks cannot appear in `next_promotion_candidates`.
- Runtime retrieval and chunk import stay disabled.
- No source excerpt text, private data, provider call, NotebookLM API call, or API key is used.
- The runner rejects input or output paths under `data/private` and `data/private-restricted`.
- The product remains vertical-agnostic and campaign-profile compatible.

## Non-Goals

- No runtime retrieval.
- No vector database.
- No embeddings.
- No LLM reranking.
- No customer transcript ingestion.
- No private data reads.
- No source excerpt text copying.
- No automatic promotion into runtime memory.
- No assumption that all `121` chunks are safe.

## Approval State

Tarik selected the all-source review coverage approach on 2026-05-06: include all sources before runtime retrieval, but promote only clean reviewed chunks. Implementation should proceed with a validator-first workflow after this spec is reviewed.
