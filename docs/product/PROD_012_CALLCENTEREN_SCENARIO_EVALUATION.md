# PROD-012 CallCenterEN Scenario Evaluation

## Purpose

PROD-012 turns the CallCenterEN / AIxBlock real-world call-center dataset idea into a local evaluation lane.

It does not copy transcripts, train on the dataset, or use dataset text in commercial runtime prompts. It uses the dataset only as pattern grounding for project-owned synthetic scenarios, then runs the same scenario turns through:

- old core: retrieval disabled
- retrieval version: opt-in RAG-018 retrieval enabled

## Source Boundary

- Dataset: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english
- Dataset file tree: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english/tree/main
- Paper: https://arxiv.org/abs/2507.02958
- License observed: `cc-by-nc-4.0`
- Reuse label: `pattern_grounding_only`
- Commercial runtime use: `false`
- Commercial model training use: `false`

Default runs do not download the dataset. If ZIPs are manually placed under `data/external/callcenteren/raw/`, the runner can scan source sentences transiently for leakage checks without writing raw transcript text into tracked artifacts.

## Scenario Rules

Every generated scenario must:

- use at least three source-pattern IDs
- be a project-owned rewrite
- avoid exact transcript sentences
- avoid high-similarity paraphrases
- avoid single-source transcript generation
- keep transcript-derived text out of commercial runtime prompts
- preserve support, handoff, refusal, and do-not-call boundaries

## Metrics

PROD-012 reports:

- `hard_failure_rate`: any safety, leakage, protected-text, non-sale, expected-winner, or latency hard failure
- `non_sale_correctness`: non-sale scenarios where the agent avoids closing and logs the right outcome
- `leakage_failure_rate`: scenario leakage findings per scenario count
- `scenario_quality_score`: source-pattern coverage, rewrite safety, outcome coverage, and turn coverage
- `sales_emotional_handling_score`: scored handling of objections, trust repair, autonomy support, and next-step quality
- `retrieval_win_rate`: quality-scored turns where RAG-018 beats the old retrieval-disabled core

## Commands

Run:

```powershell
python scripts\run_prod_012_callcenteren_scenario_evaluation.py
```

Validate:

```powershell
python scripts\validate_prod_012_callcenteren_scenario_evaluation.py
```

Default output:

```text
research/experiments/generated/PROD-012-callcenteren-scenario-evaluation/result.json
research/experiments/generated/PROD-012-callcenteren-scenario-evaluation/report.md
```

## Runtime Decision

This checkpoint can show whether retrieval performs better on real-call-pattern-grounded synthetic scenarios. It still does not make retrieval default. Runtime promotion requires a later gate that proves the gain survives broader call-outcome testing without pressure, unsupported claims, transcript leakage, or protected-context drift.
