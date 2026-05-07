# RAG-006 Chunk Review Packet

## Purpose

RAG-006 turns RAG-005 chunk candidates into human review queues before any runtime RAG promotion.

It is a review-work reduction checkpoint, not a retrieval checkpoint.

## What It Produces

- source-title review groups for unmapped chunks
- review-only source suggestions from the RAG-004 manifest
- topic-mapping review rows for off-taxonomy NotebookLM labels
- quote-review rows for chunks that referenced source excerpts
- first-slice review candidates that are mapped and topic-clean enough to inspect first

## What It Does Not Do

- it does not auto-map uncertain sources
- it does not promote chunks
- it does not import chunks into product memory
- it does not enable runtime retrieval
- it does not call NotebookLM
- it does not call an LLM, TTS provider, ASR provider, or external API
- it does not store raw source text
- it does not store source excerpt text
- it does not make the sales agent use any extracted tactic

## Commands

Run the review-packet builder against the default RAG-005 chunk result and RAG-004 source manifest:

```powershell
python scripts\run_rag_006_chunk_review_packet.py
```

Validate the RAG-006 review-packet contract:

```powershell
python scripts\validate_rag_006_chunk_review_packet.py
```

## Default Output

```text
research\experiments\generated\RAG-006-chunk-review-packet\
```

The output contains:

- `result.json`
- `report.md`

## Current Review Packet Run

The 2026-05-06 run against the RAG-005 chunk candidates and RAG-004 source manifest produced:

- `121` chunk candidates reviewed
- `46` source-title review groups
- `63` chunks needing source mapping
- `8` chunks needing topic mapping
- `80` chunks needing quote review
- `20` first-slice review candidates
- `0` auto-promoted chunks
- source excerpt text stored: `false`
- runtime retrieval disabled
- chunk import disabled

The first-slice candidates are intentionally review candidates only. After the Vinh Giang import, the queue now includes mapped communication/voice chunks such as `"Yes, And"` framing, the `3-2-1` framework, PREP, and declarative-statement guidance. They are not runtime eligible until a later checkpoint promotes a small, source-confirmed, guardrail-compatible subset.

## Review Meaning

RAG-006 helps decide what to review first. It does not decide what is true, safe, compliant, or runtime-ready.

Required review before any later promotion:

- confirm whether each unmapped source title should map to an existing RAG-004 source or become a new source candidate
- resolve every off-taxonomy topic flag
- rewrite quote-dependent chunks as paraphrased, cited knowledge
- reject manipulative, unsafe, or non-compliant tactics
- confirm campaign guardrails can block or override any promoted knowledge

## Product Boundary

RAG-006 keeps the architecture unchanged:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + reviewed sales knowledge layer
  + explicit guardrails and human escalation paths
```

Runtime retrieval remains disabled until a later checkpoint promotes a small reviewed slice and adds a guarded retrieval policy.
