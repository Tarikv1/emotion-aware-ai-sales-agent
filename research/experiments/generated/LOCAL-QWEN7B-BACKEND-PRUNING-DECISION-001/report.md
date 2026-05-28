# LOCAL-QWEN7B-BACKEND-PRUNING-DECISION-001

- status: pass
- ollama_benchmark_run: true
- ollama_target_met: false
- ollama_quality_acceptable: false
- pruning_recommended_now: false
- backend_pruning_decision: `move_to_smaller_distilled_or_constrained_selector`
- recommendation: Use Ollama evidence as backend comparison, reject pruning for now, and move to a smaller/distilled model or constrained action selector.
- smaller_model_or_distillation_remains_recommended: true
- live_wiring_allowed: false

## Ollama Metrics

{
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
}
