# RAG-016B Voice-Delivery Decision Slice

## Purpose

RAG-016B accepts the remaining RAG-016A voice/prosody candidates as project-owned advisory-only behavior rules. It does not re-review source documents and does not enable runtime retrieval by itself.

## Scope

- accepts 19 remaining voice-delivery quote-clearance candidates
- keeps source-mapping blockers and latent quote follow-ups out of runtime retrieval
- stores project-owned paraphrases, not source excerpts
- keeps runtime retrieval disabled until the RAG-017/RAG-018 registry and guarded integration path

## Hard Limits

- no hidden emotion inference
- no protected-trait or identity profiling
- no manipulation, pressure, or urgency escalation
- no changes to protected campaign, disclosure, refusal, or human-handoff text

## Commands

Run:

```powershell
python scripts\run_rag_016b_voice_delivery_decision_slice.py
```

Validate:

```powershell
python scripts\validate_rag_016b_voice_delivery_decision_slice.py
```

## Default Output

`research\experiments\generated\RAG-016B-voice-delivery-decision-slice\`

- `result.json`
- `report.md`

## Boundary

This is an acceptance and cleanup artifact only. Runtime retrieval, provider calls, embedding jobs, private data reads, chunk import, and source excerpt storage remain disabled.
