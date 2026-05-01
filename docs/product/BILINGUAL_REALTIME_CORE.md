# Bilingual Realtime Core

## Principle

The product is one reusable sales-agent core with configurable campaign profiles.

Language is campaign configuration, not a separate product fork.

```text
SalesCampaign.language -> realtime response language
SalesCampaign.locale -> voice/browser locale hint
call-control rules -> same semantics across languages
```

## Current Languages

LANG-001 validates:

- German campaign responses: `de`
- English campaign responses: `en`

The realtime core keeps the same decision labels across both languages:

- `sales_difficulty`
- `interest_state`
- `selected_strategy`
- `next_action`
- `call_control`

Only the customer-facing response text changes language.

RESP-001 guarded response generation must preserve the same response language. It can improve wording, but it cannot replace a German policy response with English stock phrasing or vice versa.

## Covered Realtime Scenarios

LANG-001 currently covers paired German/English cases for:

- price objection
- product detail lookup with bridge response
- stop / do-not-call request
- human request
- claim or guarantee boundary
- scheduling confirmation
- vague callback timing
- repeated silence

## Guardrail

The agent should not randomly switch languages.

The current deterministic prototype uses the campaign language as the response language. Later, code-switching can be added as an explicit policy, but it should still be a controlled behavior rather than accidental drift.

## Validation

Run:

```powershell
python scripts\validate_lang_001_bilingual_realtime_core.py
```

The validator checks:

- German and English campaign profiles exist.
- German and English cases cover the same realtime scenarios.
- `response_language` matches the campaign language.
- response text contains expected language markers.
- RESP-001 guarded response output preserves the campaign language.
- call-control decisions still match expectations.
- no live-path sub-agents are used inside the first-response path.

## Generated Artifacts

```text
research/experiments/generated/LANG-001-bilingual-realtime-results.json
research/experiments/generated/LANG-001-bilingual-realtime-report.md
```
