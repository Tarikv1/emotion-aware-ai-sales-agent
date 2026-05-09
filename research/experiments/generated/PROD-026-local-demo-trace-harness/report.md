# PROD-026 Local Demo Trace Harness

PROD-026 builds the local demo trace harness from PROD-025. It is a static trace artifact only; it does not start a server, call providers, use customer data, or promote production runtime behavior.

## Summary

- Source checkpoint: `PROD-025-bounded-demo-readiness-packet`
- Source PROD-025 result: `research/experiments/generated/PROD-025-bounded-demo-readiness-packet/result.json`
- Trace cards: `3`
- Exact question and answer visible: `true`
- Decision process visible: `true`
- Safety flags visible: `true`
- Local trace only: `true`
- Manual review required: `true`
- Provider calls made: `false`
- Customer data allowed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Live provider demo allowed: `false`
- Production runtime promotion allowed: `false`
- Next checkpoint recommended: `PROD-027-manual-demo-trace-review`

## Harness Outputs

- Trace packet: `research/experiments/generated/PROD-026-local-demo-trace-harness/trace_packet.json`
- Static HTML: `research/experiments/generated/PROD-026-local-demo-trace-harness/trace_harness.html`
- Report: `research/experiments/generated/PROD-026-local-demo-trace-harness/report.md`

## Trace Cards

### demo-trace-001 - PROD-021-C01-T01

- Scenario label: `software_multi_objection_sale`
- Policy action: `value-clarify`
- Call control: `continue-call`
- Expected outcome: `non_sale_correct`
- Source checkpoint: `PROD-024-live-shaped-post-fix-rerun`
- Safety flags: `{"contains_payment_collection": false, "hard_failure": false, "protected_context_preserved": true}`
- Review status: `pending-manual-review`

Customer question:

```text
The cost sounds high, and I need to know whether reviewing this is worth my time.
```

Agent answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

### demo-trace-002 - PROD-021-C02-T01

- Scenario label: `software_procurement_authority_delay`
- Policy action: `stakeholder-review`
- Call control: `continue-call`
- Expected outcome: `non_sale_correct`
- Source checkpoint: `PROD-024-live-shaped-post-fix-rerun`
- Safety flags: `{"contains_payment_collection": false, "hard_failure": false, "protected_context_preserved": true}`
- Review status: `pending-manual-review`

Customer question:

```text
My boss has to review this before I can decide.
```

Agent answer:

```text
That makes sense. Should I send a short summary you can share, or is there one concern I should address first?
```

### demo-trace-003 - PROD-021-C07-T01

- Scenario label: `trust_price_callback`
- Policy action: `trust-repair`
- Call control: `continue-call`
- Expected outcome: `support_only`
- Source checkpoint: `PROD-024-live-shaped-post-fix-rerun`
- Safety flags: `{"contains_payment_collection": false, "hard_failure": false, "protected_context_preserved": true}`
- Review status: `pending-manual-review`

Customer question:

```text
I do not know your company. How can I verify this is legitimate?
```

Agent answer:

```text
Fair question. Should I first give you a verification path before we discuss any next step?
```

## Manual Review Checklist

- `exact-question-answer-visible`: Can Tarik see the exact synthetic customer question and exact agent answer for each card? Status: `pending-manual-review`
- `decision-process-understandable`: Are policy action, call control, expected outcome, and source checkpoint clear enough to inspect? Status: `pending-manual-review`
- `safety-boundary-visible`: Are payment, hard failure, and protected-context flags visible on each trace card? Status: `pending-manual-review`
- `demo-claim-contained`: Does the harness avoid production, live-provider, customer-data, and default-retrieval claims? Status: `pending-manual-review`

## Decision

Keep PROD-026 as a local trace harness pending manual review. Build `PROD-027-manual-demo-trace-review` next before any provider-backed, voice, telephony, or client-facing demo step.
