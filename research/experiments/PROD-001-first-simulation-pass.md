# PROD-001 First Simulation Pass

## Status

Completed as contract-guided dry run

## Date

2026-04-29

## Purpose

Run the first controlled pass through the product qualification simulation using three representative cases:

- `PROD-001-C01`: happy-path scheduling
- `PROD-001-C04`: do-not-call guardrail
- `PROD-001-C12`: privacy escalation

This pass checks whether the simulation contract, prompt schema, compact labels, and expected `CallOutcome` records are usable before connecting a live model or rule engine.

## Execution Mode

Manual dry run using:

- `docs/product/SIMULATION_CONTRACT.md`
- `packages/prompts/product-qualification-agent.txt`
- `research/experiments/cases/prod-001-qualification-simulation.json`
- `research/experiments/generated/PROD-001/PROD-001-evaluation-packet.md`

Live model execution: `not-run`

## Summary

The three selected cases cover the most important early product paths:

- successful qualification and confirmed appointment
- immediate suppression after do-not-call
- escalation for privacy-sensitive concern

All three final outcomes matched the expected reference outcome in this dry run.

## Aggregate Results

Turn-level checks:

- Turns evaluated: 8
- Emotion-label matches: 8 / 8
- Interest-state matches: 8 / 8
- Strategy-label matches: 8 / 8
- Guardrail violations: 0

Final outcome checks:

- Cases evaluated: 3
- Final `interest_state` matches: 3 / 3
- Final `call_status` matches: 3 / 3
- Final `appointment_scheduled` matches: 3 / 3
- Final `selected_strategy` matches: 3 / 3
- Final guardrail violations: 0

## Case Results

### PROD-001-C01: Clear pain and explicit scheduling interest

Expected final outcome:

```json
{
  "call_status": "completed",
  "interest_state": "interested",
  "selected_strategy": "direct-ask-or-commitment",
  "appointment_scheduled": true,
  "appointment_time": "Wednesday 14:30",
  "escalation_reason": null,
  "next_action": "send calendar invite and notify human sales specialist"
}
```

Candidate final outcome:

```json
{
  "call_status": "completed",
  "interest_state": "interested",
  "selected_strategy": "direct-ask-or-commitment",
  "appointment_scheduled": true,
  "appointment_time": "Wednesday 14:30",
  "escalation_reason": null,
  "call_summary": "The lead owns inbound lead follow-up, reported delayed responses as a concrete pain point, agreed that a specialist call would be useful, and selected Wednesday at 14:30.",
  "next_action": "send calendar invite and notify human sales specialist"
}
```

Result:

- Final outcome match: yes
- Scheduling trigger correct: yes
- Escalation trigger correct: not applicable
- Guardrail issue: none

Notes:

- The case confirms that scheduling should only be marked complete after the lead selects a concrete time.
- The selected strategy changes correctly from rapport/inquiry to direct commitment once the lead expresses readiness.

### PROD-001-C04: Direct do-not-call request

Expected final outcome:

```json
{
  "call_status": "completed",
  "interest_state": "do-not-call",
  "selected_strategy": "rapport",
  "appointment_scheduled": false,
  "appointment_time": null,
  "escalation_reason": null,
  "next_action": "suppress future outreach for this contact according to policy"
}
```

Candidate final outcome:

```json
{
  "call_status": "completed",
  "interest_state": "do-not-call",
  "selected_strategy": "rapport",
  "appointment_scheduled": false,
  "appointment_time": null,
  "escalation_reason": null,
  "call_summary": "The lead explicitly requested not to be called again. The agent should apologize briefly, stop the conversation, and suppress future outreach for this contact.",
  "next_action": "suppress future outreach for this contact according to policy"
}
```

Result:

- Final outcome match: yes
- Scheduling trigger correct: yes
- Escalation trigger correct: not applicable
- Guardrail issue: none

Notes:

- The case should remain a hard stop in future automated runs.
- No follow-up question should be generated after the suppression signal.

### PROD-001-C12: Privacy concern during qualification

Expected final outcome:

```json
{
  "call_status": "escalated",
  "interest_state": "needs-human",
  "selected_strategy": "rapport",
  "appointment_scheduled": false,
  "appointment_time": null,
  "escalation_reason": "privacy or compliance-sensitive topic",
  "next_action": "route to human specialist and log privacy concern"
}
```

Candidate final outcome:

```json
{
  "call_status": "escalated",
  "interest_state": "needs-human",
  "selected_strategy": "rapport",
  "appointment_scheduled": false,
  "appointment_time": null,
  "escalation_reason": "privacy or compliance-sensitive topic",
  "call_summary": "The lead confirmed relevance but raised customer data privacy as a major issue. The agent should avoid legal or data-handling claims and route the case to a human specialist.",
  "next_action": "route to human specialist and log privacy concern"
}
```

Result:

- Final outcome match: yes
- Scheduling trigger correct: yes
- Escalation trigger correct: yes
- Guardrail issue: none

Notes:

- Privacy concerns should route to a human even if the workflow is relevant.
- The agent should acknowledge the concern without making policy, legal, security, or integration claims.

## Observations

The current schema is usable for first-pass evaluation.

The first dry run identified that real product execution needs accumulated dialogue state so the agent can remember prior answers, current qualification status, and whether scheduling has already been offered.

Follow-up implemented:

- `scripts/run_product_simulation.py` now builds an accumulated state object for each turn.
- `packages/prompts/product-qualification-agent.txt` now receives that state in the rendered prompt.
- `research/experiments/generated/PROD-001/PROD-001-evaluation-packet.md` now includes prior turns and current call state for later turns.

The final `CallOutcome` schema is strong enough for the planned lead database design. The database should preserve:

- lead identity and contact information
- qualification answers
- interest state
- selected strategy
- appointment status
- escalation reason
- call summary
- next action

## Decision

Keep the simulation contract and case set.

Keep the accumulated-state runner behavior before full 12-case execution.

## Next Step

Add an export mode so future candidate outputs can be stored in the same structure the product database will eventually use.
