# PROD-029 Grounded Full Scenario Rerun

PROD-029 reruns the PROD-027 full scenario route set with the PROD-028 synthetic campaign facts. It keeps the same 20 scenarios / 120 turns and compares old PROD-027 answers vs grounded campaign answers.

## Result

- Checkpoint id: `PROD-029-grounded-full-scenario-rerun`
- Source checkpoint: `PROD-027-full-scenario-route-evaluation`
- Grounding checkpoint: `PROD-028-synthetic-campaign-knowledge-grounding`
- Same 20 scenarios / 120 turns: `true`
- Old PROD-027 answers vs grounded campaign answers: `true`
- Same PROD-027 scenario set: `true`
- Synthetic campaign facts used: `true`
- Exact customer turns visible: `true`
- Exact PROD-027 answers visible: `true`
- Exact grounded answers visible: `true`
- Route decision process visible: `true`
- Direct answer rate: `1.0`
- Knowledge-applicable fact rate: `1.0`
- Grounded question overuse rate: `0.0`
- PROD-027 question overuse rate: `0.7833`
- Grounded answer win rate: `0.6583`
- Route correctness: `0.9167`
- Scenario route pass rate: `0.65`
- Hard failures: `0`
- Payment collection count: `0`
- Unsupported claim count: `0`
- Leakage findings: `0`
- Provider calls made: `false`
- Runtime behavior changed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Next checkpoint: `PROD-030-grounded-demo-review`

## Outputs

- `research/experiments/generated/PROD-029-grounded-full-scenario-rerun/result.json`
- `research/experiments/generated/PROD-029-grounded-full-scenario-rerun/report.md`
- `research/experiments/generated/PROD-029-grounded-full-scenario-rerun/grounded_full_scenario_set.json`
- `research/experiments/generated/PROD-029-grounded-full-scenario-rerun/grounded_full_scenario_trace.html`

## Evaluation Shape

The checkpoint preserves the PROD-027 customer turns, expected policy actions, expected call controls, and source-pattern references. For each turn it shows:

- exact customer message
- old PROD-027 agent answer
- grounded campaign answer
- expected and observed policy action
- expected and observed call control
- route correctness
- product fact markers used
- answer quality delta
- safety flags

## Interpretation

The grounded campaign answers materially improve answer usefulness while preserving the same route behavior as PROD-027. The remaining route gap is not caused by the campaign facts: route correctness stays at `0.9167`, policy-action correctness stays at `0.9167`, call-control correctness stays at `0.975`, and scenario route pass rate stays at `0.65`.

## Boundary

PROD-029 does not overwrite PROD-027. It is local evaluation only. It does not call providers, call an LLM, read private data, download datasets, collect payment, start a server, enable retrieval by default, enable composer hooks by default, or promote runtime behavior.

## Commands

```powershell
python scripts\run_prod_029_grounded_full_scenario_rerun.py
python scripts\validate_prod_029_grounded_full_scenario_rerun.py
```
