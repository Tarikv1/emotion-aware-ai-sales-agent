# PROD-043 Sales Playbook Runtime Adapter

## Summary

`PROD-043-sales-playbook-runtime-adapter` is an offline adapter/evaluator checkpoint. It reads the completed PROD-042 CallCenterEN turn-level playbook artifacts, classifies generic single-turn customer utterances, retrieves matching playbook and deterministic evaluation rules, and evaluates generic agent responses against those rules.

This checkpoint does not generate full conversations, does not modify runtime behavior, does not enable retrieval, and does not call providers or LLMs.

## Source Checkpoint

- Source checkpoint: `PROD-042-callcenteren-turn-pattern-playbook`
- Required inputs:
  - `customer_move_patterns.json`
  - `agent_response_tactics.json`
  - `sales_playbook_rules.json`
  - `evaluation_rules.json`
  - `failure_patterns.json`
  - `recovery_patterns.json`
  - `result.json`

PROD-043 reads these artifacts only. It does not regenerate or rewrite PROD-042.

## Local Commands

```powershell
python scripts\run_prod_043_sales_playbook_runtime_adapter.py
python scripts\validate_prod_043_sales_playbook_runtime_adapter.py
```

## Outputs

- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/result.json`
- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/report.md`
- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/customer_move_classification_cases.json`
- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/playbook_retrieval_cases.json`
- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/agent_response_evaluation_cases.json`
- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/agent_response_evaluations.json`
- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/runtime_adapter_review_data.json`
- `research/experiments/generated/PROD-043-sales-playbook-runtime-adapter/runtime_adapter_review.html`

## Classifier

The customer move classifier is deterministic. It uses PROD-042 customer move IDs plus abstract keyword/category signals to map a generic customer utterance to one or more `customer_move_id` values.

All classifier examples are synthetic generic test cases with:

- `example_type: synthetic_generic_test_case`
- `source_quote: false`
- `from_single_transcript: false`

## Playbook Retrieval

For each classified move, PROD-043 retrieves matching:

- sales playbook rules
- deterministic evaluation rules
- related failure patterns
- related recovery patterns
- recommended tactics
- avoided tactics
- required safety boundaries

Retrieval is offline artifact lookup only. Runtime retrieval remains disabled.

## Agent Response Evaluation

PROD-043 evaluates single-turn agent responses with deterministic checks. It detects broad tactic IDs and failure flags such as direct answer, written information offer, support routing, unsafe payment request, unsupported claim, pressure after refusal, or failed support boundary.

The checkpoint includes generic good and bad response cases per customer move where supported. It does not create multi-turn scripts or synthetic conversations.

## Boundary Rules

- Runtime behavior changed: `false`
- Retrieval enabled: `false`
- Runtime agent modified: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Dataset download performed: `false`
- Production runtime promotion allowed: `false`
- Exact transcript text used: `false`
- Source transcript sequence used: `false`
- Dataset-specific phrasing used: `false`

## Review HTML

`runtime_adapter_review.html` shows classifier cases, playbook retrieval cases, agent response evaluation cases, detected tactics, failed checks, failure flags, recovery recommendations, safety boundary status, actual-agent logic status, and coverage gaps.

## Next Checkpoint

Recommended next checkpoint: `PROD-044-core-sales-policy-update`.

Purpose of PROD-044: use PROD-043 evidence to decide whether and how to update the real sales agent core behavior. PROD-044 is not implemented by this checkpoint.
