# RAG-005 Chunk Normalization

## Purpose

RAG-005 converts NotebookLM report appendices into local, metadata-only chunk candidates for human review.

This is the next bridge after RAG-004 source manifest normalization. It links extracted sales principles, applications, guardrails, and examples to candidate source IDs without making the live sales agent use them.

## What It Produces

- stable chunk candidate IDs such as `rag005-chunk-001`
- original NotebookLM chunk IDs when present
- source-title to RAG-004 source-ID mappings
- topic IDs
- language and sales-stage metadata
- principle, application, when-not-to-use, example phrase, emotional cue, compliance note, evidence type, confidence, and citation metadata
- review flags for missing fields, source mapping, quote review, and secret-like text

## What It Does Not Do

- it does not call NotebookLM
- it does not call an LLM, TTS provider, ASR provider, or external API
- it does not enable runtime retrieval
- it does not import chunks into product memory
- it does not store raw source text
- it does not copy source excerpt text forward
- it does not make the sales agent use any extracted tactic

## Commands

Run chunk normalization against the default RAG-002 imports and RAG-004 source manifest:

```powershell
python scripts\run_rag_005_chunk_normalization.py
```

Validate the RAG-005 parser and runner contract:

```powershell
python scripts\validate_rag_005_chunk_normalization.py
```

## Default Output

```text
research\experiments\generated\RAG-005-chunk-normalization\
```

The output contains:

- `result.json`
- `report.md`

## Current Chunk Run

The 2026-05-06 run against Tarik's imported NotebookLM reports and the RAG-004 source manifest produced:

- `11` reports scanned
- `121` metadata-only chunk candidates
- `58` chunks mapped to RAG-004 source IDs
- `63` chunks still requiring source-mapping review
- `8` chunks requiring topic-mapping review because NotebookLM used narrower off-taxonomy labels
- `80` chunks with source excerpts flagged for quote review
- `0` secret-like chunk fields detected
- source excerpt text stored: `false`
- runtime retrieval disabled
- chunk import disabled

The unmapped count is expected at this stage. RAG-005 is designed to surface review work, not hide uncertain source mappings behind fuzzy guesses.

## Review Meaning

Every generated chunk remains a candidate until human review approves it.

Required review before runtime import:

- verify every source mapping against the RAG-004 manifest
- remove duplicate, vague, manipulative, unsafe, or non-compliant tactics
- confirm each chunk has a real source and useful citation metadata
- confirm the tactic is compatible with the reusable sales-agent core
- confirm campaign-specific guardrails can override or block the tactic
- review chunks flagged with `quote_review_required`

## Product Boundary

RAG-005 keeps the architecture unchanged:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + reviewed sales knowledge layer
  + explicit guardrails and human escalation paths
```

Runtime retrieval remains disabled until a later checkpoint creates a reviewed, source-tracked knowledge base and a guarded retrieval policy.
