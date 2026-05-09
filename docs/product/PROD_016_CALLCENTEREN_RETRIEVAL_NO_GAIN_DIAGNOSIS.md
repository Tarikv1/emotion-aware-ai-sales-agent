# PROD-016 CallCenterEN Retrieval No-Gain Diagnosis

## Purpose

PROD-016 diagnoses why `PROD-015` did not show a retrieval gain on the larger CallCenterEN-derived scenario slice.

This checkpoint is evidence-only. It reads the existing `PROD-015` result, analyzes retrieval status, answer changes, scoring ties, runtime classifier signals, and campaign/domain routing, then writes a diagnosis report. It does not change runtime behavior.

## Source Boundary

- Input: `research/experiments/generated/PROD-015-callcenteren-runtime-comparison/result.json`
- Upstream scenario source: `PROD-014` generated project-owned scenario prompts
- Upstream dataset reference: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english
- Commercial runtime prompt use: `false`
- Commercial model training use: `false`
- Provider calls: `false`
- Runtime retrieval default enabled: `false`

PROD-016 does not read raw CallCenterEN files. It only reads the generated PROD-015 comparison artifact.

## Metrics

- no-gain confirmed
- answer changed count
- unchanged answer count
- influenced-but-tied count
- retrieved-not-used rate
- matching success rate
- no-match rate
- unknown-runtime-signal rate
- rubric-like turn rate
- dominant old-answer share
- status by scenario label

## Diagnosis Classes

- composer influence gap
- scoring blind spot
- runtime classifier mismatch
- campaign domain mismatch
- retrieval matching gap, only if no-match rate becomes high

## Commands

Run the diagnosis:

```powershell
python scripts\run_prod_016_callcenteren_retrieval_no_gain_diagnosis.py
```

Validate:

```powershell
python scripts\validate_prod_016_callcenteren_retrieval_no_gain_diagnosis.py
```

Default output:

```text
research/experiments/generated/PROD-016-callcenteren-retrieval-no-gain-diagnosis/result.json
research/experiments/generated/PROD-016-callcenteren-retrieval-no-gain-diagnosis/report.md
```

## Runtime Decision

PROD-016 is not a runtime promotion. Retrieval remains disabled by default.

Current run:

- Analyzed turns: `180`
- Old runtime score: `810`
- Retrieval runtime score: `810`
- Score delta: `0`
- Retrieval wins: `0`
- Old wins: `0`
- Ties: `180`
- Retrieval statuses: `174` retrieved-not-used, `3` influenced, `3` blocked
- Answer changed count: `3`
- Unchanged answer count: `177`
- Influenced-but-tied count: `3`
- Retrieved-not-used rate: `0.9667`
- Matching success rate: `1.0`
- No-match rate: `0.0`
- Unknown-runtime-signal rate: `1.0`
- Rubric-like turn rate: `0.6667`
- Dominant old-answer share: `0.85`
- Hard failures: `0`
- Leakage findings: `0`
- Decision: `diagnose_before_retrieval_runtime_promotion`

Interpretation: retrieval matching is not the main bottleneck. The current runtime matched RAG items on nearly every non-blocked turn, but the deterministic composer rarely used the hints. The current scorer also lets a generic old answer tie a more targeted retrieval answer as long as both stay safe and ask a question.

Next step: add specificity and objection-fit scoring against the same fixed PROD-015 rows before changing composer hooks or running the full bank.
