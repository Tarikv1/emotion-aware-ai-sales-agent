# RESP-001 Guarded Response Generation

## Purpose

Test the first reusable response-generation layer for the vertical-agnostic sales agent.

The experiment checks whether a wording layer can improve a response while preserving the realtime policy core's decision and campaign guardrails.

## Command

```powershell
python scripts\validate_resp_001_guarded_response_generation.py
```

## Scenario

Campaign:

```text
campaign-prod-005-b2c-telecom
```

Customer transcript:

```text
Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.
```

Realtime policy classification:

- sales difficulty: `price-objection`
- emotion: `skeptical-or-negative`
- strategy: `inquiry`
- next action: `ask-follow-up`
- call control: `continue-call`

## Safe Response Result

Policy response:

```text
That makes sense. Is the main concern the price itself, or whether the review is worth the effort?
```

Guarded candidate:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Result:

- validation passed
- fallback not used
- no LLM used
- no API key required

## Unsafe Candidate Result

Unsafe candidate tested by the validator:

```text
I guarantee this will save you money and always be stable.
```

Detected forbidden claims:

- `guarantee`
- `save you money`
- `always be stable`

Result:

- validation failed
- fallback used
- final response equals policy response

## Interpretation

RESP-001 proves the important product contract:

```text
policy decides what is allowed
response generation improves how it is said
validation blocks unsafe wording
fallback keeps the live path safe
```

This prepares the project for a future LLM provider without allowing the LLM to replace taxonomy, rule baseline, call-control policy, or campaign guardrails.
