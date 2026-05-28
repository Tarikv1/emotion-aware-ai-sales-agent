# LOCAL-QWEN-LORA-MIXED-REPLAY-EVAL-001

- status: completed
- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-mixed-replay-001`
- quality_gate_passed: false
- adapter_live_ready: false
- live_wiring_allowed: false
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false

## Split Metrics

{
  "train_sample": {
    "case_count": 40,
    "schema_valid_count": 39,
    "verifier_pass_count": 36,
    "compact_contract_valid_count": 39,
    "strict_gold_semantic_match_count": 25,
    "strict_gold_response_plan_match_count": 3,
    "equivalence_match_count": 22,
    "exact_match_count": 3,
    "safety_pass_count": 36,
    "deprecated_label_count": 0,
    "case_id_label_leak_count": 0,
    "generic_label_count": 0,
    "malformed_output_count": 0,
    "and_or_drift_count": 1,
    "voice_writing_drift_count": 0,
    "not_team_team_drift_count": 0,
    "fake_side_effect_count": 0,
    "internal_policy_language_count": 1,
    "unsupported_fact_count": 0,
    "failure_class_counts": {
      "and_or_drift": 1,
      "compact_contract": 1,
      "internal_policy_language": 1,
      "safety": 4,
      "schema": 1,
      "strict_gold_response_plan": 37,
      "strict_gold_semantic": 15,
      "verifier": 4
    },
    "target_present_in_generation_prompt_count": 0,
    "latency_metrics": {
      "model_load_time_ms": 20033.791,
      "total_generation_latency_ms": 614197.209,
      "average_generation_latency_ms": 15354.93,
      "p50_generation_latency_ms": 15087.076,
      "p90_generation_latency_ms": 17281.506,
      "average_first_output_latency_ms": 6823.368,
      "peak_gpu_memory_bytes": 5976343552
    }
  },
  "validation": {
    "case_count": 65,
    "schema_valid_count": 64,
    "verifier_pass_count": 46,
    "compact_contract_valid_count": 57,
    "strict_gold_semantic_match_count": 13,
    "strict_gold_response_plan_match_count": 2,
    "equivalence_match_count": 6,
    "exact_match_count": 2,
    "safety_pass_count": 46,
    "deprecated_label_count": 0,
    "case_id_label_leak_count": 0,
    "generic_label_count": 0,
    "malformed_output_count": 1,
    "and_or_drift_count": 11,
    "voice_writing_drift_count": 0,
    "not_team_team_drift_count": 0,
    "fake_side_effect_count": 0,
    "internal_policy_language_count": 0,
    "unsupported_fact_count": 0,
    "failure_class_counts": {
      "and_or_drift": 11,
      "compact_contract": 8,
      "malformed_output": 1,
      "safety": 19,
      "schema": 1,
      "strict_gold_response_plan": 63,
      "strict_gold_semantic": 52,
      "verifier": 19
    },
    "target_present_in_generation_prompt_count": 0,
    "latency_metrics": {
      "model_load_time_ms": null,
      "total_generation_latency_ms": 970643.599,
      "average_generation_latency_ms": 14932.978,
      "p50_generation_latency_ms": 14871.229,
      "p90_generation_latency_ms": 16724.715,
      "average_first_output_latency_ms": 4387.065,
      "peak_gpu_memory_bytes": 5976994816
    }
  },
  "test": {
    "case_count": 66,
    "schema_valid_count": 64,
    "verifier_pass_count": 52,
    "compact_contract_valid_count": 61,
    "strict_gold_semantic_match_count": 8,
    "strict_gold_response_plan_match_count": 1,
    "equivalence_match_count": 8,
    "exact_match_count": 1,
    "safety_pass_count": 52,
    "deprecated_label_count": 0,
    "case_id_label_leak_count": 0,
    "generic_label_count": 0,
    "malformed_output_count": 1,
    "and_or_drift_count": 2,
    "voice_writing_drift_count": 0,
    "not_team_team_drift_count": 0,
    "fake_side_effect_count": 0,
    "internal_policy_language_count": 2,
    "unsupported_fact_count": 0,
    "failure_class_counts": {
      "and_or_drift": 2,
      "compact_contract": 5,
      "internal_policy_language": 2,
      "malformed_output": 1,
      "safety": 14,
      "schema": 2,
      "strict_gold_response_plan": 65,
      "strict_gold_semantic": 58,
      "verifier": 14
    },
    "target_present_in_generation_prompt_count": 0,
    "latency_metrics": {
      "model_load_time_ms": null,
      "total_generation_latency_ms": 920559.297,
      "average_generation_latency_ms": 13947.868,
      "p50_generation_latency_ms": 13700.35,
      "p90_generation_latency_ms": 15500.809,
      "average_first_output_latency_ms": 4575.183,
      "peak_gpu_memory_bytes": 5977319424
    }
  },
  "ood_test": {
    "case_count": 10,
    "schema_valid_count": 9,
    "verifier_pass_count": 8,
    "compact_contract_valid_count": 7,
    "strict_gold_semantic_match_count": 0,
    "strict_gold_response_plan_match_count": 0,
    "equivalence_match_count": 0,
    "exact_match_count": 0,
    "safety_pass_count": 8,
    "deprecated_label_count": 0,
    "case_id_label_leak_count": 0,
    "generic_label_count": 0,
    "malformed_output_count": 1,
    "and_or_drift_count": 0,
    "voice_writing_drift_count": 0,
    "not_team_team_drift_count": 0,
    "fake_side_effect_count": 0,
    "internal_policy_language_count": 0,
    "unsupported_fact_count": 0,
    "failure_class_counts": {
      "compact_contract": 3,
      "malformed_output": 1,
      "safety": 2,
      "schema": 1,
      "strict_gold_response_plan": 10,
      "strict_gold_semantic": 10,
      "verifier": 2
    },
    "target_present_in_generation_prompt_count": 0,
    "latency_metrics": {
      "model_load_time_ms": null,
      "total_generation_latency_ms": 125684.533,
      "average_generation_latency_ms": 12568.453,
      "p50_generation_latency_ms": 12445.181,
      "p90_generation_latency_ms": 13362.051,
      "average_first_output_latency_ms": 5613.686,
      "peak_gpu_memory_bytes": 5974889472
    }
  }
}

## Quality Gate Failures

{
  "validation": [
    "schema_valid_count_below_1.0",
    "compact_contract_valid_count_below_1.0",
    "verifier_pass_count_below_0.98",
    "strict_gold_semantic_match_count_below_0.85",
    "equivalence_match_count_below_0.9",
    "and_or_drift_count_nonzero",
    "safety_pass_count_not_100_percent"
  ],
  "test": [
    "schema_valid_count_below_1.0",
    "compact_contract_valid_count_below_1.0",
    "verifier_pass_count_below_0.98",
    "strict_gold_semantic_match_count_below_0.85",
    "equivalence_match_count_below_0.9",
    "and_or_drift_count_nonzero",
    "internal_policy_language_count_nonzero",
    "safety_pass_count_not_100_percent"
  ]
}

## Prior Comparison

{
  "base_qwen_prior": {
    "source": "research/experiments/generated/LOCAL-QWEN-GOLDSET-EVAL-001/result.json",
    "status": "available",
    "quality_gate_passed": null,
    "adapter_live_ready": null,
    "validation_metrics": null,
    "test_metrics": null
  },
  "tiny_adapter_prior": {
    "source": null,
    "status": "missing",
    "quality_gate_passed": null,
    "adapter_live_ready": null,
    "validation_metrics": null,
    "test_metrics": null
  },
  "curriculum_adapter_prior": {
    "source": "research/experiments/generated/LOCAL-QWEN-LORA-CURRICULUM-EVAL-001/result.json",
    "status": "available",
    "quality_gate_passed": false,
    "adapter_live_ready": false,
    "validation_metrics": {
      "case_count": 10,
      "schema_valid_count": 10,
      "verifier_pass_count": 8,
      "semantic_match_count": 1,
      "gold_section_semantic_match_count": 1,
      "strict_gold_semantic_match_count": 1,
      "strict_gold_response_plan_match_count": 1,
      "compact_contract_valid_count": 10,
      "deprecated_label_count": 0,
      "case_id_label_leak_count": 0,
      "generic_action_count": 0,
      "generic_sub_intent_count": 0,
      "generic_act_count": 0,
      "exact_match_count": 1,
      "compact_adapter_error_count": 0,
      "failure_class_counts": {
        "strict_gold_semantic": 9,
        "strict_gold_response_plan": 9,
        "verifier": 2
      },
      "generic_label_count": 0,
      "malformed_output_count": 0,
      "latency_metrics": {
        "model_load_time_ms": null,
        "total_generation_latency_ms": 130574.778,
        "average_generation_latency_ms": 13057.478,
        "p50_generation_latency_ms": 13248.54,
        "p90_generation_latency_ms": 13807.181,
        "average_first_output_latency_ms": 6078.076,
        "peak_gpu_memory_bytes": 5975206912
      },
      "target_present_in_generation_prompt_count": 0
    },
    "test_metrics": {
      "case_count": 10,
      "schema_valid_count": 10,
      "verifier_pass_count": 6,
      "semantic_match_count": 2,
      "gold_section_semantic_match_count": 2,
      "strict_gold_semantic_match_count": 2,
      "strict_gold_response_plan_match_count": 3,
      "compact_contract_valid_count": 9,
      "deprecated_label_count": 0,
      "case_id_label_leak_count": 0,
      "generic_action_count": 0,
      "generic_sub_intent_count": 0,
      "generic_act_count": 0,
      "exact_match_count": 1,
      "compact_adapter_error_count": 0,
      "failure_class_counts": {
        "verifier": 4,
        "strict_gold_semantic": 8,
        "strict_gold_response_plan": 7,
        "compact_contract": 1
      },
      "generic_label_count": 0,
      "malformed_output_count": 0,
      "latency_metrics": {
        "model_load_time_ms": null,
        "total_generation_latency_ms": 134432.731,
        "average_generation_latency_ms": 13443.273,
        "p50_generation_latency_ms": 13450.555,
        "p90_generation_latency_ms": 14591.825,
        "average_first_output_latency_ms": 7029.168,
        "peak_gpu_memory_bytes": 5975052288
      },
      "target_present_in_generation_prompt_count": 0
    }
  },
  "deterministic_target_baseline": {
    "status": "available",
    "meaning": "Gold compact targets are the baseline and expected to score 100% by construction after approval gate."
  }
}
