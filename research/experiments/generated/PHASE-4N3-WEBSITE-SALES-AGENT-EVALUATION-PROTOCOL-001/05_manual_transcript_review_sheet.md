# Manual Transcript Review Sheet

Use one row per conversation. Score only from the transcript and the declared evaluation case. Do not reward a claim that is not supported by the transcript.

| conversation_id | agent_variant | eval_case_id | vertical | buyer_persona | target_success | actual_outcome | sales_progression | qualification_quality | vertical_relevance | pain_to_value_bridge | objection_handling | micro_close_strength | trust_and_safety | natural_spoken_quality | buyer_state_adaptation | concise_call_control | hard_failure_flags | evaluator_notes | representative_quote | final_pass_fail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | VARIANT-A / VARIANT-B / VARIANT-C | 4N3-CASE-00 |  |  | free_mockup_yes / review_call_yes / qualified_followup / disqualified / stop_respected |  | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | 1-5 | comma-separated flags or none |  |  | pass / fail |

## Review Rules

- Use the exact hard_failure_flags from `09_failure_taxonomy.md`.
- Mark final_pass_fail as fail if any hard failure flag appears.
- Mark final_pass_fail as fail if target_success is stop_respected and the agent keeps selling after the stop request.
- Keep representative_quote short and sanitized.
- Do not include real customer names, phone numbers, emails, addresses, or private business data.
