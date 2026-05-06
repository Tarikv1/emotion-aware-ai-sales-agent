# RAG-008 Guarded Retrieval Policy

## Purpose

RAG-008 tests a guarded retrieval policy over the manually reviewed RAG-007 first slice. It creates deterministic candidate packets for review only.

This is not runtime RAG. Runtime retrieval remains disabled.

## What It Tests

- ordinary objection handling can retrieve the Yes-And response-wording rule
- broad questions can retrieve 3-2-1 and PREP response structure rules
- tone uncertainty can retrieve the voice-delivery clarification rule as advisory guidance
- refusal, do-not-call, protected script, disclosure, escalation, pressure-sensitive, and private-data contexts block retrieval

Voice and prosody candidates are included only when they are already part of the reviewed RAG-007 slice. They are advisory delivery guidance and cannot alter protected text, consent handling, compliance language, campaign facts, or human escalation.

## Commands

Run:

```powershell
python scripts\run_rag_008_guarded_retrieval_policy.py
```

Validate:

```powershell
python scripts\validate_rag_008_guarded_retrieval_policy.py
```

## Default Output

`research\experiments\generated\RAG-008-guarded-retrieval-policy\`

- `result.json`
- `report.md`

## Product Boundary

RAG-008 keeps the architecture unchanged:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + reviewed sales knowledge layer
  + explicit guardrails and human escalation paths
```

The dry-run policy uses only RAG-007 reviewed knowledge items and synthetic case prompts. It does not import chunks, auto-promote chunks, call providers, call NotebookLM, read private customer data, store source excerpt text, or connect retrieval to the runtime sales agent.

## Readiness Meaning

After RAG-008 passes, the review pipeline has a first guarded retrieval dry run. The RAG layer is still not production-ready for live agent use until a later checkpoint defines runtime gating, campaign integration, observability, fallback behavior, and human review requirements.
