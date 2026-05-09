# BRAIN-002 Runtime State Schema

Status: schema checkpoint. This document does not change live runtime behavior.

BRAIN-002 turns the BRAIN-001 architecture into the compact packet every sales-agent turn should produce before speaking, logging, retrieval influence, or voice delivery.

## Goal

Make the project converge around one auditable sales-agent loop:

```text
SalesCampaign
  -> short-term buyer state
  -> strategy
  -> safety
  -> call control
  -> retrieval status
  -> voice delivery profile
  -> response contract
  -> evidence log
```

This is the bridge between isolated RAG, voice, product, and full-sale experiments. Future simulations should score this packet, not just the final wording.

## Runtime Responsibility

The live agent core owns:

- compact buyer-state update from observable call behavior
- one selected sales move per turn
- safety and claim-boundary checks
- call-control decision
- response packet
- evidence fields for later scoring

The live agent core does not own:

- broad research lookup
- slow multi-agent review
- CRM enrichment
- post-call learning
- private-data pattern mining
- provider voice generation

Those can happen in separate tools, background tasks, review gates, or post-call workflows.

## State Packet

Every runtime turn should produce these layers.

| Layer | Required fields | Purpose |
| --- | --- | --- |
| `buyer_state` | `conversation_stage`, `interest_state`, `objection_type`, `emotional_signal`, `emotion_confidence`, `buyer_goal`, `risk_level`, `evidence_refs` | Track observable state without pretending to know hidden emotion. |
| `strategy` | `selected_move`, `reason_code`, `primary_goal`, `next_best_action`, `tactic_stack_count` | Pick one primary move so the agent does not stack pressure tactics. |
| `safety` | `blocked_actions`, `escalation_needed`, `escalation_reason`, `claim_boundary`, `protected_text_required`, `hard_failure` | Block unsafe closes, unsupported claims, and pressure behavior. |
| `call_control` | `decision`, `reason_code`, `terminal`, `next_action` | Decide whether to continue, bridge, transfer, end, schedule, or close. |
| `retrieval` | `enabled`, `status`, `registry_id`, `latency_budget_ms`, `influence_allowed`, `blocked_reason` | Keep retrieval explicit, measured, and disabled by default. |
| `voice` | `language`, `delivery_profile_id`, `pacing_profile`, `protected_text_lock`, `provider_live_enabled` | Carry delivery intent without turning voice into sales reasoning. |
| `response` | `final_response`, `response_language`, `sale_ready`, `non_sale_correct`, `outcome_reason`, `output_contract_version` | Bind the spoken answer to product outcomes and scoring. |
| `evidence_log` | `state_source`, `stores_raw_transcript_text`, `stores_private_audio`, `logs_selected_strategy`, `logs_safety_reason`, `stores_provider_payload` | Preserve auditability without storing sensitive bodies by default. |

## Call-Control Values

BRAIN-002 extends the existing call-control set with the full-sale close value.

- `continue-call`: continue normal discovery, clarification, or objection handling.
- `bridge-then-continue`: say a short bridge while slower approved lookup runs.
- `transfer-or-escalate`: route to a human or specialist path.
- `end-call`: close politely and stop the call.
- `schedule-and-end`: confirm an approved appointment or callback and stop.
- `close-and-log-sale-ready`: confirm a campaign-approved verbal commitment and log `sale_ready=true`.

`close-and-log-sale-ready` is allowed only when:

- the campaign close criteria are satisfied
- the buyer is eligible and interested
- required disclosure is satisfied
- compatibility or fit is not open
- no hard failure is present
- no payment, checkout, contract, or unsupported claim is required

## Retrieval Boundary

Retrieval remains disabled by default.

Allowed BRAIN-002 states:

- `disabled_by_default`
- `blocked_by_guardrail`

Future states such as `used_in_runtime` require a separate RAG-017 registry rebuild and RAG-018 guarded-retrieval evaluation. BRAIN-002 does not promote RAG-020 or RAG-021 into runtime.

## Voice Boundary

Voice is delivery metadata only:

- language
- delivery profile
- pacing profile
- protected-text lock
- live-provider flag

The voice layer must not choose the sales strategy, infer hidden emotion, rewrite protected text, or make a live provider call by default.

## Non-Sale Correctness

The state schema makes non-sale outcomes first-class.

The agent should log `non_sale_correct=true` when it correctly refuses to close because the right action is:

- clarify fit before closing
- transfer to support
- repair trust before continuing
- escalate to a human
- end after refusal or do-not-call

This must stay strong before optimizing close rate.

## Evidence Boundary

Default evidence logs store state references and outcome reasons, not transcript bodies, private audio, provider payloads, payment data, or customer identifiers.

The packet may later reference a secure call record by ID after a separate data-governance design, but BRAIN-002 does not introduce that storage.

## Current Implementation

`BRAIN-002` provides:

- `research/experiments/cases/brain-002-runtime-state-schema.json`
- `scripts/brain_runtime_state_schema.py`
- `scripts/run_brain_002_runtime_state_schema.py`
- `scripts/validate_brain_002_runtime_state_schema.py`
- generated JSON and Markdown report under `research/experiments/generated/BRAIN-002-runtime-state-schema/`

The generated packet uses synthetic SD-card/full-sale examples from the PROD-006 direction. It makes no provider calls, reads no private data, changes no runtime behavior, and keeps retrieval disabled by default.

## Current Use

`PROD-007` implemented the first fixture-scored full-call gauntlet:

```text
old core
  vs
BRAIN-002 packet + full-sale/RAG candidate
```

The gauntlet scores `safe_close_rate`, `hard_failure_rate`, `non_sale_correctness`, close quality, call-control correctness, retrieval status, and latency readiness.

`PROD-008` generates one BRAIN-002 state packet from each fixed call turn instead of reading fixture-scored packet answers.

`PROD-009` expands that generated packet path across retail product, telecom, B2B software, insurance service, medical equipment, home service, membership service, and automotive service calls while preserving hard failure rate `0.0`, non-sale correctness `1.0`, state packet completeness `1.0`, and retrieval disabled by default.

`PROD-010` adds harder universal objections and longer calls by carrying turn position, total turn count, and the call-level objection stack through every generated BRAIN-002 packet. It also scores objection boundary correctness and long-call state continuity.

`PROD-011` hardens the dialogue-policy layer over the PROD-010 packet evidence. It scores policy action correctness, blocked action avoidance, objection stack preservation, and state-reference completeness while keeping retrieval disabled by default and live runtime behavior unchanged.

The next use should test live-shaped transcripts or simulations against the hardened policy before any runtime promotion.
