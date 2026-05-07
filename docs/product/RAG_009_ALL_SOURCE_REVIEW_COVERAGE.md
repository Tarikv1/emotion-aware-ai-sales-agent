# RAG-009 All-Source Review Coverage

## Purpose

RAG-009 accounts for the full reviewed RAG source universe before runtime retrieval work continues.

It covers every RAG-004 source candidate and every RAG-005 chunk candidate, then separates reviewed, blocked, rejected, deferred, and next-promotion candidate chunks. It does not enable runtime retrieval.

## What It Produces

- one source-coverage row per RAG-004 source
- one chunk-coverage row per RAG-005 chunk
- blocked queues for source mapping, topic mapping, and quote clearance
- a safety rejection queue
- a promotion ledger
- a bounded next-promotion candidate list for later manual review

## Commands

Run:

```powershell
python scripts\run_rag_009_all_source_review_coverage.py
```

Validate:

```powershell
python scripts\validate_rag_009_all_source_review_coverage.py
```

## Default Output

`research\experiments\generated\RAG-009-all-source-review-coverage\`

- `result.json`
- `report.md`

## Current Official Run

- Sources accounted for: `95`
- Chunks accounted for: `121`
- Reviewed RAG-007 chunks: `9`
- Next promotion candidates: `4`
- Blocked for source mapping: `63`
- Blocked for quote clearance: `42`
- Rejected for safety: `3`
- Auto-promoted chunks: `0`

## Product Boundary

RAG-009 keeps the architecture unchanged:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + reviewed sales knowledge layer
  + explicit guardrails and human escalation paths
```

Runtime retrieval remains disabled. Chunk import remains disabled. No chunks are auto-promoted. No vector database, embedding job, LLM reranker, provider call, NotebookLM API call, customer transcript, private data, or source excerpt text is used.

Voice and prosody chunks are included in coverage, but they remain advisory. They cannot infer hidden emotion with certainty, override customer intent, alter protected text, or become runtime personalization without a later review gate.

## Readiness Meaning

After RAG-009 passes, the project has all-source review coverage. That means all imported RAG sources and chunks are accounted for, not that all chunks are safe or retrievable.

The next RAG step should either expand the manually reviewed slice from clean candidates or build a runtime-off integration harness. Live runtime retrieval still requires a later gate for campaign guardrail order, trace logging, no-match fallback, observability, and human review.
