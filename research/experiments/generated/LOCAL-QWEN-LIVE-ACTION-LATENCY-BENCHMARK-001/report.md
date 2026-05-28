# LOCAL-QWEN-LIVE-ACTION-LATENCY-BENCHMARK-001

- status: pass
- benchmark_run: true
- not_run_reason: none
- model_loaded: true
- adapter_loaded: false
- local_model_calls_made: true
- local_model_call_count: 60
- provider_calls_made: false
- openai_api_calls_made: false
- live_tts_calls_made: false
- model_redownloaded: false
- model_weights_committed: false
- runtime_behavior_changed: false
- response_text_changed: false
- target_met: False
- fastest_mode: minimal_live_action_prompt_with_replan_context

## Env Gates

{
  "ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT": true,
  "LOCAL_LLM_ENABLED": true,
  "LOCAL_LLM_MODEL_ID": "Qwen/Qwen2.5-7B-Instruct",
  "LOCAL_LLM_MODEL_PATH": "local_artifacts/models/qwen2.5-7b-instruct",
  "LOCAL_LLM_CACHE_DIR": "local_artifacts/cache/huggingface",
  "LOCAL_LLM_QUANTIZATION": "4bit",
  "LOCAL_LLM_DEVICE": "cuda",
  "LOCAL_LLM_ALLOW_MODEL_DOWNLOAD": "0"
}

## Metrics By Mode

{
  "current_compact_planner_prompt": {
    "case_count": 20,
    "prompt_token_count_total": 33173,
    "prompt_token_count_avg": 1658.65,
    "generated_token_count_total": 2343,
    "generated_token_count_avg": 117.15,
    "first_output_latency_avg_s": 6.523,
    "first_output_latency_p50_s": 8.03,
    "first_output_latency_p90_s": 10.012,
    "first_output_latency_p99_s": 12.033,
    "total_generation_latency_avg_s": 11.291,
    "total_generation_latency_p50_s": 11.232,
    "total_generation_latency_p90_s": 11.968,
    "total_generation_latency_p99_s": 13.527,
    "malformed_output_count": 14,
    "verifier_pass_count": 0,
    "replan_required_count": 0,
    "internal_language_count": 0,
    "loop_risk_count": 0
  },
  "minimal_live_action_prompt": {
    "case_count": 20,
    "prompt_token_count_total": 15011,
    "prompt_token_count_avg": 750.55,
    "generated_token_count_total": 1389,
    "generated_token_count_avg": 69.45,
    "first_output_latency_avg_s": 3.017,
    "first_output_latency_p50_s": 2.861,
    "first_output_latency_p90_s": 3.501,
    "first_output_latency_p99_s": 4.993,
    "total_generation_latency_avg_s": 6.608,
    "total_generation_latency_p50_s": 6.436,
    "total_generation_latency_p90_s": 8.292,
    "total_generation_latency_p99_s": 10.976,
    "malformed_output_count": 1,
    "verifier_pass_count": 0,
    "replan_required_count": 4,
    "internal_language_count": 0,
    "loop_risk_count": 0
  },
  "minimal_live_action_prompt_with_replan_context": {
    "case_count": 20,
    "prompt_token_count_total": 15711,
    "prompt_token_count_avg": 785.55,
    "generated_token_count_total": 1338,
    "generated_token_count_avg": 66.9,
    "first_output_latency_avg_s": 3.214,
    "first_output_latency_p50_s": 3.01,
    "first_output_latency_p90_s": 4.358,
    "first_output_latency_p99_s": 4.891,
    "total_generation_latency_avg_s": 6.496,
    "total_generation_latency_p50_s": 5.882,
    "total_generation_latency_p90_s": 8.938,
    "total_generation_latency_p99_s": 10.922,
    "malformed_output_count": 1,
    "verifier_pass_count": 0,
    "replan_required_count": 4,
    "internal_language_count": 0,
    "loop_risk_count": 1
  }
}

## Bottleneck Notes

[
  "minimal live-action first-token p50 is already above the 2s target",
  "minimal live-action first-token p90 is above the 3s target",
  "minimal live-action total-generation p50 misses the 2s target",
  "minimal live-action total-generation p90 misses the 3s target",
  "minimal live-action still has malformed output cases",
  "minimal live-action verifier pass count is zero, so latency alone cannot justify live wiring"
]
