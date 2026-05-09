# PROD-018 CallCenterEN Composer Hook Test

## Purpose

PROD-018 tests whether narrow offline composer hooks can turn `PROD-015` retrieved-but-not-used hints into more specific answers.

This is not a runtime promotion. It applies proposed hook answers to unchanged `PROD-015` rows, scores old/current/hooked answers with the `PROD-017` specificity scorer, and reports whether the hooks are worth turning into real guarded-response composer tests later.

## Source Boundary

- Input: `research/experiments/generated/PROD-015-callcenteren-runtime-comparison/result.json`
- Scoring gate: `PROD-017` specificity and objection-fit scoring
- Runtime code changed: `false`
- Runtime retrieval default enabled: `false`
- Provider calls: `false`
- Commercial runtime prompt use: `false`
- Commercial model training use: `false`

PROD-018 does not read raw CallCenterEN files. It only reads the generated PROD-015 comparison artifact.

## Hook Set

- price objection clarifier
- support handoff router
- cancellation boundary stop
- callback request low commitment
- trust repair verification
- sale eligible fit check

## Commands

Run the offline hook test:

```powershell
python scripts\run_prod_018_callcenteren_composer_hook_test.py
```

Validate:

```powershell
python scripts\validate_prod_018_callcenteren_composer_hook_test.py
```

Default output:

```text
research/experiments/generated/PROD-018-callcenteren-composer-hook-test/result.json
research/experiments/generated/PROD-018-callcenteren-composer-hook-test/report.md
```

## Runtime Decision

PROD-018 is not a runtime promotion. Retrieval remains disabled by default.

Current interpretation: the offline hooks passed the PROD-017 scoring gate without safety regressions, so the next step is a red-first runtime-composer candidate test, not a default retrieval change.

## Current Result

Default run output:

```text
research/experiments/generated/PROD-018-callcenteren-composer-hook-test/result.json
research/experiments/generated/PROD-018-callcenteren-composer-hook-test/report.md
```

Summary:

- Analyzed turns: `180`
- Eligible hook turns: `174`
- Hooked answers: `174`
- Preserved existing influenced answers: `3`
- Old runtime score: `652`
- Current retrieval score: `663`
- Hooked score: `1421`
- Hooked wins vs current retrieval: `174`
- Hooked wins vs old runtime: `177`
- Old runtime wins vs hooked: `0`
- Safety gate pass count: `180`
- Payment collection findings: `0`
- Non-sale correctness: `1.0`
- Safe-close correctness: `1.0`
- Provider calls: `false`
- Runtime behavior changed: `false`
- Runtime retrieval default enabled: `false`
- Decision: `keep_composer_hooks_for_runtime_candidate_not_default`

PROD-018 proves a composition opportunity on fixed offline rows. It does not prove that the live guarded runtime composer can safely reproduce the same behavior yet.
