# PROD-016 CallCenterEN Retrieval No-Gain Diagnosis

This checkpoint diagnoses why PROD-015 tied instead of promoting retrieval or changing runtime behavior.

## Summary

- Source PROD-015 decision: `ready_for_review_no_retrieval_gain_on_slice`
- Analyzed turns: `180`
- Old runtime score: `810`
- Retrieval runtime score: `810`
- Score delta: `0`
- No-gain confirmed: `True`
- Answer changed count: `3`
- Unchanged answer count: `177`
- Influenced but tied count: `3`
- Retrieved-not-used rate: `0.9667`
- Matching success rate: `1.0`
- No-match rate: `0.0`
- Unknown-runtime-signal rate: `1.0`
- Rubric-like turn rate: `0.6667`
- Dominant old-answer share: `0.85`
- Decision: `diagnose_before_retrieval_runtime_promotion`
- Decision meaning: diagnose before retrieval runtime promotion

## Failure Classes

### Composer influence gap

- Class: `composer_influence_gap`
- Severity: `high`
- Evidence: 174 turns were retrieved-not-used and 177 answers were unchanged.
- Interpretation: Retrieval matching exists, but retrieved hints rarely change the deterministic response composer.

### Scoring blind spot

- Class: `scoring_blind_spot`
- Severity: `high`
- Evidence: 3 influenced turns and 3 changed-answer turns still tied.
- Interpretation: The current score rewards safe generic follow-up behavior but does not measure answer specificity or objection-fit enough.

### Runtime classifier mismatch

- Class: `runtime_classifier_mismatch`
- Severity: `medium`
- Evidence: 180 turns were classified as unknown-runtime-signal and 120 customer prompts looked rubric-like.
- Interpretation: Generated test prompts may carry labels that the runtime classifier does not naturally parse from customer wording.

### Campaign domain mismatch

- Class: `campaign_domain_mismatch`
- Severity: `medium`
- Evidence: 8 scenario domains were evaluated through one campaign id `campaign-prod-005-b2b-software`.
- Interpretation: A single B2B software campaign can flatten domain-specific objections and make old/retrieval answers converge.

## Recommendations

### add_specificity_scoring_before_claiming_gain

- Priority: `P0`
- Target: `evaluation`
- Action: Add specificity and objection-fit sub-scores before claiming retrieval is better.
- Why: A generic old answer can currently tie a more targeted retrieval answer if both are safe and ask a question.
- Runtime change in this checkpoint: `False`

### add_composer_hooks_for_generated_objection_labels

- Priority: `P0`
- Target: `retrieval composer`
- Action: Add or test explicit composer hooks for generated objection labels such as needs_spouse_or_manager, callback_request, trust_repair, and price_objection.
- Why: Retrieved-but-not-used rate is 0.9667, so matching is not enough.
- Runtime change in this checkpoint: `False`

### verbalize_rubric_like_scenario_turns

- Priority: `P1`
- Target: `scenario bank`
- Action: Convert rubric-like customer turns into natural customer utterances before using them as runtime classifier evidence.
- Why: Rubric-like turn rate is 0.6667, which can hide real classifier behavior.
- Runtime change in this checkpoint: `False`

### route_scenarios_to_domain_campaigns

- Priority: `P1`
- Target: `evaluation routing`
- Action: Route multi-domain scenario slices to matching SalesCampaign profiles or mark the single-campaign result as baseline-only.
- Why: 8 domains were evaluated through `campaign-prod-005-b2b-software`.
- Runtime change in this checkpoint: `False`

### run_full_bank_only_after_diagnostic_scoring

- Priority: `P2`
- Target: `experiment sequencing`
- Action: Run the full 240-scenario bank only after the scorer can distinguish safe-generic from safe-specific answers.
- Why: A bigger run with the same blind spot would mostly confirm that both versions are safe, not which one is better.
- Runtime change in this checkpoint: `False`

## Retrieval Status By Label

| Label | Status Counts |
| --- | --- |
| callback_request | retrieved_not_used: 30 |
| cancellation_boundary | blocked: 1, influenced: 1, retrieved_not_used: 28 |
| price_objection | retrieved_not_used: 30 |
| sale_eligible | blocked: 1, influenced: 1, retrieved_not_used: 28 |
| support_handoff | retrieved_not_used: 30 |
| trust_repair | blocked: 1, influenced: 1, retrieved_not_used: 28 |

## Examples

### prod-014-cancellation_boundary-003::turn-001

- Label: `cancellation_boundary`
- Domain: `general_customer_service`
- Retrieval status: `influenced`
- Winner: `tie`
- Runtime difficulty: `unknown-runtime-signal`
- Retrieved item IDs: `rag010-response-real-timing-check, rag010-voice-cadence-as-weak-context, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`

Customer question:

```text
I cannot decide alone, so help me understand what I would need to discuss with the other decision maker.
```

Old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval runtime answer:

```text
That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?
```

### prod-014-trust_repair-004::turn-001

- Label: `trust_repair`
- Domain: `healthcare_insurance`
- Retrieval status: `influenced`
- Winner: `tie`
- Runtime difficulty: `unknown-runtime-signal`
- Retrieved item IDs: `rag010-response-real-timing-check, rag010-voice-cadence-as-weak-context, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`

Customer question:

```text
I cannot decide alone, so help me understand what I would need to discuss with the other decision maker.
```

Old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval runtime answer:

```text
That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?
```

### prod-014-sale_eligible-009::turn-001

- Label: `sale_eligible`
- Domain: `medicare`
- Retrieval status: `influenced`
- Winner: `tie`
- Runtime difficulty: `unknown-runtime-signal`
- Retrieved item IDs: `rag010-response-real-timing-check, rag010-voice-cadence-as-weak-context, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`

Customer question:

```text
I cannot decide alone, so help me understand what I would need to discuss with the other decision maker.
```

Old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval runtime answer:

```text
That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?
```

### prod-014-callback_request-001::turn-001

- Label: `callback_request`
- Domain: `auto_insurance`
- Retrieval status: `retrieved_not_used`
- Winner: `tie`
- Runtime difficulty: `unknown-runtime-signal`
- Retrieved item IDs: `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`

Customer question:

```text
I need time to think, so do not rush me into a decision.
```

Old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

### prod-014-callback_request-001::turn-002

- Label: `callback_request`
- Domain: `auto_insurance`
- Retrieval status: `retrieved_not_used`
- Winner: `tie`
- Runtime difficulty: `unknown-runtime-signal`
- Retrieved item IDs: `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag014-response-consent-based-schedule-confirmation`

Customer question:

```text
Customer raises `needs_to_think` and needs a `pain_point_question` before any close.
```

Old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

### prod-014-callback_request-001::turn-003

- Label: `callback_request`
- Domain: `auto_insurance`
- Retrieval status: `retrieved_not_used`
- Winner: `tie`
- Runtime difficulty: `unknown-runtime-signal`
- Retrieved item IDs: `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`

Customer question:

```text
Customer asks what the next safe step would be.
```

Old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

### prod-014-cancellation_boundary-001::turn-001

- Label: `cancellation_boundary`
- Domain: `auto_insurance`
- Retrieval status: `retrieved_not_used`
- Winner: `tie`
- Runtime difficulty: `unknown-runtime-signal`
- Retrieved item IDs: `rag010-response-real-timing-check, rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit`

Customer question:

```text
I am confused about what you are offering, so explain the useful part before asking me to decide.
```

Old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

### prod-014-cancellation_boundary-001::turn-002

- Label: `cancellation_boundary`
- Domain: `auto_insurance`
- Retrieval status: `retrieved_not_used`
- Winner: `tie`
- Runtime difficulty: `unknown-runtime-signal`
- Retrieved item IDs: `rag010-response-impact-bridge, rag010-response-real-timing-check, rag010-response-so-what-clarifier, rag014-response-cost-of-inaction-check`

Customer question:

```text
Customer raises `confused_about_offer` and needs a `current_problem_question` before any close.
```

Old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

## Boundary

PROD-016 is diagnosis only. It makes no provider calls, performs no downloads, changes no runtime behavior, and does not enable retrieval by default.
