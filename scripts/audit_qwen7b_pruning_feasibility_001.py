#!/usr/bin/env python3
from __future__ import annotations

import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import sys
from typing import Any

from local_ollama_qwen_utils_001 import (
    GENERATED_DIR,
    LOCAL_MODEL_PATH,
    PRUNING_PLAN_PATH,
    TARGETS_SECONDS,
    audit_side_effects,
    pruned_weight_files,
    read_json,
    rel,
    tracked_model_or_adapter_files,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN7B-PRUNING-FEASIBILITY-001"
DECISION_ID = "LOCAL-QWEN7B-BACKEND-PRUNING-DECISION-001"
OUT_DIR = GENERATED_DIR / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
DECISION_OUT_DIR = GENERATED_DIR / DECISION_ID
DECISION_RESULT_PATH = DECISION_OUT_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_OUT_DIR / "report.md"
TRANSFORMERS_BENCHMARK_PATH = GENERATED_DIR / "LOCAL-QWEN-LIVE-ACTION-LATENCY-BENCHMARK-001" / "result.json"
OLLAMA_BENCHMARK_PATH = GENERATED_DIR / "LOCAL-QWEN-OLLAMA-LIVE-ACTION-BENCHMARK-001" / "result.json"
PROBE_PATH = GENERATED_DIR / "LOCAL-QWEN-OLLAMA-BACKEND-PROBE-001" / "result.json"


def command(args: list[str], timeout_s: int = 20) -> dict[str, Any]:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout_s, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"available": False, "returncode": None, "stdout": "", "stderr": str(exc)}
    return {
        "available": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def package_versions() -> dict[str, str]:
    names = [
        "torch",
        "transformers",
        "bitsandbytes",
        "accelerate",
        "safetensors",
        "huggingface_hub",
        "peft",
        "optimum",
        "llama-cpp-python",
        "sparseml",
    ]
    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not_installed"
    return versions


def local_model_status() -> dict[str, Any]:
    markers = []
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "model.safetensors.index.json", "pytorch_model.bin.index.json"):
        if (LOCAL_MODEL_PATH / name).is_file():
            markers.append(name)
    weights = [path.name for pattern in ("*.safetensors", "*.bin", "*.gguf") for path in LOCAL_MODEL_PATH.glob(pattern)] if LOCAL_MODEL_PATH.is_dir() else []
    return {
        "path": rel(LOCAL_MODEL_PATH),
        "exists": LOCAL_MODEL_PATH.exists(),
        "is_dir": LOCAL_MODEL_PATH.is_dir(),
        "markers": sorted(markers),
        "weight_file_count": len(weights),
        "weight_file_suffixes": sorted({Path(name).suffix for name in weights}),
    }


def hardware_summary() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "processor": platform.processor(),
        "nvidia_smi": command(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version,compute_cap",
                "--format=csv,noheader",
            ],
            timeout_s=20,
        ),
    }


def live_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload.get("metrics_by_mode") if isinstance(payload.get("metrics_by_mode"), dict) else {}
    return metrics.get("minimal_live_action_prompt") if isinstance(metrics.get("minimal_live_action_prompt"), dict) else {}


def warm_live_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload.get("warm_metrics_by_mode") if isinstance(payload.get("warm_metrics_by_mode"), dict) else {}
    if isinstance(metrics.get("minimal_live_action_prompt"), dict):
        return metrics["minimal_live_action_prompt"]
    return live_metrics(payload)


def metric_value(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    return float(value) if isinstance(value, (int, float)) else None


def target_met(metrics: dict[str, Any]) -> bool:
    p50 = metric_value(metrics, "total_generation_latency_p50_s")
    p90 = metric_value(metrics, "total_generation_latency_p90_s")
    p99 = metric_value(metrics, "total_generation_latency_p99_s")
    return bool(p50 is not None and p90 is not None and p99 is not None and p50 <= TARGETS_SECONDS["p50"] and p90 <= TARGETS_SECONDS["p90"] and p99 <= TARGETS_SECONDS["p99"])


def build_pruning_audit() -> dict[str, Any]:
    transformers = read_json(TRANSFORMERS_BENCHMARK_PATH)
    ollama = read_json(OLLAMA_BENCHMARK_PATH)
    probe = read_json(PROBE_PATH)
    packages = package_versions()
    transformers_metrics = live_metrics(transformers)
    ollama_metrics = warm_live_metrics(ollama)
    ollama_ran = ollama.get("benchmark_run") is True
    ollama_p50 = metric_value(ollama_metrics, "total_generation_latency_p50_s")
    transformers_p50 = metric_value(transformers_metrics, "total_generation_latency_p50_s")
    backend_improvement = None
    if ollama_p50 is not None and transformers_p50:
        backend_improvement = round(transformers_p50 / ollama_p50, 3)

    unstructured = {
        "can_make_file_smaller": True,
        "transformers_bitsandbytes_sparse_speedup_expected": False,
        "ollama_gguf_llamacpp_sparse_unstructured_speedup_expected": False,
        "speedup_likely_without_sparse_kernels": False,
        "quality_risk": "high",
        "finding": "Unstructured pruning can zero weights, but the current practical backends are dense/quantized paths and should not be expected to accelerate arbitrary sparse masks.",
    }
    semi_structured = {
        "runtime_backend_support_practical_now": False,
        "export_run_path_realistic_now": False,
        "rtx_4070_super_acceleration_likely_in_project_stack": False,
        "implementation_complexity": "high",
        "finding": "2:4 sparsity can be hardware-relevant in supported CUDA kernels, but this project stack has no validated export/runtime path for Ollama/GGUF or the existing Transformers 4-bit path.",
    }
    structured = {
        "dense_smaller_model_possible": True,
        "export_to_runnable_local_format_possible": "uncertain",
        "recovery_fine_tuning_required": True,
        "more_promising_than_native_smaller_model": False,
        "realistic_within_current_timeline": False,
        "finding": "Structured pruning could make a smaller dense model, but it becomes a model-surgery and recovery-training project. A native smaller Qwen model or distilled selector is the simpler route.",
    }
    distillation = {
        "pruning_more_effort_than_smaller_model_distillation": True,
        "more_likely_to_hit_2_3_seconds": "smaller_model_or_distilled_action_selector",
        "safer_for_product_quality": "smaller_model_distillation_with_offline_quality_gate",
        "finding": "Distillation/smaller native model keeps a standard dense runtime path and is easier to benchmark and roll back.",
    }
    backend_first = {
        "ollama_benchmark_run": ollama_ran,
        "ollama_target_met": target_met(ollama_metrics) if ollama_ran else False,
        "ollama_quality_acceptable": ollama.get("quality_acceptable") is True,
        "p50_speedup_vs_transformers": backend_improvement,
        "finding": "Use measured Ollama latency if available. If it does not meet target with quality, pruning still lacks a low-risk path to the target.",
    }

    pruning_feasible_now = False
    pruning_recommended_now = False
    recommended_pruning_type = "none"
    expected_latency_gain_class = "low"
    implementation_risk = "high"
    quality_risk = "high"

    result = {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {
            "transformers_benchmark": rel(TRANSFORMERS_BENCHMARK_PATH),
            "ollama_probe": rel(PROBE_PATH),
            "ollama_benchmark": rel(OLLAMA_BENCHMARK_PATH),
            "local_qwen_model_path": rel(LOCAL_MODEL_PATH),
        },
        "hardware_summary": hardware_summary(),
        "installed_python_packages": packages,
        "local_model_status": local_model_status(),
        "current_inference_backend_details": {
            "transformers_quantization": (transformers.get("config") or {}).get("quantization_mode"),
            "transformers_device": (transformers.get("config") or {}).get("device"),
            "ollama_command_exists": probe.get("ollama_command_exists"),
            "ollama_api_reachable": probe.get("ollama_api_reachable"),
            "ollama_model_present": probe.get("qwen_model_present"),
            "ollama_benchmark_run": ollama_ran,
        },
        "transformers_minimal_live_action_metrics": transformers_metrics,
        "ollama_minimal_live_action_warm_metrics": ollama_metrics,
        "backend_p50_speedup_vs_transformers": backend_improvement,
        "audit_paths": {
            "unstructured_pruning": unstructured,
            "semi_structured_2_4_pruning": semi_structured,
            "structured_pruning": structured,
            "distillation_comparison": distillation,
            "backend_first_optimization": backend_first,
        },
        "pruning_feasible_now": pruning_feasible_now,
        "pruning_recommended_now": pruning_recommended_now,
        "recommended_pruning_type": recommended_pruning_type,
        "expected_latency_gain_class": expected_latency_gain_class,
        "implementation_risk": implementation_risk,
        "quality_risk": quality_risk,
        "attempt_actual_pruning_next_phase": False,
        "smaller_model_or_distillation_remains_recommended": True,
        "rationale": [
            "Current unstructured pruning has no validated sparse-kernel speed path in the measured backends.",
            "2:4 pruning is not a practical Ollama/GGUF or current 4-bit Transformers path in this repo.",
            "Structured pruning would require recovery fine-tuning and export validation, which is more complex than testing a smaller dense model.",
            "No actual pruning, training, adapter generation, or live wiring was performed.",
        ],
        "training_rerun": False,
        "actual_pruning_performed": False,
        "pruned_weights_created": False,
        "pruned_weight_files_detected": pruned_weight_files(),
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "live_wiring_allowed": False,
        "adapter_live_ready": False,
        "model_or_adapter_weights_committed": bool(tracked_model_or_adapter_files()),
        "side_effects": audit_side_effects(),
    }
    return result


def build_pruning_plan(audit: dict[str, Any]) -> dict[str, Any]:
    enabled = audit.get("pruning_recommended_now") is True
    return {
        "plan_id": "qwen7b-pruning-experiment-plan-001",
        "generated_at": utc_now(),
        "future_pruning_experiment_enabled": enabled,
        "activation_condition": "Only enable in a later approved phase if pruning_feasible_now=true and pruning_recommended_now=true.",
        "base_model_id": "Qwen/Qwen2.5-7B-Instruct",
        "base_model_path": "local_artifacts/models/qwen2.5-7b-instruct",
        "candidate_pruning_methods": [
            {
                "method": "unstructured_pruning",
                "status": "rejected_for_now",
                "reason": "No expected speedup on current dense/quantized runtime path without sparse kernels."
            },
            {
                "method": "semi_structured_2_4_pruning",
                "status": "deferred",
                "reason": "No validated export/runtime path for this project stack."
            },
            {
                "method": "structured_layer_head_mlp_pruning",
                "status": "deferred",
                "reason": "Requires recovery fine-tuning and export validation; smaller native model is simpler."
            }
        ],
        "calibration_dataset_source": "future local sanitized live-action benchmark cases plus generated contract cases; no real customer data",
        "target_sparsity_or_compression_levels": {
            "unstructured": ["30%", "50%"],
            "semi_structured_2_4": ["50% 2:4 pattern"],
            "structured": ["remove selected heads/channels/layers only after sensitivity audit"]
        },
        "recovery_fine_tuning_plan": "Not approved in this phase. Any recovery fine-tuning would need a later explicit no-provider local-only phase.",
        "output_path": "local_artifacts/pruned_models/qwen2.5-7b-pruned-experiment-001",
        "no_model_weights_committed": True,
        "benchmark_plan": [
            "Run the same live-action latency benchmark before and after pruning.",
            "Run live-action contract quality validators.",
            "Compare against smaller native/distilled model baseline."
        ],
        "quality_gate": {
            "latency_target": TARGETS_SECONDS,
            "malformed_output_count": 0,
            "verifier_pass_required": True,
            "no_internal_language": True,
            "live_wiring_allowed": False
        },
        "rollback_plan": "Delete local_artifacts/pruned_models experiment output and return to the committed baseline; never commit pruned weights.",
        "actual_pruning_performed": False,
        "model_weights_created": False,
        "live_wiring_allowed": False,
        "adapter_live_ready": False
    }


def build_backend_pruning_decision(audit: dict[str, Any] | None = None) -> dict[str, Any]:
    audit_payload = audit or read_json(RESULT_PATH)
    ollama = read_json(OLLAMA_BENCHMARK_PATH)
    ollama_metrics = warm_live_metrics(ollama)
    ollama_ran = ollama.get("benchmark_run") is True
    ollama_target = target_met(ollama_metrics) if ollama_ran else False
    quality_ok = ollama.get("quality_acceptable") is True
    pruning_high_gain = (
        audit_payload.get("pruning_feasible_now") is True
        and audit_payload.get("expected_latency_gain_class") == "high"
        and audit_payload.get("implementation_risk") != "high"
    )
    if ollama_target and quality_ok:
        decision_id = "ollama_backend_quality_benchmark_next"
        recommendation = "Run an offline Ollama backend quality benchmark next; do not wire into live runtime."
    elif ollama_ran and pruning_high_gain:
        decision_id = "actual_pruning_experiment_next"
        recommendation = "Run an explicitly approved pruning experiment next, then benchmark latency and quality."
    elif ollama_ran:
        decision_id = "move_to_smaller_distilled_or_constrained_selector"
        recommendation = "Use Ollama evidence as backend comparison, reject pruning for now, and move to a smaller/distilled model or constrained action selector."
    else:
        decision_id = "ollama_unavailable_or_not_run_move_to_smaller_model_unless_benchmark_unblocks"
        recommendation = "Ollama benchmark is not available yet; keep Qwen 7B as offline teacher and prioritize smaller/distilled model or constrained selector unless Ollama benchmark later changes the result."

    return {
        "experiment_id": DECISION_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {
            "transformers_benchmark": rel(TRANSFORMERS_BENCHMARK_PATH),
            "ollama_benchmark": rel(OLLAMA_BENCHMARK_PATH),
            "pruning_feasibility": rel(RESULT_PATH),
        },
        "ollama_benchmark_run": ollama_ran,
        "ollama_target_met": ollama_target,
        "ollama_quality_acceptable": quality_ok,
        "ollama_minimal_live_action_warm_metrics": ollama_metrics,
        "pruning_feasible_now": audit_payload.get("pruning_feasible_now"),
        "pruning_recommended_now": audit_payload.get("pruning_recommended_now"),
        "recommended_pruning_type": audit_payload.get("recommended_pruning_type"),
        "expected_latency_gain_class": audit_payload.get("expected_latency_gain_class"),
        "implementation_risk": audit_payload.get("implementation_risk"),
        "quality_risk": audit_payload.get("quality_risk"),
        "backend_pruning_decision": decision_id,
        "recommendation": recommendation,
        "smaller_model_or_distillation_remains_recommended": decision_id != "ollama_backend_quality_benchmark_next",
        "actual_pruning_experiment_recommended_next": decision_id == "actual_pruning_experiment_next",
        "live_wiring_allowed": False,
        "adapter_live_ready": False,
        "quality_benchmark_required_before_live_wiring": True,
        "training_rerun": False,
        "actual_pruning_performed": False,
        "pruned_weights_created": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "live_tts_calls_made": False,
        "provider_side_effects_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "side_effects": audit_side_effects(),
    }


def warm_live_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload.get("warm_metrics_by_mode") if isinstance(payload.get("warm_metrics_by_mode"), dict) else {}
    if isinstance(metrics.get("minimal_live_action_prompt"), dict):
        return metrics["minimal_live_action_prompt"]
    return live_metrics(payload)


def write_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result['status']}",
        f"- pruning_feasible_now: {str(result['pruning_feasible_now']).lower()}",
        f"- pruning_recommended_now: {str(result['pruning_recommended_now']).lower()}",
        f"- recommended_pruning_type: {result['recommended_pruning_type']}",
        f"- expected_latency_gain_class: {result['expected_latency_gain_class']}",
        f"- implementation_risk: {result['implementation_risk']}",
        f"- quality_risk: {result['quality_risk']}",
        f"- attempt_actual_pruning_next_phase: {str(result['attempt_actual_pruning_next_phase']).lower()}",
        f"- smaller_model_or_distillation_remains_recommended: {str(result['smaller_model_or_distillation_remains_recommended']).lower()}",
        "",
        "## Backend First",
        "",
        json.dumps(result["audit_paths"]["backend_first_optimization"], indent=2, ensure_ascii=False),
        "",
        "## Pruning Paths",
        "",
        json.dumps(result["audit_paths"], indent=2, ensure_ascii=False),
        "",
        "## Rationale",
        "",
        json.dumps(result["rationale"], indent=2, ensure_ascii=False),
    ]
    write_text(REPORT_PATH, "\n".join(lines))


def write_decision_report(result: dict[str, Any]) -> None:
    lines = [
        f"# {DECISION_ID}",
        "",
        f"- status: {result['status']}",
        f"- ollama_benchmark_run: {str(result['ollama_benchmark_run']).lower()}",
        f"- ollama_target_met: {str(result['ollama_target_met']).lower()}",
        f"- ollama_quality_acceptable: {str(result['ollama_quality_acceptable']).lower()}",
        f"- pruning_recommended_now: {str(result['pruning_recommended_now']).lower()}",
        f"- backend_pruning_decision: `{result['backend_pruning_decision']}`",
        f"- recommendation: {result['recommendation']}",
        f"- smaller_model_or_distillation_remains_recommended: {str(result['smaller_model_or_distillation_remains_recommended']).lower()}",
        f"- live_wiring_allowed: {str(result['live_wiring_allowed']).lower()}",
        "",
        "## Ollama Metrics",
        "",
        json.dumps(result.get("ollama_minimal_live_action_warm_metrics") or {}, indent=2, ensure_ascii=False),
    ]
    write_text(DECISION_REPORT_PATH, "\n".join(lines))


def write_backend_pruning_decision() -> dict[str, Any]:
    audit = read_json(RESULT_PATH)
    decision = build_backend_pruning_decision(audit)
    write_json(DECISION_RESULT_PATH, decision)
    write_decision_report(decision)
    return decision


def main() -> int:
    audit = build_pruning_audit()
    write_json(RESULT_PATH, audit)
    write_report(audit)
    write_json(PRUNING_PLAN_PATH, build_pruning_plan(audit))
    decision = build_backend_pruning_decision(audit)
    write_json(DECISION_RESULT_PATH, decision)
    write_decision_report(decision)
    print(
        json.dumps(
            {
                "status": audit["status"],
                "pruning_feasible_now": audit["pruning_feasible_now"],
                "pruning_recommended_now": audit["pruning_recommended_now"],
                "decision": decision["backend_pruning_decision"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
