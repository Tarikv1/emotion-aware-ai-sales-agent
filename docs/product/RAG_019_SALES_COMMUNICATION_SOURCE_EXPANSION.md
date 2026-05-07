# RAG-019 Sales Communication Source Expansion

## Purpose

RAG-019 adds public-source-backed sales communication guidance to the local RAG pipeline. It covers the user's requested source areas:

- cold calling
- objection handling
- closing techniques
- consultative selling
- sales psychology
- emotional intelligence in sales
- negotiation
- voice and speech delivery
- conversation design
- call-center communication
- persuasion frameworks
- storytelling for sales
- German sales communication
- real sales-call breakdowns
- ethics and compliance

## Scope

The source material is converted into project-owned paraphrased advisory rules. RAG-019 does not store raw article excerpts, copied sales scripts, copied call transcripts, private customer data, provider outputs, embeddings, or vector database records.

## Commands

Run:

```powershell
python scripts\run_rag_019_sales_communication_source_expansion.py
```

Validate:

```powershell
python scripts\validate_rag_019_sales_communication_source_expansion.py
```

## Runtime Boundary

RAG-019 does not enable runtime retrieval by itself. The accepted items become retrievable only after RAG-017 rebuilds the local runtime registry and only when guarded response generation explicitly opts in to retrieval.

The following always override RAG-019:

- refusal and do-not-call handling
- required disclosure text
- protected campaign text
- human escalation
- AI disclosure and truthful-claim requirements
- German telemarketing consent rules
- private-data and source-excerpt boundaries
