# LOCAL-QWEN-OLLAMA-LIVE-ACTION-BENCHMARK-001

- status: pass
- benchmark_run: true
- not_run_reason: none
- model_name: qwen2.5:7b
- local_model_calls_made: true
- ollama_local_model_call_count: 60
- target_met: False
- quality_acceptable: false
- fastest_mode: constrained_action_selector_prompt
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false

## Metrics By Mode

{
  "constrained_action_selector_prompt": {
    "case_count": 20,
    "prompt_token_count_total": 9482,
    "prompt_token_count_avg": 474.1,
    "generated_token_count_total": 640,
    "generated_token_count_avg": 32.0,
    "first_output_latency_avg_s": null,
    "first_output_latency_p50_s": null,
    "first_output_latency_p90_s": null,
    "first_output_latency_p99_s": null,
    "total_generation_latency_avg_s": 3.721,
    "total_generation_latency_p50_s": 3.707,
    "total_generation_latency_p90_s": 3.785,
    "total_generation_latency_p99_s": 3.942,
    "malformed_output_count": 20,
    "verifier_pass_count": 0,
    "replan_required_count": 0,
    "internal_language_count": 0,
    "loop_risk_count": 0,
    "hard_block_count": 0,
    "target_met": false
  },
  "minimal_live_action_prompt": {
    "case_count": 20,
    "prompt_token_count_total": 15011,
    "prompt_token_count_avg": 750.55,
    "generated_token_count_total": 1198,
    "generated_token_count_avg": 59.9,
    "first_output_latency_avg_s": null,
    "first_output_latency_p50_s": null,
    "first_output_latency_p90_s": null,
    "first_output_latency_p99_s": null,
    "total_generation_latency_avg_s": 7.649,
    "total_generation_latency_p50_s": 5.079,
    "total_generation_latency_p90_s": 5.351,
    "total_generation_latency_p99_s": 57.858,
    "malformed_output_count": 9,
    "verifier_pass_count": 0,
    "replan_required_count": 2,
    "internal_language_count": 0,
    "loop_risk_count": 0,
    "hard_block_count": 0,
    "target_met": false
  },
  "minimal_live_action_prompt_with_replan_context": {
    "case_count": 20,
    "prompt_token_count_total": 15711,
    "prompt_token_count_avg": 785.55,
    "generated_token_count_total": 1205,
    "generated_token_count_avg": 60.25,
    "first_output_latency_avg_s": null,
    "first_output_latency_p50_s": null,
    "first_output_latency_p90_s": null,
    "first_output_latency_p99_s": null,
    "total_generation_latency_avg_s": 5.021,
    "total_generation_latency_p50_s": 5.12,
    "total_generation_latency_p90_s": 5.298,
    "total_generation_latency_p99_s": 5.315,
    "malformed_output_count": 12,
    "verifier_pass_count": 0,
    "replan_required_count": 3,
    "internal_language_count": 0,
    "loop_risk_count": 0,
    "hard_block_count": 0,
    "target_met": false
  }
}

## Warm Metrics By Mode

{
  "constrained_action_selector_prompt": {
    "case_count": 20,
    "prompt_token_count_total": 9482,
    "prompt_token_count_avg": 474.1,
    "generated_token_count_total": 640,
    "generated_token_count_avg": 32.0,
    "first_output_latency_avg_s": null,
    "first_output_latency_p50_s": null,
    "first_output_latency_p90_s": null,
    "first_output_latency_p99_s": null,
    "total_generation_latency_avg_s": 3.721,
    "total_generation_latency_p50_s": 3.707,
    "total_generation_latency_p90_s": 3.785,
    "total_generation_latency_p99_s": 3.942,
    "malformed_output_count": 20,
    "verifier_pass_count": 0,
    "replan_required_count": 0,
    "internal_language_count": 0,
    "loop_risk_count": 0,
    "hard_block_count": 0,
    "target_met": false
  },
  "minimal_live_action_prompt": {
    "case_count": 19,
    "prompt_token_count_total": 14269,
    "prompt_token_count_avg": 751.0,
    "generated_token_count_total": 1141,
    "generated_token_count_avg": 60.05,
    "first_output_latency_avg_s": null,
    "first_output_latency_p50_s": null,
    "first_output_latency_p90_s": null,
    "first_output_latency_p99_s": null,
    "total_generation_latency_avg_s": 5.007,
    "total_generation_latency_p50_s": 5.068,
    "total_generation_latency_p90_s": 5.266,
    "total_generation_latency_p99_s": 5.4,
    "malformed_output_count": 9,
    "verifier_pass_count": 0,
    "replan_required_count": 2,
    "internal_language_count": 0,
    "loop_risk_count": 0,
    "hard_block_count": 0,
    "target_met": false
  },
  "minimal_live_action_prompt_with_replan_context": {
    "case_count": 20,
    "prompt_token_count_total": 15711,
    "prompt_token_count_avg": 785.55,
    "generated_token_count_total": 1205,
    "generated_token_count_avg": 60.25,
    "first_output_latency_avg_s": null,
    "first_output_latency_p50_s": null,
    "first_output_latency_p90_s": null,
    "first_output_latency_p99_s": null,
    "total_generation_latency_avg_s": 5.021,
    "total_generation_latency_p50_s": 5.12,
    "total_generation_latency_p90_s": 5.298,
    "total_generation_latency_p99_s": 5.315,
    "malformed_output_count": 12,
    "verifier_pass_count": 0,
    "replan_required_count": 3,
    "internal_language_count": 0,
    "loop_risk_count": 0,
    "hard_block_count": 0,
    "target_met": false
  }
}

## Cold Request

{
  "case_id": "direct_price_001",
  "mode": "minimal_live_action_prompt",
  "backend": "ollama_local",
  "model_name": "qwen2.5:7b",
  "request_phase": "cold",
  "prompt_token_count": 742,
  "generated_token_count": 57,
  "first_output_latency_s": null,
  "first_output_latency_note": "stream=false initial benchmark; first output latency unavailable",
  "total_generation_latency_s": 57.858,
  "ollama_total_duration_s": 55.829,
  "ollama_load_duration_s": 52.74,
  "ollama_prompt_eval_duration_s": 0.449,
  "ollama_eval_duration_s": 0.763,
  "malformed_output": false,
  "parse_errors": [],
  "verifier": {
    "status": "invalid",
    "valid": false,
    "replan_required": false,
    "hard_block": false,
    "errors": [
      "missing_required_fields:['say']",
      "slots_must_be_object",
      "memory_updates_must_be_object",
      "say_must_be_non_empty_string"
    ],
    "replan_reasons": [],
    "hard_block_reasons": [],
    "warnings": []
  }
}
