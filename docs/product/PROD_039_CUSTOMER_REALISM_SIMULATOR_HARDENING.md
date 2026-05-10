# PROD-039 Customer Realism Simulator Hardening

PROD-039 keeps the same fixed `PROD-037` calls and rewrites only simulated customer phrasing.

The goal is to remove artificial customer responses before any voice playback, more seeds, scenario branching, or public demo polish.

## Local Commands

```powershell
python scripts\run_prod_039_customer_realism_simulator_hardening.py
python scripts\validate_prod_039_customer_realism_simulator_hardening.py
```

## Outputs

- `research/experiments/generated/PROD-039-customer-realism-simulator-hardening/result.json`
- `research/experiments/generated/PROD-039-customer-realism-simulator-hardening/report.md`
- `research/experiments/generated/PROD-039-customer-realism-simulator-hardening/customer_realism_hardened_traces.json`
- `research/experiments/generated/PROD-039-customer-realism-simulator-hardening/customer_realism_comparison_packet.json`
- `research/experiments/generated/PROD-039-customer-realism-simulator-hardening/customer_realism_comparison.html`

## Result

- Customer realism gate passed: `true`
- Customer response changed count: `14`
- Customer opening changed count: `8`
- Agent answer changed count: `0`
- Decision snapshot changed count: `0`
- Terminal outcome changed count: `0`
- Safety flag changed count: `0`
- Hardened unrealistic phrase hits: `0`
- Same cases rerun: `true`
- One editable surface: `customer_simulator_response_phrasing`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Next build recommendation: `customer_realism_demo_surface_rerun`

## Decision

The next checkpoint is `PROD-040-customer-realism-demo-surface-rerun`.

PROD-040 should rebuild the local trace demo surface from the hardened traces and compare whether the conversation now feels better in the actual inspection UI.

## Boundary

PROD-039 does not call providers, call an LLM, read private data, download datasets, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, unblock voice playback, unblock public demo polish, or allow production runtime promotion.
