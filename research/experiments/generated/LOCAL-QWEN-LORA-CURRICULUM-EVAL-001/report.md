# LOCAL-QWEN-LORA-CURRICULUM-EVAL-001

- status: completed
- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-curriculum-001`
- adapter_live_ready: false
- quality_gate_passed: false
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false

## Split Metrics

{
  "tiny_comparison": {
    "case_count": 8,
    "schema_valid_count": 8,
    "verifier_pass_count": 7,
    "semantic_match_count": 0,
    "gold_section_semantic_match_count": 0,
    "strict_gold_semantic_match_count": 0,
    "strict_gold_response_plan_match_count": 2,
    "compact_contract_valid_count": 8,
    "deprecated_label_count": 0,
    "case_id_label_leak_count": 0,
    "generic_action_count": 0,
    "generic_sub_intent_count": 0,
    "generic_act_count": 0,
    "exact_match_count": 0,
    "compact_adapter_error_count": 0,
    "failure_class_counts": {
      "strict_gold_semantic": 8,
      "strict_gold_response_plan": 6,
      "verifier": 1
    },
    "generic_label_count": 0,
    "malformed_output_count": 0,
    "latency_metrics": {
      "model_load_time_ms": 8726.045,
      "total_generation_latency_ms": 113501.959,
      "average_generation_latency_ms": 14187.745,
      "p50_generation_latency_ms": 13995.41,
      "p90_generation_latency_ms": 15861.986,
      "average_first_output_latency_ms": 5452.931,
      "peak_gpu_memory_bytes": 5975856128
    },
    "target_present_in_generation_prompt_count": 0
  },
  "train_sample": {
    "case_count": 20,
    "schema_valid_count": 20,
    "verifier_pass_count": 19,
    "semantic_match_count": 13,
    "gold_section_semantic_match_count": 13,
    "strict_gold_semantic_match_count": 13,
    "strict_gold_response_plan_match_count": 15,
    "compact_contract_valid_count": 20,
    "deprecated_label_count": 0,
    "case_id_label_leak_count": 0,
    "generic_action_count": 0,
    "generic_sub_intent_count": 0,
    "generic_act_count": 0,
    "exact_match_count": 13,
    "compact_adapter_error_count": 0,
    "failure_class_counts": {
      "strict_gold_semantic": 7,
      "strict_gold_response_plan": 5,
      "verifier": 1
    },
    "generic_label_count": 0,
    "malformed_output_count": 0,
    "latency_metrics": {
      "model_load_time_ms": null,
      "total_generation_latency_ms": 272952.194,
      "average_generation_latency_ms": 13647.61,
      "p50_generation_latency_ms": 13473.043,
      "p90_generation_latency_ms": 14534.897,
      "average_first_output_latency_ms": 5282.226,
      "peak_gpu_memory_bytes": 5975206912
    },
    "target_present_in_generation_prompt_count": 0
  },
  "validation": {
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
  "test": {
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
}

## Prior Base/Tiny Comparison

{
  "source": "research/experiments/generated/LOCAL-QWEN-LORA-TINY-OVERFIT-001/result.json",
  "status": "available",
  "base_qwen": {
    "status": "completed",
    "adapter_loaded": false,
    "case_count": 8,
    "schema_valid_count": 0,
    "verifier_pass_count": 0,
    "compact_contract_valid_count": 0,
    "strict_gold_semantic_match_count": 0,
    "exact_target_match_count": 0,
    "malformed_compact_object_count": 8,
    "deprecated_case_id_generic_label_count": 0,
    "latency_metrics": {
      "model_load_time_ms": 9063.376,
      "total_generation_latency_ms": 46720.024,
      "average_generation_latency_ms": 5840.003,
      "p50_generation_latency_ms": 6180.026,
      "p90_generation_latency_ms": 6867.07,
      "average_first_output_latency_ms": 4978.782
    }
  },
  "lora_002": {
    "status": "completed",
    "adapter_loaded": true,
    "case_count": 8,
    "schema_valid_count": 0,
    "verifier_pass_count": 0,
    "compact_contract_valid_count": 0,
    "strict_gold_semantic_match_count": 0,
    "exact_target_match_count": 0,
    "malformed_compact_object_count": 8,
    "deprecated_case_id_generic_label_count": 0,
    "latency_metrics": {
      "model_load_time_ms": 8525.524,
      "total_generation_latency_ms": 171574.226,
      "average_generation_latency_ms": 21446.778,
      "p50_generation_latency_ms": 19935.606,
      "p90_generation_latency_ms": 28280.314,
      "average_first_output_latency_ms": 15185.753
    }
  },
  "tiny_adapter": {
    "status": "completed",
    "adapter_loaded": true,
    "case_count": 8,
    "schema_valid_count": 8,
    "verifier_pass_count": 8,
    "compact_contract_valid_count": 8,
    "strict_gold_semantic_match_count": 8,
    "exact_target_match_count": 8,
    "malformed_compact_object_count": 0,
    "deprecated_case_id_generic_label_count": 0,
    "latency_metrics": {
      "model_load_time_ms": 8568.852,
      "total_generation_latency_ms": 131160.207,
      "average_generation_latency_ms": 16395.026,
      "p50_generation_latency_ms": 17031.836,
      "p90_generation_latency_ms": 18700.586,
      "average_first_output_latency_ms": 6360.373
    }
  }
}
