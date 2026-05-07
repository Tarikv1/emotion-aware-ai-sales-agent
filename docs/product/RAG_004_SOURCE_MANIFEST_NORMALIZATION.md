# RAG-004 Source Manifest Normalization

## Purpose

RAG-004 turns the source-title references inside imported NotebookLM reports into stable local source-ID candidates.

This is the bridge between NotebookLM report artifacts and a source-tracked RAG knowledge base.

## What It Produces

- stable source IDs such as `rag004-source-001`
- canonical source titles
- raw title aliases found in reports
- topic links inferred from the report file
- report paths where each source appeared
- source type and language guesses
- review fields for URL, author/channel, source type, language, rights status, and metadata status

## What It Does Not Do

- it does not call NotebookLM
- it does not call an LLM, TTS provider, ASR provider, or external API
- it does not import RAG chunks
- it does not enable retrieval
- it does not store raw source text
- it does not make the sales agent use any extracted tactic

## Commands

Run source manifest normalization against the default RAG-002 imports folder:

```powershell
python scripts\run_rag_004_source_manifest_normalization.py
```

Validate the RAG-004 scanner and runner contract:

```powershell
python scripts\validate_rag_004_source_manifest_normalization.py
```

## Default Output

```text
research\experiments\generated\RAG-004-source-manifest-normalization\
```

The output contains:

- `result.json`
- `report.md`

## Current Manifest Run

The 2026-05-06 run against Tarik's imported NotebookLM reports produced:

- `11` reports scanned
- `95` source candidates
- `0` source candidates without topic links
- `0` secret-like source titles
- `95` source candidates still missing review metadata
- runtime retrieval disabled
- chunk import disabled

The source count is intentionally a candidate count, not a final bibliography count. Human review must merge duplicates, delete false positives, and fill URL/author/source-type/rights metadata before chunk normalization.

## Review Meaning

Every generated source is a candidate until human review fills the missing metadata and removes false positives.

Required review fields before chunk import:

- URL or durable citation location
- author, creator, publisher, or channel
- source type
- language
- rights/licensing status
- thesis citation note
- topic assignment

## Product Boundary

RAG-004 keeps the product architecture unchanged:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + reviewed sales knowledge layer
  + explicit guardrails and human escalation paths
```

The manifest is metadata-only source tracking. It is not runtime behavior.
