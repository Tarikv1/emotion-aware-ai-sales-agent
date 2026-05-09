# PROD-020 Naturalized Customer-Turn Evaluation

This checkpoint reruns the PROD-019 opt-in runtime composer hooks on naturalized customer turns.

It changes one editable surface: `evaluation_customer_turn_wording_only`. Runtime code, retrieval defaults, composer-hook defaults, and scorer rules remain unchanged.

## Summary

- Source PROD-015 decision: `ready_for_review_no_retrieval_gain_on_slice`
- Source PROD-019 decision: `keep_runtime_composer_hooks_opt_in_candidate_not_default`
- Fixed cases: `naturalized PROD-015 turn_results`
- Editable surface changed: `evaluation_customer_turn_wording_only`
- Runtime surface changed: `none`
- Analyzed turns: `180`
- Source rubric-like turns: `120`
- Naturalized questions changed: `123`
- Naturalized rubric-token count: `0`
- No rubric tokens in runtime prompts: `True`
- Source-pattern refs preserved: `180`
- Expected outcomes preserved: `180`
- Baseline total score: `734`
- Hooked total score: `1065`
- Hooked score delta vs baseline: `331`
- Opt-in hooked answers: `107`
- Hooked wins vs baseline: `107`
- Baseline wins vs hooked: `0`
- Safety gate pass count: `180`
- Payment collection count: `0`
- Non-sale correctness: `1.0`
- Safe-close correctness: `1.0`
- Runtime retrieval default enabled: `False`
- Composer hook flag default enabled: `False`
- PROD-020 gate passed: `True`
- Decision: `keep_naturalized_runtime_hooks_as_opt_in_candidate_not_default`
- Decision meaning: keep naturalized runtime hooks as opt-in candidate not default

## Label Summary

| Label | Turns | Rubric-Like Source | Hooked Answers | Baseline Score | Hooked Score | Hooked Wins Vs Baseline | Baseline Wins | Rubric Tokens In Prompts | Payment Findings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| callback_request | 30 | 20 | 26 | 153 | 229 | 26 | 0 | 0 | 0 |
| cancellation_boundary | 30 | 20 | 10 | 90 | 117 | 10 | 0 | 0 | 0 |
| price_objection | 30 | 20 | 25 | 153 | 226 | 25 | 0 | 0 | 0 |
| sale_eligible | 30 | 20 | 12 | 183 | 219 | 12 | 0 | 0 | 0 |
| support_handoff | 30 | 20 | 15 | 59 | 95 | 15 | 0 | 0 | 0 |
| trust_repair | 30 | 20 | 19 | 96 | 179 | 19 | 0 | 0 | 0 |

## Hooked Examples

### prod-014-callback_request-001::turn-001

- Label used for reporting/scoring only: `callback_request`
- Runtime hook: `callback_request_low_commitment`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `5`
- Hooked score: `8`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
I need time to think, so do not rush me into a decision.
```

Baseline answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify fit, timing, or anything you need verified before reviewing it?
```

### prod-014-callback_request-001::turn-002

- Label used for reporting/scoring only: `callback_request`
- Runtime hook: `callback_request_low_commitment`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `5`
- Hooked score: `8`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
I need time to think this through without being rushed. Can you ask what is bothering me most about this?
```

Baseline answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify fit, timing, or anything you need verified before reviewing it?
```

### prod-014-callback_request-001::turn-003

- Label used for reporting/scoring only: `callback_request`
- Runtime hook: `callback_request_low_commitment`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `5`
- Hooked score: `8`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
If I do not want to decide now, what would be a low-pressure callback step?
```

Baseline answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify fit, timing, or anything you need verified before reviewing it?
```

### prod-014-price_objection-001::turn-001

- Label used for reporting/scoring only: `price_objection`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `5`
- Hooked score: `8`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Baseline answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-price_objection-001::turn-002

- Label used for reporting/scoring only: `price_objection`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `5`
- Hooked score: `8`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
The cost sounds expensive to me. Can you first ask about timing before I decide?
```

Baseline answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the cost, the value you would get back, or the timing for reviewing it?
```

### prod-014-price_objection-001::turn-003

- Label used for reporting/scoring only: `price_objection`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `5`
- Hooked score: `8`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
If the cost is still my main concern, what should we clarify before I decide?
```

Baseline answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-sale_eligible-001::turn-001

- Label used for reporting/scoring only: `sale_eligible`
- Runtime hook: `sale_eligible_fit_check`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `5`
- Hooked score: `8`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
I am worried about being locked into something. Can you clarify the commitment before I agree to anything?
```

Baseline answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?
```

### prod-014-sale_eligible-001::turn-002

- Label used for reporting/scoring only: `sale_eligible`
- Runtime hook: `sale_eligible_fit_check`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `5`
- Hooked score: `8`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
I am worried about being locked into a commitment. Can you first ask how I would actually use it?
```

Baseline answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Before any commitment, should we confirm fit, timing, or eligibility for your situation?
```

### prod-014-support_handoff-001::turn-001

- Label used for reporting/scoring only: `support_handoff`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `3`
- Hooked score: `6`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Baseline answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-support_handoff-001::turn-002

- Label used for reporting/scoring only: `support_handoff`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `3`
- Hooked score: `6`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
The cost sounds expensive to me. Can you understand what range would feel realistic before going further?
```

Baseline answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-trust_repair-001::turn-001

- Label used for reporting/scoring only: `trust_repair`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `3`
- Hooked score: `6`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Baseline answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### prod-014-trust_repair-001::turn-002

- Label used for reporting/scoring only: `trust_repair`
- Runtime hook: `price_objection_clarifier`
- Hook basis: `transcript_signal, retrieval_advisory_hint`
- Baseline score: `3`
- Hooked score: `6`
- Hooked winner vs baseline: `hooked`

Naturalized customer question:

```text
The cost sounds expensive to me. Can you check what I am using now before making a recommendation?
```

Baseline answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hooked answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

## Boundary

PROD-020 keeps retrieval and composer hooks disabled by default. It makes no provider calls, performs no downloads, does not read raw CallCenterEN files, and does not pass scenario labels or source-pattern IDs into the runtime composer.
