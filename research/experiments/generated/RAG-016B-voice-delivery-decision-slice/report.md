# RAG-016B Voice-Delivery Decision Slice

RAG-016B accepts the remaining voice/prosody candidates as project-owned advisory-only delivery rules. Runtime retrieval remains disabled.

## Summary

- Accepted voice-delivery items: `19`
- Speech/prosody advisory items: `10`
- Emotion-recognition delivery advisory items: `9`
- Voice-delivery remaining: `0`
- Source-mapping chunks still excluded: `58`
- Source-mapping groups still excluded: `43`
- Latent quote follow-ups still excluded: `21`
- Runtime retrieval enabled: `False`

## Accepted Advisory Rules

| Knowledge ID | Chunk ID | Rule |
| --- | --- | --- |
| `rag016b-voice-clear-open-close` | `rag005-chunk-090` | Make openings and closings clear enough that the customer can follow the turn without extra cognitive load. |
| `rag016b-voice-calm-accountability` | `rag005-chunk-092` | Use calm, accountable delivery when acknowledging an issue or next step. |
| `rag016b-voice-signpost-structure` | `rag005-chunk-093` | Use simple vocal signposting so the customer can hear when the agent is moving from context to question or next step. |
| `rag016b-voice-brand-trust-clarity` | `rag005-chunk-094` | Prefer trustworthy, plain delivery over exaggerated warmth or entertainment. |
| `rag016b-voice-pause-for-comprehension` | `rag005-chunk-096` | Use brief pauses only where they help the customer process a high-value point. |
| `rag016b-voice-spontaneous-not-scriptless` | `rag005-chunk-100` | Sound natural by varying rhythm lightly while keeping the approved message intact. |
| `rag016b-voice-listening-forward` | `rag005-chunk-102` | Use delivery that sounds attentive and forward-moving, not performatively sympathetic. |
| `rag016b-voice-emphasis-sparingly` | `rag005-chunk-103` | Emphasize only the smallest number of words needed for comprehension. |
| `rag016b-voice-question-shape` | `rag005-chunk-104` | Render genuine questions with an open, non-interrogative shape. |
| `rag016b-voice-concise-turn-taking` | `rag005-chunk-105` | Keep delivery concise enough to invite customer turn-taking. |
| `rag016b-voice-no-acoustic-certainty` | `rag005-chunk-106` | Treat acoustic signals as uncertain delivery context, not as proof of emotion, truthfulness, or buying intent. |
| `rag016b-voice-no-hidden-emotion-claims` | `rag005-chunk-107` | Use multimodal uncertainty only to lower pressure or clarify; never claim to know the customer's internal state. |
| `rag016b-voice-dataset-limits` | `rag005-chunk-108` | Treat dataset-derived speech categories as development context, not live customer labels. |
| `rag016b-voice-domain-shift-caution` | `rag005-chunk-109` | Assume speech and conversation datasets may not match live sales-call conditions. |
| `rag016b-voice-observable-only` | `rag005-chunk-111` | Respond only to observable words, silence, interruptions, and explicit preferences. |
| `rag016b-voice-low-confidence-fallback` | `rag005-chunk-112` | When affect or intent confidence is low, fall back to neutral wording and optional human escalation. |
| `rag016b-voice-consent-first-adaptation` | `rag005-chunk-113` | Adapt delivery from explicit consent, explicit preference, and campaign context before any inferred signal. |
| `rag016b-voice-prosocial-pressure-limit` | `rag005-chunk-115` | Use helpful, prosocial framing only when it preserves the customer's freedom to decline. |
| `rag016b-voice-cross-modal-humility` | `rag005-chunk-119` | Treat cross-modal signals as fallible context for delivery humility. |

## Hard Limits

- Advisory-only voice and prosody guidance.
- No hidden emotion inference.
- No protected-class or identity profiling.
- No manipulation, pressure, or urgency escalation.
- No changes to protected campaign, disclosure, refusal, or handoff text.

## Boundaries

- Runtime retrieval remains disabled until RAG-017/RAG-018 opt-in runtime integration.
- The unresolved RAG-015 source-mapping blockers and latent quote follow-ups stay excluded.
- No source excerpt text, private customer data, provider calls, or NotebookLM API calls are used.
