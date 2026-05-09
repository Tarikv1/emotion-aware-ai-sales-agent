# PROD-025 Bounded Demo Readiness Packet

PROD-025 turns the clean PROD-024 evidence into a bounded demo readiness packet. It does not enable provider calls, customer data, retrieval defaults, composer-hook defaults, or production runtime promotion.

## Summary

- Source checkpoint: `PROD-024-live-shaped-post-fix-rerun`
- Source PROD-024 result: `research/experiments/generated/PROD-024-live-shaped-post-fix-rerun/result.json`
- Source calls: `7`
- Source turns: `19`
- Policy action correctness: `1.0`
- Call-control correctness: `1.0`
- Demo readiness gate passed: `true`
- Bounded demo ready: `true`
- Local dry-run only: `true`
- Manual review required: `true`
- Production runtime promotion allowed: `false`
- Live provider demo allowed: `false`
- Customer data allowed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Next checkpoint recommended: `PROD-026-local-demo-trace-harness`

## Allowed Demo Modes

- `local-trace-replay`: Replay selected synthetic post-fix turns with question, answer, policy action, call control, and safety flags visible. Provider calls default: `false`. Customer data allowed: `false`.
- `offline-scripted-call-simulation`: Run deterministic synthetic calls through the local runtime path and show structured decisions. Provider calls default: `false`. Customer data allowed: `false`.
- `human-review-packet`: Export a compact review packet for Tarik to inspect before any live/provider demo step. Provider calls default: `false`. Customer data allowed: `false`.

## Blocked Claims

- `production-ready autonomous calling`
- `customer-facing live runtime`
- `retrieval default enabled`
- `composer hooks default enabled`
- `payment collection or checkout`
- `human replacement`
- `provider/live voice readiness`

## Required Review Gates

- `product-demo-scope-review`: required before Any demo beyond local trace replay.
- `privacy-boundary-review`: required before Any use of non-synthetic lead, customer, call, or audio material.
- `provider-run-boundary-review`: required before Any live TTS, LLM, ASR, telephony, or external provider call.
- `manual-trace-review`: required before Treating the demo trace as acceptable product evidence.
- `human-approval-before-live`: required before Any client-facing, live-call, or provider-backed demonstration.

## Demo Trace Contract

- Exact question and answer visible: `true`
- Show decision process: `true`
- Private data allowed: `false`
- Required fields: `scenario_label, customer_question, agent_answer, policy_action, call_control, safety_flags, source_checkpoint`

## Demo Trace Cards

### PROD-021-C01-T01

- Scenario label: `software_multi_objection_sale`
- Policy action: `value-clarify`
- Call control: `continue-call`
- Expected outcome: `non_sale_correct`
- Safety flags: `{"contains_payment_collection": false, "hard_failure": false, "protected_context_preserved": true}`

Customer question:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

### PROD-021-C02-T01

- Scenario label: `software_procurement_authority_delay`
- Policy action: `stakeholder-review`
- Call control: `continue-call`
- Expected outcome: `non_sale_correct`
- Safety flags: `{"contains_payment_collection": false, "hard_failure": false, "protected_context_preserved": true}`

Customer question:

```text
My boss has to review this before I can decide.
```

Agent answer:

```text
That makes sense. Should I send a short summary you can share, or is there one concern I should address first?
```

### PROD-021-C07-T01

- Scenario label: `trust_price_callback`
- Policy action: `trust-repair`
- Call control: `continue-call`
- Expected outcome: `support_only`
- Safety flags: `{"contains_payment_collection": false, "hard_failure": false, "protected_context_preserved": true}`

Customer question:

```text
I do not know your company. How can I verify this is legitimate?
```

Agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

## Decision

Bounded demo readiness is accepted for local trace-only work. Build `PROD-026-local-demo-trace-harness` next, with live providers, customer data, payment handling, retrieval defaults, and composer-hook defaults still blocked.
