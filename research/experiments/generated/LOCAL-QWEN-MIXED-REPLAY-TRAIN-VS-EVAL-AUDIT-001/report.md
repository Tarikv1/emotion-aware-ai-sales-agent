# LOCAL-QWEN-MIXED-REPLAY-TRAIN-VS-EVAL-AUDIT-001

## Summary

- status: pass
- train_sample_much_better_than_heldout: true
- local_model_calls_made: false
- training_rerun: false
- adapter_live_ready: false
- live_wiring_allowed: false

## Train Sample Vs Held-Out

{
  "train_sample_strict_semantic_rate": 0.625,
  "validation_strict_semantic_rate": 0.2,
  "test_strict_semantic_rate": 0.1212,
  "validation_test_strict_semantic_rate": 0.1603,
  "train_sample_much_better_than_heldout": true,
  "caveat": "train_sample is the first 40 mixed-train rows, not a full train-set evaluation."
}

## Classification

{
  "overfitting": true,
  "underfitting": true,
  "label_sparsity": true,
  "label_confusion": true,
  "output_format_instability": true,
  "sales_action_decision_failure": false,
  "safety_verifier_conflict": true,
  "acceptable_gold_strictness_issue": true
}

## Semantic Groups Passing Train But Failing Held-Out

[
  {
    "semantic_group": "plan_fit_and_recommendation",
    "train_sample_semantic_pass_rate": 0.75,
    "heldout_semantic_pass_rate": 0.0667,
    "heldout_case_count": 30
  },
  {
    "semantic_group": "plan_change_and_signup",
    "train_sample_semantic_pass_rate": 1.0,
    "heldout_semantic_pass_rate": 0.0667,
    "heldout_case_count": 30
  }
]

## Target Cards Underrepresented In Train

[
  {
    "target_card_id": "plan_change_signup_path",
    "train_count": 3
  },
  {
    "target_card_id": "plan_change_upgrade_later",
    "train_count": 4
  }
]

## Target Cards Represented But Still Fail

[
  {
    "target_card_id": "safety_wrong_product",
    "train_count": 7,
    "heldout_case_count": 19,
    "heldout_semantic_failure_count": 19,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "plan_change_signup_path",
    "train_count": 3,
    "heldout_case_count": 14,
    "heldout_semantic_failure_count": 14,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "plan_change_upgrade_later",
    "train_count": 4,
    "heldout_case_count": 14,
    "heldout_semantic_failure_count": 14,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "objection_competitor_current_tool",
    "train_count": 13,
    "heldout_case_count": 8,
    "heldout_semantic_failure_count": 8,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "plan_fit_no_fit_free_enough",
    "train_count": 9,
    "heldout_case_count": 8,
    "heldout_semantic_failure_count": 8,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "objection_not_interested",
    "train_count": 11,
    "heldout_case_count": 8,
    "heldout_semantic_failure_count": 7,
    "heldout_semantic_failure_rate": 0.875
  },
  {
    "target_card_id": "plan_fit_pro_choice",
    "train_count": 13,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 7,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "plan_fit_recommend_after_context",
    "train_count": 13,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 7,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "safety_raw_url_or_transcript",
    "train_count": 14,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 7,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "safety_unsupported_policy_privacy",
    "train_count": 14,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 7,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "plan_fit_plus_enough",
    "train_count": 13,
    "heldout_case_count": 8,
    "heldout_semantic_failure_count": 6,
    "heldout_semantic_failure_rate": 0.75
  },
  {
    "target_card_id": "safety_no_crm_email_calendar",
    "train_count": 19,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 5,
    "heldout_semantic_failure_rate": 0.7143
  },
  {
    "target_card_id": "objection_price_with_current_tool",
    "train_count": 13,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 4,
    "heldout_semantic_failure_rate": 0.5714
  },
  {
    "target_card_id": "price_pro_direct",
    "train_count": 13,
    "heldout_case_count": 6,
    "heldout_semantic_failure_count": 4,
    "heldout_semantic_failure_rate": 0.6667
  },
  {
    "target_card_id": "objection_chatgpt_vs_current_tool",
    "train_count": 13,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 3,
    "heldout_semantic_failure_rate": 0.4286
  }
]

## Source Type Correlation

[
  {
    "source_type": "deterministic_paraphrase",
    "case_count": 95,
    "semantic_pass_count": 17,
    "semantic_pass_rate": 0.1789,
    "full_pass_count": 3,
    "full_pass_rate": 0.0316
  },
  {
    "source_type": "synthetic_control",
    "case_count": 20,
    "semantic_pass_count": 2,
    "semantic_pass_rate": 0.1,
    "full_pass_count": 0,
    "full_pass_rate": 0.0
  },
  {
    "source_type": "negative_control",
    "case_count": 15,
    "semantic_pass_count": 1,
    "semantic_pass_rate": 0.0667,
    "full_pass_count": 0,
    "full_pass_rate": 0.0
  },
  {
    "source_type": "ood_control",
    "case_count": 10,
    "semantic_pass_count": 0,
    "semantic_pass_rate": 0.0,
    "full_pass_count": 0,
    "full_pass_rate": 0.0
  },
  {
    "source_type": "original_gold",
    "case_count": 1,
    "semantic_pass_count": 1,
    "semantic_pass_rate": 1.0,
    "full_pass_count": 0,
    "full_pass_rate": 0.0
  }
]

## Length Correlations

{
  "buyer_text_length": {
    "median": 47,
    "low_or_equal": {
      "case_count": 74,
      "average_length": 38.84,
      "semantic_pass_rate": 0.1351
    },
    "high": {
      "case_count": 67,
      "average_length": 60.46,
      "semantic_pass_rate": 0.1642
    }
  },
  "target_json_length": {
    "median": 598,
    "low_or_equal": {
      "case_count": 71,
      "average_length": 554.63,
      "semantic_pass_rate": 0.0986
    },
    "high": {
      "case_count": 70,
      "average_length": 620.97,
      "semantic_pass_rate": 0.2
    }
  }
}

## Say Diversity Correlation

[
  {
    "target_card_id": "safety_wrong_product",
    "train_count": 7,
    "unique_train_say_count": 2,
    "heldout_case_count": 19,
    "heldout_semantic_failure_count": 19,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "plan_change_upgrade_later",
    "train_count": 4,
    "unique_train_say_count": 1,
    "heldout_case_count": 14,
    "heldout_semantic_failure_count": 14,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "plan_change_signup_path",
    "train_count": 3,
    "unique_train_say_count": 1,
    "heldout_case_count": 14,
    "heldout_semantic_failure_count": 14,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "plan_fit_plus_enough",
    "train_count": 13,
    "unique_train_say_count": 2,
    "heldout_case_count": 8,
    "heldout_semantic_failure_count": 6,
    "heldout_semantic_failure_rate": 0.75
  },
  {
    "target_card_id": "plan_fit_no_fit_free_enough",
    "train_count": 9,
    "unique_train_say_count": 2,
    "heldout_case_count": 8,
    "heldout_semantic_failure_count": 8,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "objection_not_interested",
    "train_count": 11,
    "unique_train_say_count": 1,
    "heldout_case_count": 8,
    "heldout_semantic_failure_count": 7,
    "heldout_semantic_failure_rate": 0.875
  },
  {
    "target_card_id": "objection_competitor_current_tool",
    "train_count": 13,
    "unique_train_say_count": 2,
    "heldout_case_count": 8,
    "heldout_semantic_failure_count": 8,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "plan_fit_recommend_after_context",
    "train_count": 13,
    "unique_train_say_count": 1,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 7,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "plan_fit_pro_choice",
    "train_count": 13,
    "unique_train_say_count": 2,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 7,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "safety_raw_url_or_transcript",
    "train_count": 14,
    "unique_train_say_count": 2,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 7,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "safety_unsupported_policy_privacy",
    "train_count": 14,
    "unique_train_say_count": 3,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 7,
    "heldout_semantic_failure_rate": 1.0
  },
  {
    "target_card_id": "safety_no_crm_email_calendar",
    "train_count": 19,
    "unique_train_say_count": 3,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 5,
    "heldout_semantic_failure_rate": 0.7143
  },
  {
    "target_card_id": "objection_chatgpt_vs_current_tool",
    "train_count": 13,
    "unique_train_say_count": 2,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 3,
    "heldout_semantic_failure_rate": 0.4286
  },
  {
    "target_card_id": "objection_price_with_current_tool",
    "train_count": 13,
    "unique_train_say_count": 2,
    "heldout_case_count": 7,
    "heldout_semantic_failure_count": 4,
    "heldout_semantic_failure_rate": 0.5714
  },
  {
    "target_card_id": "price_pro_direct",
    "train_count": 13,
    "unique_train_say_count": 2,
    "heldout_case_count": 6,
    "heldout_semantic_failure_count": 4,
    "heldout_semantic_failure_rate": 0.6667
  },
  {
    "target_card_id": "price_plus_direct",
    "train_count": 16,
    "unique_train_say_count": 2,
    "heldout_case_count": 5,
    "heldout_semantic_failure_count": 0,
    "heldout_semantic_failure_rate": 0.0
  },
  {
    "target_card_id": "plan_change_terminal_close",
    "train_count": 45,
    "unique_train_say_count": 1,
    "heldout_case_count": 2,
    "heldout_semantic_failure_count": 0,
    "heldout_semantic_failure_rate": 0.0
  }
]

## Rare Label Failure Correlation

{
  "act": [
    {
      "label": "signup_question",
      "train_count": 3,
      "heldout_case_count": 14,
      "heldout_semantic_failure_count": 14,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "plan_change_question",
      "train_count": 4,
      "heldout_case_count": 14,
      "heldout_semantic_failure_count": 14,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "pro_tier_question",
      "train_count": 13,
      "heldout_case_count": 7,
      "heldout_semantic_failure_count": 7,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "competitor_objection",
      "train_count": 26,
      "heldout_case_count": 15,
      "heldout_semantic_failure_count": 11,
      "heldout_semantic_failure_rate": 0.7333
    },
    {
      "label": "plan_fit_question",
      "train_count": 26,
      "heldout_case_count": 15,
      "heldout_semantic_failure_count": 13,
      "heldout_semantic_failure_rate": 0.8667
    },
    {
      "label": "no_fit",
      "train_count": 27,
      "heldout_case_count": 35,
      "heldout_semantic_failure_count": 34,
      "heldout_semantic_failure_rate": 0.9714
    },
    {
      "label": "price_question",
      "train_count": 29,
      "heldout_case_count": 11,
      "heldout_semantic_failure_count": 4,
      "heldout_semantic_failure_rate": 0.3636
    },
    {
      "label": "price_objection",
      "train_count": 32,
      "heldout_case_count": 7,
      "heldout_semantic_failure_count": 4,
      "heldout_semantic_failure_rate": 0.5714
    },
    {
      "label": "terminal_acceptance",
      "train_count": 45,
      "heldout_case_count": 2,
      "heldout_semantic_failure_count": 0,
      "heldout_semantic_failure_rate": 0.0
    },
    {
      "label": "safety_boundary",
      "train_count": 47,
      "heldout_case_count": 21,
      "heldout_semantic_failure_count": 19,
      "heldout_semantic_failure_rate": 0.9048
    }
  ],
  "sub": [
    {
      "label": "side_effect_boundary_request",
      "train_count": 3,
      "heldout_case_count": 3,
      "heldout_semantic_failure_count": 3,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "privacy_question",
      "train_count": 3,
      "heldout_case_count": 2,
      "heldout_semantic_failure_count": 2,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "signup_path_question",
      "train_count": 3,
      "heldout_case_count": 14,
      "heldout_semantic_failure_count": 14,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "unsupported_fact_request",
      "train_count": 3,
      "heldout_case_count": 3,
      "heldout_semantic_failure_count": 3,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "no_crm_request",
      "train_count": 4,
      "heldout_case_count": 3,
      "heldout_semantic_failure_count": 2,
      "heldout_semantic_failure_rate": 0.6667
    },
    {
      "label": "midcycle_upgrade_question",
      "train_count": 4,
      "heldout_case_count": 14,
      "heldout_semantic_failure_count": 14,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "raw_url_request",
      "train_count": 5,
      "heldout_case_count": 3,
      "heldout_semantic_failure_count": 3,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "wrong_product_question",
      "train_count": 7,
      "heldout_case_count": 19,
      "heldout_semantic_failure_count": 19,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "internal_policy_request",
      "train_count": 8,
      "heldout_case_count": 2,
      "heldout_semantic_failure_count": 2,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "raw_transcript_request",
      "train_count": 9,
      "heldout_case_count": 4,
      "heldout_semantic_failure_count": 4,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "no_calendar_request",
      "train_count": 12,
      "heldout_case_count": 1,
      "heldout_semantic_failure_count": 0,
      "heldout_semantic_failure_rate": 0.0
    },
    {
      "label": "plus_price_question",
      "train_count": 16,
      "heldout_case_count": 5,
      "heldout_semantic_failure_count": 0,
      "heldout_semantic_failure_rate": 0.0
    },
    {
      "label": "no_interest",
      "train_count": 20,
      "heldout_case_count": 16,
      "heldout_semantic_failure_count": 15,
      "heldout_semantic_failure_rate": 0.9375
    },
    {
      "label": "pro_tier_choice",
      "train_count": 26,
      "heldout_case_count": 13,
      "heldout_semantic_failure_count": 11,
      "heldout_semantic_failure_rate": 0.8462
    },
    {
      "label": "plus_sufficiency_question",
      "train_count": 26,
      "heldout_case_count": 15,
      "heldout_semantic_failure_count": 13,
      "heldout_semantic_failure_rate": 0.8667
    },
    {
      "label": "current_competitor_tool",
      "train_count": 39,
      "heldout_case_count": 22,
      "heldout_semantic_failure_count": 15,
      "heldout_semantic_failure_rate": 0.6818
    },
    {
      "label": "terminal_thanks_acceptance",
      "train_count": 45,
      "heldout_case_count": 2,
      "heldout_semantic_failure_count": 0,
      "heldout_semantic_failure_rate": 0.0
    }
  ],
  "action": [
    {
      "label": "answer_signup_path",
      "train_count": 3,
      "heldout_case_count": 14,
      "heldout_semantic_failure_count": 14,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "answer_plan_change",
      "train_count": 4,
      "heldout_case_count": 14,
      "heldout_semantic_failure_count": 14,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "recommend_plan",
      "train_count": 13,
      "heldout_case_count": 7,
      "heldout_semantic_failure_count": 7,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "answer_without_inventing_facts",
      "train_count": 14,
      "heldout_case_count": 7,
      "heldout_semantic_failure_count": 7,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "compare_competitor_context",
      "train_count": 26,
      "heldout_case_count": 15,
      "heldout_semantic_failure_count": 11,
      "heldout_semantic_failure_rate": 0.7333
    },
    {
      "label": "answer_plan_fit",
      "train_count": 26,
      "heldout_case_count": 15,
      "heldout_semantic_failure_count": 13,
      "heldout_semantic_failure_rate": 0.8667
    },
    {
      "label": "disqualify_no_fit",
      "train_count": 27,
      "heldout_case_count": 35,
      "heldout_semantic_failure_count": 34,
      "heldout_semantic_failure_rate": 0.9714
    },
    {
      "label": "answer_price",
      "train_count": 29,
      "heldout_case_count": 11,
      "heldout_semantic_failure_count": 4,
      "heldout_semantic_failure_rate": 0.3636
    },
    {
      "label": "reframe_price_objection",
      "train_count": 32,
      "heldout_case_count": 7,
      "heldout_semantic_failure_count": 4,
      "heldout_semantic_failure_rate": 0.5714
    },
    {
      "label": "respect_boundary",
      "train_count": 33,
      "heldout_case_count": 14,
      "heldout_semantic_failure_count": 12,
      "heldout_semantic_failure_rate": 0.8571
    },
    {
      "label": "terminal_close",
      "train_count": 45,
      "heldout_case_count": 2,
      "heldout_semantic_failure_count": 0,
      "heldout_semantic_failure_rate": 0.0
    }
  ],
  "strategy": [
    {
      "label": "compare_options",
      "train_count": 13,
      "heldout_case_count": 8,
      "heldout_semantic_failure_count": 8,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "choice_close",
      "train_count": 20,
      "heldout_case_count": 35,
      "heldout_semantic_failure_count": 35,
      "heldout_semantic_failure_rate": 1.0
    },
    {
      "label": "no_fit_close",
      "train_count": 27,
      "heldout_case_count": 35,
      "heldout_semantic_failure_count": 34,
      "heldout_semantic_failure_rate": 0.9714
    },
    {
      "label": "value_reframe",
      "train_count": 32,
      "heldout_case_count": 7,
      "heldout_semantic_failure_count": 4,
      "heldout_semantic_failure_rate": 0.5714
    },
    {
      "label": "value_before_plan_selection",
      "train_count": 39,
      "heldout_case_count": 22,
      "heldout_semantic_failure_count": 16,
      "heldout_semantic_failure_rate": 0.7273
    },
    {
      "label": "terminal_close",
      "train_count": 45,
      "heldout_case_count": 2,
      "heldout_semantic_failure_count": 0,
      "heldout_semantic_failure_rate": 0.0
    },
    {
      "label": "boundary_without_side_effects",
      "train_count": 47,
      "heldout_case_count": 21,
      "heldout_semantic_failure_count": 19,
      "heldout_semantic_failure_rate": 0.9048
    },
    {
      "label": "answer_without_inventing_facts",
      "train_count": 64,
      "heldout_case_count": 11,
      "heldout_semantic_failure_count": 4,
      "heldout_semantic_failure_rate": 0.3636
    }
  ]
}

## Safety/Sales/Explanation Category Performance

[
  {
    "category": "other_sales",
    "case_count": 53,
    "semantic_failure_count": 46,
    "semantic_failure_rate": 0.8679,
    "safety_or_verifier_failure_count": 13
  },
  {
    "category": "price_value_recommendation",
    "case_count": 48,
    "semantic_failure_count": 36,
    "semantic_failure_rate": 0.75,
    "safety_or_verifier_failure_count": 7
  },
  {
    "category": "safety_boundary",
    "case_count": 40,
    "semantic_failure_count": 38,
    "semantic_failure_rate": 0.95,
    "safety_or_verifier_failure_count": 15
  }
]
