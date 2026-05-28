# LOCAL-QWEN-MIXED-REPLAY-DECODING-AUDIT-001

## Summary

- status: pass
- case_count: 141
- failed_case_count: 138
- malformed_output_count: 3
- incomplete_json_count: 3
- invalid_compact_field_count: 31
- failures_are_mostly_semantic_not_formatting: true
- local_model_calls_made: false
- training_rerun: false

## Compact Contract Failures By Field

{
  "act": 2,
  "action": 6,
  "facts": 2,
  "rel": 1,
  "strategy": 8,
  "sub": 12
}

## First Complete JSON Stop Behavior

{
  "completed_and_stopped_after_first_json_count": 138,
  "case_count": 141,
  "rate": 0.9787,
  "non_stop_case_ids": [
    "balanced_safety_and_boundary_373",
    "balanced_safety_and_boundary_380",
    "balanced_ood_control_006"
  ]
}

## Generated Tokens

{
  "full_pass": 113.667,
  "failed": 124.717
}

## Invalid Label Values

[
  {
    "field": "sub",
    "value": "skeptical",
    "count": 8,
    "allowed_values_sample": [
      "affiliation_boundary_question",
      "asr_noise_input",
      "campaign_leakage_boundary",
      "coding_research_use_case",
      "coding_voice_use_case",
      "coding_writing_use_case",
      "current_chatgpt_and_other_ai_user",
      "current_chatgpt_or_other_ai_unknown",
      "current_chatgpt_user",
      "current_competitor_tool",
      "current_other_ai_user",
      "disallowed_purchase_request",
      "enterprise_security_question",
      "hallucination_pressure_request",
      "heavy_daily_use",
      "internal_policy_request",
      "light_occasional_use",
      "midcycle_upgrade_question",
      "model_vs_subscription_question",
      "no_calendar_request"
    ]
  },
  {
    "field": "strategy",
    "value": "choose_one_plan_first",
    "count": 6,
    "allowed_values_sample": [
      "answer_without_inventing_facts",
      "boundary_without_side_effects",
      "choice_close",
      "compare_options",
      "diagnose_before_recommend",
      "explain_without_overclaiming",
      "no_fit_close",
      "preserve_buyer_words",
      "respect_boundary",
      "terminal_close",
      "value_before_plan_selection",
      "value_reframe"
    ]
  },
  {
    "field": "act",
    "value": "wrong_product_question",
    "count": 2,
    "allowed_values_sample": [
      "adoption_state",
      "affiliation_question",
      "competitor_objection",
      "current_tool_context",
      "negative_control",
      "no_fit",
      "orientation_or_explanation",
      "plan_change_question",
      "plan_fit_question",
      "price_objection",
      "price_question",
      "pro_tier_question",
      "safety_boundary",
      "signup_question",
      "source_question",
      "team_scope",
      "terminal_acceptance",
      "usage_intensity",
      "use_case_scope"
    ]
  },
  {
    "field": "action",
    "value": "recommendation_close",
    "count": 2,
    "allowed_values_sample": [
      "answer_affiliation_boundary",
      "answer_plan_category",
      "answer_plan_change",
      "answer_plan_fit",
      "answer_price",
      "answer_signup_path",
      "answer_source",
      "answer_team_controls",
      "answer_without_inventing_facts",
      "ask_individual_usage_intensity",
      "ask_usage_intensity",
      "ask_use_case_gap",
      "compare_competitor_context",
      "disqualify_no_fit",
      "recommend_plan",
      "reframe_price_objection",
      "respect_boundary",
      "terminal_close"
    ]
  },
  {
    "field": "sub",
    "value": "legal_use_case",
    "count": 2,
    "allowed_values_sample": [
      "affiliation_boundary_question",
      "asr_noise_input",
      "campaign_leakage_boundary",
      "coding_research_use_case",
      "coding_voice_use_case",
      "coding_writing_use_case",
      "current_chatgpt_and_other_ai_user",
      "current_chatgpt_or_other_ai_unknown",
      "current_chatgpt_user",
      "current_competitor_tool",
      "current_other_ai_user",
      "disallowed_purchase_request",
      "enterprise_security_question",
      "hallucination_pressure_request",
      "heavy_daily_use",
      "internal_policy_request",
      "light_occasional_use",
      "midcycle_upgrade_question",
      "model_vs_subscription_question",
      "no_calendar_request"
    ]
  },
  {
    "field": "action",
    "value": "ask_use_case_intensity",
    "count": 2,
    "allowed_values_sample": [
      "answer_affiliation_boundary",
      "answer_plan_category",
      "answer_plan_change",
      "answer_plan_fit",
      "answer_price",
      "answer_signup_path",
      "answer_source",
      "answer_team_controls",
      "answer_without_inventing_facts",
      "ask_individual_usage_intensity",
      "ask_usage_intensity",
      "ask_use_case_gap",
      "compare_competitor_context",
      "disqualify_no_fit",
      "recommend_plan",
      "reframe_price_objection",
      "respect_boundary",
      "terminal_close"
    ]
  },
  {
    "field": "sub",
    "value": "wrong_use_case",
    "count": 2,
    "allowed_values_sample": [
      "affiliation_boundary_question",
      "asr_noise_input",
      "campaign_leakage_boundary",
      "coding_research_use_case",
      "coding_voice_use_case",
      "coding_writing_use_case",
      "current_chatgpt_and_other_ai_user",
      "current_chatgpt_or_other_ai_unknown",
      "current_chatgpt_user",
      "current_competitor_tool",
      "current_other_ai_user",
      "disallowed_purchase_request",
      "enterprise_security_question",
      "hallucination_pressure_request",
      "heavy_daily_use",
      "internal_policy_request",
      "light_occasional_use",
      "midcycle_upgrade_question",
      "model_vs_subscription_question",
      "no_calendar_request"
    ]
  },
  {
    "field": "rel",
    "value": "vs",
    "count": 1,
    "allowed_values_sample": []
  }
]

## Constrained Decoding Interpretation

{
  "estimated_fixable_case_count": 16,
  "estimated_fixable_fraction_of_failed": 0.1159,
  "would_fix_large_percentage": false,
  "interpretation": "Constrained decoding would remove malformed/invalid-label cases, but the dominant failure mass is semantic and response-plan selection."
}
