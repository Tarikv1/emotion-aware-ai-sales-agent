# PROD-022 PROD-021 Review Gap Packet

This review gap packet reads the completed PROD-021 result and extracts the exact customer turn, exact agent answer, policy action miss, and call-control miss evidence needed before any runtime promotion.

No runtime behavior change is made. No provider calls were made. No private data was read. Retrieval and composer hooks remain disabled by default.

## Summary

- Source checkpoint: `PROD-021-live-shaped-dialogue-policy-simulation`
- Source result: `research/experiments/generated/PROD-021-live-shaped-dialogue-policy-simulation/result.json`
- Source customer turns: `19`
- Source policy action correctness: `0.4737`
- Source call-control correctness: `0.8421`
- Gap turns: `10`
- Policy action misses: `10`
- Call-control misses: `3`
- Protected context gaps: `0`
- Hook gain turns: `4`
- Hard failures: `0`
- Leakage findings: `0`
- Runtime promotion allowed: `false`
- Next checkpoint recommended: `PROD-023-runtime-policy-call-control-fix`

## Gap Categories

| Category | Turns | Fix Target |
| --- | ---: | --- |
| `policy_action_router_gap` | `10` | `runtime_policy_router_specialization` |
| `call_control_sale_ready_gap` | `1` | `sale_ready_call_control_detector` |
| `call_control_procurement_delay_gap` | `2` | `procurement_review_continuation_guard` |

## Prioritized Next Actions

1. `runtime_policy_router_specialization`
   Action: Fix policy-action routing for the ten gap turns before changing retrieval or voice behavior.
   Rationale: The failed gate is mostly policy/action routing, not hooks; hook wording gain cannot substitute for correct dialogue state.

2. `procurement_review_continuation_guard`
   Action: Stop treating written-info or delayed-approval language as an end-call signal.
   Rationale: Two call-control misses came from procurement review language that should remain a low-pressure continuation.

3. `sale_ready_call_control_detector`
   Action: Add sale-ready recognition for verbal next-step agreement without payment collection.
   Rationale: One call-control miss blocked the MVP safe-close metric even though the customer was ready for a next step.

4. `keep_composer_hooks_opt_in`
   Action: Keep PROD-020 hooks available only behind the explicit opt-in flag.
   Rationale: The hooks improved four turns and caused no safety regression, but runtime promotion remains blocked.

## Gap Turns

### PROD-021-C01-T01

- Scenario label: `software_multi_objection_sale`
- Stage: `relevance-check`
- Policy action miss: expected `value-clarify`, observed `clarify-fit`
- Call-control miss: expected `continue-call`, observed `continue-call`
- Hook applied: `true`
- Recommended fix target: `runtime_policy_router_specialization`
- Why it matters: The hook improved wording, but the runtime policy action still stayed generic, so hook gain should not be treated as policy correctness.

Exact customer turn:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Exact agent answers:

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval-only answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hook answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### PROD-021-C01-T02

- Scenario label: `software_multi_objection_sale`
- Stage: `comparison`
- Policy action miss: expected `fair-compare`, observed `clarify-fit`
- Call-control miss: expected `continue-call`, observed `continue-call`
- Hook applied: `false`
- Recommended fix target: `runtime_policy_router_specialization`
- Why it matters: The answer remained safe, but the runtime policy action missed the specific sales state needed for a reliable next move.

Exact customer turn:

```text
We already use another provider, so compare this fairly without pressure.
```

Exact agent answers:

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval-only answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hook answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

### PROD-021-C01-T03

- Scenario label: `software_multi_objection_sale`
- Stage: `timing-openness-check`
- Policy action miss: expected `autonomy-check`, observed `clarify-fit`
- Call-control miss: expected `continue-call`, observed `continue-call`
- Hook applied: `true`
- Recommended fix target: `runtime_policy_router_specialization`
- Why it matters: The hook improved wording, but the runtime policy action still stayed generic, so hook gain should not be treated as policy correctness.

Exact customer turn:

```text
I need time to think; do not rush me into a commitment today.
```

Exact agent answers:

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval-only answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hook answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify fit, timing, or anything you need verified before reviewing it?
```

### PROD-021-C01-T04

- Scenario label: `software_multi_objection_sale`
- Stage: `commitment-confirmation`
- Policy action miss: expected `close-and-log-sale-ready`, observed `clarify-fit`
- Call-control miss: expected `close-and-log-sale-ready`, observed `continue-call`
- Hook applied: `false`
- Recommended fix target: `sale_ready_call_control_detector`
- Why it matters: The customer gave sale-ready language with no payment collection, but runtime call control kept asking instead of logging the sale-ready outcome.

Exact customer turn:

```text
If this fits our process and there is no payment today, I am ready to agree to the next step.
```

Exact agent answers:

Default-off answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Retrieval-only answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

Opt-in hook answer:

```text
Thanks. To check fit without wasting time, is your main concern whether this is relevant for your situation, the price, or the timing?
```

### PROD-021-C02-T01

- Scenario label: `software_procurement_authority_delay`
- Stage: `authority-check`
- Policy action miss: expected `stakeholder-review`, observed `clarify-fit`
- Call-control miss: expected `continue-call`, observed `continue-call`
- Hook applied: `false`
- Recommended fix target: `runtime_policy_router_specialization`
- Why it matters: The answer remained safe, but the runtime policy action missed the specific sales state needed for a reliable next move.

Exact customer turn:

```text
My boss has to review this before I can decide.
```

Exact agent answers:

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval-only answer:

```text
That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?
```

Opt-in hook answer:

```text
That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?
```

### PROD-021-C02-T02

- Scenario label: `software_procurement_authority_delay`
- Stage: `procurement-review`
- Policy action miss: expected `procurement-review`, observed `autonomy-check`
- Call-control miss: expected `continue-call`, observed `end-call`
- Hook applied: `false`
- Recommended fix target: `procurement_review_continuation_guard`
- Why it matters: The customer asked for written review or delayed approval, which should stay in a low-pressure continuation path rather than end the call.

Exact customer turn:

```text
Procurement needs written information and nothing firm from me today.
```

Exact agent answers:

Default-off answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

Retrieval-only answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

Opt-in hook answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

### PROD-021-C02-T03

- Scenario label: `software_procurement_authority_delay`
- Stage: `procurement-review`
- Policy action miss: expected `procurement-review`, observed `autonomy-check`
- Call-control miss: expected `continue-call`, observed `end-call`
- Hook applied: `false`
- Recommended fix target: `procurement_review_continuation_guard`
- Why it matters: The customer asked for written review or delayed approval, which should stay in a low-pressure continuation path rather than end the call.

Exact customer turn:

```text
Next week might work for review, but I cannot commit to anything firm now.
```

Exact agent answers:

Default-off answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

Retrieval-only answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

Opt-in hook answer:

```text
Thanks, I understand the timing is not firm. I will log a follow-up instead of forcing an appointment now.
```

### PROD-021-C07-T01

- Scenario label: `trust_price_callback`
- Stage: `trust-repair`
- Policy action miss: expected `trust-repair`, observed `clarify-fit`
- Call-control miss: expected `continue-call`, observed `continue-call`
- Hook applied: `false`
- Recommended fix target: `runtime_policy_router_specialization`
- Why it matters: The answer remained safe, but the runtime policy action missed the specific sales state needed for a reliable next move.

Exact customer turn:

```text
I do not know your company. How can I verify this is legitimate?
```

Exact agent answers:

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval-only answer:

```text
Fair. Trust matters on a cold call. To make this useful, should I send company context, security details, or a specialist review path first?
```

Opt-in hook answer:

```text
Fair. Trust matters on a cold call. To make this useful, should I send company context, security details, or a specialist review path first?
```

### PROD-021-C07-T02

- Scenario label: `trust_price_callback`
- Stage: `price-check`
- Policy action miss: expected `value-clarify`, observed `clarify-fit`
- Call-control miss: expected `continue-call`, observed `continue-call`
- Hook applied: `true`
- Recommended fix target: `runtime_policy_router_specialization`
- Why it matters: The hook improved wording, but the runtime policy action still stayed generic, so hook gain should not be treated as policy correctness.

Exact customer turn:

```text
The cost sounds high; is this worth my time?
```

Exact agent answers:

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval-only answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hook answer:

```text
That makes sense. Is the bigger concern the price, the terms, or whether the value is worth reviewing now?
```

### PROD-021-C07-T03

- Scenario label: `trust_price_callback`
- Stage: `callback`
- Policy action miss: expected `autonomy-check`, observed `clarify-fit`
- Call-control miss: expected `continue-call`, observed `continue-call`
- Hook applied: `true`
- Recommended fix target: `runtime_policy_router_specialization`
- Why it matters: The hook improved wording, but the runtime policy action still stayed generic, so hook gain should not be treated as policy correctness.

Exact customer turn:

```text
Send me a short summary and call back later; I need time to think.
```

Exact agent answers:

Default-off answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Retrieval-only answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

Opt-in hook answer:

```text
That makes sense. Would a brief callback later help, or should we first clarify fit, timing, or anything you need verified before reviewing it?
```

## Decision

Keep composer hooks opt-in. Fix runtime policy routing and call-control before any demo or default-runtime discussion.
