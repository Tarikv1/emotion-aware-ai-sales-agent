# PROD-027 Full Scenario Route Evaluation

PROD-027 expands the local demo trace idea into a strong multi-turn scenario evaluation. It uses the accepted `PROD-014` CallCenterEN abstract scenario bank as pattern grounding, then creates project-owned full scenarios and runs the local guarded runtime through every turn.

## Result

- Checkpoint id: `PROD-027-full-scenario-route-evaluation`
- Source checkpoint: `PROD-014-callcenteren-scenario-bank`
- Strong evaluation set: `true`
- Full scenarios: `20`
- Turns per scenario: `6`
- Exact customer turns visible: `true`
- Exact agent answers visible: `true`
- Route decision process visible: `true`
- Local evaluation only: `true`
- Provider calls made: `false`
- Customer data allowed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Next checkpoint: `PROD-028-full-scenario-demo-review`

## Outputs

- `research/experiments/generated/PROD-027-full-scenario-route-evaluation/result.json`
- `research/experiments/generated/PROD-027-full-scenario-route-evaluation/report.md`
- `research/experiments/generated/PROD-027-full-scenario-route-evaluation/full_scenario_set.json`
- `research/experiments/generated/PROD-027-full-scenario-route-evaluation/full_scenario_route_trace.html`

## Evaluation Shape

Each scenario has six customer turns that cover opening, discovery, objection or boundary handling, clarification, close/callback/handoff, and wrap-up. Each turn records the exact customer message, exact agent answer, expected and observed policy action, expected and observed call control, route correctness, safety flags, and decision trace.

## Boundary

The scenario text is project-owned and generated from abstract pattern labels. It does not store source transcripts, reconstruct source calls, use a single source call as a scenario, call providers, read private data, collect payment, enable retrieval by default, enable composer hooks by default, or promote production runtime behavior.

## Commands

```powershell
python scripts\run_prod_027_full_scenario_route_evaluation.py
python scripts\validate_prod_027_full_scenario_route_evaluation.py
```
