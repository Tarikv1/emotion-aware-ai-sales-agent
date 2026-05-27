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
- validation_semantic_match: 10
- test_schema_valid: 10
- test_verifier_pass: 9
- test_semantic_match: 9

## Base Versus Adapter Delta

{
  "validation": {
    "schema_valid_delta": 3,
    "verifier_pass_delta": 3,
    "semantic_match_delta": 3
  },
  "test": {
    "schema_valid_delta": 3,
    "verifier_pass_delta": 2,
    "semantic_match_delta": 2
  }
}

## Latency

{
  "model_load_time_ms": 10119.008,
  "total_generation_latency_ms": 396543.416,
  "average_generation_latency_ms": 19827.171,
  "p50_generation_latency_ms": 19619.458,
  "p90_generation_latency_ms": 20932.229,
  "average_first_output_latency_ms": 12390.263,
  "peak_gpu_memory_bytes": 6073434112
}

## Side Effects

- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false
- raw_private_transcript_included: false
