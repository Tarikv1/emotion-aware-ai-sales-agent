# PROD-018 CallCenterEN Composer Hook Test

This checkpoint tests an offline composer hook only surface on unchanged PROD-015 rows and scores it with the PROD-017 specificity scorer.

## Summary

- Source PROD-015 decision: `ready_for_review_no_retrieval_gain_on_slice`
- Fixed cases: `unchanged PROD-015 turn_results`
- Editable surface changed: `offline_composer_hook_only`
- Analyzed turns: `180`
- Eligible hook turns: `174`
- Hooked answers: `174`
- Preserved existing influenced answers: `3`
- Current retrieval total score: `663`
- Hooked total score: `1421`
- Hooked score delta vs current: `758`
- Hooked wins vs current: `174`
- Hooked wins vs old: `177`
- Old wins against hooked: `0`
- Safety gate pass count: `180`
- Payment collection count: `0`
- Non-sale correctness: `1.0`
- Safe-close correctness: `1.0`
- PROD-018 gate passed: `True`
- Decision: `keep_composer_hooks_for_runtime_candidate_not_default`
- Decision meaning: keep composer hooks for runtime candidate not default

## Hook Set

### Price objection clarifier

- Hook ID: `price_objection_clarifier`
- Scenario labels: `price_objection`
- Purpose: Separate cost, value, terms, and timing before any close.

### Support handoff router

- Hook ID: `support_handoff_router`
- Scenario labels: `support_handoff`
- Purpose: Route unresolved service issues to a specialist instead of guessing.

### Cancellation boundary stop

- Hook ID: `cancellation_boundary_stop`
- Scenario labels: `cancellation_boundary`
- Purpose: Stop the sales discussion and confirm whether the customer wants no further calls.

### Callback request low commitment

- Hook ID: `callback_request_low_commitment`
- Scenario labels: `callback_request`
- Purpose: Offer a low-commitment callback or relevant summary without forcing a decision.

### Trust repair verification

- Hook ID: `trust_repair_verification`
- Scenario labels: `trust_repair`
- Purpose: Offer verifiable company or specialist context without pressure.

### Sale eligible fit check

- Hook ID: `sale_eligible_fit_check`
- Scenario labels: `sale_eligible`
- Purpose: Check fit, timing, or eligibility before any verbal commitment.

## Label Summary

| Label | Turns | Hooked Answers | Current Score | Hooked Score | Hooked Wins Vs Current | Hooked Wins Vs Old | Payment Findings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| callback_request | 30 | 30 | 150 | 240 | 30 | 30 | 0 |
| cancellation_boundary | 30 | 28 | 59 | 231 | 28 | 29 | 0 |
| price_objection | 30 | 30 | 150 | 240 | 30 | 30 | 0 |
| sale_eligible | 30 | 28 | 153 | 237 | 28 | 29 | 0 |
| support_handoff | 30 | 30 | 58 | 240 | 30 | 30 | 0 |
| trust_repair | 30 | 28 | 93 | 233 | 28 | 29 | 0 |

## Hooked Examples

### prod-014-callback_request-001::turn-001

- Label: `callback_request`
- Hook: `callback_request_low_commitment`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
I need time to think, so do not rush me into a decision.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
That makes sense. Would a brief callback later help, or should I send the one detail that would make this worth reviewing first?
```

### prod-014-callback_request-001::turn-002

- Label: `callback_request`
- Hook: `callback_request_low_commitment`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
Customer raises `needs_to_think` and needs a `pain_point_question` before any close.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
That makes sense. Would a brief callback later help, or should I send the one detail that would make this worth reviewing first?
```

### prod-014-callback_request-001::turn-003

- Label: `callback_request`
- Hook: `callback_request_low_commitment`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
Customer asks what the next safe step would be.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
That makes sense. Would a brief callback later help, or should I send the one detail that would make this worth reviewing first?
```

### prod-014-cancellation_boundary-001::turn-001

- Label: `cancellation_boundary`
- Hook: `cancellation_boundary_stop`
- Current retrieval score: `3`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
I am confused about what you are offering, so explain the useful part before asking me to decide.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
Understood. I can stop the sales discussion here. Do you want me to mark that you do not want further calls?
```

### prod-014-cancellation_boundary-001::turn-002

- Label: `cancellation_boundary`
- Hook: `cancellation_boundary_stop`
- Current retrieval score: `3`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
Customer raises `confused_about_offer` and needs a `current_problem_question` before any close.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
Understood. I can stop the sales discussion here. Do you want me to mark that you do not want further calls?
```

### prod-014-cancellation_boundary-001::turn-003

- Label: `cancellation_boundary`
- Hook: `cancellation_boundary_stop`
- Current retrieval score: `1`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
Customer asks what the next safe step would be.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
Understood. I can stop the sales discussion here. Do you want me to mark that you do not want further calls?
```

### prod-014-price_objection-001::turn-001

- Label: `price_objection`
- Hook: `price_objection_clarifier`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Current retrieval answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-price_objection-001::turn-002

- Label: `price_objection`
- Hook: `price_objection_clarifier`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
Customer raises `too_expensive` and needs a `timeline_question` before any close.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
That makes sense. Is the bigger concern the cost, the value you would get back, or the timing for reviewing it?
```

### prod-014-price_objection-001::turn-003

- Label: `price_objection`
- Hook: `price_objection_clarifier`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
Customer asks what the next safe step would be.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-sale_eligible-001::turn-001

- Label: `sale_eligible`
- Hook: `sale_eligible_fit_check`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
I am worried about being locked into something, so clarify the commitment before any close.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?
```

### prod-014-sale_eligible-001::turn-002

- Label: `sale_eligible`
- Hook: `sale_eligible_fit_check`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
Customer raises `contract_fear` and needs a `usage_question` before any close.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?
```

### prod-014-sale_eligible-001::turn-003

- Label: `sale_eligible`
- Hook: `sale_eligible_fit_check`
- Current retrieval score: `5`
- Hooked score: `8`
- Hooked winner vs current: `hooked`
- Hooked winner vs old: `hooked`

Customer question:

```text
Customer asks what the next safe step would be.
```

Current retrieval answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Hooked answer:

```text
That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?
```

## Recommendations

### keep_hooks_as_runtime_candidate_only

- Priority: `P0`
- Action: Keep the composer hooks as a candidate for a later guarded runtime implementation, not as default retrieval behavior.
- Why: This checkpoint is offline and fixed-case only.

### convert_hooks_into_runtime_composer_tests_next

- Priority: `P0`
- Action: If accepted, add red-first tests around the real guarded response composer before moving any hook into runtime code.
- Why: The offline hook improved 174 fixed rows versus current retrieval.

### keep_prod_017_as_promotion_gate

- Priority: `P1`
- Action: Keep PROD-017 scoring as the gate for any later runtime composer change.
- Why: Safe generic answers should not pass as equivalent to safe specific answers.

## Boundary

PROD-018 changes no runtime code. It makes no provider calls, performs no downloads, and does not enable retrieval by default.
