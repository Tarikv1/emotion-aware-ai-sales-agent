# LOCAL-QWEN-COMPACT-PLANNER-SMOKE-001

## Previous Full-Schema Smoke

- previous_status: pass
- previous_schema_valid_count: 8
- previous_verifier_pass_count: 8
- previous_latency_total_ms: 325385.843
- previous_generated_tokens: 2951

## New Smoke

- status: pass
- runner_implemented: true
- primary_model: Qwen/Qwen2.5-7B-Instruct
- local_model_path: local_artifacts/models/qwen2.5-7b-instruct
- cache_path: local_artifacts/cache/huggingface
- dependencies_available: true
- model_artifact_found: true
- model_download_attempted: false
- inference_attempted: true
- model_loaded: true
- dependency_status: ready
- dependency_install_attempted: false
- dependency_install_succeeded: false
- dependency_versions: {"torch": "2.11.0+cu128", "transformers": "5.9.0", "accelerate": "1.13.0", "bitsandbytes": "0.49.2", "safetensors": "0.7.0", "huggingface_hub": "1.16.4"}
- missing_dependencies: none
- cuda_available: true
- gpu_name: NVIDIA GeForce RTX 4070 SUPER
- quantization_mode_requested: 4bit
- quantization_mode_actually_used: 4bit
- fallback_used: false
- planner_schema_mode: compact
- compact_adapter_status: enabled
- smoke_case_count: 8
- schema_valid_count: 8
- verifier_pass_count: 8
- schema_valid_before_repair_count: 8
- schema_valid_after_repair_count: 8
- compact_schema_valid_count: 8
- compact_expanded_schema_valid_count: 8
- compact_adapter_error_count: 0
- repair_applied_count: 0
- repair_types: {}
- truncation_count: 0
- needs_fact_check_before_repair_count: 0
- needs_fact_check_after_repair_count: 0
- buyer_word_preservation_errors_before_repair: 0
- buyer_word_preservation_errors_after_repair: 0
- failed_case_count: 0
- latency_metrics: {"model_load_time_ms": 12038.674, "first_output_latency_ms": 2543.867, "total_generation_latency_ms": 98913.497, "tokens_generated": 1034, "prompt_tokens_total": 9015, "prompt_tokens_max": 1147, "completed_json_object_count": 8, "output_truncated_count": 0, "timed_out_count": 0, "peak_gpu_memory_bytes": 6081472000}
- token_reduction_vs_full: 1917
- latency_reduction_ms_vs_full: 226472.346
- generation_settings: {"do_sample": false, "max_output_tokens": 256, "stop_after_first_complete_json_object": true, "temperature": "default deterministic greedy generation; no sampling temperature is set"}
- approved_campaign_fact_summaries_added: {"public_plan_names": "ChatGPT public plan categories include Free, Plus, Pro, Business, and Enterprise; source fixture also tracks Go.", "individual_plans": "Free, Plus, and Pro are individual ChatGPT plan categories.", "team_plans": "Business is the self-serve team workspace plan; Enterprise is for larger organization-level controls and contact sales.", "self_serve_path": "Individual plans use the official ChatGPT plans page or ChatGPT profile upgrade flow.", "pro_tier_general": "Pro has 100 dollar and 200 dollar tiers; exact current terms can change and the official source is authoritative."}
- planner_json_compactness_scope: max_output_tokens and compact prompt apply to planner JSON only; longer buyer-facing answers remain allowed when response strategy and buyer need justify them.
- local_model_calls_made: true
- local_model_call_count: 8
- provider_calls_made: false
- model_weights_committed: false
- runtime_behavior_changed: false
- response_text_changed: false
- WSL required: false
- WSL optional for future training: true

## Failed Cases

- none
