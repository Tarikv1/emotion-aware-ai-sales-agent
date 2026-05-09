# PROD-017 CallCenterEN Specificity Scoring

## Purpose

PROD-017 adds an evaluation-only scorer for the fixed `PROD-015` old-runtime versus retrieval-runtime rows.

The goal is to separate safe-generic answers from safe-specific answers before changing retrieval composer hooks or claiming runtime improvement.

## Source Boundary

- Input: `research/experiments/generated/PROD-015-callcenteren-runtime-comparison/result.json`
- Upstream diagnosis: `PROD-016` showed composer influence gap and scoring blind spot
- Commercial runtime prompt use: `false`
- Commercial model training use: `false`
- Provider calls: `false`
- Runtime behavior changes: `false`
- Runtime retrieval default enabled: `false`

PROD-017 does not read raw CallCenterEN files. It only re-scores the generated PROD-015 comparison artifact.

## Scoring Components

- safety gate
- question relevance
- customer specificity
- requirement fit
- objection fit
- generic answer penalty

The scorer keeps hard-failure, leakage, non-sale, and safe-close boundaries outside any quality claim. It is meant to improve evaluation sensitivity, not to promote retrieval.

## Commands

Run the scorer:

```powershell
python scripts\run_prod_017_callcenteren_specificity_scoring.py
```

Validate:

```powershell
python scripts\validate_prod_017_callcenteren_specificity_scoring.py
```

Default output:

```text
research/experiments/generated/PROD-017-callcenteren-specificity-scoring/result.json
research/experiments/generated/PROD-017-callcenteren-specificity-scoring/report.md
```

## Runtime Decision

PROD-017 is not a runtime promotion. Retrieval remains disabled by default.

Current run:

- Analyzed turns: `180`
- PROD-015 ties: `180`
- PROD-017 old total score: `652`
- PROD-017 retrieval total score: `663`
- Score delta: `11`
- Retrieval wins: `3`
- Old wins: `0`
- Ties: `177`
- Changed from PROD-015 tie: `3`
- Specificity blind spot confirmed: `true`
- Influenced retrieval win rate: `1.0`
- Retrieval changed answers: `3`
- Absolute quality gap count: `177`
- Generic old-answer rate: `1.0`
- Generic retrieval-answer rate: `0.9833`
- Hard failures: `0`
- Leakage findings: `0`
- Decision: `use_specificity_scoring_before_composer_hook_test`

Interpretation: the scorer now distinguishes the three safe-specific retrieval answers that PROD-015 treated as ties. That confirms the evaluator blind spot. It does not prove broad retrieval improvement because `177/180` answers still tie and almost all answers remain generic.

Follow-up: PROD-018 used this scorer as the gate for a narrow offline composer-hook test. PROD-019 should keep this scorer as the gate for any real guarded runtime-composer candidate.
