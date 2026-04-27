# Prompt And Evaluation Workflow

## Purpose

Describe how the first baseline responses should be produced and compared.

## Workflow

1. Select or create a test case with:
   - recent dialogue context
   - current user utterance
   - compact emotion label
   - adaptive strategy label
2. Generate a response with the non-adaptive baseline prompt.
3. Generate a response with the adaptive baseline prompt.
4. Evaluate both responses using `EVALUATION_RUBRIC.md`.
5. Record the result in an experiment note under `research/experiments/`.

For the first pass, use:

- `research/experiments/EXP-001-phase1-prompt-baseline.md`
- `research/experiments/EXP-001-case-pack.md`

For the second pass, use:

- `research/experiments/EXP-002-dataset-derived-baseline.md`
- `research/experiments/EXP-002-dataset-derived-case-pack.md`

## Prompt files

- `packages/prompts/baseline-non-adaptive.txt`
- `packages/prompts/baseline-adaptive.txt`

## Repeatable runner

Use:

`scripts/run_prompt_baseline.py`

This script takes a structured JSON case file and generates a repeatable markdown packet with:

- rendered non-adaptive prompts
- rendered adaptive prompts
- response slots
- rubric score placeholders

Current structured case files:

- `research/experiments/cases/exp-001-seed.json`
- `research/experiments/cases/exp-002-dataset-derived.json`

## Current adaptive policy

Use the phase-1 mapping:

- `positive` -> `direct-ask-or-commitment`
- `neutral` -> `evidence-or-benefit`
- `skeptical-or-negative` -> `inquiry`

## Output expectation

Each case should produce:

- one non-adaptive response
- one adaptive response
- one rubric-based comparison record
