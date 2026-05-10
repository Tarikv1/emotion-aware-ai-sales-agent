# PROD-040 CallCenterEN Conditional Customer Simulation

PROD-040 replaces the planned same-text demo rerun with a stronger customer simulator checkpoint.

Every customer response is generated from the current call state and the immediately preceding agent answer. CallCenterEN is used through the leakage-checked PROD-013/PROD-014 abstract pattern banks only, not copied transcript wording.

## Local Commands

```powershell
python scripts\run_prod_040_callcenteren_conditional_customer_simulation.py
python scripts\validate_prod_040_callcenteren_conditional_customer_simulation.py
```

## Outputs

- `research/experiments/generated/PROD-040-callcenteren-conditional-customer-simulation/result.json`
- `research/experiments/generated/PROD-040-callcenteren-conditional-customer-simulation/report.md`
- `research/experiments/generated/PROD-040-callcenteren-conditional-customer-simulation/conditional_customer_traces.json`
- `research/experiments/generated/PROD-040-callcenteren-conditional-customer-simulation/conditional_customer_trace_demo.html`
- `research/experiments/generated/PROD-040-callcenteren-conditional-customer-simulation/conditional_customer_trace_demo_data.json`

## Result

- Conditional customer turn count: `19`
- Agent-conditioned customer reply count: `19`
- Unique customer response count: `19`
- Repeated customer response count: `0`
- Agent opening line visible count: `8`
- Conversation sequence starts with agent count: `8`
- CallCenterEN pattern source count: `59`
- Scenario bank source count: `8`
- Abstract pattern only: `true`
- Exact transcript text used: `false`
- All calls start with cold opening: `true`
- All calls end by customer decision: `true`
- Fixed turn limit used: `false`
- Loop guard triggered: `false`
- Accepted deals: `4`
- Rejected deals: `4`
- Hard failures: `0`
- Payment collection count: `0`
- Leakage findings: `0`

## What To Review

Open the local HTML surface and inspect whether the customer responses now feel like reactions to the agent answer, not standalone scripted lines.

The important panels are:

- `Agent Answer Signals`
- `Why Customer Changed`
- `CallCenterEN Pattern Basis`
- `State Before / Delta / After`
- `Decision Snapshot`

## Decision

The next checkpoint is `PROD-041-conditional-simulation-review`.

PROD-041 should be a human review of whether these conditional conversations are realistic enough to unblock voice playback, scenario branching, more seeds, or public demo polish.

## Boundary

PROD-040 does not call providers, call an LLM, read private data, download datasets, store raw transcripts, copy transcript text, export transcript-derived commercial runtime prompts, start a server, collect payment, enable retrieval by default, enable composer hooks by default, change runtime behavior, or allow production runtime promotion.
