# RAG-011 Blocker Cleanup Packet

## Purpose

RAG-011 narrows the remaining RAG blocker cleanup work after RAG-010.

It creates human-review proposals for high-confidence source mappings and a bounded set of quote-clearance cards. It does not resolve blockers by itself and does not enable runtime retrieval.

## What It Produces

- source-mapping candidate groups from RAG-006 `candidate_source_suggestions`
- quote-clearance cards from RAG-009 `quote_clearance_queue`
- a summary of current blockers and possible cleanup impact after human acceptance
- no source excerpt text
- no runtime-eligible chunks

## Commands

Run:

```powershell
python scripts\run_rag_011_blocker_cleanup_packet.py
```

Validate:

```powershell
python scripts\validate_rag_011_blocker_cleanup_packet.py
```

## Default Output

`research\experiments\generated\RAG-011-blocker-cleanup-packet\`

- `result.json`
- `report.md`

## Current Official Run

- Source-mapping blockers: `63`
- Source-mapping candidate groups: `3`
- Source-mapping candidate chunks: `5`
- Quote-clearance blockers: `42`
- Quote-clearance review cards: `12`
- Potential blocker reduction after human acceptance: `17`
- `blockers_resolved_now`: `0`
- Auto-promoted chunks: `0`

## Cleanup Rules

- Source mapping proposals are included only when the RAG-006 suggestion score meets the configured threshold.
- Quote-clearance cards are metadata-only review cards.
- Quote dependencies remain unresolved until a later human-accepted paraphrase checkpoint.
- `blockers_resolved_now` stays `0`.
- No chunk is auto-promoted or imported.

## Product Boundary

Runtime retrieval remains disabled. Chunk import remains disabled. No embedding job, vector database, LLM reranker, provider call, NotebookLM API call, private customer data, or source excerpt text is used.

RAG-011 is cleanup planning, not runtime readiness. Runtime integration still requires reviewed source mapping, quote clearance, campaign guardrail ordering, trace logging, no-match fallback, observability, and human review.
