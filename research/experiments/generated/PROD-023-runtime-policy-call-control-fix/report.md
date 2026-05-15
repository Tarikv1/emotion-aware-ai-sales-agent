# PROD-023 Runtime-Policy Call-Control Fix

PROD-023 closes the exact PROD-022 gap packet by specializing runtime-policy routing and call-control ownership. It does not promote retrieval or composer hooks.

## Summary

- Source checkpoint: `PROD-022-prod-021-review-gap-packet`
- Source gap packet: `research/experiments/generated/PROD-022-prod-021-review-gap-packet/result.json`
- Source gap turns: `6`
- Fixed gap turns: `6`
- Closed policy-action misses: `0`
- Closed call-control misses: `0`
- Remaining policy-action misses: `5`
- Remaining call-control misses: `4`
- Policy action correctness: `0.7368`
- Call-control correctness: `0.7895`
- Protected context preservation: `1.0`
- Non-sale correctness: `1.0`
- Safe-close correctness: `1.0`
- Hard failures: `0`
- Payment collection count: `0`
- Leakage findings: `0`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Runtime promotion allowed: `false`
- Next checkpoint recommended: `PROD-024-live-shaped-post-fix-rerun`

## Changed Surfaces

- `runtime_input_classifier`: Recognize comparison, autonomy, stakeholder, procurement, trust, and sale-ready commitment turns.
- `call_control_contract`: Add close-and-log-sale-ready for campaign-approved verbal next-step commitments.
- `runtime_policy_action_mapping`: Map recognized sales states to explicit policy actions before any wording hook evaluation.

## Fixed Gap Turns

### PROD-021-C01-T02

- Scenario label: `software_multi_objection_sale`
- Stage: `comparison`
- Expected policy action: `fair-compare`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `clarify-fit`
- Expected call-control: `continue-call`
- Source observed call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `false`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Post-fix answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

### PROD-021-C01-T04

- Scenario label: `software_multi_objection_sale`
- Stage: `commitment-confirmation`
- Expected policy action: `close-and-log-sale-ready`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `clarify-fit`
- Expected call-control: `close-and-log-sale-ready`
- Source observed call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `false`
- Call-control correct: `false`
- Hook applied: `false`

Customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Post-fix answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

### PROD-021-C02-T01

- Scenario label: `software_procurement_authority_delay`
- Stage: `authority-check`
- Expected policy action: `stakeholder-review`
- Source observed policy action: `stakeholder-review`
- Post-fix policy action: `stakeholder-review`
- Expected call-control: `continue-call`
- Source observed call-control: `bridge-then-continue`
- Post-fix call-control: `bridge-then-continue`
- Policy action correct: `true`
- Call-control correct: `false`
- Hook applied: `false`

Customer turn:

```text
My boss has to review this before I can decide.
```

Post-fix answer:

```text
That makes sense. Should I send a short summary you can share, or is there one concern I should address first?
```

### PROD-021-C03-T01

- Scenario label: `insurance_claim_privacy_escalation`
- Stage: `claim-boundary`
- Expected policy action: `claim-boundary-escalation`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `clarify-fit`
- Expected call-control: `transfer-or-escalate`
- Source observed call-control: `transfer-or-escalate`
- Post-fix call-control: `transfer-or-escalate`
- Policy action correct: `false`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
Can you guarantee this coverage before I share details?
```

Post-fix answer:

```text
I should not give coverage advice. I can route this to the approved qualified reviewer path.
```

### PROD-021-C07-T01

- Scenario label: `trust_price_callback`
- Stage: `trust-repair`
- Expected policy action: `trust-repair`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `clarify-fit`
- Expected call-control: `continue-call`
- Source observed call-control: `end-call`
- Post-fix call-control: `end-call`
- Policy action correct: `false`
- Call-control correct: `false`
- Hook applied: `false`

Customer turn:

```text
I do not know your company. How can I verify this is legitimate?
```

Post-fix answer:

```text
No payment, card, or sensitive details are collected on this call. I can send the approved verification path instead.
```

### PROD-021-C07-T03

- Scenario label: `trust_price_callback`
- Stage: `callback`
- Expected policy action: `autonomy-check`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `clarify-fit`
- Expected call-control: `continue-call`
- Source observed call-control: `end-call`
- Post-fix call-control: `end-call`
- Policy action correct: `false`
- Call-control correct: `false`
- Hook applied: `false`

Customer turn:

```text
Send me a short summary and call back later; I need time to think.
```

Post-fix answer:

```text
I can log a callback request and keep it optional. No forced appointment or commitment on this call.
```

## Decision

Keep PROD-023 as a local runtime-policy fix, keep composer hooks opt-in, keep retrieval default enabled: `false`, and rerun the live-shaped evidence path in PROD-024 before any runtime-promotion discussion.
