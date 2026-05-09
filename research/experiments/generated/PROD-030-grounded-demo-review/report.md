# PROD-030 Grounded Demo Review

PROD-030 reviews the PROD-029 grounded full-scenario rerun and records accepted/rejected/revise status per grounded answer and route gap.

## Result

- Checkpoint id: `PROD-030-grounded-demo-review`
- Source checkpoint: `PROD-029-grounded-full-scenario-rerun`
- Accepted grounded answers: `120`
- Revised grounded answers: `0`
- Rejected grounded answers: `0`
- Route accepted turns: `110`
- Route gap turns: `10`
- Route gap scenarios: `7`
- Demo-ready turns: `110`
- Demo-ready scenarios: `13`
- Full demo set allowed: `false`
- Local demo subset allowed: `true`
- Runtime campaign profile promotion allowed: `false`
- Provider calls made: `false`
- Runtime behavior changed: `false`
- Next checkpoint: `PROD-031-grounded-route-gap-fix`

## Decision

- Grounded answer layer: accepted as a candidate for demo review.
- Route gaps: revise before full-demo or runtime-profile promotion.
- Runtime campaign profile: candidate-only, not promoted.

## Route Gap Types

- `autonomy-check_policy_mismatch`
- `scheduling-confirmation_call-control-mismatch`
- `unknown-runtime-signal_policy_mismatch`

## Recommended Demo Scenarios

- `prod-029-scenario-004` (cancellation_boundary): first demo-ready scenario for this covered label
- `prod-029-scenario-001` (sale_eligible): first demo-ready scenario for this covered label
- `prod-029-scenario-005` (support_handoff): first demo-ready scenario for this covered label
- `prod-029-scenario-006` (trust_repair): first demo-ready scenario for this covered label

## Scenario Review

| Scenario | Label | Answer Status | Route Status | Demo Status | Route Gaps |
| --- | --- | --- | --- | --- | ---: |
| prod-029-scenario-001 | sale_eligible | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-002 | price_objection | accepted | route-gap-needs-policy-review | revise-before-demo | 2 |
| prod-029-scenario-003 | callback_request | accepted | route-gap-needs-policy-review | revise-before-demo | 1 |
| prod-029-scenario-004 | cancellation_boundary | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-005 | support_handoff | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-006 | trust_repair | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-007 | sale_eligible | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-008 | price_objection | accepted | route-gap-needs-policy-review | revise-before-demo | 2 |
| prod-029-scenario-009 | callback_request | accepted | route-gap-needs-policy-review | revise-before-demo | 1 |
| prod-029-scenario-010 | cancellation_boundary | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-011 | support_handoff | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-012 | trust_repair | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-013 | sale_eligible | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-014 | price_objection | accepted | route-gap-needs-policy-review | revise-before-demo | 2 |
| prod-029-scenario-015 | callback_request | accepted | route-gap-needs-policy-review | revise-before-demo | 1 |
| prod-029-scenario-016 | cancellation_boundary | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-017 | support_handoff | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-018 | trust_repair | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-019 | sale_eligible | accepted | accepted | demo-ready | 0 |
| prod-029-scenario-020 | price_objection | accepted | route-gap-needs-policy-review | revise-before-demo | 1 |

## Route Gap Turns

### prod-029-scenario-002 - price_objection

- Turn: `prod-029-scenario-002::turn-003`
- Gap type: `unknown-runtime-signal_policy_mismatch`
- Expected policy/control: `clarify-fit` / `continue-call`
- Observed policy/control: `value-clarify` / `continue-call`
- Grounded answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

- Turn: `prod-029-scenario-002::turn-005`
- Gap type: `autonomy-check_policy_mismatch`
- Expected policy/control: `autonomy-check` / `continue-call`
- Observed policy/control: `clarify-fit` / `continue-call`
- Grounded answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

### prod-029-scenario-003 - callback_request

- Turn: `prod-029-scenario-003::turn-006`
- Gap type: `scheduling-confirmation_call-control-mismatch`
- Expected policy/control: `schedule-callback` / `schedule-and-end`
- Observed policy/control: `human-escalation` / `transfer-or-escalate`
- Grounded answer:

```text
Confirmed for the specialist callback. The next step stays non-binding, with no payment handled in this call.
```

### prod-029-scenario-008 - price_objection

- Turn: `prod-029-scenario-008::turn-003`
- Gap type: `unknown-runtime-signal_policy_mismatch`
- Expected policy/control: `clarify-fit` / `continue-call`
- Observed policy/control: `value-clarify` / `continue-call`
- Grounded answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

- Turn: `prod-029-scenario-008::turn-005`
- Gap type: `autonomy-check_policy_mismatch`
- Expected policy/control: `autonomy-check` / `continue-call`
- Observed policy/control: `clarify-fit` / `continue-call`
- Grounded answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

### prod-029-scenario-009 - callback_request

- Turn: `prod-029-scenario-009::turn-006`
- Gap type: `scheduling-confirmation_call-control-mismatch`
- Expected policy/control: `schedule-callback` / `schedule-and-end`
- Observed policy/control: `human-escalation` / `transfer-or-escalate`
- Grounded answer:

```text
Confirmed for the specialist callback. The next step stays non-binding, with no payment handled in this call.
```

### prod-029-scenario-014 - price_objection

- Turn: `prod-029-scenario-014::turn-003`
- Gap type: `unknown-runtime-signal_policy_mismatch`
- Expected policy/control: `clarify-fit` / `continue-call`
- Observed policy/control: `value-clarify` / `continue-call`
- Grounded answer:

```text
RouteSignal CRM is a lead-routing and callback-ownership CRM. We can keep this to fit, price, or setup facts before any next step.
```

- Turn: `prod-029-scenario-014::turn-005`
- Gap type: `autonomy-check_policy_mismatch`
- Expected policy/control: `autonomy-check` / `continue-call`
- Observed policy/control: `clarify-fit` / `continue-call`
- Grounded answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

### prod-029-scenario-015 - callback_request

- Turn: `prod-029-scenario-015::turn-006`
- Gap type: `scheduling-confirmation_call-control-mismatch`
- Expected policy/control: `schedule-callback` / `schedule-and-end`
- Observed policy/control: `human-escalation` / `transfer-or-escalate`
- Grounded answer:

```text
Confirmed for the specialist callback. The next step stays non-binding, with no payment handled in this call.
```

### prod-029-scenario-020 - price_objection

- Turn: `prod-029-scenario-020::turn-005`
- Gap type: `autonomy-check_policy_mismatch`
- Expected policy/control: `autonomy-check` / `continue-call`
- Observed policy/control: `clarify-fit` / `continue-call`
- Grounded answer:

```text
There is no rush. The next step is only a non-binding 30-minute workflow review, and RouteSignal CRM pricing or security details can be checked before any commitment.
```

