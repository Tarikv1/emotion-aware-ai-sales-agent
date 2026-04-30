# PROD-004 LLM Agent Run

Status: blocked pending live model credentials.

This checkpoint adds a live LLM runner for the PROD-004 sales difficulty gauntlet without recording synthetic or guessed LLM results.

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

## Current Result

The local environment does not currently expose `OPENAI_API_KEY`, so the runner exits before calling a live model.

Expected blocker message:

```text
Missing OPENAI_API_KEY. Set OPENAI_API_KEY to run the LLM product agent. The runner did not call a live model.
```

## Next Evaluation Question

Once credentials are available, compare the LLM agent against the PROD-004 rule baseline:

- Does it improve emotion detection?
- Does it improve hard sales judgment on objections, authority gaps, timing delays, and competitor comparisons?
- Does it preserve guardrails by escalating claim-boundary and human-request cases instead of over-selling?
