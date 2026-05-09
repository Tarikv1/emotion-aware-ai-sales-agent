# PROD-026 Local Demo Trace Harness

PROD-026 builds the local trace-only demo harness from the accepted `PROD-025` bounded demo readiness packet. It creates a structured trace packet, Markdown report, and static HTML file for manual review.

## Result

- Checkpoint id: `PROD-026-local-demo-trace-harness`
- Source checkpoint: `PROD-025-bounded-demo-readiness-packet`
- Exact question and answer visible: `true`
- Decision process visible: `true`
- Safety flags visible: `true`
- Local trace only: `true`
- Manual review required: `true`
- Provider calls made: `false`
- Customer data allowed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Production runtime promotion allowed: `false`
- Live provider demo allowed: `false`
- Next checkpoint: `PROD-027-manual-demo-trace-review`

## Outputs

- `research/experiments/generated/PROD-026-local-demo-trace-harness/result.json`
- `research/experiments/generated/PROD-026-local-demo-trace-harness/report.md`
- `research/experiments/generated/PROD-026-local-demo-trace-harness/trace_packet.json`
- `research/experiments/generated/PROD-026-local-demo-trace-harness/trace_harness.html`

## Trace Content

Each trace card shows the synthetic customer question, agent answer, policy action, call control, expected outcome, source checkpoint, safety flags, and pending manual review status.

## Boundary

The harness is a static local artifact. It does not start a server, call providers, read private data, allow customer data, enable payment handling, enable retrieval by default, enable composer hooks by default, or make customer-facing product claims.

## Commands

```powershell
python scripts\run_prod_026_local_demo_trace_harness.py
python scripts\validate_prod_026_local_demo_trace_harness.py
```
