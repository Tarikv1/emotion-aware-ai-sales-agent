# RAG-012 Accepted Cleanup

## Purpose

`RAG-012` records the human-accepted cleanup decisions from the `RAG-011` blocker cleanup packet.

It creates `17 accepted cleanup decisions`:

- `5` accepted source-mapping chunk decisions from `3` source proposal groups.
- `12` accepted quote-clearance rewrites as project-owned paraphrases.

Runtime retrieval remains disabled.

## What It Produces

`RAG-012` creates a new review artifact only. It does not rewrite older RAG outputs.

The artifact contains:

- accepted source IDs for the five source-mapping chunks
- project-owned rewrite rules for the twelve quote-clearance cards
- explicit follow-up flags for accepted source mappings that still need quote clearance
- remaining blocker counts after the accepted cleanup slice
- runtime, provider, private-data, and source-excerpt boundaries

## Commands

Run the accepted cleanup artifact builder:

```powershell
python scripts\run_rag_012_accepted_cleanup.py
```

Validate the checkpoint:

```powershell
python scripts\validate_rag_012_accepted_cleanup.py
```

## Default Output

```text
research\experiments\generated\RAG-012-accepted-cleanup\
```

The default files are:

- `result.json`
- `report.md`

## Current Official Run

The official `RAG-012` run accepts:

- `5` source-mapping chunk decisions
- `12` quote-clearance rewrite decisions
- `17` cleanup decisions total

After acceptance:

- source-mapping blockers move from `63` to `58`
- the original quote-clearance blocker queue moves from `42` to `30`
- `5` accepted source-mapping chunks still require quote-clearance follow-up before any future promotion
- older artifacts record `0` blockers resolved because they are not mutated

## Cleanup Rules

- Source mappings are metadata cleanup only.
- Accepted source mappings do not automatically clear quote dependencies.
- Quote-clearance cards become project-owned paraphrases or they stay blocked.
- Voice/prosody items are advisory delivery guidance only.
- Persuasion items must stay low-pressure, consent-preserving, and campaign-fact-bound.
- Anti-manipulation guardrails override conversion goals.

## Product Boundary

`RAG-012` is not runtime retrieval.

It does not:

- import chunks into runtime memory
- build embeddings
- query a vector database
- call NotebookLM or another provider
- read private customer data
- store source excerpt text
- auto-promote chunks

A later runtime integration gate is required before any reviewed RAG knowledge can affect the live sales agent.
