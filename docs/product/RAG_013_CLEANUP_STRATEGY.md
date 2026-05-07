# RAG-013 Cleanup Strategy

## Purpose

`RAG-013` partitions the remaining RAG cleanup work after `RAG-012`.

It is a strategy packet only. Runtime retrieval remains disabled.

## What It Produces

The strategy packet identifies:

- the five quote follow-ups created by accepted source mappings in `RAG-012`
- the remaining source-mapping chunks and source-title review batches
- the remaining original quote-clearance chunks grouped by review lane
- the recommended checkpoint order before any runtime integration work

It does not mutate `RAG-009`, `RAG-011`, or `RAG-012`.

## Commands

Run the cleanup strategy builder:

```powershell
python scripts\run_rag_013_cleanup_strategy.py
```

Validate the checkpoint:

```powershell
python scripts\validate_rag_013_cleanup_strategy.py
```

## Default Output

```text
research\experiments\generated\RAG-013-cleanup-strategy\
```

The default files are:

- `result.json`
- `report.md`

## Current Official Run

The official RAG-013 run reports:

- remaining source-mapping chunks: `58`
- remaining source-mapping groups: `43`
- remaining original quote-clearance chunks: `30`
- quote follow-ups from accepted source mappings: `5`
- known cleanup work count before runtime is `93`
- recommended next checkpoint: `RAG-014-source-mapped-quote-followup`

The strategy also reports latent quote-follow-up work behind remaining source-mapping chunks. Those are not counted as active quote-clearance rows until source metadata is reviewed.

## Recommended Cleanup Order

1. `RAG-014-source-mapped-quote-followup`: clear or reject the `5` quote follow-ups created by RAG-012 accepted source mappings.
2. `RAG-015-source-mapping-batches`: batch remaining source-title mapping review, starting with larger groups.
3. `RAG-016-quote-clearance-batches`: rewrite or reject remaining quote-dependent chunks by lane.
4. `RAG-017-clean-candidate-reaudit`: re-audit clean candidates before any runtime-off retrieval harness.

## Product Boundary

`RAG-013` does not:

- enable runtime retrieval
- import chunks into runtime memory
- build embeddings
- query a vector database
- call NotebookLM or another provider
- read private customer data
- store source excerpt text
- auto-promote chunks
- resolve blockers by itself

A later runtime integration gate is required before any reviewed RAG knowledge can affect the live sales agent.
