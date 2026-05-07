# RAG-017 Runtime Knowledge Registry

## Purpose

RAG-017 creates the runtime-eligible local registry from accepted, project-owned RAG slices only. It is a deterministic local registry, not a hosted retrieval service.

## Included

- RAG-007 reviewed first slice
- RAG-010 reviewed expansion slice
- accepted RAG-012 quote-clearance items
- accepted RAG-014 source-mapped quote follow-up items
- accepted RAG-016A ethical-persuasion items
- RAG-016B voice-delivery advisory items
- RAG-019 public-source-backed sales communication advisory items

## Excluded

- unresolved source-mapping blockers
- unresolved source-mapping groups
- latent quote-clearance follow-ups
- raw source excerpts
- copied public sales scripts or call transcripts
- private customer data

## Commands

Run:

```powershell
python scripts\run_rag_017_runtime_knowledge_registry.py
```

Validate:

```powershell
python scripts\validate_rag_017_runtime_knowledge_registry.py
```

## Runtime Boundary

The registry is opt-in only. Default runtime retrieval remains disabled, and `retrieval_used_in_runtime` must stay false in registry artifacts. Guarded response generation may use it only when explicitly called with retrieval enabled.

No external vector database, embedding provider, provider call, NotebookLM API call, or private-data read is used.
