# PROD-020 Naturalized Customer-Turn Evaluation

## Purpose

PROD-020 tests whether the `PROD-019` opt-in runtime composer-hook gain survives after rubric-like generated customer turns are rewritten into natural customer wording.

This is not a default runtime promotion. Runtime retrieval and composer hooks stay disabled by default.

## Source Boundary

- Input: `research/experiments/generated/PROD-015-callcenteren-runtime-comparison/result.json`
- Prior gate: `research/experiments/generated/PROD-019-guarded-runtime-composer-hooks/result.json`
- Scoring gate: `PROD-017` specificity and objection-fit scoring
- Editable surface changed: `evaluation_customer_turn_wording_only`
- Runtime surface changed: `none`
- Composer hook default enabled: `false`
- Runtime retrieval default enabled: `false`
- Provider calls: `false`
- Commercial runtime prompt use of CallCenterEN text: `false`
- Commercial model training use: `false`

PROD-020 does not read raw CallCenterEN files. It uses generated fixed evaluation rows, naturalizes the customer turn text, and passes only the naturalized customer turn into the real guarded composer. Scenario labels and source-pattern IDs remain reporting/scoring metadata only.

## Naturalization Gate

The runtime prompt must not contain rubric markers such as:

- `Customer raises`
- `Customer asks`
- backtick-wrapped labels
- underscore labels such as `too_expensive`
- discovery labels such as `timeline_question`

Source-pattern references are preserved in the artifact for thesis traceability, but they are not passed into the composer.

## Commands

Run the checkpoint:

```powershell
python scripts\run_prod_020_naturalized_customer_turn_evaluation.py
```

Validate:

```powershell
python scripts\validate_prod_020_naturalized_customer_turn_evaluation.py
```

Default output:

```text
research/experiments/generated/PROD-020-naturalized-customer-turn-evaluation/result.json
research/experiments/generated/PROD-020-naturalized-customer-turn-evaluation/report.md
```

## Runtime Decision

PROD-020 is an evaluation robustness gate. It can support keeping runtime composer hooks as an opt-in candidate, but it cannot promote retrieval or composer hooks to default behavior.

Current interpretation: the `PROD-019` hook gain survives after naturalizing the runtime prompts, so the hooks remain an opt-in candidate for the next live-shaped dialogue-policy test. Retrieval and composer hooks still remain disabled by default.

## Current Result

Default run output:

```text
research/experiments/generated/PROD-020-naturalized-customer-turn-evaluation/result.json
research/experiments/generated/PROD-020-naturalized-customer-turn-evaluation/report.md
```

Summary:

- Analyzed turns: `180`
- Source rubric-like turns: `120`
- Naturalized questions changed: `123`
- Naturalized rubric-token count: `0`
- Source-pattern refs preserved: `180`
- Expected outcomes preserved: `180`
- Baseline total score: `734`
- Hooked total score: `1065`
- Hooked score delta vs baseline: `331`
- Opt-in hooked answers: `107`
- Hooked without evaluation labels: `107`
- Hooked wins vs baseline: `107`
- Baseline wins vs hooked: `0`
- Ties vs baseline: `73`
- Safety gate pass count: `180`
- Payment collection findings: `0`
- Expected outcome correctness: `180/180`
- Non-sale correctness: `1.0`
- Safe-close correctness: `1.0`
- Provider calls: `false`
- LLM used: `false`
- Runtime retrieval default enabled: `false`
- Composer hook flag default enabled: `false`
- Decision: `keep_naturalized_runtime_hooks_as_opt_in_candidate_not_default`

PROD-020 proves that the opt-in hook gain is not only an artifact of obvious rubric tokens such as `too_expensive` or `timeline_question` in the runtime prompt. It still does not justify default retrieval or default hook promotion because the next gate must test live-shaped multi-turn behavior against the hardened PROD-011 dialogue policy.
