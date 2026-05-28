# LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-001

- status: pass
- benchmark_run: true
- target_met: false
- quality_acceptable: true
- recommendation_id: `non_llm_classifier_or_backend_optimization`
- recommendation: No tested small model/mode met the live latency target. Move to a non-LLM classifier/action selector or further backend optimization.
- smaller_model_path_remains_viable: true
- distillation_or_finetuning_recommended: true
- non_llm_classifier_recommended: true
- two_head_split_recommended: false
- live_wiring_allowed: false
- adapter_live_ready: false

## Best Model Mode

{
  "model_name": "smollm2:1.7b",
  "mode": "ultra_minimal_action_id_only",
  "p50": 2.411,
  "p90": 2.427,
  "p99": 2.435,
  "target_met": false,
  "quality_acceptable": true,
  "verifier_pass_count": 20,
  "malformed_output_count": 0
}

## Recommended Actions

[
  "No tested small model/mode met the live latency target. Move to a non-LLM classifier/action selector or further backend optimization.",
  "qwen2.5:1.5b is close enough to justify Qwen 7B teacher -> Qwen 1.5B distillation as a follow-up.",
  "smollm2 or llama3.2 was the strongest observed model family; run a follow-up quality benchmark on that model.",
  "Add a deterministic or classical action selector baseline because the live 2-3 second budget remains unproven for local LLMs."
]
