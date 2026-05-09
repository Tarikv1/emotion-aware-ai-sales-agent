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
- Recommended demo scenarios: `4`
- Full demo set allowed: `false`
- Local demo subset allowed: `true`
- Runtime campaign profile promotion allowed: `false`
- Provider calls made: `false`
- Runtime behavior changed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Next checkpoint: `PROD-031-grounded-route-gap-fix`

## Outputs

- `research/experiments/generated/PROD-030-grounded-demo-review/result.json`
- `research/experiments/generated/PROD-030-grounded-demo-review/report.md`
- `research/experiments/generated/PROD-030-grounded-demo-review/demo_review_packet.json`
- `research/experiments/generated/PROD-030-grounded-demo-review/demo_review_trace.html`

## Interpretation

The grounded answer layer is accepted as a demo candidate because every grounded answer is safe, direct, and supported by the synthetic campaign facts where needed. The full scenario set is not accepted as a complete demo set because `10` route turns still need policy or call-control revision.

The demo-ready scenario labels are:

- `cancellation_boundary`
- `sale_eligible`
- `support_handoff`
- `trust_repair`

The route-gap scenario labels are:

- `callback_request`
- `price_objection`

The route-gap types are:

- `unknown-runtime-signal_policy_mismatch`
- `autonomy-check_policy_mismatch`
- `scheduling-confirmation_call-control-mismatch`

## Boundary

PROD-030 is a local review gate only. It does not overwrite PROD-029, call providers, call an LLM, read private data, download datasets, collect payment, start a server, enable retrieval by default, enable composer hooks by default, promote the runtime campaign profile, or allow production runtime promotion.

## Commands

```powershell
python scripts\run_prod_030_grounded_demo_review.py
python scripts\validate_prod_030_grounded_demo_review.py
```
