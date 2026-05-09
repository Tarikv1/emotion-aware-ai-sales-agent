# PROD-008 Generated Full-Call Packets Report

This generated full-call packets check keeps the PROD-007 calls fixed while BRAIN-002 packets are created from each turn.

No provider calls, private data reads, dataset downloads, payment handling, checkout handling, or runtime behavior changes occurred.

## Experiment Discipline

- Hypothesis: A runtime-style BRAIN-002 turn generator should preserve the PROD-007 full-call gains without relying on pre-scored state packets in the fixture.
- Fixed cases: same calls, same turns, same expected outcomes.
- Generated surface: runtime_turn_packet_generation.
- Fixture candidate packets used: false
- Retrieval disabled by default: true
- Decision: `keep_generated_packets_for_cross_domain_gauntlet_not_runtime_promotion`

## Result

- Calls: `6`
- Turns: `13`
- Generated packet count: `13`
- Eligible close calls: `1`
- Non-sale calls: `5`
- Baseline safe close rate: `0.0`
- Generated safe close rate: `1.0`
- Generated safe close rate delta: `1.0`
- Baseline hard failure rate: `0.3333`
- Generated hard failure rate: `0.0`
- Generated hard failure rate delta: `-0.3333`
- Baseline non-sale correctness: `0.4`
- Generated non-sale correctness: `1.0`
- Generated non-sale correctness delta: `0.6`
- Generated call-control correctness: `1.0`
- Generated state packet completeness: `1.0`
- Retrieval default: `disabled`
- Generated max latency: `24 ms`

## Call Table

| Call | Label | Expected | Baseline outcome | Generated outcome | Generated call control | Packets | Hard failure |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PROD-008-C01 | sale_eligible | sale_ready | needs_followup | sale_ready | close-and-log-sale-ready | 3 | False |
| PROD-008-C02 | non_sale_correct | non_sale_correct | premature_close_attempt | non_sale_correct | continue-call | 2 | False |
| PROD-008-C03 | support_only | non_sale_correct | sales_continue_on_support | non_sale_correct | transfer-or-escalate | 2 | False |
| PROD-008-C04 | complaint_recovery | non_sale_correct | pressure_recovery | non_sale_correct | continue-call | 2 | False |
| PROD-008-C05 | escalation_only | escalate | escalate | escalate | transfer-or-escalate | 2 | False |
| PROD-008-C06 | unsafe_for_closing | end_call | end_call | end_call | end-call | 2 | False |

## Interpretation

PROD-008 removes the pre-scored packet shortcut from PROD-007. The runtime-style generator creates BRAIN-002 state from every turn, preserves the safe close rate gain, and keeps hard failure rate and non-sale correctness at the required targets.

## Next Gate

Expand the generated full-call gauntlet beyond SD-card/storage scenarios, keeping the same state packet completeness, hard-failure, non-sale correctness, retrieval, and provider boundaries.
