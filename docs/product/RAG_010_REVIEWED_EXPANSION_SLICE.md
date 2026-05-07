# RAG-010 Reviewed Expansion Slice

## Purpose

RAG-010 manually reviews the four clean RAG-009 next-promotion candidates and promotes them into a second reviewed RAG artifact.

It expands the reviewed knowledge slice with bounded consultative discovery guidance, but it does not enable runtime retrieval.

## What It Produces

- three response-wording rules for impact discovery, respectful impact clarification, and real timing checks
- one voice-delivery rule for treating speech cadence as a weak context cue
- source IDs, source titles, topic IDs, and project-owned paraphrases
- no source excerpt text
- no runtime-eligible chunks

## Commands

Run:

```powershell
python scripts\run_rag_010_reviewed_expansion_slice.py
```

Validate:

```powershell
python scripts\validate_rag_010_reviewed_expansion_slice.py
```

## Default Output

`research\experiments\generated\RAG-010-reviewed-expansion-slice\`

- `result.json`
- `report.md`

## Reviewed Candidates

| Chunk ID | Decision | Product rewrite |
| --- | --- | --- |
| `rag005-chunk-029` | promote as response wording | Ask a neutral business-impact question without inventing PR, retention, executive, or financial risk. |
| `rag005-chunk-030` | promote as response wording | Use one respectful impact clarifier when the customer gives a vague or operational problem. |
| `rag005-chunk-031` | promote as response wording | Ask about real timing or decision windows without creating urgency or scarcity. |
| `rag005-chunk-036` | promote as voice delivery | Treat speech cadence as weak delivery context only; never infer hidden emotion, intent, consent, refusal, urgency, or truthfulness from cadence alone. |

## Product Boundary

RAG-010 keeps the architecture unchanged:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + reviewed sales knowledge layer
  + explicit guardrails and human escalation paths
```

Runtime retrieval remains disabled. Chunk import remains disabled. No chunks are auto-promoted. No embedding job, vector database, LLM reranker, provider call, NotebookLM API call, private customer data, or source excerpt text is used.

The cadence item is advisory voice/prosody guidance only. It may guide pacing or a gentle check-in in a later reviewed system, but it cannot diagnose customer emotion or override explicit customer words.

## Readiness Meaning

After RAG-010 passes, the reviewed slice has four more manually accepted, project-owned paraphrased items. This is still review infrastructure, not runtime retrieval readiness.

The next RAG step should decide whether to build a runtime-off integration harness or first resolve more RAG-009 source-mapping and quote-clearance blocks.
