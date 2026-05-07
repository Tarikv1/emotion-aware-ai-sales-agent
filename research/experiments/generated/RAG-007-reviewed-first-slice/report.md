# RAG-007 Reviewed First Slice

RAG-007 creates a manually reviewed, paraphrased first knowledge slice. Runtime retrieval remains disabled.

## Summary

- Selected chunks: `9`
- Knowledge items: `9`
- Response wording items: `5`
- Voice delivery items: `4`
- Auto-promoted chunks: `0`
- Selected from RAG-006 first-slice queue: `4`
- Selected from RAG-006 quote queue after manual clearance: `9`
- Manual quote clearances: `9`
- Runtime retrieval enabled: `False`
- Retrieval eligible now: `False`
- Chunk import enabled: `False`
- Source metadata final: `False`

## Response wording

| Knowledge ID | Source Chunk | Rule |
| --- | --- | --- |
| `rag007-response-yes-and-objection-framing` | `rag005-chunk-017` | Acknowledge the customer's concern before moving to a useful next step; do not use agreement language to blur factual or compliance boundaries. |
| `rag007-response-declarative-clarity` | `rag005-chunk-020` | Use short declarative statements when clarity matters, especially after an objection or broad question. |
| `rag007-response-empathy-echo` | `rag005-chunk-022` | Reflect a customer's key concern or emotional phrase sparingly before responding, so the reply shows listening without mechanical repetition. |
| `rag007-response-prep-structure` | `rag005-chunk-024` | For a persuasive explanation, state the point, give the reason, add one concrete example, and return to the point. |
| `rag007-response-3-2-1-structure` | `rag005-chunk-025` | When an answer could sprawl, constrain it into a small numbered structure such as three points, two options, or one key takeaway. |

## Voice delivery

| Knowledge ID | Source Chunk | Rule |
| --- | --- | --- |
| `rag007-voice-yes-and-posture` | `rag005-chunk-091` | Use a non-defensive delivery posture when acknowledging objections; the voice should sound constructive rather than argumentative. |
| `rag007-voice-tone-mismatch-uncertainty` | `rag005-chunk-098` | If words and vocal delivery appear misaligned, treat that as uncertainty and ask a gentle clarification instead of assuming hidden emotion or intent. |
| `rag007-voice-trustworthy-not-forced-friendly` | `rag005-chunk-099` | Prefer a trustworthy, straightforward, moderately warm delivery over forced friendliness or entertainment. |
| `rag007-voice-bounded-vocal-toolbox` | `rag005-chunk-101` | Use controlled variation in pace, pitch, volume, warmth, and silence to support clarity and engagement. |

## Review Rules

- All items are project-owned paraphrases.
- Quote-queue items require manual clearance and keep source excerpt text out of the artifact.
- Quote-dependent source text is not copied forward.
- Campaign guardrails, customer refusal, compliance text, and human escalation override every item.
- Tone mismatch is treated as uncertainty that can justify a gentle clarification, not as a certain hidden state.

## Boundaries

- Runtime retrieval remains disabled.
- Chunk import remains disabled.
- No provider or NotebookLM API calls are made.
- No private customer inputs are used.
