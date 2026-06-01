# Outcome Metrics Mapping

## 4N3 Metrics In Thesis Terms

| Metric | Thesis use |
| --- | --- |
| micro_close_success_rate | Measures whether the agent can move qualified buyers toward a free mockup or review call. |
| qualified_followup_rate | Measures next-step creation when the buyer is not ready for an immediate close. |
| disqualification_correctness | Measures whether the agent avoids wasting effort or pressuring poor-fit buyers. |
| stop_request_compliance_rate | Measures safety and consent compliance. |
| average_sales_progression_score | Measures sales effectiveness across the rubric. |
| average_objection_handling_score | Measures response quality under buyer resistance. |
| average_spoken_naturalness_score | Supports human-likeness evaluation. |
| safety_violation_count | Counts serious boundary failures. |
| fake_claim_count | Counts fabricated identity, guarantee, side-effect, or business claims. |
| internal_language_leak_count | Counts internal prompt/test wording leaks. |
| average_turns_to_close | Measures call efficiency. |
| latency_ms | Measures real-time feasibility if runtime data is captured. |

## Aggregation Plan

Calculate metrics per agent_variant on the same case matrix. Compare the generic baseline, Atlas structured agent, and future emotion-aware variant only when each variant has comparable coverage.

## Evidence Boundary

This file maps metrics. It does not contain results. Empty templates for future values are in `11_placeholder_result_tables.md`.
