# PROD-023 Runtime-Policy Call-Control Fix

PROD-023 closes the exact PROD-022 gap packet by specializing runtime-policy routing and call-control ownership. It does not promote retrieval or composer hooks.

## Summary

- Source checkpoint: `PROD-022-prod-021-review-gap-packet`
- Source gap packet: `research/experiments/generated/PROD-022-prod-021-review-gap-packet/result.json`
- Source gap turns: `10`
- Fixed gap turns: `10`
- Closed policy-action misses: `10`
- Closed call-control misses: `3`
- Remaining policy-action misses: `0`
- Remaining call-control misses: `0`
- Policy action correctness: `1.0`
- Call-control correctness: `1.0`
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

### PROD-021-C01-T01

- Scenario label: `software_multi_objection_sale`
- Stage: `relevance-check`
- Expected policy action: `value-clarify`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `value-clarify`
- Expected call-control: `continue-call`
- Source observed call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Post-fix answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

### PROD-021-C01-T02

- Scenario label: `software_multi_objection_sale`
- Stage: `comparison`
- Expected policy action: `fair-compare`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `fair-compare`
- Expected call-control: `continue-call`
- Source observed call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Post-fix answer:

```text
That is fair. Should we compare price, terms, or fit first without pressure?
```

### PROD-021-C01-T03

- Scenario label: `software_multi_objection_sale`
- Stage: `timing-openness-check`
- Expected policy action: `autonomy-check`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `autonomy-check`
- Expected call-control: `continue-call`
- Source observed call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
I need time to think; do not rush me into a commitment today.
```

Post-fix answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

### PROD-021-C01-T04

- Scenario label: `software_multi_objection_sale`
- Stage: `commitment-confirmation`
- Expected policy action: `close-and-log-sale-ready`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `close-and-log-sale-ready`
- Expected call-control: `close-and-log-sale-ready`
- Source observed call-control: `continue-call`
- Post-fix call-control: `close-and-log-sale-ready`
- Policy action correct: `true`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Post-fix answer:

```text
Confirmed. I will mark this as sale-ready for the next step, with no payment handled on this call.
```

### PROD-021-C02-T01

- Scenario label: `software_procurement_authority_delay`
- Stage: `authority-check`
- Expected policy action: `stakeholder-review`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `stakeholder-review`
- Expected call-control: `continue-call`
- Source observed call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
My boss has to review this before I can decide.
```

Post-fix answer:

```text
That makes sense. Should I send a short summary you can share, or is there one concern I should address first?
```

### PROD-021-C02-T02

- Scenario label: `software_procurement_authority_delay`
- Stage: `procurement-review`
- Expected policy action: `procurement-review`
- Source observed policy action: `autonomy-check`
- Post-fix policy action: `procurement-review`
- Expected call-control: `continue-call`
- Source observed call-control: `end-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
Procurement needs written information and nothing firm from me today.
```

Post-fix answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

### PROD-021-C02-T03

- Scenario label: `software_procurement_authority_delay`
- Stage: `procurement-review`
- Expected policy action: `procurement-review`
- Source observed policy action: `autonomy-check`
- Post-fix policy action: `procurement-review`
- Expected call-control: `continue-call`
- Source observed call-control: `end-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
Next week might work for review, but I cannot commit to anything firm now.
```

Post-fix answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

### PROD-021-C07-T01

- Scenario label: `trust_price_callback`
- Stage: `trust-repair`
- Expected policy action: `trust-repair`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `trust-repair`
- Expected call-control: `continue-call`
- Source observed call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
I do not know your company. How can I verify this is legitimate?
```

Post-fix answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

### PROD-021-C07-T02

- Scenario label: `trust_price_callback`
- Stage: `price-check`
- Expected policy action: `value-clarify`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `value-clarify`
- Expected call-control: `continue-call`
- Source observed call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
The cost sounds high; is this worth my time?
```

Post-fix answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

### PROD-021-C07-T03

- Scenario label: `trust_price_callback`
- Stage: `callback`
- Expected policy action: `autonomy-check`
- Source observed policy action: `clarify-fit`
- Post-fix policy action: `autonomy-check`
- Expected call-control: `continue-call`
- Source observed call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Hook applied: `false`

Customer turn:

```text
Send me a short summary and call back later; I need time to think.
```

Post-fix answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

## Decision

Keep PROD-023 as a local runtime-policy fix, keep composer hooks opt-in, keep retrieval default enabled: `false`, and rerun the live-shaped evidence path in PROD-024 before any runtime-promotion discussion.
