# RESP-001 Guarded Response Generation

## Purpose

RESP-001 adds the first reusable response-generation layer for the sales agent.

This is not an insurance-only feature and not a voice-only feature. It belongs to the reusable sales-agent core and can be used by any campaign and any channel.

## Layer Position

```text
customer says something
  -> speech/text input
  -> realtime sales-agent policy core
  -> guarded response generation
  -> optional segment-aware speech naturalness
  -> voice or text output
```

The realtime core decides:

- customer state
- emotion estimate
- sales difficulty
- sales strategy
- next action
- call control
- safe policy response

The response-generation layer decides:

- whether the wording can be made more natural
- whether the candidate wording stays inside guardrails
- whether to use the candidate or fall back to the policy response

The speech naturalness layer comes after this. It can add rare mid-utterance fillers to freeform voice output, but it must not alter the guarded response meaning or protected campaign/compliance segments. See `docs/product/VOICE_012_SPEECH_NATURALNESS_LAYER.md`.

## Why This Matters

The project needs the agent to become better at sales without becoming unsafe.

So the product should not let an LLM freely decide everything. Instead:

```text
rules and campaign policy decide what is allowed
response generation improves how it is said
validation blocks unsafe wording
fallback preserves safe behavior
```

This means future LLMs can improve naturalness, persuasion quality, objection handling, and emotional adaptation while the deterministic policy still protects call-control, compliance, and campaign boundaries.

## Current Provider

RESP-001 uses a local deterministic provider:

```text
provider: local-guarded-composer
llm_used: false
requires_api_key: false
api_calls_made: false
```

This is intentional. It proves the contract before any real provider or API key is introduced.

## Guardrail Inputs

RESP-001 uses:

- universal forbidden claims
- campaign-specific forbidden claims
- campaign allowed claims
- required disclosures
- escalation triggers
- human handoff role
- realtime decision snapshot

These inputs come from the same vertical-agnostic `SalesCampaign` model used across product docs and simulations.

## Candidate And Fallback

The response layer produces:

- `policy_response`: deterministic safe baseline
- `candidate_response`: improved wording
- `final_response`: the response allowed to reach the customer

If validation passes:

```text
final_response = candidate_response
```

If validation fails:

```text
final_response = policy_response
```

The live path does not creatively repair unsafe claims yet. It falls back immediately.

## Example

For a price objection, the realtime policy response is:

```text
That makes sense. Is the main concern the price itself, or whether the review is worth the effort?
```

RESP-001 can improve the wording to:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

If a candidate says:

```text
I guarantee this will save you money and always be stable.
```

RESP-001 blocks it and falls back to the policy response.

## Future LLM Role

A future LLM should plug in as a candidate-response provider, not as the final authority.

Expected future flow:

```text
policy decision
  -> LLM candidate wording
  -> guardrail validation
  -> optional repair or fallback
  -> final response
```

This preserves the product architecture:

- reusable sales-agent core
- configurable SalesCampaign profiles
- model-assisted wording
- deterministic safety and call-control
