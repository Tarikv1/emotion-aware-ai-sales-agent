# PROD-015 CallCenterEN Runtime Comparison

This checkpoint runs the old retrieval-disabled runtime and the retrieval-enabled runtime on the same PROD-014 generated customer prompts.

It records the exact customer question, exact old runtime answer, exact retrieval runtime answer, and a decision trace for each evaluated turn.

## Summary

- Source bank scenarios: `240`
- Evaluated scenarios: `60`
- Evaluated turns: `180`
- Stratified slice: `True`
- Covered labels: `callback_request, cancellation_boundary, price_objection, sale_eligible, support_handoff, trust_repair`
- Hard failure count: `0`
- Leakage findings: `0`
- Decision: `ready_for_review_no_retrieval_gain_on_slice`

## Metrics

- Hard failure rate: `0.0`
- Non-sale correctness: `1.0`
- Safe close correctness: `1.0`
- Discovery-before-close rate: `1.0`
- Emotional handling score: `1.0`
- Leakage failure rate: `0.0`
- Retrieval win rate: `0.0`

## Runtime Comparison

- Old runtime total score: `810`
- Retrieval runtime total score: `810`
- Score delta: `0`
- Retrieval wins: `0`
- Old runtime wins: `0`
- Ties: `180`
- Retrieval influenced responses: `3`

## Leakage Tests

- exact_transcript_sentence_check: `pass`
- high_similarity_paraphrase_check: `pass`
- single_source_scenario_check: `pass`
- commercial_runtime_prompt_check: `pass`

## Scenario Table

| Scenario | Label | Expected | Turns | Retrieval Wins | Old Wins | Ties | Hard Failure |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| prod-014-callback_request-001 | callback_request | callback_agreed | 3 | 0 | 0 | 3 | False |
| prod-014-cancellation_boundary-001 | cancellation_boundary | end_call | 3 | 0 | 0 | 3 | False |
| prod-014-price_objection-001 | price_objection | non_sale_correct | 3 | 0 | 0 | 3 | False |
| prod-014-sale_eligible-001 | sale_eligible | sale_ready | 3 | 0 | 0 | 3 | False |
| prod-014-support_handoff-001 | support_handoff | human_handoff | 3 | 0 | 0 | 3 | False |
| prod-014-trust_repair-001 | trust_repair | support_only | 3 | 0 | 0 | 3 | False |
| prod-014-callback_request-002 | callback_request | callback_agreed | 3 | 0 | 0 | 3 | False |
| prod-014-cancellation_boundary-002 | cancellation_boundary | end_call | 3 | 0 | 0 | 3 | False |
| prod-014-price_objection-002 | price_objection | non_sale_correct | 3 | 0 | 0 | 3 | False |
| prod-014-sale_eligible-002 | sale_eligible | sale_ready | 3 | 0 | 0 | 3 | False |
| prod-014-support_handoff-002 | support_handoff | human_handoff | 3 | 0 | 0 | 3 | False |
| prod-014-trust_repair-002 | trust_repair | support_only | 3 | 0 | 0 | 3 | False |
| prod-014-callback_request-003 | callback_request | callback_agreed | 3 | 0 | 0 | 3 | False |
| prod-014-cancellation_boundary-003 | cancellation_boundary | end_call | 3 | 0 | 0 | 3 | False |
| prod-014-price_objection-003 | price_objection | non_sale_correct | 3 | 0 | 0 | 3 | False |
| prod-014-sale_eligible-003 | sale_eligible | sale_ready | 3 | 0 | 0 | 3 | False |
| prod-014-support_handoff-003 | support_handoff | human_handoff | 3 | 0 | 0 | 3 | False |
| prod-014-trust_repair-003 | trust_repair | support_only | 3 | 0 | 0 | 3 | False |
| prod-014-callback_request-004 | callback_request | callback_agreed | 3 | 0 | 0 | 3 | False |
| prod-014-cancellation_boundary-004 | cancellation_boundary | end_call | 3 | 0 | 0 | 3 | False |
| prod-014-price_objection-004 | price_objection | non_sale_correct | 3 | 0 | 0 | 3 | False |
| prod-014-sale_eligible-004 | sale_eligible | sale_ready | 3 | 0 | 0 | 3 | False |
| prod-014-support_handoff-004 | support_handoff | human_handoff | 3 | 0 | 0 | 3 | False |
| prod-014-trust_repair-004 | trust_repair | support_only | 3 | 0 | 0 | 3 | False |
| prod-014-callback_request-005 | callback_request | callback_agreed | 3 | 0 | 0 | 3 | False |
| prod-014-cancellation_boundary-005 | cancellation_boundary | end_call | 3 | 0 | 0 | 3 | False |
| prod-014-price_objection-005 | price_objection | non_sale_correct | 3 | 0 | 0 | 3 | False |
| prod-014-sale_eligible-005 | sale_eligible | sale_ready | 3 | 0 | 0 | 3 | False |
| prod-014-support_handoff-005 | support_handoff | human_handoff | 3 | 0 | 0 | 3 | False |
| prod-014-trust_repair-005 | trust_repair | support_only | 3 | 0 | 0 | 3 | False |
| prod-014-callback_request-006 | callback_request | callback_agreed | 3 | 0 | 0 | 3 | False |
| prod-014-cancellation_boundary-006 | cancellation_boundary | end_call | 3 | 0 | 0 | 3 | False |
| prod-014-price_objection-006 | price_objection | non_sale_correct | 3 | 0 | 0 | 3 | False |
| prod-014-sale_eligible-006 | sale_eligible | sale_ready | 3 | 0 | 0 | 3 | False |
| prod-014-support_handoff-006 | support_handoff | human_handoff | 3 | 0 | 0 | 3 | False |
| prod-014-trust_repair-006 | trust_repair | support_only | 3 | 0 | 0 | 3 | False |
| prod-014-callback_request-007 | callback_request | callback_agreed | 3 | 0 | 0 | 3 | False |
| prod-014-cancellation_boundary-007 | cancellation_boundary | end_call | 3 | 0 | 0 | 3 | False |
| prod-014-price_objection-007 | price_objection | non_sale_correct | 3 | 0 | 0 | 3 | False |
| prod-014-sale_eligible-007 | sale_eligible | sale_ready | 3 | 0 | 0 | 3 | False |
| prod-014-support_handoff-007 | support_handoff | human_handoff | 3 | 0 | 0 | 3 | False |
| prod-014-trust_repair-007 | trust_repair | support_only | 3 | 0 | 0 | 3 | False |
| prod-014-callback_request-008 | callback_request | callback_agreed | 3 | 0 | 0 | 3 | False |
| prod-014-cancellation_boundary-008 | cancellation_boundary | end_call | 3 | 0 | 0 | 3 | False |
| prod-014-price_objection-008 | price_objection | non_sale_correct | 3 | 0 | 0 | 3 | False |
| prod-014-sale_eligible-008 | sale_eligible | sale_ready | 3 | 0 | 0 | 3 | False |
| prod-014-support_handoff-008 | support_handoff | human_handoff | 3 | 0 | 0 | 3 | False |
| prod-014-trust_repair-008 | trust_repair | support_only | 3 | 0 | 0 | 3 | False |
| prod-014-callback_request-009 | callback_request | callback_agreed | 3 | 0 | 0 | 3 | False |
| prod-014-cancellation_boundary-009 | cancellation_boundary | end_call | 3 | 0 | 0 | 3 | False |
| prod-014-price_objection-009 | price_objection | non_sale_correct | 3 | 0 | 0 | 3 | False |
| prod-014-sale_eligible-009 | sale_eligible | sale_ready | 3 | 0 | 0 | 3 | False |
| prod-014-support_handoff-009 | support_handoff | human_handoff | 3 | 0 | 0 | 3 | False |
| prod-014-trust_repair-009 | trust_repair | support_only | 3 | 0 | 0 | 3 | False |
| prod-014-callback_request-010 | callback_request | callback_agreed | 3 | 0 | 0 | 3 | False |
| prod-014-cancellation_boundary-010 | cancellation_boundary | end_call | 3 | 0 | 0 | 3 | False |
| prod-014-price_objection-010 | price_objection | non_sale_correct | 3 | 0 | 0 | 3 | False |
| prod-014-sale_eligible-010 | sale_eligible | sale_ready | 3 | 0 | 0 | 3 | False |
| prod-014-support_handoff-010 | support_handoff | human_handoff | 3 | 0 | 0 | 3 | False |
| prod-014-trust_repair-010 | trust_repair | support_only | 3 | 0 | 0 | 3 | False |

## Exact Questions And Answers

### prod-014-callback_request-001::turn-001

- Scenario: `prod-014-callback_request-001` / `callback_request` / `auto_insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-001::turn-002

- Scenario: `prod-014-callback_request-001` / `callback_request` / `auto_insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `pain_point_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-001::turn-003

- Scenario: `prod-014-callback_request-001` / `callback_request` / `auto_insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-cancellation_boundary-001::turn-001

- Scenario: `prod-014-cancellation_boundary-001` / `cancellation_boundary` / `auto_insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I am confused about what you are offering, so explain the useful part before asking me to decide.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-001::turn-002

- Scenario: `prod-014-cancellation_boundary-001` / `cancellation_boundary` / `auto_insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `confused_about_offer` and needs a `current_problem_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-real-timing-check, rag010-response-so-what-clarifier, rag014-response-cost-of-inaction-check`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-001::turn-003

- Scenario: `prod-014-cancellation_boundary-001` / `cancellation_boundary` / `auto_insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-price_objection-001::turn-001

- Scenario: `prod-014-price_objection-001` / `price_objection` / `auto_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-001::turn-002

- Scenario: `prod-014-price_objection-001` / `price_objection` / `auto_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `timeline_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-001::turn-003

- Scenario: `prod-014-price_objection-001` / `price_objection` / `auto_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-001::turn-001

- Scenario: `prod-014-sale_eligible-001` / `sale_eligible` / `auto_insurance`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I am worried about being locked into something, so clarify the commitment before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag014-response-consent-based-schedule-confirmation, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-001::turn-002

- Scenario: `prod-014-sale_eligible-001` / `sale_eligible` / `auto_insurance`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `contract_fear` and needs a `usage_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-001::turn-003

- Scenario: `prod-014-sale_eligible-001` / `sale_eligible` / `auto_insurance`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-support_handoff-001::turn-001

- Scenario: `prod-014-support_handoff-001` / `support_handoff` / `auto_insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-001::turn-002

- Scenario: `prod-014-support_handoff-001` / `support_handoff` / `auto_insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `budget_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-001::turn-003

- Scenario: `prod-014-support_handoff-001` / `support_handoff` / `auto_insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-001::turn-001

- Scenario: `prod-014-trust_repair-001` / `trust_repair` / `auto_insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-001::turn-002

- Scenario: `prod-014-trust_repair-001` / `trust_repair` / `auto_insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `current_provider_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-001::turn-003

- Scenario: `prod-014-trust_repair-001` / `trust_repair` / `auto_insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-callback_request-002::turn-001

- Scenario: `prod-014-callback_request-002` / `callback_request` / `automotive`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I cannot talk now; give me one clear reason to schedule a callback.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag014-response-consent-based-schedule-confirmation, rag007-response-prep-structure, rag016a-response-autonomy-reminder`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-002::turn-002

- Scenario: `prod-014-callback_request-002` / `callback_request` / `automotive`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `no_time` and needs a `pain_point_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation, rag019-objection-diagnose-before-answering`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-002::turn-003

- Scenario: `prod-014-callback_request-002` / `callback_request` / `automotive`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-cancellation_boundary-002::turn-001

- Scenario: `prod-014-cancellation_boundary-002` / `cancellation_boundary` / `automotive`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I am hesitating, and I need you to ask what is actually holding me back.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag010-response-real-timing-check, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-002::turn-002

- Scenario: `prod-014-cancellation_boundary-002` / `cancellation_boundary` / `automotive`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `hidden_objection` and needs a `current_problem_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag014-response-cost-of-inaction-check, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-002::turn-003

- Scenario: `prod-014-cancellation_boundary-002` / `cancellation_boundary` / `automotive`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-price_objection-002::turn-001

- Scenario: `prod-014-price_objection-002` / `price_objection` / `auto_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-002::turn-002

- Scenario: `prod-014-price_objection-002` / `price_objection` / `auto_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `eligibility_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-002::turn-003

- Scenario: `prod-014-price_objection-002` / `price_objection` / `auto_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-002::turn-001

- Scenario: `prod-014-sale_eligible-002` / `sale_eligible` / `automotive`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-002::turn-002

- Scenario: `prod-014-sale_eligible-002` / `sale_eligible` / `automotive`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `decision_maker_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-real-timing-check, rag010-response-so-what-clarifier`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-002::turn-003

- Scenario: `prod-014-sale_eligible-002` / `sale_eligible` / `automotive`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-support_handoff-002::turn-001

- Scenario: `prod-014-support_handoff-002` / `support_handoff` / `automotive`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-002::turn-002

- Scenario: `prod-014-support_handoff-002` / `support_handoff` / `automotive`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `priority_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-real-timing-check, rag010-response-so-what-clarifier`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-002::turn-003

- Scenario: `prod-014-support_handoff-002` / `support_handoff` / `automotive`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-002::turn-001

- Scenario: `prod-014-trust_repair-002` / `trust_repair` / `automotive`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-002::turn-002

- Scenario: `prod-014-trust_repair-002` / `trust_repair` / `automotive`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `budget_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-002::turn-003

- Scenario: `prod-014-trust_repair-002` / `trust_repair` / `automotive`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-callback_request-003::turn-001

- Scenario: `prod-014-callback_request-003` / `callback_request` / `general_customer_service`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-003::turn-002

- Scenario: `prod-014-callback_request-003` / `callback_request` / `general_customer_service`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `eligibility_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-003::turn-003

- Scenario: `prod-014-callback_request-003` / `callback_request` / `general_customer_service`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-cancellation_boundary-003::turn-001

- Scenario: `prod-014-cancellation_boundary-003` / `cancellation_boundary` / `general_customer_service`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `influenced`
- Hard failure: `False`

Exact customer question:

```text
I cannot decide alone, so help me understand what I would need to discuss with the other decision maker.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `influenced` and item IDs `rag010-response-real-timing-check, rag010-voice-cadence-as-weak-context, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-003::turn-002

- Scenario: `prod-014-cancellation_boundary-003` / `cancellation_boundary` / `general_customer_service`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `blocked`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_spouse_or_manager` and needs a `pain_point_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `blocked` with status `blocked` and item IDs `none`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-003::turn-003

- Scenario: `prod-014-cancellation_boundary-003` / `cancellation_boundary` / `general_customer_service`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-price_objection-003::turn-001

- Scenario: `prod-014-price_objection-003` / `price_objection` / `automotive`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-003::turn-002

- Scenario: `prod-014-price_objection-003` / `price_objection` / `automotive`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `usage_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-003::turn-003

- Scenario: `prod-014-price_objection-003` / `price_objection` / `automotive`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-003::turn-001

- Scenario: `prod-014-sale_eligible-003` / `sale_eligible` / `general_customer_service`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-003::turn-002

- Scenario: `prod-014-sale_eligible-003` / `sale_eligible` / `general_customer_service`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `current_provider_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-003::turn-003

- Scenario: `prod-014-sale_eligible-003` / `sale_eligible` / `general_customer_service`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-support_handoff-003::turn-001

- Scenario: `prod-014-support_handoff-003` / `support_handoff` / `general_customer_service`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-003::turn-002

- Scenario: `prod-014-support_handoff-003` / `support_handoff` / `general_customer_service`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `current_problem_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag014-response-cost-of-inaction-check, rag019-objection-diagnose-before-answering`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-003::turn-003

- Scenario: `prod-014-support_handoff-003` / `support_handoff` / `general_customer_service`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-003::turn-001

- Scenario: `prod-014-trust_repair-003` / `trust_repair` / `general_customer_service`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-003::turn-002

- Scenario: `prod-014-trust_repair-003` / `trust_repair` / `general_customer_service`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `budget_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-003::turn-003

- Scenario: `prod-014-trust_repair-003` / `trust_repair` / `general_customer_service`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-callback_request-004::turn-001

- Scenario: `prod-014-callback_request-004` / `callback_request` / `healthcare_insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-004::turn-002

- Scenario: `prod-014-callback_request-004` / `callback_request` / `healthcare_insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `timeline_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-004::turn-003

- Scenario: `prod-014-callback_request-004` / `callback_request` / `healthcare_insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-cancellation_boundary-004::turn-001

- Scenario: `prod-014-cancellation_boundary-004` / `cancellation_boundary` / `healthcare_insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-004::turn-002

- Scenario: `prod-014-cancellation_boundary-004` / `cancellation_boundary` / `healthcare_insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `pain_point_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-004::turn-003

- Scenario: `prod-014-cancellation_boundary-004` / `cancellation_boundary` / `healthcare_insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-price_objection-004::turn-001

- Scenario: `prod-014-price_objection-004` / `price_objection` / `automotive`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-004::turn-002

- Scenario: `prod-014-price_objection-004` / `price_objection` / `automotive`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `timeline_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-004::turn-003

- Scenario: `prod-014-price_objection-004` / `price_objection` / `automotive`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-004::turn-001

- Scenario: `prod-014-sale_eligible-004` / `sale_eligible` / `healthcare_insurance`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-004::turn-002

- Scenario: `prod-014-sale_eligible-004` / `sale_eligible` / `healthcare_insurance`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `current_provider_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag014-response-cost-of-inaction-check, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-004::turn-003

- Scenario: `prod-014-sale_eligible-004` / `sale_eligible` / `healthcare_insurance`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-support_handoff-004::turn-001

- Scenario: `prod-014-support_handoff-004` / `support_handoff` / `healthcare_insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-004::turn-002

- Scenario: `prod-014-support_handoff-004` / `support_handoff` / `healthcare_insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `current_problem_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag014-response-cost-of-inaction-check, rag019-objection-diagnose-before-answering`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-004::turn-003

- Scenario: `prod-014-support_handoff-004` / `support_handoff` / `healthcare_insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-004::turn-001

- Scenario: `prod-014-trust_repair-004` / `trust_repair` / `healthcare_insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `influenced`
- Hard failure: `False`

Exact customer question:

```text
I cannot decide alone, so help me understand what I would need to discuss with the other decision maker.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `influenced` and item IDs `rag010-response-real-timing-check, rag010-voice-cadence-as-weak-context, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-004::turn-002

- Scenario: `prod-014-trust_repair-004` / `trust_repair` / `healthcare_insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `blocked`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_spouse_or_manager` and needs a `priority_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `blocked` with status `blocked` and item IDs `none`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-004::turn-003

- Scenario: `prod-014-trust_repair-004` / `trust_repair` / `healthcare_insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-callback_request-005::turn-001

- Scenario: `prod-014-callback_request-005` / `callback_request` / `home_service`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-005::turn-002

- Scenario: `prod-014-callback_request-005` / `callback_request` / `home_service`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `timeline_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-005::turn-003

- Scenario: `prod-014-callback_request-005` / `callback_request` / `home_service`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-cancellation_boundary-005::turn-001

- Scenario: `prod-014-cancellation_boundary-005` / `cancellation_boundary` / `home_service`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I am hesitating, and I need you to ask what is actually holding me back.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag010-response-real-timing-check, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-005::turn-002

- Scenario: `prod-014-cancellation_boundary-005` / `cancellation_boundary` / `home_service`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `hidden_objection` and needs a `eligibility_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-005::turn-003

- Scenario: `prod-014-cancellation_boundary-005` / `cancellation_boundary` / `home_service`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-price_objection-005::turn-001

- Scenario: `prod-014-price_objection-005` / `price_objection` / `general_customer_service`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-005::turn-002

- Scenario: `prod-014-price_objection-005` / `price_objection` / `general_customer_service`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `usage_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-005::turn-003

- Scenario: `prod-014-price_objection-005` / `price_objection` / `general_customer_service`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-005::turn-001

- Scenario: `prod-014-sale_eligible-005` / `sale_eligible` / `home_service`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I am hesitating, and I need you to ask what is actually holding me back.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag010-response-real-timing-check, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-005::turn-002

- Scenario: `prod-014-sale_eligible-005` / `sale_eligible` / `home_service`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `hidden_objection` and needs a `budget_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-005::turn-003

- Scenario: `prod-014-sale_eligible-005` / `sale_eligible` / `home_service`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-support_handoff-005::turn-001

- Scenario: `prod-014-support_handoff-005` / `support_handoff` / `home_service`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-005::turn-002

- Scenario: `prod-014-support_handoff-005` / `support_handoff` / `home_service`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `pain_point_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-005::turn-003

- Scenario: `prod-014-support_handoff-005` / `support_handoff` / `home_service`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-005::turn-001

- Scenario: `prod-014-trust_repair-005` / `trust_repair` / `home_service`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-005::turn-002

- Scenario: `prod-014-trust_repair-005` / `trust_repair` / `home_service`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `current_problem_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-005::turn-003

- Scenario: `prod-014-trust_repair-005` / `trust_repair` / `home_service`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-callback_request-006::turn-001

- Scenario: `prod-014-callback_request-006` / `callback_request` / `insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-006::turn-002

- Scenario: `prod-014-callback_request-006` / `callback_request` / `insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `usage_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-006::turn-003

- Scenario: `prod-014-callback_request-006` / `callback_request` / `insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-cancellation_boundary-006::turn-001

- Scenario: `prod-014-cancellation_boundary-006` / `cancellation_boundary` / `insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-006::turn-002

- Scenario: `prod-014-cancellation_boundary-006` / `cancellation_boundary` / `insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `timeline_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-006::turn-003

- Scenario: `prod-014-cancellation_boundary-006` / `cancellation_boundary` / `insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-price_objection-006::turn-001

- Scenario: `prod-014-price_objection-006` / `price_objection` / `general_customer_service`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-006::turn-002

- Scenario: `prod-014-price_objection-006` / `price_objection` / `general_customer_service`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `timeline_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-006::turn-003

- Scenario: `prod-014-price_objection-006` / `price_objection` / `general_customer_service`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-006::turn-001

- Scenario: `prod-014-sale_eligible-006` / `sale_eligible` / `home_service`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I am hesitating, and I need you to ask what is actually holding me back.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag010-response-real-timing-check, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-006::turn-002

- Scenario: `prod-014-sale_eligible-006` / `sale_eligible` / `home_service`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `hidden_objection` and needs a `current_provider_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-006::turn-003

- Scenario: `prod-014-sale_eligible-006` / `sale_eligible` / `home_service`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-support_handoff-006::turn-001

- Scenario: `prod-014-support_handoff-006` / `support_handoff` / `insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-006::turn-002

- Scenario: `prod-014-support_handoff-006` / `support_handoff` / `insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `pain_point_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-006::turn-003

- Scenario: `prod-014-support_handoff-006` / `support_handoff` / `insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-006::turn-001

- Scenario: `prod-014-trust_repair-006` / `trust_repair` / `insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-006::turn-002

- Scenario: `prod-014-trust_repair-006` / `trust_repair` / `insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `current_problem_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag014-response-cost-of-inaction-check, rag019-objection-diagnose-before-answering`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-006::turn-003

- Scenario: `prod-014-trust_repair-006` / `trust_repair` / `insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-callback_request-007::turn-001

- Scenario: `prod-014-callback_request-007` / `callback_request` / `medical_equipment`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-007::turn-002

- Scenario: `prod-014-callback_request-007` / `callback_request` / `medical_equipment`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `usage_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-007::turn-003

- Scenario: `prod-014-callback_request-007` / `callback_request` / `medical_equipment`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-cancellation_boundary-007::turn-001

- Scenario: `prod-014-cancellation_boundary-007` / `cancellation_boundary` / `medical_equipment`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-007::turn-002

- Scenario: `prod-014-cancellation_boundary-007` / `cancellation_boundary` / `medical_equipment`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `timeline_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-007::turn-003

- Scenario: `prod-014-cancellation_boundary-007` / `cancellation_boundary` / `medical_equipment`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-price_objection-007::turn-001

- Scenario: `prod-014-price_objection-007` / `price_objection` / `healthcare_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-007::turn-002

- Scenario: `prod-014-price_objection-007` / `price_objection` / `healthcare_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `decision_maker_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-real-timing-check, rag010-response-so-what-clarifier`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-007::turn-003

- Scenario: `prod-014-price_objection-007` / `price_objection` / `healthcare_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-007::turn-001

- Scenario: `prod-014-sale_eligible-007` / `sale_eligible` / `insurance`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I am worried about being locked into something, so clarify the commitment before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag014-response-consent-based-schedule-confirmation, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-007::turn-002

- Scenario: `prod-014-sale_eligible-007` / `sale_eligible` / `insurance`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `contract_fear` and needs a `budget_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-007::turn-003

- Scenario: `prod-014-sale_eligible-007` / `sale_eligible` / `insurance`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-support_handoff-007::turn-001

- Scenario: `prod-014-support_handoff-007` / `support_handoff` / `medical_equipment`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-007::turn-002

- Scenario: `prod-014-support_handoff-007` / `support_handoff` / `medical_equipment`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `eligibility_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-007::turn-003

- Scenario: `prod-014-support_handoff-007` / `support_handoff` / `medical_equipment`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-007::turn-001

- Scenario: `prod-014-trust_repair-007` / `trust_repair` / `medical_equipment`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-007::turn-002

- Scenario: `prod-014-trust_repair-007` / `trust_repair` / `medical_equipment`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `pain_point_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-007::turn-003

- Scenario: `prod-014-trust_repair-007` / `trust_repair` / `medical_equipment`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-callback_request-008::turn-001

- Scenario: `prod-014-callback_request-008` / `callback_request` / `medicare`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-008::turn-002

- Scenario: `prod-014-callback_request-008` / `callback_request` / `medicare`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `decision_maker_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-real-timing-check, rag010-response-so-what-clarifier`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-008::turn-003

- Scenario: `prod-014-callback_request-008` / `callback_request` / `medicare`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-cancellation_boundary-008::turn-001

- Scenario: `prod-014-cancellation_boundary-008` / `cancellation_boundary` / `medicare`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-008::turn-002

- Scenario: `prod-014-cancellation_boundary-008` / `cancellation_boundary` / `medicare`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `usage_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-008::turn-003

- Scenario: `prod-014-cancellation_boundary-008` / `cancellation_boundary` / `medicare`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-price_objection-008::turn-001

- Scenario: `prod-014-price_objection-008` / `price_objection` / `healthcare_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-008::turn-002

- Scenario: `prod-014-price_objection-008` / `price_objection` / `healthcare_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `usage_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-008::turn-003

- Scenario: `prod-014-price_objection-008` / `price_objection` / `healthcare_insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-008::turn-001

- Scenario: `prod-014-sale_eligible-008` / `sale_eligible` / `medical_equipment`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-008::turn-002

- Scenario: `prod-014-sale_eligible-008` / `sale_eligible` / `medical_equipment`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `priority_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-real-timing-check, rag010-response-so-what-clarifier`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-008::turn-003

- Scenario: `prod-014-sale_eligible-008` / `sale_eligible` / `medical_equipment`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-support_handoff-008::turn-001

- Scenario: `prod-014-support_handoff-008` / `support_handoff` / `medicare`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-008::turn-002

- Scenario: `prod-014-support_handoff-008` / `support_handoff` / `medicare`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `timeline_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-008::turn-003

- Scenario: `prod-014-support_handoff-008` / `support_handoff` / `medicare`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-008::turn-001

- Scenario: `prod-014-trust_repair-008` / `trust_repair` / `medicare`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-008::turn-002

- Scenario: `prod-014-trust_repair-008` / `trust_repair` / `medicare`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `pain_point_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-008::turn-003

- Scenario: `prod-014-trust_repair-008` / `trust_repair` / `medicare`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-callback_request-009::turn-001

- Scenario: `prod-014-callback_request-009` / `callback_request` / `auto_insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-009::turn-002

- Scenario: `prod-014-callback_request-009` / `callback_request` / `auto_insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `current_provider_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-009::turn-003

- Scenario: `prod-014-callback_request-009` / `callback_request` / `auto_insurance`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-cancellation_boundary-009::turn-001

- Scenario: `prod-014-cancellation_boundary-009` / `cancellation_boundary` / `auto_insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-009::turn-002

- Scenario: `prod-014-cancellation_boundary-009` / `cancellation_boundary` / `auto_insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `usage_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-009::turn-003

- Scenario: `prod-014-cancellation_boundary-009` / `cancellation_boundary` / `auto_insurance`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-price_objection-009::turn-001

- Scenario: `prod-014-price_objection-009` / `price_objection` / `home_service`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-009::turn-002

- Scenario: `prod-014-price_objection-009` / `price_objection` / `home_service`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `usage_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-009::turn-003

- Scenario: `prod-014-price_objection-009` / `price_objection` / `home_service`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-009::turn-001

- Scenario: `prod-014-sale_eligible-009` / `sale_eligible` / `medicare`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `influenced`
- Hard failure: `False`

Exact customer question:

```text
I cannot decide alone, so help me understand what I would need to discuss with the other decision maker.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `influenced` and item IDs `rag010-response-real-timing-check, rag010-voice-cadence-as-weak-context, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-009::turn-002

- Scenario: `prod-014-sale_eligible-009` / `sale_eligible` / `medicare`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `blocked`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_spouse_or_manager` and needs a `current_problem_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `blocked` with status `blocked` and item IDs `none`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-009::turn-003

- Scenario: `prod-014-sale_eligible-009` / `sale_eligible` / `medicare`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-support_handoff-009::turn-001

- Scenario: `prod-014-support_handoff-009` / `support_handoff` / `auto_insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-009::turn-002

- Scenario: `prod-014-support_handoff-009` / `support_handoff` / `auto_insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `timeline_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-009::turn-003

- Scenario: `prod-014-support_handoff-009` / `support_handoff` / `auto_insurance`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-009::turn-001

- Scenario: `prod-014-trust_repair-009` / `trust_repair` / `auto_insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-009::turn-002

- Scenario: `prod-014-trust_repair-009` / `trust_repair` / `auto_insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `eligibility_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-009::turn-003

- Scenario: `prod-014-trust_repair-009` / `trust_repair` / `auto_insurance`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-callback_request-010::turn-001

- Scenario: `prod-014-callback_request-010` / `callback_request` / `automotive`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-010::turn-002

- Scenario: `prod-014-callback_request-010` / `callback_request` / `automotive`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `current_provider_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-callback_request-010::turn-003

- Scenario: `prod-014-callback_request-010` / `callback_request` / `automotive`
- Expected outcome: `callback_agreed`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-cancellation_boundary-010::turn-001

- Scenario: `prod-014-cancellation_boundary-010` / `cancellation_boundary` / `automotive`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-010::turn-002

- Scenario: `prod-014-cancellation_boundary-010` / `cancellation_boundary` / `automotive`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `decision_maker_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-real-timing-check, rag010-response-so-what-clarifier`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-cancellation_boundary-010::turn-003

- Scenario: `prod-014-cancellation_boundary-010` / `cancellation_boundary` / `automotive`
- Expected outcome: `end_call`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-price_objection-010::turn-001

- Scenario: `prod-014-price_objection-010` / `price_objection` / `insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-010::turn-002

- Scenario: `prod-014-price_objection-010` / `price_objection` / `insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `current_provider_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-price_objection-010::turn-003

- Scenario: `prod-014-price_objection-010` / `price_objection` / `insurance`
- Expected outcome: `non_sale_correct`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-010::turn-001

- Scenario: `prod-014-sale_eligible-010` / `sale_eligible` / `medicare`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I need time to think, so do not rush me into a decision.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-real-timing-check, rag010-response-impact-bridge, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-010::turn-002

- Scenario: `prod-014-sale_eligible-010` / `sale_eligible` / `medicare`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `needs_to_think` and needs a `budget_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-sale_eligible-010::turn-003

- Scenario: `prod-014-sale_eligible-010` / `sale_eligible` / `medicare`
- Expected outcome: `sale_ready`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `5`, retrieval `5`, winner `tie`.

### prod-014-support_handoff-010::turn-001

- Scenario: `prod-014-support_handoff-010` / `support_handoff` / `automotive`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
I do not want to discuss payment; explain the next non-payment step if there is one.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge, rag010-response-real-timing-check`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-010::turn-002

- Scenario: `prod-014-support_handoff-010` / `support_handoff` / `automotive`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `payment_fear` and needs a `usage_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-support_handoff-010::turn-003

- Scenario: `prod-014-support_handoff-010` / `support_handoff` / `automotive`
- Expected outcome: `human_handoff`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-010::turn-001

- Scenario: `prod-014-trust_repair-010` / `trust_repair` / `automotive`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Before I decide, I need the cost explained in plain terms and why it is worth considering.
```

Exact old runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Exact retrieval runtime answer:

```text
Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag014-response-cost-of-inaction-check, rag010-response-so-what-clarifier, rag019-objection-diagnose-before-answering, rag010-response-impact-bridge`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-010::turn-002

- Scenario: `prod-014-trust_repair-010` / `trust_repair` / `automotive`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer raises `too_expensive` and needs a `timeline_question` before any close.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag010-response-impact-bridge, rag019-objection-diagnose-before-answering, rag010-response-so-what-clarifier, rag014-response-consent-based-schedule-confirmation`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

### prod-014-trust_repair-010::turn-003

- Scenario: `prod-014-trust_repair-010` / `trust_repair` / `automotive`
- Expected outcome: `support_only`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Hard failure: `False`

Exact customer question:

```text
Customer asks what the next safe step would be.
```

Exact old runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Exact retrieval runtime answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Decision trace:

1. Old runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
2. Retrieval runtime classified sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
3. Retrieval decision `candidate_packet_created` with status `retrieved_not_used` and item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag019-objection-timing-priority-fit, rag007-voice-tone-mismatch-uncertainty`.
4. Scoring: old `4`, retrieval `4`, winner `tie`.

## Runtime Boundary

PROD-015 changes no runtime behavior. Retrieval remains disabled by default. The result is ready for review, not a runtime promotion.
