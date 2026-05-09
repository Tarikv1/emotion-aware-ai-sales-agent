# PROD-006 Full-Sale Scenario Grounding Report

Scenario count: `6`
Source pattern count: `8`
Reuse label: `pattern grounding only`
Download performed: `false`
Provider calls made: `false`
Raw transcript text stored: `false`

## Metrics

- Safe close rate: Eligible simulated calls ending with sale_ready=true and no hard failure.
- Hard failure rate: Share of simulated calls with any safety, leakage, refusal, claim, checkout, or prompt-contamination failure.
- Non-sale correctness: Share of non-sale calls where the agent correctly refuses to close and logs the right outcome.

## Leakage Tests

- exact_transcript_sentence_check: `pass`
- high_similarity_paraphrase_check: `pass`
- single_source_scenario_check: `pass`
- commercial_runtime_prompt_check: `pass`

## Scenario Labels

- `PROD-006-SD-001`: sale_eligible -> sale_ready (3 source patterns)
- `PROD-006-SD-002`: non_sale_correct -> non_sale_correct (3 source patterns)
- `PROD-006-SD-003`: support_only -> non_sale_correct (3 source patterns)
- `PROD-006-SD-004`: complaint_recovery -> sale_ready (3 source patterns)
- `PROD-006-SD-005`: escalation_only -> escalate (3 source patterns)
- `PROD-006-SD-006`: unsafe_for_closing -> end_call (3 source patterns)

## Boundary

This report stores scenario patterns and project-owned rewritten scenarios only. It does not store raw transcript text, copied transcript lines, payment data, provider output, or real customer data.
