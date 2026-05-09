# PROD-029 Grounded Full Scenario Rerun

PROD-029 reruns the PROD-027 full scenario route set using the PROD-028 synthetic campaign facts. It keeps the same 20 scenarios / 120 turns and compares old PROD-027 answers vs grounded campaign answers.

## Summary

- Source checkpoint: `PROD-027-full-scenario-route-evaluation`
- Grounding checkpoint: `PROD-028-synthetic-campaign-knowledge-grounding`
- Same 20 scenarios / 120 turns: `true`
- Old PROD-027 answers vs grounded campaign answers: `true`
- Same PROD-027 scenario set: `true`
- Synthetic campaign facts used: `true`
- Scenario count: `20`
- Turn count: `120`
- Exact customer turns visible: `true`
- Exact PROD-027 answers visible: `true`
- Exact grounded answers visible: `true`
- Route decision process visible: `true`
- Direct answer rate: `1.0`
- Knowledge-applicable fact rate: `1.0`
- Grounded question overuse rate: `0.0`
- PROD-027 question overuse rate: `0.7833`
- Grounded answer win rate: `0.6583`
- Hard failures: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`
- Provider calls made: `false`
- Runtime behavior changed: `false`
- Decision: `grounded_answers_improve_full_scenario_demo_candidate`
- Next checkpoint: `PROD-030-grounded-demo-review`

## Metrics

- route_correctness: `0.9167`
- policy_action_correctness: `0.9167`
- call_control_correctness: `0.975`
- scenario_route_pass_rate: `0.65`
- direct_answer_rate: `1.0`
- knowledge_applicable_fact_rate: `1.0`
- grounded_question_overuse_rate: `0.0`
- prod_027_question_overuse_rate: `0.7833`
- grounded_answer_win_rate: `0.6583`
- unsupported_claim_rate: `0.0`
- leakage_failure_rate: `0.0`

## Scenario Table

| Scenario | Label | Route Turns | Grounded Wins | Hard Failure |
| --- | --- | ---: | ---: | --- |
| prod-029-scenario-001 | sale_eligible | 6/6 | 4/6 | False |
| prod-029-scenario-002 | price_objection | 4/6 | 6/6 | False |
| prod-029-scenario-003 | callback_request | 5/6 | 4/6 | False |
| prod-029-scenario-004 | cancellation_boundary | 6/6 | 1/6 | False |
| prod-029-scenario-005 | support_handoff | 6/6 | 3/6 | False |
| prod-029-scenario-006 | trust_repair | 6/6 | 5/6 | False |
| prod-029-scenario-007 | sale_eligible | 6/6 | 4/6 | False |
| prod-029-scenario-008 | price_objection | 4/6 | 6/6 | False |
| prod-029-scenario-009 | callback_request | 5/6 | 4/6 | False |
| prod-029-scenario-010 | cancellation_boundary | 6/6 | 1/6 | False |
| prod-029-scenario-011 | support_handoff | 6/6 | 3/6 | False |
| prod-029-scenario-012 | trust_repair | 6/6 | 5/6 | False |
| prod-029-scenario-013 | sale_eligible | 6/6 | 4/6 | False |
| prod-029-scenario-014 | price_objection | 4/6 | 6/6 | False |
| prod-029-scenario-015 | callback_request | 5/6 | 4/6 | False |
| prod-029-scenario-016 | cancellation_boundary | 6/6 | 1/6 | False |
| prod-029-scenario-017 | support_handoff | 6/6 | 3/6 | False |
| prod-029-scenario-018 | trust_repair | 6/6 | 5/6 | False |
| prod-029-scenario-019 | sale_eligible | 6/6 | 4/6 | False |
| prod-029-scenario-020 | price_objection | 5/6 | 6/6 | False |

## Exact Comparison Traces

### prod-029-scenario-001 - sale_eligible

- Source scenario: `prod-027-scenario-001`
- Review status: `pending-manual-review`

#### prod-029-scenario-001::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, Growth, callback ownership`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is relevant if routing, callback ownership, or team reporting are real gaps. Growth is the usual fit for routing automation; the review stays non-binding.
```

#### prod-029-scenario-001::turn-002

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59, no payment`

Exact customer turn:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
The lower entry point is Starter at $29 per user per month annually, while Growth is $59 for routing automation and team reporting. No payment is handled on this call.
```

#### prod-029-scenario-001::turn-003

- Expected policy action: `fair-compare`
- Observed policy action: `fair-compare`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, CSV, Slack, Zapier, callback ownership`

Exact customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Old PROD-027 answer:

```text
That is fair. Should we compare price, terms, or fit first without pressure?
```

Grounded campaign answer:

```text
I would not replace a setup that already works. RouteSignal CRM is worth reviewing only if routing, callback ownership, or reporting are the gaps; it supports CRM handoffs, CSV import, Slack, and Zapier.
```

#### prod-029-scenario-001::turn-004

- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I need time to think; do not rush me into a commitment today.
```

Old PROD-027 answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-001::turn-005

- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Old PROD-027 answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

Grounded campaign answer:

```text
Confirmed as sale-ready for a solutions specialist review. The next step is the non-binding workflow review, with no payment collected here.
```

#### prod-029-scenario-001::turn-006

- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
I am giving a verbal commitment to the next step, not payment.
```

Old PROD-027 answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

Grounded campaign answer:

```text
Confirmed as sale-ready for a solutions specialist review. The next step is the non-binding workflow review, with no payment collected here.
```

### prod-029-scenario-002 - price_objection

- Source scenario: `prod-027-scenario-002`
- Review status: `pending-manual-review`

#### prod-029-scenario-002::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-002::turn-002

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59`

Exact customer turn:

```text
The price is my main concern, so explain value before asking me to decide.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. If cost is the blocker, we can compare the smaller plan against your routing needs first.
```

#### prod-029-scenario-002::turn-003

- Expected policy action: `clarify-fit`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `false`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
My specific objection is too expensive, and I need a practical answer before moving forward.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-002::turn-004

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59`

Exact customer turn:

```text
I need to know whether this is worth the effort before I spend more time on it.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. If cost is the blocker, we can compare the smaller plan against your routing needs first.
```

#### prod-029-scenario-002::turn-005

- Expected policy action: `autonomy-check`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `false`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I do not want to be rushed, so ask what I need before any next step.
```

Old PROD-027 answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-002::turn-006

- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `14-day, annual billing, specialist`

Exact customer turn:

```text
Send written information so I can review it without giving you anything firm today.
```

Old PROD-027 answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

Grounded campaign answer:

```text
For written review, I would send the plan range, annual billing terms, 14-day sandbox, setup and migration fees, cancellation boundary, and specialist quote requirement.
```

### prod-029-scenario-003 - callback_request

- Source scenario: `prod-027-scenario-003`
- Review status: `pending-manual-review`

#### prod-029-scenario-003::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-003::turn-002

- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I cannot talk now; call back later if there is a real reason.
```

Old PROD-027 answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-003::turn-003

- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
Before a callback later, tell me the one point that makes this worth reviewing.
```

Old PROD-027 answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-003::turn-004

- Expected policy action: `autonomy-follow-up`
- Observed policy action: `autonomy-follow-up`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
Maybe next week, but nothing firm from me yet.
```

Old PROD-027 answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

Grounded campaign answer:

```text
No problem. I will log a later callback and keep it to a RouteSignal CRM workflow review, not a commitment today.
```

#### prod-029-scenario-003::turn-005

- Expected policy action: `schedule-callback`
- Observed policy action: `schedule-callback`
- Expected call control: `schedule-and-end`
- Observed call control: `schedule-and-end`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
Wednesday 10 works for a callback.
```

Old PROD-027 answer:

```text
Confirmed. I will record that callback time for the specialist. Goodbye.
```

Grounded campaign answer:

```text
Confirmed for the specialist callback. The next step stays non-binding, with no payment handled in this call.
```

#### prod-029-scenario-003::turn-006

- Expected policy action: `schedule-callback`
- Observed policy action: `human-escalation`
- Expected call control: `schedule-and-end`
- Observed call control: `transfer-or-escalate`
- Route correct: `false`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
Use Wednesday 10 works and keep it as a specialist callback only.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Confirmed for the specialist callback. The next step stays non-binding, with no payment handled in this call.
```

### prod-029-scenario-004 - cancellation_boundary

- Source scenario: `prod-027-scenario-004`
- Review status: `pending-manual-review`

#### prod-029-scenario-004::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-004::turn-002

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
I am not interested in continuing this sales conversation.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-004::turn-003

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
Do not call me again about this.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-004::turn-004

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
Stop calling; I do not want a follow-up.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-004::turn-005

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
No thank you, end the call.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-004::turn-006

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
Please mark this as do not call.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

### prod-029-scenario-005 - support_handoff

- Source scenario: `prod-027-scenario-005`
- Review status: `pending-manual-review`

#### prod-029-scenario-005::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM details should be checked by a solutions specialist; they can confirm support, security, integration, or migration scope without turning this into a close.
```

#### prod-029-scenario-005::turn-002

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
My service issue is unresolved and I need a human specialist before any offer.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

#### prod-029-scenario-005::turn-003

- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, Scale, CSV, Slack, Zapier, SSO, audit logs, specialist`

Exact customer turn:

```text
Which exact service details are included? I do not want you to guess.
```

Old PROD-027 answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

Grounded campaign answer:

```text
RouteSignal CRM includes lead inbox, routing, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import; Scale adds SSO, audit logs, sandbox, and custom roles. A solutions specialist should confirm exact security scope.
```

#### prod-029-scenario-005::turn-004

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
I want a representative or advisor to handle this.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

#### prod-029-scenario-005::turn-005

- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, Scale, CSV, Slack, Zapier, SSO, audit logs, specialist`

Exact customer turn:

```text
Check the approved service details before answering.
```

Old PROD-027 answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

Grounded campaign answer:

```text
RouteSignal CRM includes lead inbox, routing, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import; Scale adds SSO, audit logs, sandbox, and custom roles. A solutions specialist should confirm exact security scope.
```

#### prod-029-scenario-005::turn-006

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
Route me to a specialist instead of continuing automatically.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

### prod-029-scenario-006 - trust_repair

- Source scenario: `prod-027-scenario-006`
- Review status: `pending-manual-review`

#### prod-029-scenario-006::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-006::turn-002

- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
I do not know your company. How can I verify this is legitimate?
```

Old PROD-027 answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

Grounded campaign answer:

```text
The safe verification path is written context plus a solutions specialist review before any commitment. In this simulation, RouteSignal CRM keeps billing outside this call.
```

#### prod-029-scenario-006::turn-003

- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
I do not trust this yet, so give me a verification path before any next step.
```

Old PROD-027 answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

Grounded campaign answer:

```text
The safe verification path is written context plus a solutions specialist review before any commitment. In this simulation, RouteSignal CRM keeps billing outside this call.
```

#### prod-029-scenario-006::turn-004

- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `14-day, annual billing, specialist`

Exact customer turn:

```text
Send written information so I can check it before speaking further.
```

Old PROD-027 answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

Grounded campaign answer:

```text
For written review, I would send the plan range, annual billing terms, 14-day sandbox, setup and migration fees, cancellation boundary, and specialist quote requirement.
```

#### prod-029-scenario-006::turn-005

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
I want a human advisor if this goes any further.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

#### prod-029-scenario-006::turn-006

- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
Before continuing, verify this is legitimate without asking me to commit.
```

Old PROD-027 answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

Grounded campaign answer:

```text
The safe verification path is written context plus a solutions specialist review before any commitment. In this simulation, RouteSignal CRM keeps billing outside this call.
```

### prod-029-scenario-007 - sale_eligible

- Source scenario: `prod-027-scenario-007`
- Review status: `pending-manual-review`

#### prod-029-scenario-007::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, Growth, callback ownership`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is relevant if routing, callback ownership, or team reporting are real gaps. Growth is the usual fit for routing automation; the review stays non-binding.
```

#### prod-029-scenario-007::turn-002

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59, no payment`

Exact customer turn:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
The lower entry point is Starter at $29 per user per month annually, while Growth is $59 for routing automation and team reporting. No payment is handled on this call.
```

#### prod-029-scenario-007::turn-003

- Expected policy action: `fair-compare`
- Observed policy action: `fair-compare`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, CSV, Slack, Zapier, callback ownership`

Exact customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Old PROD-027 answer:

```text
That is fair. Should we compare price, terms, or fit first without pressure?
```

Grounded campaign answer:

```text
I would not replace a setup that already works. RouteSignal CRM is worth reviewing only if routing, callback ownership, or reporting are the gaps; it supports CRM handoffs, CSV import, Slack, and Zapier.
```

#### prod-029-scenario-007::turn-004

- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I need time to think; do not rush me into a commitment today.
```

Old PROD-027 answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-007::turn-005

- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Old PROD-027 answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

Grounded campaign answer:

```text
Confirmed as sale-ready for a solutions specialist review. The next step is the non-binding workflow review, with no payment collected here.
```

#### prod-029-scenario-007::turn-006

- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
I am giving a verbal commitment to the next step, not payment.
```

Old PROD-027 answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

Grounded campaign answer:

```text
Confirmed as sale-ready for a solutions specialist review. The next step is the non-binding workflow review, with no payment collected here.
```

### prod-029-scenario-008 - price_objection

- Source scenario: `prod-027-scenario-008`
- Review status: `pending-manual-review`

#### prod-029-scenario-008::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this auto insurance option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-008::turn-002

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59`

Exact customer turn:

```text
The price is my main concern, so explain value before asking me to decide.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. If cost is the blocker, we can compare the smaller plan against your routing needs first.
```

#### prod-029-scenario-008::turn-003

- Expected policy action: `clarify-fit`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `false`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
My specific objection is too expensive, and I need a practical answer before moving forward.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-008::turn-004

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59`

Exact customer turn:

```text
I need to know whether this is worth the effort before I spend more time on it.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. If cost is the blocker, we can compare the smaller plan against your routing needs first.
```

#### prod-029-scenario-008::turn-005

- Expected policy action: `autonomy-check`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `false`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I do not want to be rushed, so ask what I need before any next step.
```

Old PROD-027 answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-008::turn-006

- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `14-day, annual billing, specialist`

Exact customer turn:

```text
Send written information so I can review it without giving you anything firm today.
```

Old PROD-027 answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

Grounded campaign answer:

```text
For written review, I would send the plan range, annual billing terms, 14-day sandbox, setup and migration fees, cancellation boundary, and specialist quote requirement.
```

### prod-029-scenario-009 - callback_request

- Source scenario: `prod-027-scenario-009`
- Review status: `pending-manual-review`

#### prod-029-scenario-009::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-009::turn-002

- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I cannot talk now; call back later if there is a real reason.
```

Old PROD-027 answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-009::turn-003

- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
Before a callback later, tell me the one point that makes this worth reviewing.
```

Old PROD-027 answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-009::turn-004

- Expected policy action: `autonomy-follow-up`
- Observed policy action: `autonomy-follow-up`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
Maybe next week, but nothing firm from me yet.
```

Old PROD-027 answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

Grounded campaign answer:

```text
No problem. I will log a later callback and keep it to a RouteSignal CRM workflow review, not a commitment today.
```

#### prod-029-scenario-009::turn-005

- Expected policy action: `schedule-callback`
- Observed policy action: `schedule-callback`
- Expected call control: `schedule-and-end`
- Observed call control: `schedule-and-end`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
Wednesday 10 works for a callback.
```

Old PROD-027 answer:

```text
Confirmed. I will record that callback time for the specialist. Goodbye.
```

Grounded campaign answer:

```text
Confirmed for the specialist callback. The next step stays non-binding, with no payment handled in this call.
```

#### prod-029-scenario-009::turn-006

- Expected policy action: `schedule-callback`
- Observed policy action: `human-escalation`
- Expected call control: `schedule-and-end`
- Observed call control: `transfer-or-escalate`
- Route correct: `false`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
Use Wednesday 10 works and keep it as a specialist callback only.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Confirmed for the specialist callback. The next step stays non-binding, with no payment handled in this call.
```

### prod-029-scenario-010 - cancellation_boundary

- Source scenario: `prod-027-scenario-010`
- Review status: `pending-manual-review`

#### prod-029-scenario-010::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-010::turn-002

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
I am not interested in continuing this sales conversation.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-010::turn-003

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
Do not call me again about this.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-010::turn-004

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
Stop calling; I do not want a follow-up.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-010::turn-005

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
No thank you, end the call.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-010::turn-006

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
Please mark this as do not call.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

### prod-029-scenario-011 - support_handoff

- Source scenario: `prod-027-scenario-011`
- Review status: `pending-manual-review`

#### prod-029-scenario-011::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM details should be checked by a solutions specialist; they can confirm support, security, integration, or migration scope without turning this into a close.
```

#### prod-029-scenario-011::turn-002

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
My service issue is unresolved and I need a human specialist before any offer.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

#### prod-029-scenario-011::turn-003

- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, Scale, CSV, Slack, Zapier, SSO, audit logs, specialist`

Exact customer turn:

```text
Which exact service details are included? I do not want you to guess.
```

Old PROD-027 answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

Grounded campaign answer:

```text
RouteSignal CRM includes lead inbox, routing, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import; Scale adds SSO, audit logs, sandbox, and custom roles. A solutions specialist should confirm exact security scope.
```

#### prod-029-scenario-011::turn-004

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
I want a representative or advisor to handle this.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

#### prod-029-scenario-011::turn-005

- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, Scale, CSV, Slack, Zapier, SSO, audit logs, specialist`

Exact customer turn:

```text
Check the approved service details before answering.
```

Old PROD-027 answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

Grounded campaign answer:

```text
RouteSignal CRM includes lead inbox, routing, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import; Scale adds SSO, audit logs, sandbox, and custom roles. A solutions specialist should confirm exact security scope.
```

#### prod-029-scenario-011::turn-006

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
Route me to a specialist instead of continuing automatically.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

### prod-029-scenario-012 - trust_repair

- Source scenario: `prod-027-scenario-012`
- Review status: `pending-manual-review`

#### prod-029-scenario-012::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-012::turn-002

- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
I do not know your company. How can I verify this is legitimate?
```

Old PROD-027 answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

Grounded campaign answer:

```text
The safe verification path is written context plus a solutions specialist review before any commitment. In this simulation, RouteSignal CRM keeps billing outside this call.
```

#### prod-029-scenario-012::turn-003

- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
I do not trust this yet, so give me a verification path before any next step.
```

Old PROD-027 answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

Grounded campaign answer:

```text
The safe verification path is written context plus a solutions specialist review before any commitment. In this simulation, RouteSignal CRM keeps billing outside this call.
```

#### prod-029-scenario-012::turn-004

- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `14-day, annual billing, specialist`

Exact customer turn:

```text
Send written information so I can check it before speaking further.
```

Old PROD-027 answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

Grounded campaign answer:

```text
For written review, I would send the plan range, annual billing terms, 14-day sandbox, setup and migration fees, cancellation boundary, and specialist quote requirement.
```

#### prod-029-scenario-012::turn-005

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
I want a human advisor if this goes any further.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

#### prod-029-scenario-012::turn-006

- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
Before continuing, verify this is legitimate without asking me to commit.
```

Old PROD-027 answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

Grounded campaign answer:

```text
The safe verification path is written context plus a solutions specialist review before any commitment. In this simulation, RouteSignal CRM keeps billing outside this call.
```

### prod-029-scenario-013 - sale_eligible

- Source scenario: `prod-027-scenario-013`
- Review status: `pending-manual-review`

#### prod-029-scenario-013::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, Growth, callback ownership`

Exact customer turn:

```text
I can listen briefly about this general customer service option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is relevant if routing, callback ownership, or team reporting are real gaps. Growth is the usual fit for routing automation; the review stays non-binding.
```

#### prod-029-scenario-013::turn-002

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59, no payment`

Exact customer turn:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
The lower entry point is Starter at $29 per user per month annually, while Growth is $59 for routing automation and team reporting. No payment is handled on this call.
```

#### prod-029-scenario-013::turn-003

- Expected policy action: `fair-compare`
- Observed policy action: `fair-compare`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, CSV, Slack, Zapier, callback ownership`

Exact customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Old PROD-027 answer:

```text
That is fair. Should we compare price, terms, or fit first without pressure?
```

Grounded campaign answer:

```text
I would not replace a setup that already works. RouteSignal CRM is worth reviewing only if routing, callback ownership, or reporting are the gaps; it supports CRM handoffs, CSV import, Slack, and Zapier.
```

#### prod-029-scenario-013::turn-004

- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I need time to think; do not rush me into a commitment today.
```

Old PROD-027 answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-013::turn-005

- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Old PROD-027 answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

Grounded campaign answer:

```text
Confirmed as sale-ready for a solutions specialist review. The next step is the non-binding workflow review, with no payment collected here.
```

#### prod-029-scenario-013::turn-006

- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
I am giving a verbal commitment to the next step, not payment.
```

Old PROD-027 answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

Grounded campaign answer:

```text
Confirmed as sale-ready for a solutions specialist review. The next step is the non-binding workflow review, with no payment collected here.
```

### prod-029-scenario-014 - price_objection

- Source scenario: `prod-027-scenario-014`
- Review status: `pending-manual-review`

#### prod-029-scenario-014::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-014::turn-002

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59`

Exact customer turn:

```text
The price is my main concern, so explain value before asking me to decide.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. If cost is the blocker, we can compare the smaller plan against your routing needs first.
```

#### prod-029-scenario-014::turn-003

- Expected policy action: `clarify-fit`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `false`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
My specific objection is too expensive, and I need a practical answer before moving forward.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-014::turn-004

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59`

Exact customer turn:

```text
I need to know whether this is worth the effort before I spend more time on it.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. If cost is the blocker, we can compare the smaller plan against your routing needs first.
```

#### prod-029-scenario-014::turn-005

- Expected policy action: `autonomy-check`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `false`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I do not want to be rushed, so ask what I need before any next step.
```

Old PROD-027 answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-014::turn-006

- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `14-day, annual billing, specialist`

Exact customer turn:

```text
Send written information so I can review it without giving you anything firm today.
```

Old PROD-027 answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

Grounded campaign answer:

```text
For written review, I would send the plan range, annual billing terms, 14-day sandbox, setup and migration fees, cancellation boundary, and specialist quote requirement.
```

### prod-029-scenario-015 - callback_request

- Source scenario: `prod-027-scenario-015`
- Review status: `pending-manual-review`

#### prod-029-scenario-015::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this general customer service option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-015::turn-002

- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I cannot talk now; call back later if there is a real reason.
```

Old PROD-027 answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-015::turn-003

- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
Before a callback later, tell me the one point that makes this worth reviewing.
```

Old PROD-027 answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-015::turn-004

- Expected policy action: `autonomy-follow-up`
- Observed policy action: `autonomy-follow-up`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
Maybe next week, but nothing firm from me yet.
```

Old PROD-027 answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

Grounded campaign answer:

```text
No problem. I will log a later callback and keep it to a RouteSignal CRM workflow review, not a commitment today.
```

#### prod-029-scenario-015::turn-005

- Expected policy action: `schedule-callback`
- Observed policy action: `schedule-callback`
- Expected call control: `schedule-and-end`
- Observed call control: `schedule-and-end`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
Wednesday 10 works for a callback.
```

Old PROD-027 answer:

```text
Confirmed. I will record that callback time for the specialist. Goodbye.
```

Grounded campaign answer:

```text
Confirmed for the specialist callback. The next step stays non-binding, with no payment handled in this call.
```

#### prod-029-scenario-015::turn-006

- Expected policy action: `schedule-callback`
- Observed policy action: `human-escalation`
- Expected call control: `schedule-and-end`
- Observed call control: `transfer-or-escalate`
- Route correct: `false`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
Use Wednesday 10 works and keep it as a specialist callback only.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Confirmed for the specialist callback. The next step stays non-binding, with no payment handled in this call.
```

### prod-029-scenario-016 - cancellation_boundary

- Source scenario: `prod-027-scenario-016`
- Review status: `pending-manual-review`

#### prod-029-scenario-016::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this general customer service option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-016::turn-002

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
I am not interested in continuing this sales conversation.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-016::turn-003

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
Do not call me again about this.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-016::turn-004

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
Stop calling; I do not want a follow-up.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-016::turn-005

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
No thank you, end the call.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

#### prod-029-scenario-016::turn-006

- Expected policy action: `end-call`
- Observed policy action: `end-call`
- Expected call control: `end-call`
- Observed call control: `end-call`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: ``

Exact customer turn:

```text
Please mark this as do not call.
```

Old PROD-027 answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

Grounded campaign answer:

```text
Understood. I will mark this as do not call and end the sales conversation now.
```

### prod-029-scenario-017 - support_handoff

- Source scenario: `prod-027-scenario-017`
- Review status: `pending-manual-review`

#### prod-029-scenario-017::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
I can listen briefly about this general customer service option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM details should be checked by a solutions specialist; they can confirm support, security, integration, or migration scope without turning this into a close.
```

#### prod-029-scenario-017::turn-002

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
My service issue is unresolved and I need a human specialist before any offer.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

#### prod-029-scenario-017::turn-003

- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, Scale, CSV, Slack, Zapier, SSO, audit logs, specialist`

Exact customer turn:

```text
Which exact service details are included? I do not want you to guess.
```

Old PROD-027 answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

Grounded campaign answer:

```text
RouteSignal CRM includes lead inbox, routing, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import; Scale adds SSO, audit logs, sandbox, and custom roles. A solutions specialist should confirm exact security scope.
```

#### prod-029-scenario-017::turn-004

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
I want a representative or advisor to handle this.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

#### prod-029-scenario-017::turn-005

- Expected policy action: `technical-escalation`
- Observed policy action: `technical-escalation`
- Expected call control: `bridge-then-continue`
- Observed call control: `bridge-then-continue`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, Scale, CSV, Slack, Zapier, SSO, audit logs, specialist`

Exact customer turn:

```text
Check the approved service details before answering.
```

Old PROD-027 answer:

```text
Good question. I want to check the approved product information before answering, so I do not guess on plan details.
```

Grounded campaign answer:

```text
RouteSignal CRM includes lead inbox, routing, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import; Scale adds SSO, audit logs, sandbox, and custom roles. A solutions specialist should confirm exact security scope.
```

#### prod-029-scenario-017::turn-006

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
Route me to a specialist instead of continuing automatically.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

### prod-029-scenario-018 - trust_repair

- Source scenario: `prod-027-scenario-018`
- Review status: `pending-manual-review`

#### prod-029-scenario-018::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this general customer service option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-018::turn-002

- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
I do not know your company. How can I verify this is legitimate?
```

Old PROD-027 answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

Grounded campaign answer:

```text
The safe verification path is written context plus a solutions specialist review before any commitment. In this simulation, RouteSignal CRM keeps billing outside this call.
```

#### prod-029-scenario-018::turn-003

- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
I do not trust this yet, so give me a verification path before any next step.
```

Old PROD-027 answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

Grounded campaign answer:

```text
The safe verification path is written context plus a solutions specialist review before any commitment. In this simulation, RouteSignal CRM keeps billing outside this call.
```

#### prod-029-scenario-018::turn-004

- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `14-day, annual billing, specialist`

Exact customer turn:

```text
Send written information so I can check it before speaking further.
```

Old PROD-027 answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

Grounded campaign answer:

```text
For written review, I would send the plan range, annual billing terms, 14-day sandbox, setup and migration fees, cancellation boundary, and specialist quote requirement.
```

#### prod-029-scenario-018::turn-005

- Expected policy action: `human-escalation`
- Observed policy action: `human-escalation`
- Expected call control: `transfer-or-escalate`
- Observed call control: `transfer-or-escalate`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `specialist`

Exact customer turn:

```text
I want a human advisor if this goes any further.
```

Old PROD-027 answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

Grounded campaign answer:

```text
Of course. I will route this to a solutions specialist; they can confirm integration, security, migration, or support details before any offer.
```

#### prod-029-scenario-018::turn-006

- Expected policy action: `trust-repair`
- Observed policy action: `trust-repair`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, specialist`

Exact customer turn:

```text
Before continuing, verify this is legitimate without asking me to commit.
```

Old PROD-027 answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

Grounded campaign answer:

```text
The safe verification path is written context plus a solutions specialist review before any commitment. In this simulation, RouteSignal CRM keeps billing outside this call.
```

### prod-029-scenario-019 - sale_eligible

- Source scenario: `prod-027-scenario-019`
- Review status: `pending-manual-review`

#### prod-029-scenario-019::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, Growth, callback ownership`

Exact customer turn:

```text
I can listen briefly about this healthcare insurance option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is relevant if routing, callback ownership, or team reporting are real gaps. Growth is the usual fit for routing automation; the review stays non-binding.
```

#### prod-029-scenario-019::turn-002

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59, no payment`

Exact customer turn:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
The lower entry point is Starter at $29 per user per month annually, while Growth is $59 for routing automation and team reporting. No payment is handled on this call.
```

#### prod-029-scenario-019::turn-003

- Expected policy action: `fair-compare`
- Observed policy action: `fair-compare`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal, CSV, Slack, Zapier, callback ownership`

Exact customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Old PROD-027 answer:

```text
That is fair. Should we compare price, terms, or fit first without pressure?
```

Grounded campaign answer:

```text
I would not replace a setup that already works. RouteSignal CRM is worth reviewing only if routing, callback ownership, or reporting are the gaps; it supports CRM handoffs, CSV import, Slack, and Zapier.
```

#### prod-029-scenario-019::turn-004

- Expected policy action: `autonomy-check`
- Observed policy action: `autonomy-check`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I need time to think; do not rush me into a commitment today.
```

Old PROD-027 answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-019::turn-005

- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Old PROD-027 answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

Grounded campaign answer:

```text
Confirmed as sale-ready for a solutions specialist review. The next step is the non-binding workflow review, with no payment collected here.
```

#### prod-029-scenario-019::turn-006

- Expected policy action: `close-and-log-sale-ready`
- Observed policy action: `close-and-log-sale-ready`
- Expected call control: `close-and-log-sale-ready`
- Observed call control: `close-and-log-sale-ready`
- Route correct: `true`
- Answer quality delta: `0`
- Fact markers used: `no payment, specialist`

Exact customer turn:

```text
I am giving a verbal commitment to the next step, not payment.
```

Old PROD-027 answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

Grounded campaign answer:

```text
Confirmed as sale-ready for a solutions specialist review. The next step is the non-binding workflow review, with no payment collected here.
```

### prod-029-scenario-020 - price_objection

- Source scenario: `prod-027-scenario-020`
- Review status: `pending-manual-review`

#### prod-029-scenario-020::turn-001

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I can listen briefly about this automotive option, but first tell me why this matters for my situation.
```

Old PROD-027 answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-020::turn-002

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59`

Exact customer turn:

```text
The price is my main concern, so explain value before asking me to decide.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. If cost is the blocker, we can compare the smaller plan against your routing needs first.
```

#### prod-029-scenario-020::turn-003

- Expected policy action: `clarify-fit`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
My specific objection is needs to think, and I need a practical answer before moving forward.
```

Old PROD-027 answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Grounded campaign answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

#### prod-029-scenario-020::turn-004

- Expected policy action: `value-clarify`
- Observed policy action: `value-clarify`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `Starter, Growth, $29, $59`

Exact customer turn:

```text
I need to know whether this is worth the effort before I spend more time on it.
```

Old PROD-027 answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

Grounded campaign answer:

```text
On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. If cost is the blocker, we can compare the smaller plan against your routing needs first.
```

#### prod-029-scenario-020::turn-005

- Expected policy action: `autonomy-check`
- Observed policy action: `clarify-fit`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `false`
- Answer quality delta: `2`
- Fact markers used: `RouteSignal`

Exact customer turn:

```text
I do not want to be rushed, so ask what I need before any next step.
```

Old PROD-027 answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Grounded campaign answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

#### prod-029-scenario-020::turn-006

- Expected policy action: `procurement-review`
- Observed policy action: `procurement-review`
- Expected call control: `continue-call`
- Observed call control: `continue-call`
- Route correct: `true`
- Answer quality delta: `2`
- Fact markers used: `14-day, annual billing, specialist`

Exact customer turn:

```text
Send written information so I can review it without giving you anything firm today.
```

Old PROD-027 answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

Grounded campaign answer:

```text
For written review, I would send the plan range, annual billing terms, 14-day sandbox, setup and migration fees, cancellation boundary, and specialist quote requirement.
```

