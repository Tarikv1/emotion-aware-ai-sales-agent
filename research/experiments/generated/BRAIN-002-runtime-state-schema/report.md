# BRAIN-002 Runtime State Schema Report

BRAIN-002 defines the runtime state schema for the sales-agent brain.
This is a schema checkpoint only: no runtime behavior changed, no provider calls were made, and retrieval disabled by default remains the rule.

## Summary

- Turn examples: `6`
- Sale-ready examples: `1`
- Non-sale correctness examples: `5`
- Hard failures: `0`
- Retrieval default: `disabled`

## State Layers

- `buyer_state`: conversation_stage, interest_state, objection_type, emotional_signal, emotion_confidence, buyer_goal, risk_level, evidence_refs
- `strategy`: selected_move, reason_code, primary_goal, next_best_action, tactic_stack_count
- `safety`: blocked_actions, escalation_needed, escalation_reason, claim_boundary, protected_text_required, hard_failure
- `call_control`: decision, reason_code, terminal, next_action
- `retrieval`: enabled, status, registry_id, latency_budget_ms, influence_allowed, blocked_reason
- `voice`: language, delivery_profile_id, pacing_profile, protected_text_lock, provider_live_enabled
- `response`: final_response, response_language, sale_ready, non_sale_correct, outcome_reason, output_contract_version
- `evidence_log`: state_source, stores_raw_transcript_text, stores_private_audio, logs_selected_strategy, logs_safety_reason, stores_provider_payload

## Call Control

Allowed values: `continue-call, bridge-then-continue, transfer-or-escalate, end-call, schedule-and-end, close-and-log-sale-ready`

`close-and-log-sale-ready` is the full-sale close value. It can only appear when the response packet has `sale_ready=true`, no hard failure, and the campaign close criteria are satisfied.

## Boundaries

- Retrieval disabled by default.
- RAG-020/RAG-021 remain advisory until a separate registry rebuild and guarded evaluation.
- Voice profile is delivery metadata, not a sales-reasoning layer.
- Non-sale correctness remains a required gate before optimizing close rate.
