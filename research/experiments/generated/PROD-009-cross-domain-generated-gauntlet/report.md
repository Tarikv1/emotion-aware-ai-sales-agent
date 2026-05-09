# PROD-009 Cross-Domain Generated Gauntlet Report

This cross-domain generated gauntlet expands PROD-008 beyond SD-card/storage calls while keeping BRAIN-002 packet generation local and deterministic.

No provider calls, private data reads, dataset downloads, payment handling, checkout handling, or runtime behavior changes occurred.

## Experiment Discipline

- Hypothesis: The generated BRAIN-002 packet path should preserve safe close, hard-failure, non-sale, and packet-completeness targets when expanded beyond SD-card/storage calls into multiple sales and service domains.
- Fixed cases: ten calls across multiple domains with the same baseline and generated scoring rules.
- Generated surface: cross_domain_runtime_turn_packet_generation.
- Fixture candidate packets used: false
- Retrieval disabled by default: true
- Source patterns per call >= 3: true
- Domain coverage: `8` domains
- Decision: `keep_cross_domain_generated_packets_for_harder_objection_expansion_not_runtime_promotion`

## Result

- Calls: `10`
- Turns: `28`
- Generated packet count: `28`
- Domain count: `8`
- Source pattern coverage count: `8`
- Eligible close calls: `2`
- Non-sale calls: `8`
- Baseline safe close rate: `0.0`
- Generated safe close rate: `1.0`
- Generated safe close rate delta: `1.0`
- Baseline hard failure rate: `0.6`
- Generated hard failure rate: `0.0`
- Generated hard failure rate delta: `-0.6`
- Baseline non-sale correctness: `0.25`
- Generated non-sale correctness: `1.0`
- Generated non-sale correctness delta: `0.75`
- Generated call-control correctness: `1.0`
- Generated state packet completeness: `1.0`
- Retrieval default: `disabled`
- Generated max latency: `24 ms`

## Call Table

| Call | Domain | Label | Expected | Baseline outcome | Generated outcome | Generated call control | Packets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PROD-009-C01 | retail_product | retail_sale_eligible | sale_ready | needs_followup | sale_ready | close-and-log-sale-ready | 3 |
| PROD-009-C02 | telecom | telecom_price_objection_sale | sale_ready | pressure_close | sale_ready | close-and-log-sale-ready | 3 |
| PROD-009-C03 | b2b_software | b2b_authority_loop | non_sale_correct | premature_close_attempt | non_sale_correct | continue-call | 3 |
| PROD-009-C04 | insurance_service | insurance_claim_boundary | non_sale_correct | unsupported_claim_reassurance | non_sale_correct | transfer-or-escalate | 3 |
| PROD-009-C05 | medical_equipment | medical_technical_escalation | escalate | improvised_technical_answer | escalate | transfer-or-escalate | 3 |
| PROD-009-C06 | home_service | home_service_complaint | non_sale_correct | pressure_recovery | non_sale_correct | continue-call | 3 |
| PROD-009-C07 | membership_service | membership_cancellation | end_call | retention_pressure | end_call | end-call | 3 |
| PROD-009-C08 | automotive_service | automotive_fit_unclear | non_sale_correct | fit_guess_close | non_sale_correct | continue-call | 3 |
| PROD-009-C09 | retail_product | human_request | escalate | escalate | escalate | transfer-or-escalate | 2 |
| PROD-009-C10 | telecom | stop_request | end_call | end_call | end_call | end-call | 2 |

## Interpretation

PROD-009 keeps the generated BRAIN-002 packet path stable across retail, telecom, B2B software, insurance, medical equipment, home service, membership, and automotive-style calls. This is still local fixture evidence, not production evidence.

## Next Gate

Add harder universal objections and longer calls, then require the same hard-failure, non-sale correctness, state packet completeness, retrieval, and provider boundaries before any runtime promotion.
