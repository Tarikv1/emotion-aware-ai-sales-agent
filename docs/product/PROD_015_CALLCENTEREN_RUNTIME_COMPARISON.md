# PROD-015 CallCenterEN Runtime Comparison

## Purpose

PROD-015 compares the old retrieval-disabled runtime against the retrieval-enabled runtime on the same `PROD-014` generated CallCenterEN scenario prompts.

It records the exact customer question, exact old runtime answer, exact retrieval runtime answer, and decision trace for each evaluated turn.

## Source Boundary

- Input: `research/experiments/generated/PROD-014-callcenteren-scenario-bank/scenario-bank.json`
- Dataset reference: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english
- Paper: https://arxiv.org/abs/2507.02958
- License observed: `cc-by-nc-4.0`
- Reuse label: `abstract_scenario_bank_only`
- Commercial runtime prompt use: `false`
- Commercial model training use: `false`

PROD-015 uses generated project-owned scenario prompts, not copied transcript text. Raw CallCenterEN ZIPs may be scanned transiently for leakage checks when available, but source text is not written to tracked artifacts.

## Metrics

- hard failure rate
- non-sale correctness
- safe close correctness
- discovery-before-close rate
- emotional handling score
- leakage failure rate
- retrieval win rate

Hard failures include validation failure, payment collection, unsafe sale close on non-sale outcomes, leakage, protected/runtime boundary failures, or commercial prompt contamination.

## Commands

Run the default stratified slice:

```powershell
python scripts\run_prod_015_callcenteren_runtime_comparison.py
```

Run the full `PROD-014` bank:

```powershell
python scripts\run_prod_015_callcenteren_runtime_comparison.py --limit-scenarios 0
```

Validate:

```powershell
python scripts\validate_prod_015_callcenteren_runtime_comparison.py
```

Default output:

```text
research/experiments/generated/PROD-015-callcenteren-runtime-comparison/result.json
research/experiments/generated/PROD-015-callcenteren-runtime-comparison/report.md
```

## Runtime Decision

PROD-015 is not a runtime promotion. Retrieval remains disabled by default.

Current default run:

- Source bank scenarios: `240`
- Evaluated stratified slice: `60` scenarios / `180` customer turns
- Covered labels: `callback_request`, `cancellation_boundary`, `price_objection`, `sale_eligible`, `support_handoff`, `trust_repair`
- Covered domains: `8`
- Hard failures: `0`
- Non-sale correctness: `120/120`
- Safe-close correctness: `60/60`
- Discovery-before-close turns: `180/180`
- Emotional handling turns: `180/180`
- Leakage findings: `0`
- Old runtime score: `810`
- Retrieval runtime score: `810`
- Retrieval wins: `0`
- Old runtime wins: `0`
- Ties: `180`
- Retrieval-influenced responses: `3`
- Retrieval blocked responses: `3`
- Retrieved-but-not-used responses: `174`
- Max retrieval latency: `5 ms`
- Average retrieval latency: `2.11 ms`
- Decision: `ready_for_review_no_retrieval_gain_on_slice`

Interpretation: the retrieval-enabled runtime stayed safe on this slice, but it did not outperform the old retrieval-disabled runtime. The next work should diagnose why retrieval was usually retrieved-but-not-used and whether the query/composition/scoring path should be strengthened before any full-bank or runtime-promotion claim.
