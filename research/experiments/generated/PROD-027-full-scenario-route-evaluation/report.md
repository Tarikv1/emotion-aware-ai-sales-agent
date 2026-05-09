# PROD-027 Full Scenario Route Evaluation

PROD-027 runs a strong full scenario route evaluation from the PROD-014 CallCenterEN abstract scenario bank. It expands selected pattern-derived scenarios into multi-turn route tests without copying source transcript text.

## Summary

- Source checkpoint: `PROD-014-callcenteren-scenario-bank`
- Strong evaluation set: `true`
- Full scenarios: `20`
- Turns per scenario: `6`
- Total turns: `120`
- Exact customer turns visible: `true`
- Exact agent answers visible: `true`
- Route decision process visible: `true`
- Local evaluation only: `true`
- Provider calls made: `false`
- Customer data allowed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Hard failures: `0`
- Payment collection count: `0`
- Leakage findings: `0`
- Decision: `route_gaps_found_review_before_demo`
- Next checkpoint recommended: `PROD-028-full-scenario-demo-review`

## Metrics

- route_correctness: `0.9167`
- policy_action_correctness: `0.9167`
- call_control_correctness: `0.975`
- scenario_route_pass_rate: `0.65`
- non_sale_correctness: `1.0`
- safe_close_correctness: `1.0`
- discovery_before_close_rate: `0.95`
- emotion_handling_score: `0.9083`
- hard_failure_rate: `0.0`
- leakage_failure_rate: `0.0`

## Scenario Route Table

| Scenario | Label | Domain | Route Turns | Passed | Hard Failure |
| --- | --- | --- | ---: | --- | --- |
| prod-027-scenario-001 | sale_eligible | auto_insurance | 6/6 | True | False |
| prod-027-scenario-002 | price_objection | auto_insurance | 4/6 | False | False |
| prod-027-scenario-003 | callback_request | auto_insurance | 5/6 | False | False |
| prod-027-scenario-004 | cancellation_boundary | auto_insurance | 6/6 | True | False |
| prod-027-scenario-005 | support_handoff | auto_insurance | 6/6 | True | False |
| prod-027-scenario-006 | trust_repair | auto_insurance | 6/6 | True | False |
| prod-027-scenario-007 | sale_eligible | automotive | 6/6 | True | False |
| prod-027-scenario-008 | price_objection | auto_insurance | 4/6 | False | False |
| prod-027-scenario-009 | callback_request | automotive | 5/6 | False | False |
| prod-027-scenario-010 | cancellation_boundary | automotive | 6/6 | True | False |
| prod-027-scenario-011 | support_handoff | automotive | 6/6 | True | False |
| prod-027-scenario-012 | trust_repair | automotive | 6/6 | True | False |
| prod-027-scenario-013 | sale_eligible | general_customer_service | 6/6 | True | False |
| prod-027-scenario-014 | price_objection | automotive | 4/6 | False | False |
| prod-027-scenario-015 | callback_request | general_customer_service | 5/6 | False | False |
| prod-027-scenario-016 | cancellation_boundary | general_customer_service | 6/6 | True | False |
| prod-027-scenario-017 | support_handoff | general_customer_service | 6/6 | True | False |
| prod-027-scenario-018 | trust_repair | general_customer_service | 6/6 | True | False |
| prod-027-scenario-019 | sale_eligible | healthcare_insurance | 6/6 | True | False |
| prod-027-scenario-020 | price_objection | automotive | 5/6 | False | False |

## Exact Full Scenario Traces

### prod-027-scenario-001 - sale_eligible

- Source scenario: `prod-014-sale_eligible-001`
- Expected outcome: `sale_ready`
- Review status: `pending-manual-review`

#### prod-027-scenario-001::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-001::turn-002

- Stage: `discovery`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-001::turn-003

- Stage: `comparison`
- Expected policy action: `fair-compare`
- Observed policy action: `fair-compare`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `provider-comparison`
- Strategy: `inquiry`

Exact customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Exact agent answer:

```text
That is fair. Should we compare price, terms, or fit first without pressure?
```

#### prod-027-scenario-001::turn-004

- Stage: `autonomy_check`
- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `autonomy-check`
- Strategy: `inquiry`

Exact customer turn:

```text
I need time to think; do not rush me into a commitment today.
```

Exact agent answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

#### prod-027-scenario-001::turn-005

- Stage: `sale_ready_check`
- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `True`
- Sales difficulty: `sale-ready-commitment`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Exact agent answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

#### prod-027-scenario-001::turn-006

- Stage: `commitment_confirmation`
- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `True`
- Sales difficulty: `sale-ready-commitment`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
I am giving a verbal commitment to the next step, not payment.
```

Exact agent answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

### prod-027-scenario-002 - price_objection

- Source scenario: `prod-014-price_objection-001`
- Expected outcome: `non_sale_correct`
- Review status: `pending-manual-review`

#### prod-027-scenario-002::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-002::turn-002

- Stage: `price_discussion`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
The price is my main concern, so explain value before asking me to decide.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-002::turn-003

- Stage: `objection_handling`
- Expected policy action: `clarify-fit`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `False`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
My specific objection is too expensive, and I need a practical answer before moving forward.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-002::turn-004

- Stage: `value_check`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
I need to know whether this is worth the effort before I spend more time on it.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-002::turn-005

- Stage: `autonomy_check`
- Expected policy action: `autonomy-check`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `False`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I do not want to be rushed, so ask what I need before any next step.
```

Exact agent answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

#### prod-027-scenario-002::turn-006

- Stage: `written_info`
- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `procurement-review`
- Strategy: `inquiry`

Exact customer turn:

```text
Send written information so I can review it without giving you anything firm today.
```

Exact agent answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

### prod-027-scenario-003 - callback_request

- Source scenario: `prod-014-callback_request-001`
- Expected outcome: `callback_agreed`
- Review status: `pending-manual-review`

#### prod-027-scenario-003::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-003::turn-002

- Stage: `time_boundary`
- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `autonomy-check`
- Strategy: `inquiry`

Exact customer turn:

```text
I cannot talk now; call back later if there is a real reason.
```

Exact agent answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

#### prod-027-scenario-003::turn-003

- Stage: `callback_reason`
- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `autonomy-check`
- Strategy: `inquiry`

Exact customer turn:

```text
Before a callback later, tell me the one point that makes this worth reviewing.
```

Exact agent answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

#### prod-027-scenario-003::turn-004

- Stage: `timing_delay`
- Expected policy action: `autonomy-follow-up`
- Observed policy action: `autonomy-follow-up`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `timing-delay`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
Maybe next week, but nothing firm from me yet.
```

Exact agent answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

#### prod-027-scenario-003::turn-005

- Stage: `callback_time`
- Expected policy action: `schedule-callback`
- Observed policy action: `schedule-callback`
- Expected call control: `schedule-and-end`
- Observed call control: `schedule-and-end`
- Route correct: `True`
- Sales difficulty: `scheduling-confirmation`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
Wednesday 10 works for a callback.
```

Exact agent answer:

```text
Confirmed. I will record that callback time for the specialist. Goodbye.
```

#### prod-027-scenario-003::turn-006

- Stage: `wrap_up`
- Expected policy action: `schedule-callback`
- Observed policy action: `human-escalation`
- Expected call control: `schedule-and-end`
- Observed call control: `transfer-or-escalate`
- Route correct: `False`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
Use Wednesday 10 works and keep it as a specialist callback only.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### prod-027-scenario-004 - cancellation_boundary

- Source scenario: `prod-014-cancellation_boundary-001`
- Expected outcome: `end_call`
- Review status: `pending-manual-review`

#### prod-027-scenario-004::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-004::turn-002

- Stage: `boundary`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
I am not interested in continuing this sales conversation.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-004::turn-003

- Stage: `suppression`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
Do not call me again about this.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-004::turn-004

- Stage: `repeat_boundary`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
Stop calling; I do not want a follow-up.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-004::turn-005

- Stage: `closing`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
No thank you, end the call.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-004::turn-006

- Stage: `final_boundary`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
Please mark this as do not call.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

### prod-027-scenario-005 - support_handoff

- Source scenario: `prod-014-support_handoff-001`
- Expected outcome: `human_handoff`
- Review status: `pending-manual-review`

#### prod-027-scenario-005::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-005::turn-002

- Stage: `support_need`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
My service issue is unresolved and I need a human specialist before any offer.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

#### prod-027-scenario-005::turn-003

- Stage: `detail_lookup`
- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `True`
- Sales difficulty: `product-detail-lookup`
- Strategy: `evidence-or-benefit`

Exact customer turn:

```text
Which exact service details are included? I do not want you to guess.
```

Exact agent answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

#### prod-027-scenario-005::turn-004

- Stage: `human_request`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
I want a representative or advisor to handle this.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

#### prod-027-scenario-005::turn-005

- Stage: `verification`
- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `True`
- Sales difficulty: `product-detail-lookup`
- Strategy: `evidence-or-benefit`

Exact customer turn:

```text
Check the approved service details before answering.
```

Exact agent answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

#### prod-027-scenario-005::turn-006

- Stage: `handoff`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
Route me to a specialist instead of continuing automatically.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### prod-027-scenario-006 - trust_repair

- Source scenario: `prod-014-trust_repair-001`
- Expected outcome: `support_only`
- Review status: `pending-manual-review`

#### prod-027-scenario-006::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-006::turn-002

- Stage: `trust_gap`
- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `trust-gap`
- Strategy: `rapport`

Exact customer turn:

```text
I do not know your company. How can I verify this is legitimate?
```

Exact agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

#### prod-027-scenario-006::turn-003

- Stage: `verification`
- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `trust-gap`
- Strategy: `rapport`

Exact customer turn:

```text
I do not trust this yet, so give me a verification path before any next step.
```

Exact agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

#### prod-027-scenario-006::turn-004

- Stage: `written_context`
- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `procurement-review`
- Strategy: `inquiry`

Exact customer turn:

```text
Send written information so I can check it before speaking further.
```

Exact agent answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

#### prod-027-scenario-006::turn-005

- Stage: `human_review`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
I want a human advisor if this goes any further.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

#### prod-027-scenario-006::turn-006

- Stage: `trust_repair`
- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `trust-gap`
- Strategy: `rapport`

Exact customer turn:

```text
Before continuing, verify this is legitimate without asking me to commit.
```

Exact agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

### prod-027-scenario-007 - sale_eligible

- Source scenario: `prod-014-sale_eligible-002`
- Expected outcome: `sale_ready`
- Review status: `pending-manual-review`

#### prod-027-scenario-007::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-007::turn-002

- Stage: `discovery`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-007::turn-003

- Stage: `comparison`
- Expected policy action: `fair-compare`
- Observed policy action: `fair-compare`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `provider-comparison`
- Strategy: `inquiry`

Exact customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Exact agent answer:

```text
That is fair. Should we compare price, terms, or fit first without pressure?
```

#### prod-027-scenario-007::turn-004

- Stage: `autonomy_check`
- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `autonomy-check`
- Strategy: `inquiry`

Exact customer turn:

```text
I need time to think; do not rush me into a commitment today.
```

Exact agent answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

#### prod-027-scenario-007::turn-005

- Stage: `sale_ready_check`
- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `True`
- Sales difficulty: `sale-ready-commitment`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Exact agent answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

#### prod-027-scenario-007::turn-006

- Stage: `commitment_confirmation`
- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `True`
- Sales difficulty: `sale-ready-commitment`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
I am giving a verbal commitment to the next step, not payment.
```

Exact agent answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

### prod-027-scenario-008 - price_objection

- Source scenario: `prod-014-price_objection-002`
- Expected outcome: `non_sale_correct`
- Review status: `pending-manual-review`

#### prod-027-scenario-008::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-008::turn-002

- Stage: `price_discussion`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
The price is my main concern, so explain value before asking me to decide.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-008::turn-003

- Stage: `objection_handling`
- Expected policy action: `clarify-fit`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `False`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
My specific objection is too expensive, and I need a practical answer before moving forward.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-008::turn-004

- Stage: `value_check`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
I need to know whether this is worth the effort before I spend more time on it.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-008::turn-005

- Stage: `autonomy_check`
- Expected policy action: `autonomy-check`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `False`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I do not want to be rushed, so ask what I need before any next step.
```

Exact agent answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

#### prod-027-scenario-008::turn-006

- Stage: `written_info`
- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `procurement-review`
- Strategy: `inquiry`

Exact customer turn:

```text
Send written information so I can review it without giving you anything firm today.
```

Exact agent answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

### prod-027-scenario-009 - callback_request

- Source scenario: `prod-014-callback_request-002`
- Expected outcome: `callback_agreed`
- Review status: `pending-manual-review`

#### prod-027-scenario-009::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-009::turn-002

- Stage: `time_boundary`
- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `autonomy-check`
- Strategy: `inquiry`

Exact customer turn:

```text
I cannot talk now; call back later if there is a real reason.
```

Exact agent answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

#### prod-027-scenario-009::turn-003

- Stage: `callback_reason`
- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `autonomy-check`
- Strategy: `inquiry`

Exact customer turn:

```text
Before a callback later, tell me the one point that makes this worth reviewing.
```

Exact agent answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

#### prod-027-scenario-009::turn-004

- Stage: `timing_delay`
- Expected policy action: `autonomy-follow-up`
- Observed policy action: `autonomy-follow-up`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `timing-delay`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
Maybe next week, but nothing firm from me yet.
```

Exact agent answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

#### prod-027-scenario-009::turn-005

- Stage: `callback_time`
- Expected policy action: `schedule-callback`
- Observed policy action: `schedule-callback`
- Expected call control: `schedule-and-end`
- Observed call control: `schedule-and-end`
- Route correct: `True`
- Sales difficulty: `scheduling-confirmation`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
Wednesday 10 works for a callback.
```

Exact agent answer:

```text
Confirmed. I will record that callback time for the specialist. Goodbye.
```

#### prod-027-scenario-009::turn-006

- Stage: `wrap_up`
- Expected policy action: `schedule-callback`
- Observed policy action: `human-escalation`
- Expected call control: `schedule-and-end`
- Observed call control: `transfer-or-escalate`
- Route correct: `False`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
Use Wednesday 10 works and keep it as a specialist callback only.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### prod-027-scenario-010 - cancellation_boundary

- Source scenario: `prod-014-cancellation_boundary-002`
- Expected outcome: `end_call`
- Review status: `pending-manual-review`

#### prod-027-scenario-010::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-010::turn-002

- Stage: `boundary`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
I am not interested in continuing this sales conversation.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-010::turn-003

- Stage: `suppression`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
Do not call me again about this.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-010::turn-004

- Stage: `repeat_boundary`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
Stop calling; I do not want a follow-up.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-010::turn-005

- Stage: `closing`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
No thank you, end the call.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-010::turn-006

- Stage: `final_boundary`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
Please mark this as do not call.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

### prod-027-scenario-011 - support_handoff

- Source scenario: `prod-014-support_handoff-002`
- Expected outcome: `human_handoff`
- Review status: `pending-manual-review`

#### prod-027-scenario-011::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-011::turn-002

- Stage: `support_need`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
My service issue is unresolved and I need a human specialist before any offer.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

#### prod-027-scenario-011::turn-003

- Stage: `detail_lookup`
- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `True`
- Sales difficulty: `product-detail-lookup`
- Strategy: `evidence-or-benefit`

Exact customer turn:

```text
Which exact service details are included? I do not want you to guess.
```

Exact agent answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

#### prod-027-scenario-011::turn-004

- Stage: `human_request`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
I want a representative or advisor to handle this.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

#### prod-027-scenario-011::turn-005

- Stage: `verification`
- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `True`
- Sales difficulty: `product-detail-lookup`
- Strategy: `evidence-or-benefit`

Exact customer turn:

```text
Check the approved service details before answering.
```

Exact agent answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

#### prod-027-scenario-011::turn-006

- Stage: `handoff`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
Route me to a specialist instead of continuing automatically.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### prod-027-scenario-012 - trust_repair

- Source scenario: `prod-014-trust_repair-002`
- Expected outcome: `support_only`
- Review status: `pending-manual-review`

#### prod-027-scenario-012::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-012::turn-002

- Stage: `trust_gap`
- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `trust-gap`
- Strategy: `rapport`

Exact customer turn:

```text
I do not know your company. How can I verify this is legitimate?
```

Exact agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

#### prod-027-scenario-012::turn-003

- Stage: `verification`
- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `trust-gap`
- Strategy: `rapport`

Exact customer turn:

```text
I do not trust this yet, so give me a verification path before any next step.
```

Exact agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

#### prod-027-scenario-012::turn-004

- Stage: `written_context`
- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `procurement-review`
- Strategy: `inquiry`

Exact customer turn:

```text
Send written information so I can check it before speaking further.
```

Exact agent answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

#### prod-027-scenario-012::turn-005

- Stage: `human_review`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
I want a human advisor if this goes any further.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

#### prod-027-scenario-012::turn-006

- Stage: `trust_repair`
- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `trust-gap`
- Strategy: `rapport`

Exact customer turn:

```text
Before continuing, verify this is legitimate without asking me to commit.
```

Exact agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

### prod-027-scenario-013 - sale_eligible

- Source scenario: `prod-014-sale_eligible-003`
- Expected outcome: `sale_ready`
- Review status: `pending-manual-review`

#### prod-027-scenario-013::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this general customer service option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-013::turn-002

- Stage: `discovery`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-013::turn-003

- Stage: `comparison`
- Expected policy action: `fair-compare`
- Observed policy action: `fair-compare`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `provider-comparison`
- Strategy: `inquiry`

Exact customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Exact agent answer:

```text
That is fair. Should we compare price, terms, or fit first without pressure?
```

#### prod-027-scenario-013::turn-004

- Stage: `autonomy_check`
- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `autonomy-check`
- Strategy: `inquiry`

Exact customer turn:

```text
I need time to think; do not rush me into a commitment today.
```

Exact agent answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

#### prod-027-scenario-013::turn-005

- Stage: `sale_ready_check`
- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `True`
- Sales difficulty: `sale-ready-commitment`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Exact agent answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

#### prod-027-scenario-013::turn-006

- Stage: `commitment_confirmation`
- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `True`
- Sales difficulty: `sale-ready-commitment`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
I am giving a verbal commitment to the next step, not payment.
```

Exact agent answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

### prod-027-scenario-014 - price_objection

- Source scenario: `prod-014-price_objection-003`
- Expected outcome: `non_sale_correct`
- Review status: `pending-manual-review`

#### prod-027-scenario-014::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-014::turn-002

- Stage: `price_discussion`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
The price is my main concern, so explain value before asking me to decide.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-014::turn-003

- Stage: `objection_handling`
- Expected policy action: `clarify-fit`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `False`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
My specific objection is too expensive, and I need a practical answer before moving forward.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-014::turn-004

- Stage: `value_check`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
I need to know whether this is worth the effort before I spend more time on it.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-014::turn-005

- Stage: `autonomy_check`
- Expected policy action: `autonomy-check`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `False`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I do not want to be rushed, so ask what I need before any next step.
```

Exact agent answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

#### prod-027-scenario-014::turn-006

- Stage: `written_info`
- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `procurement-review`
- Strategy: `inquiry`

Exact customer turn:

```text
Send written information so I can review it without giving you anything firm today.
```

Exact agent answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

### prod-027-scenario-015 - callback_request

- Source scenario: `prod-014-callback_request-003`
- Expected outcome: `callback_agreed`
- Review status: `pending-manual-review`

#### prod-027-scenario-015::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this general customer service option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-015::turn-002

- Stage: `time_boundary`
- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `autonomy-check`
- Strategy: `inquiry`

Exact customer turn:

```text
I cannot talk now; call back later if there is a real reason.
```

Exact agent answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

#### prod-027-scenario-015::turn-003

- Stage: `callback_reason`
- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `autonomy-check`
- Strategy: `inquiry`

Exact customer turn:

```text
Before a callback later, tell me the one point that makes this worth reviewing.
```

Exact agent answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

#### prod-027-scenario-015::turn-004

- Stage: `timing_delay`
- Expected policy action: `autonomy-follow-up`
- Observed policy action: `autonomy-follow-up`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `timing-delay`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
Maybe next week, but nothing firm from me yet.
```

Exact agent answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

#### prod-027-scenario-015::turn-005

- Stage: `callback_time`
- Expected policy action: `schedule-callback`
- Observed policy action: `schedule-callback`
- Expected call control: `schedule-and-end`
- Observed call control: `schedule-and-end`
- Route correct: `True`
- Sales difficulty: `scheduling-confirmation`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
Wednesday 10 works for a callback.
```

Exact agent answer:

```text
Confirmed. I will record that callback time for the specialist. Goodbye.
```

#### prod-027-scenario-015::turn-006

- Stage: `wrap_up`
- Expected policy action: `schedule-callback`
- Observed policy action: `human-escalation`
- Expected call control: `schedule-and-end`
- Observed call control: `transfer-or-escalate`
- Route correct: `False`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
Use Wednesday 10 works and keep it as a specialist callback only.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### prod-027-scenario-016 - cancellation_boundary

- Source scenario: `prod-014-cancellation_boundary-003`
- Expected outcome: `end_call`
- Review status: `pending-manual-review`

#### prod-027-scenario-016::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this general customer service option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-016::turn-002

- Stage: `boundary`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
I am not interested in continuing this sales conversation.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-016::turn-003

- Stage: `suppression`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
Do not call me again about this.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-016::turn-004

- Stage: `repeat_boundary`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
Stop calling; I do not want a follow-up.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-016::turn-005

- Stage: `closing`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
No thank you, end the call.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

#### prod-027-scenario-016::turn-006

- Stage: `final_boundary`
- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `True`
- Sales difficulty: `do-not-call`
- Strategy: `rapport`

Exact customer turn:

```text
Please mark this as do not call.
```

Exact agent answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

### prod-027-scenario-017 - support_handoff

- Source scenario: `prod-014-support_handoff-003`
- Expected outcome: `human_handoff`
- Review status: `pending-manual-review`

#### prod-027-scenario-017::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this general customer service option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-017::turn-002

- Stage: `support_need`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
My service issue is unresolved and I need a human specialist before any offer.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

#### prod-027-scenario-017::turn-003

- Stage: `detail_lookup`
- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `True`
- Sales difficulty: `product-detail-lookup`
- Strategy: `evidence-or-benefit`

Exact customer turn:

```text
Which exact service details are included? I do not want you to guess.
```

Exact agent answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

#### prod-027-scenario-017::turn-004

- Stage: `human_request`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
I want a representative or advisor to handle this.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

#### prod-027-scenario-017::turn-005

- Stage: `verification`
- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `True`
- Sales difficulty: `product-detail-lookup`
- Strategy: `evidence-or-benefit`

Exact customer turn:

```text
Check the approved service details before answering.
```

Exact agent answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

#### prod-027-scenario-017::turn-006

- Stage: `handoff`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
Route me to a specialist instead of continuing automatically.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### prod-027-scenario-018 - trust_repair

- Source scenario: `prod-014-trust_repair-003`
- Expected outcome: `support_only`
- Review status: `pending-manual-review`

#### prod-027-scenario-018::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this general customer service option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-018::turn-002

- Stage: `trust_gap`
- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `trust-gap`
- Strategy: `rapport`

Exact customer turn:

```text
I do not know your company. How can I verify this is legitimate?
```

Exact agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

#### prod-027-scenario-018::turn-003

- Stage: `verification`
- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `trust-gap`
- Strategy: `rapport`

Exact customer turn:

```text
I do not trust this yet, so give me a verification path before any next step.
```

Exact agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

#### prod-027-scenario-018::turn-004

- Stage: `written_context`
- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `procurement-review`
- Strategy: `inquiry`

Exact customer turn:

```text
Send written information so I can check it before speaking further.
```

Exact agent answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

#### prod-027-scenario-018::turn-005

- Stage: `human_review`
- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `True`
- Sales difficulty: `human-request`
- Strategy: `rapport`

Exact customer turn:

```text
I want a human advisor if this goes any further.
```

Exact agent answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

#### prod-027-scenario-018::turn-006

- Stage: `trust_repair`
- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `trust-gap`
- Strategy: `rapport`

Exact customer turn:

```text
Before continuing, verify this is legitimate without asking me to commit.
```

Exact agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

### prod-027-scenario-019 - sale_eligible

- Source scenario: `prod-014-sale_eligible-004`
- Expected outcome: `sale_ready`
- Review status: `pending-manual-review`

#### prod-027-scenario-019::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this healthcare insurance option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-019::turn-002

- Stage: `discovery`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-019::turn-003

- Stage: `comparison`
- Expected policy action: `fair-compare`
- Observed policy action: `fair-compare`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `provider-comparison`
- Strategy: `inquiry`

Exact customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Exact agent answer:

```text
That is fair. Should we compare price, terms, or fit first without pressure?
```

#### prod-027-scenario-019::turn-004

- Stage: `autonomy_check`
- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `autonomy-check`
- Strategy: `inquiry`

Exact customer turn:

```text
I need time to think; do not rush me into a commitment today.
```

Exact agent answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

#### prod-027-scenario-019::turn-005

- Stage: `sale_ready_check`
- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `True`
- Sales difficulty: `sale-ready-commitment`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Exact agent answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

#### prod-027-scenario-019::turn-006

- Stage: `commitment_confirmation`
- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `True`
- Sales difficulty: `sale-ready-commitment`
- Strategy: `direct-ask-or-commitment`

Exact customer turn:

```text
I am giving a verbal commitment to the next step, not payment.
```

Exact agent answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

### prod-027-scenario-020 - price_objection

- Source scenario: `prod-014-price_objection-004`
- Expected outcome: `non_sale_correct`
- Review status: `pending-manual-review`

#### prod-027-scenario-020::turn-001

- Stage: `opening`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Exact agent answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

#### prod-027-scenario-020::turn-002

- Stage: `price_discussion`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
The price is my main concern, so explain value before asking me to decide.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-020::turn-003

- Stage: `objection_handling`
- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
My specific objection is needs to think, and I need a practical answer before moving forward.
```

Exact agent answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

#### prod-027-scenario-020::turn-004

- Stage: `value_check`
- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `price-objection`
- Strategy: `inquiry`

Exact customer turn:

```text
I need to know whether this is worth the effort before I spend more time on it.
```

Exact agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

#### prod-027-scenario-020::turn-005

- Stage: `autonomy_check`
- Expected policy action: `autonomy-check`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `False`
- Sales difficulty: `unknown-runtime-signal`
- Strategy: `inquiry`

Exact customer turn:

```text
I do not want to be rushed, so ask what I need before any next step.
```

Exact agent answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

#### prod-027-scenario-020::turn-006

- Stage: `written_info`
- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `True`
- Sales difficulty: `procurement-review`
- Strategy: `inquiry`

Exact customer turn:

```text
Send written information so I can review it without giving you anything firm today.
```

Exact agent answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

## Boundary

PROD-027 is local evaluation only. It does not promote production runtime behavior, enable live providers, enable customer data, enable payment handling, or make retrieval or composer hooks default.
