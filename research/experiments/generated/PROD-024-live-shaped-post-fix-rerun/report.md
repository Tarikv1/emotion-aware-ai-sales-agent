# PROD-024 Live-Shaped Post-Fix Rerun

PROD-024 is the live-shaped post-fix rerun after PROD-023. It checks the full dialogue-policy path, not only the ten gap turns.

## Summary

- Source checkpoint: `PROD-023-runtime-policy-call-control-fix`
- Source PROD-023 result: `research/experiments/generated/PROD-023-runtime-policy-call-control-fix/result.json`
- Calls: `7`
- Customer turns: `19`
- Policy action correctness: `1.0`
- Call-control correctness: `1.0`
- Protected context preservation: `1.0`
- Non-sale correctness: `1.0`
- Safe-close correctness: `1.0`
- State reference completeness: `1.0`
- Hard failures: `0`
- Payment collection count: `0`
- Leakage findings: `0`
- Post-fix gate passed: `true`
- Legacy PROD-021 gate passed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Runtime promotion allowed: `false`
- Bounded demo discussion allowed: `true`
- Next checkpoint recommended: `PROD-025-bounded-demo-readiness-packet`

## Interpretation

- The post-fix gate passes because policy action, call-control, protected contexts, non-sale handling, safe-close handling, and leakage boundaries are clean across all live-shaped turns.
- The legacy PROD-021 gate stays false because that older hypothesis required composer-hook gain. PROD-024 does not use hook gain as a promotion criterion.
- Keep composer hooks opt-in and keep retrieval default enabled: `false`.
- `close-and-log-sale-ready` remains the explicit safe-close control for campaign-approved verbal next-step agreement.

## Post-Fix Turn Trace

### PROD-021-C01-T01

- Scenario label: `software_multi_objection_sale`
- Stage: `relevance-check`
- Expected policy action: `value-clarify`
- Post-fix policy action: `value-clarify`
- Expected call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

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
- Post-fix policy action: `fair-compare`
- Expected call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

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
- Post-fix policy action: `autonomy-check`
- Expected call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

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
- Post-fix policy action: `close-and-log-sale-ready`
- Expected call-control: `close-and-log-sale-ready`
- Post-fix call-control: `close-and-log-sale-ready`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

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
- Post-fix policy action: `stakeholder-review`
- Expected call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

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
- Post-fix policy action: `procurement-review`
- Expected call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

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
- Post-fix policy action: `procurement-review`
- Expected call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
Next week might work for review, but I cannot commit to anything firm now.
```

Post-fix answer:

```text
Understood. What written information would help procurement review this without asking you for anything firm today?
```

### PROD-021-C03-T01

- Scenario label: `insurance_claim_privacy_escalation`
- Stage: `claim-boundary`
- Expected policy action: `claim-boundary-escalation`
- Post-fix policy action: `claim-boundary-escalation`
- Expected call-control: `transfer-or-escalate`
- Post-fix call-control: `transfer-or-escalate`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
Can you guarantee this coverage before I share details?
```

Post-fix answer:

```text
I hear the certainty concern. I do not want to make a claim that depends on details we have not checked, so the safest next step is to route this to a solutions specialist.
```

### PROD-021-C03-T02

- Scenario label: `insurance_claim_privacy_escalation`
- Stage: `privacy-boundary`
- Expected policy action: `privacy-safe-escalation`
- Post-fix policy action: `privacy-safe-escalation`
- Expected call-control: `transfer-or-escalate`
- Post-fix call-control: `transfer-or-escalate`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
I am worried about privacy and want a real person before I answer.
```

Post-fix answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### PROD-021-C03-T03

- Scenario label: `insurance_claim_privacy_escalation`
- Stage: `privacy-boundary`
- Expected policy action: `privacy-safe-escalation`
- Post-fix policy action: `privacy-safe-escalation`
- Expected call-control: `transfer-or-escalate`
- Post-fix call-control: `transfer-or-escalate`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
Please route this to a human specialist before we discuss anything else.
```

Post-fix answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### PROD-021-C04-T01

- Scenario label: `medical_technical_safety_escalation`
- Stage: `technical-boundary`
- Expected policy action: `technical-escalation`
- Post-fix policy action: `technical-escalation`
- Expected call-control: `transfer-or-escalate`
- Post-fix call-control: `transfer-or-escalate`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
I need a human specialist for the device safety details before I decide.
```

Post-fix answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### PROD-021-C04-T02

- Scenario label: `medical_technical_safety_escalation`
- Stage: `technical-boundary`
- Expected policy action: `technical-escalation`
- Post-fix policy action: `technical-escalation`
- Expected call-control: `transfer-or-escalate`
- Post-fix call-control: `transfer-or-escalate`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
A specialist is required here; I do not want an automatic answer.
```

Post-fix answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### PROD-021-C05-T01

- Scenario label: `membership_refusal_end_call`
- Stage: `refusal`
- Expected policy action: `end-call`
- Post-fix policy action: `end-call`
- Expected call-control: `end-call`
- Post-fix call-control: `end-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
No thank you, I want to cancel and stop the sales call.
```

Post-fix answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

### PROD-021-C05-T02

- Scenario label: `membership_refusal_end_call`
- Stage: `refusal`
- Expected policy action: `end-call`
- Post-fix policy action: `end-call`
- Expected call-control: `end-call`
- Post-fix call-control: `end-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
Stop calling me. I am not interested.
```

Post-fix answer:

```text
Understood. I will mark this contact so you are not called again. Goodbye.
```

### PROD-021-C06-T01

- Scenario label: `home_service_support_handoff`
- Stage: `support-boundary`
- Expected policy action: `support-first-escalation`
- Post-fix policy action: `support-first-escalation`
- Expected call-control: `transfer-or-escalate`
- Post-fix call-control: `transfer-or-escalate`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
My service issue is unresolved, and I need a real person, not an upsell.
```

Post-fix answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### PROD-021-C06-T02

- Scenario label: `home_service_support_handoff`
- Stage: `support-boundary`
- Expected policy action: `support-first-escalation`
- Post-fix policy action: `support-first-escalation`
- Expected call-control: `transfer-or-escalate`
- Post-fix call-control: `transfer-or-escalate`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
Please route me to a human support specialist before trying to sell anything else.
```

Post-fix answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

### PROD-021-C07-T01

- Scenario label: `trust_price_callback`
- Stage: `trust-repair`
- Expected policy action: `trust-repair`
- Post-fix policy action: `trust-repair`
- Expected call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

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
- Post-fix policy action: `value-clarify`
- Expected call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

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
- Post-fix policy action: `autonomy-check`
- Expected call-control: `continue-call`
- Post-fix call-control: `continue-call`
- Policy action correct: `true`
- Call-control correct: `true`
- Protected context preserved: `true`

Customer turn:

```text
Send me a short summary and call back later; I need time to think.
```

Post-fix answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify what you need before any next step?
```

## Decision

Keep composer hooks opt-in, treat PROD-024 as a post-fix evidence gate rather than runtime promotion, and prepare `PROD-025-bounded-demo-readiness-packet` next.
