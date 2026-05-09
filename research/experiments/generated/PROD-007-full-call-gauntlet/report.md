# PROD-007 Full-Call Gauntlet Report

This full-call gauntlet compares the old core against the BRAIN-002/full-sale candidate on the same fixed PROD-006-style calls.

No provider calls, private data reads, dataset downloads, payment handling, checkout handling, or runtime behavior changes occurred.

## Experiment Discipline

- Hypothesis: The BRAIN-002/full-sale candidate should improve sale-ready decisions and non-sale correctness over the old core on the same fixed calls without increasing hard failures.
- Fixed cases: same calls, same turns, same expected outcomes for baseline and candidate.
- Baseline: old core pre full-sale state contract.
- Change: BRAIN-002 runtime state decision packet.
- Decision: `keep_brain_002_candidate_for_next_gauntlet_expansion_not_runtime_promotion`

## Result

- Calls: `6`
- Turns: `13`
- Eligible close calls: `1`
- Non-sale calls: `5`
- Baseline safe close rate: `0.0`
- Candidate safe close rate: `1.0`
- Candidate safe close rate delta: `1.0`
- Baseline hard failure rate: `0.3333`
- Candidate hard failure rate: `0.0`
- Candidate hard failure rate delta: `-0.3333`
- Baseline non-sale correctness: `0.4`
- Candidate non-sale correctness: `1.0`
- Candidate non-sale correctness delta: `0.6`
- Candidate call-control correctness: `1.0`
- Retrieval default: `disabled`
- Retrieval disabled by default: `true`
- Candidate max latency: `22 ms`

## Call Table

| Call | Label | Expected | Baseline outcome | Candidate outcome | Candidate call control | Hard failure |
| --- | --- | --- | --- | --- | --- | --- |
| PROD-007-C01 | sale_eligible | sale_ready | needs_followup | sale_ready | close-and-log-sale-ready | False |
| PROD-007-C02 | non_sale_correct | non_sale_correct | premature_close_attempt | non_sale_correct | continue-call | False |
| PROD-007-C03 | support_only | non_sale_correct | sales_continue_on_support | non_sale_correct | transfer-or-escalate | False |
| PROD-007-C04 | complaint_recovery | non_sale_correct | pressure_recovery | non_sale_correct | continue-call | False |
| PROD-007-C05 | escalation_only | escalate | escalate | escalate | transfer-or-escalate | False |
| PROD-007-C06 | unsafe_for_closing | end_call | end_call | end_call | end-call | False |

## Interpretation

The BRAIN-002/full-sale candidate wins this fixed gauntlet because it can log a safe sale-ready close while also preserving non-sale correctness. This does not promote the candidate to live runtime. It only justifies expanding the gauntlet and then connecting the state packet to actual response generation.

## Next Gate

Expand from fixture-scored calls to generated full-call packets where the runtime produces the BRAIN-002 state packet from each turn, then rerun the same metrics before any client-facing claim.
