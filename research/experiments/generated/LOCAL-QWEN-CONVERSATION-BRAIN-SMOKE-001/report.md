# LOCAL-QWEN-CONVERSATION-BRAIN-SMOKE-001

- status: not_run
- runner_implemented: true
- primary_model: Qwen/Qwen2.5-7B-Instruct
- local_model_path: local_artifacts/models/qwen2.5-7b-instruct
- cache_path: local_artifacts/cache/huggingface
- dependencies_available: false
- model_artifact_found: false
- model_download_attempted: false
- inference_attempted: false
- model_loaded: false
- dependency_status: missing_or_not_ready
- missing_dependencies: torch, transformers, accelerate, bitsandbytes
- cuda_available: false
- gpu_name: NVIDIA GeForce RTX 4070 SUPER
- quantization_mode: 4bit
- smoke_case_count: 0
- schema_valid_count: 0
- verifier_pass_count: 0
- failed_case_count: 0
- latency_metrics: {"model_load_time_ms": null, "first_output_latency_ms": null, "total_generation_latency_ms": null, "tokens_generated": null, "peak_gpu_memory_bytes": null}
- local_model_calls_made: false
- provider_calls_made: false
- runtime_behavior_changed: false
- response_text_changed: false
- WSL required: false
- WSL optional for future training: true

## Failed Cases

- none

## Notes

- ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT=1 and LOCAL_LLM_ENABLED=true are required before inference.
