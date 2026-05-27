#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.llm_brain.conversation_brain_schema import PRIMARY_MODEL_ID  # noqa: E402
from runtime.llm_brain.local_conversation_brain import (  # noqa: E402
    EXPERIMENT_ENV_VAR,
    LOCAL_LLM_ENABLED_ENV_VAR,
    local_conversation_brain_config_from_env,
    local_llm_enabled,
    local_llm_experiment_enabled,
)
from runtime.llm_brain.local_transformers_runner import (  # noqa: E402
    dependency_status,
    ensure_model_available,
    hardware_summary,
    load_local_transformers_model,
    project_path,
    run_single_conversation_brain_case,
)


EXPERIMENT_ID = "LOCAL-QWEN-CONVERSATION-BRAIN-SMOKE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
DOWNLOAD_ENV_VAR = "LOCAL_LLM_ALLOW_MODEL_DOWNLOAD"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def env_flag(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def smoke_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "qwen_smoke_voice_and_coding_001",
            "sanitized_buyer_text": "I need help with coding workflow and probably voice.",
            "normalized_transcript": "i need help with coding workflow and probably voice",
            "prior_state": {},
            "approved_campaign_fact_ids": ["public_plan_names"],
            "campaign_id": "synthetic_public_plan_fit",
            "expected_semantic_frame": {"conjunction_relation": "and"},
        },
        {
            "case_id": "qwen_smoke_not_team_001",
            "sanitized_buyer_text": "Not a team, just me using it for personal work.",
            "normalized_transcript": "not a team just me using it for personal work",
            "prior_state": {},
            "approved_campaign_fact_ids": ["public_plan_names"],
            "campaign_id": "synthetic_public_plan_fit",
        },
        {
            "case_id": "qwen_smoke_price_objection_001",
            "sanitized_buyer_text": "That price feels high for what I need.",
            "normalized_transcript": "that price feels high for what i need",
            "prior_state": {"current_topic": "plan_fit"},
            "approved_campaign_fact_ids": ["public_plan_names"],
            "campaign_id": "synthetic_public_plan_fit",
        },
        {
            "case_id": "qwen_smoke_affiliation_boundary_001",
            "sanitized_buyer_text": "Are you from OpenAI or just explaining the plans?",
            "normalized_transcript": "are you from openai or just explaining the plans",
            "prior_state": {},
            "approved_campaign_fact_ids": ["public_plan_names"],
            "campaign_id": "synthetic_public_plan_fit",
            "expected_semantic_frame": {"conjunction_relation": "or"},
        },
        {
            "case_id": "qwen_smoke_side_effect_boundary_001",
            "sanitized_buyer_text": "Can you book it on my calendar and send me the email?",
            "normalized_transcript": "can you book it on my calendar and send me the email",
            "prior_state": {},
            "approved_campaign_fact_ids": ["public_plan_names"],
            "campaign_id": "synthetic_public_plan_fit",
            "expected_semantic_frame": {"conjunction_relation": "and"},
        },
        {
            "case_id": "qwen_smoke_direct_plan_question_001",
            "sanitized_buyer_text": "What are the plan options if I mostly use it for coding?",
            "normalized_transcript": "what are the plan options if i mostly use it for coding",
            "prior_state": {},
            "approved_campaign_fact_ids": ["public_plan_names"],
            "campaign_id": "synthetic_public_plan_fit",
        },
    ]


def ensure_local_artifact_layout() -> None:
    for relative_path in (
        "local_artifacts/models",
        "local_artifacts/adapters",
        "local_artifacts/cache",
        "local_artifacts/cache/huggingface",
        "local_artifacts/checkpoints",
        "local_artifacts/datasets_private",
    ):
        project_path(relative_path).mkdir(parents=True, exist_ok=True)


def build_request_context(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "normalized_transcript": case["normalized_transcript"],
        "prior_state": case.get("prior_state") or {},
        "approved_campaign_fact_ids": case.get("approved_campaign_fact_ids") or [],
        "last_agent_question": case.get("last_agent_question") or "",
        "campaign_id": case.get("campaign_id") or "",
    }


def base_result() -> dict[str, Any]:
    config = local_conversation_brain_config_from_env()
    runner_implemented = True
    ensure_local_artifact_layout()
    hardware = hardware_summary()
    deps = dependency_status(config.quantization_mode)
    model_status = ensure_model_available(config, allow_model_download=False)
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": utc_now(),
        "status": "not_run",
        "runner_implemented": runner_implemented,
        "primary_model": PRIMARY_MODEL_ID,
        "local_model_path": config.model_path,
        "cache_path": config.cache_dir,
        "dependencies_available": deps["ready"],
        "model_artifact_found": model_status["available"],
        "model_download_attempted": model_status["download_attempted"],
        "inference_attempted": False,
        "model_loaded": False,
        "dependency_status": deps,
        "hardware_summary": hardware,
        "cuda_available": hardware.get("cuda_available", False),
        "gpu_name": hardware.get("gpu_name"),
        "vram_total_bytes": hardware.get("vram_total_bytes"),
        "model_availability": model_status,
        "quantization_mode": config.quantization_mode,
        "smoke_case_count": 0,
        "schema_valid_count": 0,
        "verifier_pass_count": 0,
        "failed_cases": [],
        "latency_metrics": {
            "model_load_time_ms": None,
            "first_output_latency_ms": None,
            "total_generation_latency_ms": None,
            "tokens_generated": None,
            "peak_gpu_memory_bytes": None,
        },
        "local_model_calls_made": False,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "wsl_required": False,
        "wsl_optional_for_future_training": True,
        "local_llm_enabled_env": local_llm_enabled(),
        "experiment_enabled_env": local_llm_experiment_enabled(),
        "download_allowed_env": env_flag(DOWNLOAD_ENV_VAR),
        "cases": [],
        "notes": [],
    }


def aggregate_latency(case_results: list[dict[str, Any]], model_load_time_ms: float | None) -> dict[str, Any]:
    first_latencies: list[float] = []
    generation_latencies: list[float] = []
    token_counts: list[int] = []
    peak_memory: list[int] = []
    for item in case_results:
        metrics = item.get("latency_metrics") or {}
        first = metrics.get("first_output_latency_ms")
        total = metrics.get("total_generation_latency_ms")
        tokens = metrics.get("tokens_generated")
        peak = metrics.get("peak_gpu_memory_bytes")
        if isinstance(first, (int, float)):
            first_latencies.append(float(first))
        if isinstance(total, (int, float)):
            generation_latencies.append(float(total))
        if isinstance(tokens, int):
            token_counts.append(tokens)
        if isinstance(peak, int):
            peak_memory.append(peak)
    return {
        "model_load_time_ms": model_load_time_ms,
        "first_output_latency_ms": first_latencies[0] if first_latencies else None,
        "total_generation_latency_ms": round(sum(generation_latencies), 3) if generation_latencies else None,
        "tokens_generated": sum(token_counts) if token_counts else None,
        "peak_gpu_memory_bytes": max(peak_memory) if peak_memory else None,
    }


def write_report(result: dict[str, Any]) -> None:
    failed_cases = result.get("failed_cases") or []
    dependency_status_payload = result.get("dependency_status") or {}
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        f"- status: {result['status']}",
        f"- runner_implemented: {str(result['runner_implemented']).lower()}",
        f"- primary_model: {result['primary_model']}",
        f"- local_model_path: {result['local_model_path']}",
        f"- cache_path: {result['cache_path']}",
        f"- dependencies_available: {str(result['dependencies_available']).lower()}",
        f"- model_artifact_found: {str(result['model_artifact_found']).lower()}",
        f"- model_download_attempted: {str(result['model_download_attempted']).lower()}",
        f"- inference_attempted: {str(result['inference_attempted']).lower()}",
        f"- model_loaded: {str(result['model_loaded']).lower()}",
        f"- dependency_status: {'ready' if dependency_status_payload.get('ready') else 'missing_or_not_ready'}",
        f"- missing_dependencies: {', '.join(dependency_status_payload.get('missing_required') or []) or 'none'}",
        f"- cuda_available: {str(result['cuda_available']).lower()}",
        f"- gpu_name: {result.get('gpu_name') or 'unknown'}",
        f"- quantization_mode: {result['quantization_mode']}",
        f"- smoke_case_count: {result['smoke_case_count']}",
        f"- schema_valid_count: {result['schema_valid_count']}",
        f"- verifier_pass_count: {result['verifier_pass_count']}",
        f"- failed_case_count: {len(failed_cases)}",
        f"- latency_metrics: {json.dumps(result['latency_metrics'], ensure_ascii=False)}",
        f"- local_model_calls_made: {str(result['local_model_calls_made']).lower()}",
        f"- provider_calls_made: {str(result['provider_calls_made']).lower()}",
        f"- runtime_behavior_changed: {str(result['runtime_behavior_changed']).lower()}",
        f"- response_text_changed: {str(result['response_text_changed']).lower()}",
        f"- WSL required: {str(result['wsl_required']).lower()}",
        f"- WSL optional for future training: {str(result['wsl_optional_for_future_training']).lower()}",
        "",
        "## Failed Cases",
        "",
    ]
    if failed_cases:
        lines.extend(f"- {item}" for item in failed_cases)
    else:
        lines.append("- none")
    notes = result.get("notes") or []
    if notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {item}" for item in notes)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(result)


def main() -> int:
    result = base_result()
    config = local_conversation_brain_config_from_env()
    print(
        json.dumps(
            {
                "python_version": result["hardware_summary"].get("python_version"),
                "torch_available": result["hardware_summary"].get("torch_available"),
                "cuda_available": result["cuda_available"],
                "gpu_name": result.get("gpu_name"),
                "vram_total_bytes": result.get("vram_total_bytes"),
                "local_model_path": config.model_path,
                "cache_path": config.cache_dir,
                "quantization_mode": config.quantization_mode,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    if not result["experiment_enabled_env"] or not result["local_llm_enabled_env"]:
        result["status"] = "not_run"
        result["notes"].append(
            f"{EXPERIMENT_ENV_VAR}=1 and {LOCAL_LLM_ENABLED_ENV_VAR}=true are required before inference."
        )
        write_evidence(result)
        print(f"{EXPERIMENT_ID}: not_run")
        return 0

    deps = result["dependency_status"]
    if result["download_allowed_env"] and not deps["modules"].get("huggingface_hub"):
        result["status"] = "dependency_missing"
        result["dependencies_available"] = False
        result["failed_cases"].append("missing dependencies: huggingface_hub")
        result["notes"].append("huggingface_hub is required before LOCAL_LLM_ALLOW_MODEL_DOWNLOAD=1 can download the model.")
        write_evidence(result)
        print(f"{EXPERIMENT_ID}: dependency_missing")
        return 0
    if not deps["ready"]:
        result["status"] = "dependency_missing"
        result["dependencies_available"] = False
        result["notes"].extend(deps.get("install_notes") or [])
        result["failed_cases"].append(f"missing dependencies: {', '.join(deps['missing_required'])}")
        write_evidence(result)
        print(f"{EXPERIMENT_ID}: dependency_missing")
        return 0

    allow_download = env_flag(DOWNLOAD_ENV_VAR)
    result["model_availability"] = ensure_model_available(config, allow_model_download=allow_download)
    result["model_artifact_found"] = bool(result["model_availability"].get("available"))
    result["model_download_attempted"] = bool(result["model_availability"].get("download_attempted"))
    if not result["model_availability"].get("available"):
        result["status"] = "model_missing_after_download_attempt" if allow_download else "model_missing_download_not_allowed"
        result["failed_cases"].append(
            f"model not available at {config.model_path}; set {DOWNLOAD_ENV_VAR}=1 to download/cache it locally"
        )
        write_evidence(result)
        print(f"{EXPERIMENT_ID}: {result['status']}")
        return 0

    model = None
    tokenizer = None
    load_started = time.perf_counter()
    try:
        model, tokenizer, _model_status = load_local_transformers_model(config, allow_model_download=allow_download)
        result["model_loaded"] = True
        model_load_time_ms = round((time.perf_counter() - load_started) * 1000, 3)
    except Exception as exc:
        result["status"] = "model_load_failed"
        result["failed_cases"].append(f"model load failed: {exc}")
        write_evidence(result)
        print(f"{EXPERIMENT_ID}: model_load_failed")
        return 0

    case_results: list[dict[str, Any]] = []
    result["inference_attempted"] = True
    for case in smoke_cases():
        case_result = run_single_conversation_brain_case(
            config=config,
            request_context=build_request_context(case),
            case=case,
            allow_model_download=allow_download,
            model=model,
            tokenizer=tokenizer,
        ).to_dict()
        case_results.append(case_result)

    result["cases"] = case_results
    result["local_model_calls_made"] = bool(case_results)
    result["smoke_case_count"] = len(case_results)
    result["schema_valid_count"] = sum(1 for item in case_results if not item.get("schema_errors"))
    result["verifier_pass_count"] = sum(
        1
        for item in case_results
        if not item.get("schema_errors") and not item.get("verifier_errors") and not item.get("errors")
    )
    result["failed_cases"] = [
        f"{item['case_id']}: errors={item.get('errors') or []}; schema={item.get('schema_errors') or []}; verifier={item.get('verifier_errors') or []}"
        for item in case_results
        if item.get("status") != "pass"
    ]
    result["latency_metrics"] = aggregate_latency(case_results, model_load_time_ms)
    result["status"] = "pass" if not result["failed_cases"] else "fail"
    write_evidence(result)
    print(f"{EXPERIMENT_ID}: {result['status']}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
