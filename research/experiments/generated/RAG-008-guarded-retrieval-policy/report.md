# RAG-008 Guarded Retrieval Policy

RAG-008 creates a dry-run retrieval packet over the RAG-017 runtime knowledge registry. Runtime retrieval remains disabled.

## Summary

- Query cases: `8`
- Retrieved cases: `3`
- Blocked cases: `5`
- Retrieved item packets: `9`
- Runtime retrieval enabled by default: `False`
- Retrieval used in runtime: `False`
- Chunk import enabled: `False`
- Only runtime registry used: `True`

## Retrieved Cases

| Case | Retrieved Knowledge |
| --- | --- |
| `ordinary_objection_yes_and` | `rag007-response-yes-and-objection-framing`, `rag010-response-real-timing-check`, `rag016a-response-autonomy-reminder` |
| `broad_question_structure` | `rag007-response-3-2-1-structure`, `rag016a-response-concise-benefit-set`, `rag007-response-prep-structure` |
| `tone_uncertainty_clarification` | `rag007-voice-tone-mismatch-uncertainty`, `rag010-voice-cadence-as-weak-context`, `rag016b-voice-no-acoustic-certainty` |

## Blocked Cases

| Case | Block Reason |
| --- | --- |
| `customer_refusal_blocks` | `customer_refusal_overrides_retrieval` |
| `protected_script_blocks` | `protected_script_text_must_not_change` |
| `human_escalation_blocks` | `human_escalation_overrides_retrieval` |
| `pressure_sensitive_blocks` | `pressure_sensitive_context_blocks_style_retrieval` |
| `private_data_request_blocks` | `private_data_request_blocks_retrieval` |

## Boundaries

- Runtime retrieval remains disabled.
- Candidate packets are not used by the runtime sales agent.
- Chunk import remains disabled.
- Voice-delivery items are advisory only.
- No provider or NotebookLM API calls are made.
- No private customer inputs are used.
- No source excerpt text is stored.
