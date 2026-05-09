# RAG-020 Sales Persuasion Emotion Deep Dive

RAG-020 adds a deeper public-source-backed pack for sales strategy, ethical persuasion, buyer confidence, and emotion understanding limits.

It complements RAG-019. It does not overwrite RAG-019 and does not change the RAG-018 runtime behavior by itself.

## Scope

- Insight-led sales: teach a useful reframing before pitching.
- Behavior-change design: diagnose ability, motivation, and context before asking for a larger step.
- Autonomy-supportive persuasion: use open questions, reflections, summaries, and buyer-stated reasons.
- Buyer confidence: reduce confusion with clear tradeoffs and evidence.
- Negotiation readiness: compare options and no-deal alternatives transparently.
- Emotion understanding limits: treat affect signals as uncertain context, not hidden-state proof.
- Deescalation: repair confusion or frustration before persuading.
- AI risk and compliance: block unvalidated emotion classifiers, biometric emotion recognition, deceptive synthetic voice use, and unsupported AI claims.

## Run

```powershell
python scripts\run_rag_020_sales_persuasion_emotion_deep_dive.py
```

Default output folder:

```text
research\experiments\generated\RAG-020-sales-persuasion-emotion-deep-dive\
```

Validate:

```powershell
python scripts\validate_rag_020_sales_persuasion_emotion_deep_dive.py
```

## Runtime Boundary

RAG-020 is advisory-only in this pass. The generated rules are not imported into the RAG-017 runtime knowledge registry yet.

Runtime use requires a separate registry rebuild and RAG-018 guarded-retrieval evaluation. Compliance, refusal, protected text, and human escalation override every RAG-020 rule.

## Source Boundary

The case file stores URLs, source metadata, and project-owned paraphrases only. It does not store source excerpts, copied scripts, call transcripts, private customer data, embeddings, provider outputs, or vector database records.
