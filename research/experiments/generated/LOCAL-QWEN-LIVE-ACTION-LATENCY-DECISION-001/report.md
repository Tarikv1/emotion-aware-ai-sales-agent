# LOCAL-QWEN-LIVE-ACTION-LATENCY-DECISION-001

## Recommendation

- status: pass
- benchmark_run: true
- target_met: False
- fastest_mode: minimal_live_action_prompt_with_replan_context
- latency_classification: far_above_target
- recommendation_id: `smaller_model_or_constrained_selector_before_live_use`
- recommendation: Treat Qwen 7B as an offline teacher, not the live model; test a smaller/distilled model or constrained action selector.
- live_wiring_allowed: false
- adapter_live_ready: false

## Minimal Live-Action Metrics

{
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
}

## Recommended Actions

[
  "Test a smaller model or distillation path.",
  "Prototype a constrained classifier/action selector for live use.",
  "Keep Qwen 7B for offline teacher/evaluation work unless a faster backend changes the latency result."
]

## Bottleneck Notes

[
  "minimal live-action first-token p50 is already above the 2s target",
  "minimal live-action first-token p90 is above the 3s target",
  "minimal live-action total-generation p50 misses the 2s target",
  "minimal live-action total-generation p90 misses the 3s target",
  "minimal live-action still has malformed output cases",
  "minimal live-action verifier pass count is zero, so latency alone cannot justify live wiring"
]
