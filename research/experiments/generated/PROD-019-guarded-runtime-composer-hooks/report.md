# PROD-019 Guarded Runtime Composer Hooks

This checkpoint tests opt-in runtime composer hooks through the actual guarded response composer.

It changes one editable surface: guarded runtime composer hook flag only. Default-off behavior unchanged remains a hard gate.

## Summary

- Source PROD-015 decision: `ready_for_review_no_retrieval_gain_on_slice`
- Fixed cases: `unchanged PROD-015 turn_results`
- Editable surface changed: `guarded_runtime_composer_hook_flag_only`
- Analyzed turns: `180`
- Default-off answer drift count: `0`
- Opt-in hooked answers: `98`
- Hooked without evaluation labels: `98`
- Current retrieval total score: `663`
- Hooked total score: `916`
- Hooked score delta vs current: `253`
- Hooked wins vs current: `92`
- Current wins against hooked: `0`
- Safety gate pass count: `180`
- Payment collection count: `0`
- Non-sale correctness: `1.0`
- Safe-close correctness: `1.0`
- Runtime retrieval default enabled: `False`
- Composer hook flag default enabled: `False`
- PROD-019 gate passed: `True`
- Decision: `keep_runtime_composer_hooks_opt_in_candidate_not_default`
- Decision meaning: keep runtime composer hooks opt-in candidate not default

## Label Summary

| Label | Turns | Hooked Answers | Current Score | Hooked Score | Hooked Wins Vs Current | Default Drift | Payment Findings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| callback_request | 30 | 19 | 150 | 203 | 19 | 0 | 0 |
| cancellation_boundary | 30 | 14 | 59 | 93 | 13 | 0 | 0 |
| price_objection | 30 | 18 | 150 | 199 | 18 | 0 | 0 |
| sale_eligible | 30 | 15 | 153 | 198 | 15 | 0 | 0 |
| support_handoff | 30 | 18 | 58 | 99 | 18 | 0 | 0 |
| trust_repair | 30 | 14 | 93 | 124 | 9 | 0 | 0 |

## Hooked Examples

### prod-014-callback_request-001::turn-001

- Label used for reporting only: `callback_request`
- Runtime hook: `callback_request_low_commitment`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`

Customer question:

```text
I need time to think, so do not rush me into a decision.
```

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify fit, timing, or anything you need verified before reviewing it?
```

### prod-014-callback_request-001::turn-002

- Label used for reporting only: `callback_request`
- Runtime hook: `sale_eligible_fit_check`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `5`
- Hooked score: `7`
- Hooked winner vs current: `hooked`

Customer question:

```text
Customer raises `needs_to_think` and needs a `pain_point_question` before any close.
```

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?
```

### prod-014-cancellation_boundary-001::turn-002

- Label used for reporting only: `cancellation_boundary`
- Runtime hook: `sale_eligible_fit_check`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `3`
- Hooked score: `3`
- Hooked winner vs current: `tie`

Customer question:

```text
Customer raises `confused_about_offer` and needs a `current_problem_question` before any close.
```

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?
```

### prod-014-price_objection-001::turn-001

- Label used for reporting only: `price_objection`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`

Customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Default-off answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-price_objection-001::turn-002

- Label used for reporting only: `price_objection`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`

Customer question:

```text
Customer raises `too_expensive` and needs a `timeline_question` before any close.
```

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the cost, the value you would get back, or the timing for reviewing it?
```

### prod-014-sale_eligible-001::turn-001

- Label used for reporting only: `sale_eligible`
- Runtime hook: `sale_eligible_fit_check`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`

Customer question:

```text
I am worried about being locked into something, so clarify the commitment before any close.
```

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?
```

### prod-014-sale_eligible-001::turn-002

- Label used for reporting only: `sale_eligible`
- Runtime hook: `sale_eligible_fit_check`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`

Customer question:

```text
Customer raises `contract_fear` and needs a `usage_question` before any close.
```

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?
```

### prod-014-support_handoff-001::turn-001

- Label used for reporting only: `support_handoff`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `3`
- Hooked score: `6`
- Hooked winner vs current: `hooked`

Customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Default-off answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-support_handoff-001::turn-002

- Label used for reporting only: `support_handoff`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `3`
- Hooked score: `6`
- Hooked winner vs current: `hooked`

Customer question:

```text
Customer raises `too_expensive` and needs a `budget_question` before any close.
```

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-trust_repair-001::turn-001

- Label used for reporting only: `trust_repair`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `3`
- Hooked score: `6`
- Hooked winner vs current: `hooked`

Customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Default-off answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-trust_repair-001::turn-002

- Label used for reporting only: `trust_repair`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `3`
- Hooked score: `6`
- Hooked winner vs current: `hooked`

Customer question:

```text
Customer raises `too_expensive` and needs a `current_provider_question` before any close.
```

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-callback_request-002::turn-001

- Label used for reporting only: `callback_request`
- Runtime hook: `callback_request_low_commitment`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`

Customer question:

```text
I cannot talk now; give me one clear reason to schedule a callback.
```

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify fit, timing, or anything you need verified before reviewing it?
```

## Boundary

PROD-019 keeps retrieval and composer hooks disabled by default. It makes no provider calls, performs no downloads, and does not use CallCenterEN-derived text in commercial runtime prompts.
