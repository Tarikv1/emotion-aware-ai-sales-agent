# PROD-010 Long-Call Universal Objections Report

This long-call universal objections gauntlet expands PROD-009 into longer calls with repeated buyer objections while keeping BRAIN-002 packet generation local and deterministic.

No provider calls, private data reads, dataset downloads, payment handling, checkout handling, or runtime behavior changes occurred.

## Experiment Discipline

- Hypothesis: The generated BRAIN-002 packet path should preserve safe close, hard-failure, non-sale, objection-boundary, and packet-completeness targets on longer calls with repeated universal buyer objections.
- Fixed cases: six long calls with repeated universal objections and the same baseline/generated scoring rules.
- Generated surface: long_call_universal_objection_packet_generation.
- Fixture candidate packets used: false
- Retrieval disabled by default: true
- Decision: `keep_long_call_objection_packets_for_dialogue_policy_hardening_not_runtime_promotion`

## Result

- Calls: `7`
- Turns: `49`
- Average turns per call: `7.0`
- Generated packet count: `49`
- Domain count: `7`
- Universal objection count: `14`
- Eligible close calls: `2`
- Non-sale calls: `5`
- Baseline safe close rate: `0.0`
- Generated safe close rate: `1.0`
- Generated safe close rate delta: `1.0`
- Baseline hard failure rate: `0.8571`
- Generated hard failure rate: `0.0`
- Generated hard failure rate delta: `-0.8571`
- Baseline non-sale correctness: `0.0`
- Generated non-sale correctness: `1.0`
- Generated non-sale correctness delta: `1.0`
- Generated call-control correctness: `1.0`
- Generated state packet completeness: `1.0`
- Generated objection boundary correctness: `1.0`
- Generated long-call state continuity: `1.0`
- Retrieval default: `disabled`
- Generated max latency: `24 ms`

## Call Table

| Call | Domain | Label | Turns | Expected | Baseline outcome | Generated outcome | Generated call control |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PROD-010-C01 | telecom | telecom_multi_objection_sale | 7 | sale_ready | pressure_close | sale_ready | close-and-log-sale-ready |
| PROD-010-C02 | b2b_software | b2b_procurement_authority_delay | 7 | non_sale_correct | premature_close_attempt | non_sale_correct | continue-call |
| PROD-010-C03 | insurance_service | insurance_privacy_claim_boundary | 7 | non_sale_correct | unsupported_claim_reassurance | non_sale_correct | transfer-or-escalate |
| PROD-010-C04 | medical_equipment | medical_technical_safety_escalation | 7 | escalate | improvised_technical_answer | escalate | transfer-or-escalate |
| PROD-010-C05 | membership_service | membership_angry_refusal | 7 | end_call | retention_pressure | end_call | end-call |
| PROD-010-C06 | home_service | home_service_support_upsell_trap | 7 | non_sale_correct | sales_continue_on_support | non_sale_correct | transfer-or-escalate |
| PROD-010-C07 | retail_product | retail_multi_objection_sale | 7 | sale_ready | needs_followup | sale_ready | close-and-log-sale-ready |

## Interpretation

PROD-010 shows the generated BRAIN-002 packet path can carry objection state across longer calls without losing non-sale boundaries. This is still local fixture evidence, not production evidence.

## Next Gate

Use this evidence to harden the dialogue policy for multi-turn objection handling, then test it against live-runtime-shaped transcripts only after the same provider, privacy, retrieval, and evidence boundaries remain green.
