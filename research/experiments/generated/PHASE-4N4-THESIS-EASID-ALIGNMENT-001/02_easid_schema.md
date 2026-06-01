# EASID Schema

## Purpose

EASID records emotion-aware sales interaction data at the turn level. The schema should preserve enough structure to analyze buyer state, emotion cues, persuasion choices, outcomes, latency, and safety without depending on public storage of private raw audio.

## Turn-Level Tabular Schema

| Field | Type | Description |
| --- | --- | --- |
| conversation_id | string | Stable synthetic or sanitized conversation id. |
| turn_id | integer | Turn index within a conversation. |
| agent_variant | string | Generic baseline, Atlas structured agent, or future emotion-aware variant. |
| campaign_id | string | Campaign or sales package identifier. |
| vertical | string | Business vertical, such as restaurant or plumber. |
| buyer_persona | string | Scenario persona used for evaluation. |
| buyer_turn_text | string | Synthetic or sanitized buyer utterance. |
| agent_response_text | string | Synthetic or sanitized agent response. |
| buyer_state_label | enum | Buyer state label from the taxonomy. |
| emotion_label | enum | Emotion label from the emotion taxonomy. |
| emotion_confidence | number/null | Confidence only if produced by a real annotation/model process. |
| sentiment_score | number/null | Optional sentiment score. |
| acoustic_features_available | boolean | Whether audio/prosody features are available. |
| pitch_mean | number/null | Optional pitch mean if audio is available. |
| pitch_range | number/null | Optional pitch range if audio is available. |
| speech_rate | number/null | Optional words or syllables per minute. |
| pause_count | integer/null | Optional pause count. |
| interruption_count | integer/null | Optional interruption count. |
| text_emotion_cues | array[string] | Text markers supporting the emotion label. |
| objection_type | string/null | Objection category, if present. |
| persuasion_strategy | string/null | Ethical persuasion strategy selected by the agent. |
| sales_stage | string | Opening, diagnosis, objection handling, close, follow-up, disqualification, or stop. |
| recommended_next_action | string/null | Next action suggested by the agent or evaluator. |
| micro_close_attempted | boolean | Whether the agent attempted a small next-step close. |
| micro_close_outcome | string/null | Accepted, deferred, rejected, not_applicable, or stopped. |
| outcome_label | string | Conversation or turn outcome label. |
| hard_failure_flags | array[string] | 4N3 hard failure flags, if any. |
| safety_flags | array[string] | Safety/compliance flags, if any. |
| latency_ms | integer/null | Response latency if measured. |
| evaluator_scores | object | Manual rubric scores keyed by dimension. |
| privacy_redaction_status | string | synthetic_sanitized, sanitized, or restricted_private. |
| raw_audio_stored | boolean | Whether raw audio is stored in private restricted storage. |
| raw_transcript_stored | boolean | Whether raw transcript is stored in private restricted storage. |
| notes | string | Reviewer notes without private raw data. |

## Privacy Rules

- public evidence must not store raw private audio
- raw private transcript/audio should be avoided or stored only in private restricted storage if needed
- public EASID examples must be synthetic/sanitized
- public artifacts should keep buyer_turn_text and agent_response_text synthetic or sanitized
- any future private data export needs a separate compliance and consent review

## JSON Object Shape

Each JSONL row should contain all schema fields. Optional numeric fields should use `null` when no measured data exists. Do not fill missing measurements with invented values.
