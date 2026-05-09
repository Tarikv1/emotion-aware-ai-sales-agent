# PROD-019 Guarded Runtime Composer Hooks

## Purpose

PROD-019 moves the successful `PROD-018` offline composer-hook idea into the actual guarded response composer as an explicit opt-in runtime candidate.

This is not a default runtime promotion. The default guarded response path must stay unchanged unless `--composer-hooks-enabled` is passed together with guarded retrieval.

## Source Boundary

- Input: `research/experiments/generated/PROD-015-callcenteren-runtime-comparison/result.json`
- Offline evidence source: `research/experiments/generated/PROD-018-callcenteren-composer-hook-test/result.json`
- Scoring gate: `PROD-017` specificity and objection-fit scoring
- Runtime surface changed: `generate_guarded_response` local deterministic composer
- Editable surface changed: `guarded_runtime_composer_hook_flag_only`
- Composer hook default enabled: `false`
- Runtime retrieval default enabled: `false`
- Provider calls: `false`
- Commercial runtime prompt use of CallCenterEN text: `false`
- Commercial model training use: `false`

PROD-019 does not read raw CallCenterEN files. It uses generated fixed evaluation rows and passes only the customer turn text into the real runtime composer. Scenario labels are used for reporting and scoring only, not as composer input.

## Opt-In Runtime Flag

Generate the same guarded response path with retrieval and candidate composer hooks:

```powershell
python scripts\generate_guarded_response.py `
  --campaign campaign-prod-005-b2b-software `
  --stage relevance-check `
  --transcript "Customer raises too_expensive and needs a timeline_question before any close." `
  --retrieval-enabled `
  --retrieval-registry research\experiments\generated\RAG-017-runtime-knowledge-registry\result.json `
  --retrieval-max-results 4 `
  --retrieval-min-score 1 `
  --composer-hooks-enabled
```

If retrieval is not enabled, the composer hook flag records `retrieval_not_enabled` and does not alter the response.

## Commands

Run the checkpoint:

```powershell
python scripts\run_prod_019_guarded_runtime_composer_hooks.py
```

Validate:

```powershell
python scripts\validate_prod_019_guarded_runtime_composer_hooks.py
```

Default output:

```text
research/experiments/generated/PROD-019-guarded-runtime-composer-hooks/result.json
research/experiments/generated/PROD-019-guarded-runtime-composer-hooks/report.md
```

## Runtime Decision

PROD-019 is an opt-in runtime-composer candidate gate. Retrieval and composer hooks remain disabled by default.

Current interpretation: the actual runtime hook path improves signal-detectable generic answers while preserving default-off behavior, safety, non-sale correctness, safe-close correctness, and leakage boundaries. The next step is a broader naturalized prompt or live-shaped simulation check, not default retrieval promotion.

## Current Result

Default run output:

```text
research/experiments/generated/PROD-019-guarded-runtime-composer-hooks/result.json
research/experiments/generated/PROD-019-guarded-runtime-composer-hooks/report.md
```

Summary:

- Analyzed turns: `180`
- Default-off answer drift count: `0`
- Opt-in hooked answers: `98`
- Hooked without evaluation labels: `98`
- Preserved existing influenced answers: `3`
- Current retrieval score: `663`
- Default-off score: `663`
- Hooked score: `916`
- Hooked score delta vs current: `253`
- Hooked wins vs current: `92`
- Current wins against hooked: `0`
- Ties vs current: `88`
- Safety gate pass count: `180`
- Payment collection findings: `0`
- Non-sale correctness: `1.0`
- Safe-close correctness: `1.0`
- Provider calls: `false`
- LLM used: `false`
- Runtime retrieval default enabled: `false`
- Composer hook flag default enabled: `false`
- Decision: `keep_runtime_composer_hooks_opt_in_candidate_not_default`

PROD-019 proves the hooks can run through the real guarded composer behind an explicit flag. It does not prove default retrieval readiness because the evaluated customer turns still include rubric-like generated phrasing.
