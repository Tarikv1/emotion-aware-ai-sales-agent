# LOCAL-QWEN-LORA-EVAL-001

- status: completed
- exact_blocker: None
- model_loaded: true
- adapter_loaded: true
- adapter_saved: true
- adapter_path: `local_artifacts/adapters/qwen2.5-sales-brain-lora-001`
- adapter_files_committed: false
- validation_rows: 10
- test_rows: 10

## Adapter Metrics

- validation_schema_valid: 10
- validation_verifier_pass: 10
- validation_semantic_match: 0
- validation_strict_gold_semantic_match: 0
- validation_strict_gold_response_plan_match: 7
- validation_compact_contract_valid: 0
- validation_deprecated_label_count: 20
- validation_case_id_label_leak_count: 6
- validation_generic_action_count: 8
- validation_generic_sub_intent_count: 0
- test_schema_valid: 10
- test_verifier_pass: 9
- test_semantic_match: 0
- test_strict_gold_semantic_match: 0
- test_strict_gold_response_plan_match: 7
- test_compact_contract_valid: 0
- test_deprecated_label_count: 17
- test_case_id_label_leak_count: 8
- test_generic_action_count: 8
- test_generic_sub_intent_count: 0

## Base Versus Adapter Delta

{
  "validation": {
    "schema_valid_delta": 3,
    "verifier_pass_delta": 3,
    "semantic_match_delta": -7
  },
  "test": {
    "schema_valid_delta": 3,
    "verifier_pass_delta": 2,
    "semantic_match_delta": -7
  }
}

## Latency

{
  "model_load_time_ms": 9376.135,
  "total_generation_latency_ms": 355394.152,
  "average_generation_latency_ms": 17769.708,
  "p50_generation_latency_ms": 17697.999,
  "p90_generation_latency_ms": 18583.489,
  "average_first_output_latency_ms": 11003.917,
  "peak_gpu_memory_bytes": 6073434112
}

## Side Effects

- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false
- raw_private_transcript_included: false
