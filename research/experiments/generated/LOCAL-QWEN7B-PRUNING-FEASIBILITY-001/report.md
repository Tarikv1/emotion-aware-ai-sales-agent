# LOCAL-QWEN7B-PRUNING-FEASIBILITY-001

- status: pass
- pruning_feasible_now: false
- pruning_recommended_now: false
- recommended_pruning_type: none
- expected_latency_gain_class: low
- implementation_risk: high
- quality_risk: high
- attempt_actual_pruning_next_phase: false
- smaller_model_or_distillation_remains_recommended: true

## Backend First

{
  "ollama_benchmark_run": false,
  "ollama_target_met": false,
  "ollama_quality_acceptable": false,
  "p50_speedup_vs_transformers": null,
  "finding": "Use measured Ollama latency if available. If it does not meet target with quality, pruning still lacks a low-risk path to the target."
}

## Pruning Paths

{
  "unstructured_pruning": {
    "can_make_file_smaller": true,
    "transformers_bitsandbytes_sparse_speedup_expected": false,
    "ollama_gguf_llamacpp_sparse_unstructured_speedup_expected": false,
    "speedup_likely_without_sparse_kernels": false,
    "quality_risk": "high",
    "finding": "Unstructured pruning can zero weights, but the current practical backends are dense/quantized paths and should not be expected to accelerate arbitrary sparse masks."
  },
  "semi_structured_2_4_pruning": {
    "runtime_backend_support_practical_now": false,
    "export_run_path_realistic_now": false,
    "rtx_4070_super_acceleration_likely_in_project_stack": false,
    "implementation_complexity": "high",
    "finding": "2:4 sparsity can be hardware-relevant in supported CUDA kernels, but this project stack has no validated export/runtime path for Ollama/GGUF or the existing Transformers 4-bit path."
  },
  "structured_pruning": {
    "dense_smaller_model_possible": true,
    "export_to_runnable_local_format_possible": "uncertain",
    "recovery_fine_tuning_required": true,
    "more_promising_than_native_smaller_model": false,
    "realistic_within_current_timeline": false,
    "finding": "Structured pruning could make a smaller dense model, but it becomes a model-surgery and recovery-training project. A native smaller Qwen model or distilled selector is the simpler route."
  },
  "distillation_comparison": {
    "pruning_more_effort_than_smaller_model_distillation": true,
    "more_likely_to_hit_2_3_seconds": "smaller_model_or_distilled_action_selector",
    "safer_for_product_quality": "smaller_model_distillation_with_offline_quality_gate",
    "finding": "Distillation/smaller native model keeps a standard dense runtime path and is easier to benchmark and roll back."
  },
  "backend_first_optimization": {
    "ollama_benchmark_run": false,
    "ollama_target_met": false,
    "ollama_quality_acceptable": false,
    "p50_speedup_vs_transformers": null,
    "finding": "Use measured Ollama latency if available. If it does not meet target with quality, pruning still lacks a low-risk path to the target."
  }
}

## Rationale

[
  "Current unstructured pruning has no validated sparse-kernel speed path in the measured backends.",
  "2:4 pruning is not a practical Ollama/GGUF or current 4-bit Transformers path in this repo.",
  "Structured pruning would require recovery fine-tuning and export validation, which is more complex than testing a smaller dense model.",
  "No actual pruning, training, adapter generation, or live wiring was performed."
]
