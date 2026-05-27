# LOCAL-QWEN-CURRICULUM-EVAL-ERROR-AUDIT-001

- status: pass
- failed_case_count: 26
- acceptable_alternative_count: 7
- unacceptable_wrong_sales_move_count: 6
- local_model_calls_made: false
- provider_calls_made: false

## Class Counts

{
  "acceptable_alternative": 7,
  "compact_contract_issue": 1,
  "response_plan_mismatch": 22,
  "schema_issue": 0,
  "strict_semantic_mismatch": 25,
  "unacceptable_wrong_sales_move": 6,
  "verifier_issue": 7,
  "wrong_act": 5,
  "wrong_action": 8,
  "wrong_facts": 6,
  "wrong_preserve_avoid": 20,
  "wrong_say": 26,
  "wrong_strategy": 12,
  "wrong_sub": 10,
  "wrong_update": 5
}

## Wrong Labels

{
  "top_wrong_labels_predicted": [
    {
      "field": "strategy",
      "predicted": "boundary_without_side_effects",
      "count": 5
    },
    {
      "field": "action",
      "predicted": "respect_boundary",
      "count": 5
    },
    {
      "field": "strategy",
      "predicted": "diagnose_before_recommend",
      "count": 4
    },
    {
      "field": "strategy",
      "predicted": "value_before_plan_selection",
      "count": 3
    },
    {
      "field": "act",
      "predicted": "safety_boundary",
      "count": 3
    },
    {
      "field": "sub",
      "predicted": "model_vs_subscription_question",
      "count": 2
    },
    {
      "field": "sub",
      "predicted": "current_chatgpt_and_other_ai_user",
      "count": 1
    },
    {
      "field": "sub",
      "predicted": "coding_writing_use_case",
      "count": 1
    },
    {
      "field": "act",
      "predicted": "current_tool_context",
      "count": 1
    },
    {
      "field": "sub",
      "predicted": "tts_boundary_request",
      "count": 1
    },
    {
      "field": "action",
      "predicted": "ask_usage_intensity",
      "count": 1
    },
    {
      "field": "act",
      "predicted": "signup_question",
      "count": 1
    },
    {
      "field": "sub",
      "predicted": "signup_path_question",
      "count": 1
    },
    {
      "field": "action",
      "predicted": "terminal_close",
      "count": 1
    },
    {
      "field": "sub",
      "predicted": "silence_or_unclear_audio",
      "count": 1
    },
    {
      "field": "sub",
      "predicted": "no_crm_request",
      "count": 1
    },
    {
      "field": "sub",
      "predicted": "current_other_ai_user",
      "count": 1
    },
    {
      "field": "action",
      "predicted": "ask_use_case_gap",
      "count": 1
    },
    {
      "field": "sub",
      "predicted": "no_storage_restriction",
      "count": 1
    }
  ],
  "top_expected_labels_missed": [
    {
      "field": "strategy",
      "expected": "preserve_buyer_words",
      "count": 4
    },
    {
      "field": "strategy",
      "expected": "explain_without_overclaiming",
      "count": 2
    },
    {
      "field": "action",
      "expected": "reframe_price_objection",
      "count": 2
    },
    {
      "field": "strategy",
      "expected": "value_reframe",
      "count": 2
    },
    {
      "field": "sub",
      "expected": "current_chatgpt_or_other_ai_unknown",
      "count": 1
    },
    {
      "field": "sub",
      "expected": "coding_voice_use_case",
      "count": 1
    },
    {
      "field": "strategy",
      "expected": "respect_boundary",
      "count": 1
    },
    {
      "field": "act",
      "expected": "adoption_state",
      "count": 1
    },
    {
      "field": "act",
      "expected": "price_question",
      "count": 1
    },
    {
      "field": "sub",
      "expected": "plus_price_question",
      "count": 1
    },
    {
      "field": "action",
      "expected": "answer_price",
      "count": 1
    },
    {
      "field": "strategy",
      "expected": "answer_without_inventing_facts",
      "count": 1
    },
    {
      "field": "action",
      "expected": "ask_use_case_gap",
      "count": 1
    },
    {
      "field": "act",
      "expected": "safety_boundary",
      "count": 1
    },
    {
      "field": "sub",
      "expected": "side_effect_boundary_request",
      "count": 1
    },
    {
      "field": "action",
      "expected": "respect_boundary",
      "count": 1
    },
    {
      "field": "strategy",
      "expected": "boundary_without_side_effects",
      "count": 1
    },
    {
      "field": "sub",
      "expected": "asr_noise_input",
      "count": 1
    },
    {
      "field": "act",
      "expected": "terminal_acceptance",
      "count": 1
    },
    {
      "field": "sub",
      "expected": "terminal_thanks_acceptance",
      "count": 1
    }
  ]
}

## Confusion Matrix

{
  "action": [
    {
      "expected": "reframe_price_objection",
      "predicted": "respect_boundary",
      "count": 2
    },
    {
      "expected": "answer_price",
      "predicted": "respect_boundary",
      "count": 1
    },
    {
      "expected": "ask_use_case_gap",
      "predicted": "ask_usage_intensity",
      "count": 1
    },
    {
      "expected": "respect_boundary",
      "predicted": "terminal_close",
      "count": 1
    },
    {
      "expected": "terminal_close",
      "predicted": "respect_boundary",
      "count": 1
    },
    {
      "expected": "answer_plan_category",
      "predicted": "respect_boundary",
      "count": 1
    },
    {
      "expected": "ask_usage_intensity",
      "predicted": "ask_use_case_gap",
      "count": 1
    }
  ],
  "sub": [
    {
      "expected": "current_chatgpt_or_other_ai_unknown",
      "predicted": "current_chatgpt_and_other_ai_user",
      "count": 1
    },
    {
      "expected": "coding_voice_use_case",
      "predicted": "coding_writing_use_case",
      "count": 1
    },
    {
      "expected": "plus_price_question",
      "predicted": "tts_boundary_request",
      "count": 1
    },
    {
      "expected": "side_effect_boundary_request",
      "predicted": "signup_path_question",
      "count": 1
    },
    {
      "expected": "asr_noise_input",
      "predicted": "silence_or_unclear_audio",
      "count": 1
    },
    {
      "expected": "terminal_thanks_acceptance",
      "predicted": "no_crm_request",
      "count": 1
    },
    {
      "expected": "plan_category_explanation",
      "predicted": "model_vs_subscription_question",
      "count": 1
    },
    {
      "expected": "coding_research_use_case",
      "predicted": "current_other_ai_user",
      "count": 1
    },
    {
      "expected": "unsupported_fact_request",
      "predicted": "model_vs_subscription_question",
      "count": 1
    },
    {
      "expected": "privacy_question",
      "predicted": "no_storage_restriction",
      "count": 1
    }
  ]
}
