# LOCAL-QWEN-MIXED-REPLAY-NEXT-DECISION-001

## Recommendation

- recommended_next_option: `option_4_two_head_architecture`
- more_training_recommended_immediately: false
- data_expansion_recommended: false
- label_simplification_recommended: true
- constrained_decoding_recommended: true
- two_head_architecture_recommended: true
- adapter_live_ready: false
- live_wiring_allowed: false

## Rationale

{
  "dominant_blocker": "Structured semantic and response-plan selection, not pure JSON formatting.",
  "evidence": {
    "strict_semantic_failures": 120,
    "response_plan_failures": 138,
    "wrong_action": 45,
    "wrong_strategy": 60,
    "wrong_sales_move": 9,
    "format_failure_case_count": 16,
    "semantic_failure_case_count": 138,
    "train_sample_much_better_than_heldout": true,
    "train_underfitting_response_plan": true
  }
}

## Recommended Options

[
  "option_4_two_head_architecture",
  "option_2_label_simplification",
  "option_6_smaller_task_for_lora",
  "option_3_constrained_decoding"
]

## Rejected Or Deferred Options

{
  "option_1_more_data": "Not the immediate next step: train_sample is better than held-out, but represented target cards still fail and train response-plan exactness is weak.",
  "option_5_retrieval_example_conditioning": "Useful later as an offline ablation, but it does not address structured-label brittleness by itself.",
  "option_7_different_base_model_comparison": "Premature before reducing task shape; a different base could mask the architecture issue without proving it."
}

## Option Scores

{
  "option_1_more_data": 6,
  "option_2_label_simplification": 161,
  "option_3_constrained_decoding": 16,
  "option_4_two_head_architecture": 196,
  "option_5_retrieval_example_conditioning": 10,
  "option_6_smaller_task_for_lora": 276,
  "option_7_different_base_model_comparison": 3
}
