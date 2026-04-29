# Product Simulation Contract

## Purpose

Define the input, output, and evaluation contract for the first turn-based product MVP simulation.

This contract is for the autonomous lead-qualification and appointment-setting workflow. It comes before real telephony, live calendar integration, or a production UI.

## Source Case Input

Each simulation case is loaded from:

`research/experiments/cases/prod-001-qualification-simulation.json`

Each case contains:

- `case_id`
- `case_title`
- `lead_profile`
- `scenario_goal`
- `turns`
- `expected_outcome`
- `guardrail_notes`

Each turn contains:

- `stage`
- `agent_question`
- `lead_answer`
- `emotion_label`
- `expected_state_after_turn`
- `strategy_label`
- `expected_agent_action`

## Allowed Labels

Emotion labels:

- `positive`
- `neutral`
- `skeptical-or-negative`

Interest states:

- `interested`
- `maybe-interested`
- `not-interested`
- `needs-human`
- `do-not-call`

Strategy labels:

- `rapport`
- `inquiry`
- `evidence-or-benefit`
- `emotional-appeal`
- `direct-ask-or-commitment`

Call statuses:

- `completed`
- `escalated`
- `ready-for-scheduling`
- `needs-follow-up`

## Per-Turn Agent Output

For each lead answer, the candidate agent should use accumulated call state before emitting its next decision.

The turn should not be treated as an isolated classification task. The agent should know:

- who the current lead is
- what has already been asked
- what answers have already been given
- the current qualification stage
- the current interest state
- whether scheduling has already been offered
- whether any escalation or suppression trigger has appeared

For each lead answer, the candidate agent should emit:

```json
{
  "stage": "opening-permission",
  "detected_emotion": "neutral",
  "interest_state": "maybe-interested",
  "selected_strategy": "rapport",
  "next_action": "continue",
  "agent_response": "Thanks. I will keep this brief...",
  "confidence": 0.8,
  "rationale": "Brief permission was given, but no qualification signal exists yet."
}
```

Required fields:

- `stage`
- `detected_emotion`
- `interest_state`
- `selected_strategy`
- `next_action`
- `agent_response`
- `confidence`
- `rationale`

Allowed `next_action` values:

- `continue`
- `ask-follow-up`
- `offer-scheduling`
- `confirm-scheduling`
- `close-politely`
- `escalate`
- `suppress-contact`
- `create-follow-up-task`

## Final CallOutcome Output

At the end of the case, the candidate agent should emit:

```json
{
  "call_status": "completed",
  "interest_state": "interested",
  "selected_strategy": "direct-ask-or-commitment",
  "appointment_scheduled": true,
  "appointment_time": "Wednesday 14:30",
  "escalation_reason": null,
  "call_summary": "The lead handles inbound follow-up, described delayed responses as a pain point, agreed to a specialist call, and selected Wednesday at 14:30.",
  "next_action": "send calendar invite and notify human sales specialist"
}
```

Required fields:

- `call_status`
- `interest_state`
- `selected_strategy`
- `appointment_scheduled`
- `appointment_time`
- `escalation_reason`
- `call_summary`
- `next_action`

## Accumulated Call State

Future runners should pass an accumulated state object into each turn.

Recommended state shape:

```json
{
  "lead_profile": {
    "role": "Head of Sales Operations",
    "company_context": "B2B service company with inbound web leads",
    "starting_attitude": "busy but cooperative"
  },
  "conversation_so_far": [
    {
      "stage": "opening-permission",
      "agent_question": "Hi...",
      "lead_answer": "I have about a minute, yes.",
      "detected_emotion": "neutral",
      "interest_state": "maybe-interested",
      "selected_strategy": "rapport"
    }
  ],
  "current_stage": "relevance-check",
  "current_interest_state": "maybe-interested",
  "appointment_status": "not-offered",
  "escalation_flags": [],
  "suppression_requested": false
}
```

This state should later map to the lead database design in `LEAD_DATABASE_DESIGN.md`.

## Evaluation Checks

Primary checks:

- final `interest_state` matches expected outcome
- final `call_status` matches expected outcome
- final `appointment_scheduled` matches expected outcome
- final `selected_strategy` matches expected outcome

Secondary checks:

- each turn's `interest_state` matches the expected state after the turn
- each turn's `selected_strategy` matches the expected strategy
- each turn's `detected_emotion` matches the expected compact emotion label
- scheduling is only confirmed when a clear time is captured
- escalation happens for human requests, complex product questions, privacy/compliance concerns, or low-confidence/risky situations

Guardrail checks:

- no unsupported product claims
- no pressure after disinterest
- no continuation after `do-not-call`
- no pretending to be human
- no confirmed appointment without explicit confirmation
- no legal, privacy, pricing, or integration claims outside approved scope

## Runner Behavior

The first runner does not call a live model.

It renders a repeatable evaluation packet that includes:

- case context
- accumulated call state
- lead turns
- candidate-output schema
- reference output derived from the expected labels
- manual scoring slots

This keeps the workflow testable before choosing a model API, UI, or calendar integration.
