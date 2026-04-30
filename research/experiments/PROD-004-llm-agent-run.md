# PROD-004 LLM Agent Run

Status: completed.

This checkpoint records a live LLM runner and completed LLM run for the PROD-004 sales difficulty gauntlet.

## Purpose

PROD-004 tests whether the reusable sales-agent core can handle difficult selling moments across campaign profiles, not just one product vertical. The LLM run is intended to compare a model-backed agent against the deterministic rule baseline on the same cases, campaign configs, and scoring labels.

## Runner

- Script: `scripts/run_llm_product_agent.py`
- Validator: `scripts/validate_llm_product_agent_runner.py`
- Case file: `research/experiments/cases/prod-004-sales-difficulty-gauntlet.json`
- Default prompt: `packages/prompts/product-qualification-agent.txt`

## Command

```powershell
python scripts\run_llm_product_agent.py `
  --cases research\experiments\cases\prod-004-sales-difficulty-gauntlet.json `
  --out research\experiments\generated\PROD-004-llm-agent-results.json `
  --report-out research\experiments\generated\PROD-004-llm-agent-report.md
```

## Result

- Model: `gpt-4o-mini`
- Results JSON: `research/experiments/generated/PROD-004-llm-agent-results.json`
- Report: `research/experiments/generated/PROD-004-llm-agent-report.md`
- Comparison: `research/experiments/PROD-004-llm-vs-rule-comparison.md`

Aggregate LLM results:

- Turn emotion matches: 13 / 20
- Turn interest-state matches: 18 / 20
- Turn strategy matches: 7 / 20
- Final call-status matches: 10 / 14
- Final interest-state matches: 12 / 14
- Final strategy matches: 6 / 14
- Final appointment matches: 14 / 14

## Evaluation Question

Compared with the deterministic rule baseline, the LLM agent improved emotion detection, interest-state detection, final call-status judgment, and final interest-state judgment. The main weakness is weaker alignment with the internal strategy taxonomy.

Next improvement target: tighten the output contract so impossible combinations are normalized, especially `interest_state = needs-human` with `call_status = completed`.
