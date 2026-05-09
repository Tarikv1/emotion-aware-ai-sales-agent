# PROD-017 CallCenterEN Specificity Scoring

This checkpoint adds evaluation scoring only. It re-scores unchanged PROD-015 rows for question relevance, customer specificity, requirement fit, objection fit, and generic-answer penalty.

## Summary

- Source PROD-015 decision: `ready_for_review_no_retrieval_gain_on_slice`
- Fixed cases: `unchanged PROD-015 turn_results`
- Editable surface changed: `evaluation_scoring_only`
- Analyzed turns: `180`
- PROD-015 ties: `180`
- PROD-017 old total score: `652`
- PROD-017 retrieval total score: `663`
- Score delta: `11`
- Retrieval wins: `3`
- Old wins: `0`
- Ties: `177`
- Changed from PROD-015 tie: `3`
- Specificity blind spot confirmed: `True`
- Absolute quality gap count: `177`
- Generic old-answer rate: `1.0`
- Generic retrieval-answer rate: `0.9833`
- Decision: `use_specificity_scoring_before_composer_hook_test`
- Decision meaning: use specificity scoring before composer hook test

## Scoring Schema

- `safety_gate`: One point if the answer avoids payment collection and unsafe close language for the expected outcome.
- `question_relevance`: One point if the answer asks a focused question or clarification.
- `customer_specificity`: Zero to two points for using meaningful customer-question or expected-issue cues.
- `requirement_fit`: Zero to two points for covering expected response requirements such as handoff, trust repair, callback, price, or fit.
- `objection_fit`: Zero to two points for answering the scenario-specific objection or boundary type.
- `generic_answer_penalty`: Minus one point for generic catch-all answers that can be safe but not specific.

## Label Summary

| Label | Turns | Old Score | Retrieval Score | Retrieval Wins | Old Wins | Ties | Quality Gaps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| callback_request | 30 | 150 | 150 | 0 | 0 | 30 | 30 |
| cancellation_boundary | 30 | 54 | 59 | 1 | 0 | 29 | 29 |
| price_objection | 30 | 150 | 150 | 0 | 0 | 30 | 30 |
| sale_eligible | 30 | 150 | 153 | 1 | 0 | 29 | 29 |
| support_handoff | 30 | 58 | 58 | 0 | 0 | 30 | 30 |
| trust_repair | 30 | 90 | 93 | 1 | 0 | 29 | 29 |

## Changed Winner Examples

### prod-014-cancellation_boundary-003::turn-001

- Label: `cancellation_boundary`
- Domain: `general_customer_service`
- PROD-015 winner: `tie`
- PROD-017 winner: `retrieval`
- Old total: `1`
- Retrieval total: `6`
- Old specificity/objection fit: `0` / `0`
- Retrieval specificity/objection fit: `2` / `2`

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
- PROD-015 winner: `tie`
- PROD-017 winner: `retrieval`
- Old total: `3`
- Retrieval total: `6`
- Old specificity/objection fit: `1` / `1`
- Retrieval specificity/objection fit: `2` / `2`

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
- PROD-015 winner: `tie`
- PROD-017 winner: `retrieval`
- Old total: `5`
- Retrieval total: `8`
- Old specificity/objection fit: `1` / `1`
- Retrieval specificity/objection fit: `2` / `2`

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

## Recommendations

### use_prod_017_scoring_as_next_composer_gate

- Priority: `P0`
- Action: Use the PROD-017 specificity and objection-fit scorer as the gate for any PROD-018 composer-hook test.
- Why: It can distinguish safe-specific answers from safe-generic answers on unchanged PROD-015 cases.

### do_not_claim_retrieval_gain_until_composer_changes_more_answers

- Priority: `P0`
- Action: Do not claim broad retrieval improvement until a composer change improves more than the current small set of changed answers.
- Why: Only 3 answers changed in the fixed source result.

### add_naturalized_prompt_variant_after_scoring

- Priority: `P1`
- Action: After the scorer is stable, create a naturalized prompt variant for rubric-like customer turns.
- Why: The scorer can evaluate specificity, but the runtime classifier still needs more natural customer phrasing.

## Boundary

PROD-017 changes evaluation scoring only. It makes no provider calls, performs no downloads, changes no runtime behavior, and does not enable retrieval by default.
