# RAG-011 Blocker Cleanup Packet Design

## Context

RAG-009 left two large blocker classes before any runtime integration work:

- `63` chunks blocked for source mapping
- `42` chunks blocked for quote clearance

RAG-010 promoted the four clean next-promotion candidates and did not touch these queues.

## Decision

RAG-011 creates an offline cleanup packet that narrows the next human-review work. It does not mutate RAG-009, clear quote dependencies, import chunks, or promote knowledge items.

The checkpoint has two cleanup lanes:

1. **Source mapping candidates:** use RAG-006 `candidate_source_suggestions` only when the score meets a conservative threshold. These become human-review mapping proposals, not automatic mappings.
2. **Quote clearance cards:** select a bounded first slice of RAG-009 quote-clearance blockers and package metadata-only review cards that ask for project-owned paraphrases. These cards copy no source excerpt text and do not mark quote clearance resolved.

## Scope

RAG-011 reads:

- `research/experiments/generated/RAG-009-all-source-review-coverage/result.json`
- `research/experiments/generated/RAG-006-chunk-review-packet/result.json`
- `research/experiments/cases/rag-011-blocker-cleanup-packet.json`

RAG-011 writes:

- `research/experiments/generated/RAG-011-blocker-cleanup-packet/result.json`
- `research/experiments/generated/RAG-011-blocker-cleanup-packet/report.md`

## Safety Boundary

RAG-011 keeps all runtime flags false:

- no runtime retrieval
- no chunk import
- no embeddings or vector database
- no LLM reranking
- no provider or NotebookLM API calls
- no private customer data reads
- no source excerpt text storage
- no auto-promotion

The artifact may report **potential blocker reduction after human acceptance**, but `blockers_resolved_now` stays `0`.

## Readiness Meaning

After RAG-011 passes, the project has a reviewed work packet for the next cleanup slice. It is still not runtime retrieval ready. Runtime integration remains blocked until source mapping, quote clearance, campaign guardrail ordering, trace logging, no-match fallback, and human review gates are addressed.
