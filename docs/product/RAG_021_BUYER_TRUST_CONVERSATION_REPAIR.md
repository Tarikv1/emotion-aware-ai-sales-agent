# RAG-021 Buyer Trust Conversation Repair

RAG-021 adds a second deeper public-source-backed pack for buyer value mapping, trust repair, autonomy-safe persuasion, clarity, conversation repair, emotion regulation support, implementation-intention next steps, and AI transparency.

It complements RAG-020. It does not overwrite RAG-020 and does not change RAG-018 runtime behavior by itself.

## Scope

- B2B value mapping: identify the buyer's value dimension before pitching.
- Trust repair: answer ability, benevolence, and integrity gaps differently.
- Autonomy and reactance: avoid controlling language and preserve real choice.
- Cognitive load and clarity: reduce decision complexity and use plain language.
- Conversation repair: invite correction before answering an assumed concern.
- Emotion regulation support: slow down, reframe, and repair without diagnosing emotion.
- Action commitment design: turn accepted next steps into specific plans without coercion.
- AI transparency and handoff: disclose capability limits and route risky contexts to a human.

## Run

```powershell
python scripts\run_rag_021_buyer_trust_conversation_repair.py
```

Default output folder:

```text
research\experiments\generated\RAG-021-buyer-trust-conversation-repair\
```

Validate:

```powershell
python scripts\validate_rag_021_buyer_trust_conversation_repair.py
```

## Runtime Boundary

RAG-021 is advisory-only in this pass. The generated rules are not imported into the RAG-017 runtime knowledge registry yet.

Runtime use requires a separate registry rebuild and RAG-018 guarded-retrieval evaluation. Compliance, refusal, protected text, and human escalation override every RAG-021 rule.

## Source Boundary

The case file stores URLs, source metadata, and project-owned paraphrases only. It does not store source excerpts, copied scripts, call transcripts, private customer data, embeddings, provider outputs, or vector database records.
