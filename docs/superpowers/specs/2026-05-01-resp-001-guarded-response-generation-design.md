# RESP-001 Guarded Response Generation Design

## Purpose

RESP-001 defines the reusable response-generation layer for the vertical-agnostic sales agent.

The layer sits after the realtime policy decision and before channel output such as voice, chat, or transcript logging. Its job is to improve wording while preserving the policy-owned decision:

```text
customer transcript
  -> realtime sales-agent core
  -> guarded response generation
  -> voice/text channel output
```

## Product Principle

The agent is not tied to one product category.

The same response-generation contract must work for telecom, energy, B2B software, insurance, home services, consumer products, and later campaign types. Campaign-specific rules come from `SalesCampaign` fields such as allowed claims, forbidden claims, required disclosures, escalation triggers, scheduling goal, and human handoff role.

## Goals

- Keep the realtime core in control of state, strategy, next action, and call control.
- Allow response wording to become more natural and persuasive without inventing claims.
- Prove a no-key provider-safe contract before adding any external LLM.
- Validate candidate responses before they can become final responses.
- Fall back to the deterministic policy response when validation fails.
- Keep the layer reusable across voice and text channels.

## Non-Goals

- Do not call a real LLM provider in RESP-001.
- Do not require or read an API key.
- Do not replace the rule baseline, taxonomy, or call-control policy.
- Do not implement full semantic compliance review yet.
- Do not quote customer text verbatim by default, because unsafe claims can be repeated accidentally.

## Components

### Realtime Policy Core

Existing runtime code classifies the turn and chooses:

- detected emotion
- sales difficulty
- interest state
- selected strategy
- next action
- call control
- policy-safe agent response

This remains the source of truth for what the agent is allowed to do next.

### Guarded Response Generator

`scripts/generate_guarded_response.py` builds a candidate response using a local deterministic composer.

The first provider is intentionally simple:

```text
provider = local-guarded-composer
llm_used = false
requires_api_key = false
api_calls_made = false
```

This lets the product test the interface and safety behavior without secret handling or network risk.

### Guardrail Validator

The validator checks the candidate response against:

- universal forbidden claims
- campaign-specific forbidden claims
- fallback rule

If the candidate contains a forbidden claim, the layer does not attempt creative live-path repair. It uses the policy response as the final response.

## Output Contract

RESP-001 returns:

- `response_generation_id`
- `provider`
- `llm_used`
- `requires_api_key`
- `api_calls_made`
- `campaign`
- `stage`
- `input_type`
- `transcript`
- `policy_response`
- `candidate_response`
- `final_response`
- `validation`
- `guardrails`
- `decision_snapshot`
- `response_constraints`
- `latency`

The final response is the only text that should be spoken or shown to the customer.

## Safety Model

The response layer can improve how something is said, but not what the agent is allowed to decide.

Allowed:

- make wording clearer
- ask a more natural follow-up question
- adapt tone to the sales difficulty
- route to a human specialist with campaign-specific role wording

Not allowed:

- change call control
- override do-not-call handling
- confirm an appointment without policy confirmation
- invent product facts
- promise outcomes, savings, coverage, performance, or approval
- ignore escalation triggers

## Latency Model

RESP-001 is designed for the live path. A local composer should run effectively immediately. A future LLM provider must preserve this structure:

```text
policy response available immediately
candidate response generated quickly
candidate validated
fallback if validation fails or times out
```

If generation cannot finish within the live budget, the product should speak the policy response or bridge response rather than making the customer wait.

## Testing

`scripts/validate_resp_001_guarded_response_generation.py` proves:

- the generator exists
- no LLM or API key is used
- a safe price-objection response is contextual and does not fall back
- an unsafe candidate response is blocked
- forbidden claims are reported
- fallback uses the deterministic policy response
- generated output and report do not contain secret-like tokens

## Future Extension

RESP-002 can add provider adapters for LLM-based wording. The adapter must still return a candidate response into the same validation and fallback contract.
