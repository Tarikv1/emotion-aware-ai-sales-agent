#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import replace
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

SMOKE_APPROVED_FACT_SUMMARIES = {
    # Summaries are derived from the existing public OpenAI source bundle and campaign fixture.
    "public_plan_names": "ChatGPT public plan categories include Free, Plus, Pro, Business, and Enterprise; source fixture also tracks Go.",
    "individual_plans": "Free, Plus, and Pro are individual ChatGPT plan categories.",
    "team_plans": "Business is the self-serve team workspace plan; Enterprise is for larger organization-level controls and contact sales.",
    "self_serve_path": "Individual plans use the official ChatGPT plans page or ChatGPT profile upgrade flow.",
    "pro_tier_general": "Pro has 100 dollar and 200 dollar tiers; exact current terms can change and the official source is authoritative.",
}
SMOKE_APPROVED_FACT_IDS = list(SMOKE_APPROVED_FACT_SUMMARIES)
PHASE_4H10_BASELINE_SUMMARY = {
    "status": "fail",
    "smoke_case_count": 8,
    "schema_valid_count": 5,
    "verifier_pass_count": 0,
    "total_generation_latency_ms": 435166.75,
    "tokens_generated": 4089,
    "provider_calls_made": False,
    "runtime_behavior_changed": False,
    "response_text_changed": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def env_flag(name: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() in {"1", "true", "yes", "on"}


def existing_smoke_summary() -> dict[str, Any] | None:
    if not RESULT_PATH.is_file():
        return None
    try:
        previous = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(previous, dict):
        return None
    latency = previous.get("latency_metrics") if isinstance(previous.get("latency_metrics"), dict) else {}
    return {
        "status": previous.get("status"),
        "smoke_case_count": previous.get("smoke_case_count"),
        "schema_valid_count": previous.get("schema_valid_count"),
        "verifier_pass_count": previous.get("verifier_pass_count"),
        "schema_valid_before_repair_count": previous.get("schema_valid_before_repair_count"),
        "schema_valid_after_repair_count": previous.get("schema_valid_after_repair_count"),
        "repair_applied_count": previous.get("repair_applied_count"),
        "needs_fact_check_before_repair_count": previous.get("needs_fact_check_before_repair_count"),
        "needs_fact_check_after_repair_count": previous.get("needs_fact_check_after_repair_count"),
        "buyer_word_preservation_errors_after_repair": previous.get("buyer_word_preservation_errors_after_repair"),
        "total_generation_latency_ms": latency.get("total_generation_latency_ms"),
        "tokens_generated": latency.get("tokens_generated"),
    }


def smoke_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "qwen_smoke_chatgpt_and_other_ai_tools_001",
            "sanitized_buyer_text": "I use ChatGPT and other AI tools.",
            "normalized_transcript": "i use chatgpt and other ai tools",
            "prior_state": {},
            "approved_campaign_fact_ids": SMOKE_APPROVED_FACT_IDS,
            "campaign_id": "synthetic_public_plan_fit",
            "expected_semantic_frame": {"conjunction_relation": "and"},
            "smoke_contract": {
                "buyer_words_to_preserve_allowed": ["ChatGPT", "other AI tools"],
            },
        },
        {
            "case_id": "qwen_smoke_chatgpt_or_claude_001",
            "sanitized_buyer_text": "I use ChatGPT or maybe Claude.",
            "normalized_transcript": "i use chatgpt or maybe claude",
            "prior_state": {},
            "approved_campaign_fact_ids": SMOKE_APPROVED_FACT_IDS,
            "campaign_id": "synthetic_public_plan_fit",
            "expected_semantic_frame": {"conjunction_relation": "or"},
            "smoke_contract": {
                "buyer_words_to_preserve_allowed": ["ChatGPT", "Claude", "maybe"],
                "do_not_preserve": ["Plus", "Pro", "Business", "Enterprise"],
            },
        },
        {
            "case_id": "qwen_smoke_by_myself_not_team_001",
            "sanitized_buyer_text": "I'm by myself, not a team.",
            "normalized_transcript": "i'm by myself not a team",
            "prior_state": {},
            "approved_campaign_fact_ids": SMOKE_APPROVED_FACT_IDS,
            "campaign_id": "synthetic_public_plan_fit",
            "smoke_contract": {
                "buyer_words_to_preserve_allowed": ["by myself", "not a team"],
                "preferred_draft_response": "You said by myself, not a team. Individual plans are the right lane.",
                "must_not_include_should_not_contain": ["team"],
            },
        },
        {
            "case_id": "qwen_smoke_coding_workflow_and_voice_001",
            "sanitized_buyer_text": "I use it for coding workflow and probably voice.",
            "normalized_transcript": "i use it for coding workflow and probably voice",
            "prior_state": {},
            "approved_campaign_fact_ids": SMOKE_APPROVED_FACT_IDS,
            "campaign_id": "synthetic_public_plan_fit",
            "expected_semantic_frame": {"conjunction_relation": "and"},
            "smoke_contract": {
                "buyer_words_to_preserve_allowed": ["coding workflow", "voice"],
            },
        },
        {
            "case_id": "qwen_smoke_plan_menu_question_001",
            "sanitized_buyer_text": "What are Free, Plus, Pro, Business, and Enterprise?",
            "normalized_transcript": "what are free plus pro business and enterprise",
            "prior_state": {},
            "approved_campaign_fact_ids": SMOKE_APPROVED_FACT_IDS,
            "campaign_id": "synthetic_public_plan_fit",
            "expected_semantic_frame": {"conjunction_relation": "and"},
            "smoke_contract": {
                "buyer_words_to_preserve_allowed": ["Free", "Plus", "Pro", "Business", "Enterprise"],
                "conjunction_relation": "and",
            },
        },
        {
            "case_id": "qwen_smoke_plus_enough_for_coding_001",
            "sanitized_buyer_text": "Is Plus enough for coding?",
            "normalized_transcript": "is plus enough for coding",
            "prior_state": {},
            "approved_campaign_fact_ids": SMOKE_APPROVED_FACT_IDS,
            "campaign_id": "synthetic_public_plan_fit",
            "smoke_contract": {
                "buyer_words_to_preserve_allowed": ["Plus", "enough", "coding"],
            },
        },
        {
            "case_id": "qwen_smoke_lower_pro_upgrade_later_001",
            "sanitized_buyer_text": "What if I start with the lower Pro tier and upgrade later?",
            "normalized_transcript": "what if i start with the lower pro tier and upgrade later",
            "prior_state": {},
            "approved_campaign_fact_ids": SMOKE_APPROVED_FACT_IDS,
            "campaign_id": "synthetic_public_plan_fit",
            "smoke_contract": {
                "buyer_words_to_preserve_allowed": ["lower Pro tier", "upgrade later", "start", "later"],
            },
        },
        {
            "case_id": "qwen_smoke_terminal_acceptance_close_001",
            "sanitized_buyer_text": "Ok, I'll check that, thanks.",
            "normalized_transcript": "ok i'll check that thanks",
            "prior_state": {},
            "approved_campaign_fact_ids": SMOKE_APPROVED_FACT_IDS,
            "campaign_id": "synthetic_public_plan_fit",
            "smoke_contract": {
                "buyer_words_to_preserve_allowed": ["check", "thanks"],
                "preferred_draft_response": "Thanks.",
                "max_sentence_count": 1,
                "should_ask_question": False,
            },
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
    approved_ids = case.get("approved_campaign_fact_ids") or []
    approved_summaries = {
        fact_id: SMOKE_APPROVED_FACT_SUMMARIES[fact_id]
        for fact_id in approved_ids
        if fact_id in SMOKE_APPROVED_FACT_SUMMARIES
    }
    return {
        "normalized_transcript": case["normalized_transcript"],
        "prior_state": case.get("prior_state") or {},
        "approved_campaign_fact_ids": approved_ids,
        "approved_campaign_fact_summaries": approved_summaries,
        "smoke_contract": case.get("smoke_contract") or {},
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
        "dependency_install_attempted": env_flag("LOCAL_LLM_DEPENDENCY_INSTALL_ATTEMPTED"),
        "dependency_install_succeeded": env_flag("LOCAL_LLM_DEPENDENCY_INSTALL_SUCCEEDED"),
        "dependency_versions": deps.get("versions") or {},
        "hardware_summary": hardware,
        "cuda_available": hardware.get("cuda_available", False),
        "gpu_name": hardware.get("gpu_name"),
        "vram_total_bytes": hardware.get("vram_total_bytes"),
        "model_availability": model_status,
        "quantization_mode": config.quantization_mode,
        "quantization_mode_requested": config.quantization_mode,
        "quantization_mode_actually_used": None,
        "fallback_used": False,
        "fallback_attempts": [],
        "phase_4h10_baseline_summary": PHASE_4H10_BASELINE_SUMMARY,
        "previous_smoke_summary": existing_smoke_summary(),
        "smoke_case_count": 0,
        "schema_valid_count": 0,
        "verifier_pass_count": 0,
        "schema_valid_before_repair_count": 0,
        "schema_valid_after_repair_count": 0,
        "repair_applied_count": 0,
        "repair_types": [],
        "repair_type_counts": {},
        "needs_fact_check_before_repair_count": 0,
        "needs_fact_check_after_repair_count": 0,
        "buyer_word_preservation_errors_before_repair": 0,
        "buyer_word_preservation_errors_after_repair": 0,
        "approved_campaign_fact_summaries_added": SMOKE_APPROVED_FACT_SUMMARIES,
        "planner_json_compactness_scope": "max_output_tokens and compact prompt apply to planner JSON only; longer buyer-facing answers remain allowed when response strategy and buyer need justify them.",
        "generation_settings": {
            "do_sample": False,
            "max_output_tokens": config.max_output_tokens,
            "stop_after_first_complete_json_object": True,
            "temperature": "default deterministic greedy generation; no sampling temperature is set",
        },
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
    prompt_token_counts: list[int] = []
    peak_memory: list[int] = []
    output_truncated_count = 0
    timed_out_count = 0
    completed_json_count = 0
    for item in case_results:
        metrics = item.get("latency_metrics") or {}
        first = metrics.get("first_output_latency_ms")
        total = metrics.get("total_generation_latency_ms")
        tokens = metrics.get("tokens_generated")
        prompt_tokens = metrics.get("prompt_token_count")
        peak = metrics.get("peak_gpu_memory_bytes")
        if isinstance(first, (int, float)):
            first_latencies.append(float(first))
        if isinstance(total, (int, float)):
            generation_latencies.append(float(total))
        if isinstance(tokens, int):
            token_counts.append(tokens)
        if isinstance(prompt_tokens, int):
            prompt_token_counts.append(prompt_tokens)
        if isinstance(peak, int):
            peak_memory.append(peak)
        if metrics.get("output_truncated") is True:
            output_truncated_count += 1
        if metrics.get("timed_out") is True:
            timed_out_count += 1
        if metrics.get("completed_json_object") is True:
            completed_json_count += 1
    return {
        "model_load_time_ms": model_load_time_ms,
        "first_output_latency_ms": first_latencies[0] if first_latencies else None,
        "total_generation_latency_ms": round(sum(generation_latencies), 3) if generation_latencies else None,
        "tokens_generated": sum(token_counts) if token_counts else None,
        "prompt_tokens_total": sum(prompt_token_counts) if prompt_token_counts else None,
        "prompt_tokens_max": max(prompt_token_counts) if prompt_token_counts else None,
        "completed_json_object_count": completed_json_count,
        "output_truncated_count": output_truncated_count,
        "timed_out_count": timed_out_count,
        "peak_gpu_memory_bytes": max(peak_memory) if peak_memory else None,
    }


def write_report(result: dict[str, Any]) -> None:
    failed_cases = result.get("failed_cases") or []
    dependency_status_payload = result.get("dependency_status") or {}
    previous = result.get("phase_4h10_baseline_summary") or result.get("previous_smoke_summary") or {}
    lines = [
        f"# {EXPERIMENT_ID}",
        "",
        "## Previous Smoke",
        "",
        f"- previous_status: {previous.get('status', 'unknown')}",
        f"- previous_schema_valid_count: {previous.get('schema_valid_count', 'unknown')}",
        f"- previous_verifier_pass_count: {previous.get('verifier_pass_count', 'unknown')}",
        f"- previous_latency_total_ms: {previous.get('total_generation_latency_ms', 'unknown')}",
        f"- previous_generated_tokens: {previous.get('tokens_generated', 'unknown')}",
        "",
        "## New Smoke",
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
        f"- dependency_install_attempted: {str(result['dependency_install_attempted']).lower()}",
        f"- dependency_install_succeeded: {str(result['dependency_install_succeeded']).lower()}",
        f"- dependency_versions: {json.dumps(result['dependency_versions'], ensure_ascii=False)}",
        f"- missing_dependencies: {', '.join(dependency_status_payload.get('missing_required') or []) or 'none'}",
        f"- cuda_available: {str(result['cuda_available']).lower()}",
        f"- gpu_name: {result.get('gpu_name') or 'unknown'}",
        f"- quantization_mode_requested: {result['quantization_mode_requested']}",
        f"- quantization_mode_actually_used: {result['quantization_mode_actually_used'] or 'none'}",
        f"- fallback_used: {str(result['fallback_used']).lower()}",
        f"- smoke_case_count: {result['smoke_case_count']}",
        f"- schema_valid_count: {result['schema_valid_count']}",
        f"- verifier_pass_count: {result['verifier_pass_count']}",
        f"- schema_valid_before_repair_count: {result['schema_valid_before_repair_count']}",
        f"- schema_valid_after_repair_count: {result['schema_valid_after_repair_count']}",
        f"- repair_applied_count: {result['repair_applied_count']}",
        f"- repair_types: {json.dumps(result['repair_type_counts'], ensure_ascii=False)}",
        f"- needs_fact_check_before_repair_count: {result['needs_fact_check_before_repair_count']}",
        f"- needs_fact_check_after_repair_count: {result['needs_fact_check_after_repair_count']}",
        f"- buyer_word_preservation_errors_before_repair: {result['buyer_word_preservation_errors_before_repair']}",
        f"- buyer_word_preservation_errors_after_repair: {result['buyer_word_preservation_errors_after_repair']}",
        f"- failed_case_count: {len(failed_cases)}",
        f"- latency_metrics: {json.dumps(result['latency_metrics'], ensure_ascii=False)}",
        f"- generation_settings: {json.dumps(result['generation_settings'], ensure_ascii=False)}",
        f"- approved_campaign_fact_summaries_added: {json.dumps(result['approved_campaign_fact_summaries_added'], ensure_ascii=False)}",
        f"- planner_json_compactness_scope: {result['planner_json_compactness_scope']}",
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
    model_load_time_ms: float | None = None
    load_configs = [config]
    if config.quantization_mode == "4bit":
        load_configs.append(replace(config, quantization_mode="8bit"))
    for load_config in load_configs:
        load_started = time.perf_counter()
        try:
            model, tokenizer, _model_status = load_local_transformers_model(
                load_config,
                allow_model_download=allow_download,
            )
            config = load_config
            result["model_loaded"] = True
            result["quantization_mode_actually_used"] = load_config.quantization_mode
            result["fallback_used"] = load_config.quantization_mode != result["quantization_mode_requested"]
            model_load_time_ms = round((time.perf_counter() - load_started) * 1000, 3)
            result["fallback_attempts"].append(
                {
                    "quantization_mode": load_config.quantization_mode,
                    "status": "loaded",
                    "error": None,
                    "load_time_ms": model_load_time_ms,
                }
            )
            break
        except Exception as exc:
            result["fallback_attempts"].append(
                {
                    "quantization_mode": load_config.quantization_mode,
                    "status": "failed",
                    "error": str(exc),
                    "load_time_ms": round((time.perf_counter() - load_started) * 1000, 3),
                }
            )
    if model is None or tokenizer is None:
        result["status"] = "model_load_failed"
        first_error = (result["fallback_attempts"] or [{}])[0].get("error") or "unknown model load error"
        result["failed_cases"].append(f"model load failed: {first_error}")
        if len(result["fallback_attempts"]) > 1:
            result["notes"].append("4-bit load failed; 8-bit fallback was attempted and also failed.")
        else:
            result["notes"].append("No feasible fallback was attempted after model load failure.")
        write_evidence(result)
        print(f"{EXPERIMENT_ID}: model_load_failed")
        return 0

    case_results: list[dict[str, Any]] = []
    result["inference_attempted"] = True
    for case in smoke_cases():
        request_context = build_request_context(case)
        case_for_verifier = {
            **case,
            "approved_campaign_fact_summaries": request_context["approved_campaign_fact_summaries"],
            "smoke_contract": request_context["smoke_contract"],
        }
        case_result = run_single_conversation_brain_case(
            config=config,
            request_context=request_context,
            case=case_for_verifier,
            allow_model_download=allow_download,
            model=model,
            tokenizer=tokenizer,
        ).to_dict()
        case_results.append(case_result)

    result["cases"] = case_results
    result["local_model_calls_made"] = bool(case_results)
    result["smoke_case_count"] = len(case_results)
    result["schema_valid_before_repair_count"] = sum(
        1
        for item in case_results
        if item.get("planner_output") is not None and not item.get("raw_schema_errors_before_repair")
    )
    result["schema_valid_count"] = sum(
        1 for item in case_results if item.get("planner_output") is not None and not item.get("schema_errors")
    )
    result["schema_valid_after_repair_count"] = result["schema_valid_count"]
    result["verifier_pass_count"] = sum(
        1
        for item in case_results
        if not item.get("schema_errors") and not item.get("verifier_errors") and not item.get("errors")
    )
    repair_types: list[str] = [
        repair_type
        for item in case_results
        for repair_type in (item.get("repair_types") or [])
        if isinstance(repair_type, str)
    ]
    repair_type_counts: dict[str, int] = {}
    for repair_type in repair_types:
        repair_type_counts[repair_type] = repair_type_counts.get(repair_type, 0) + 1
    result["repair_applied_count"] = sum(1 for item in case_results if item.get("repair_applied"))
    result["repair_types"] = sorted(repair_type_counts)
    result["repair_type_counts"] = dict(sorted(repair_type_counts.items()))
    result["needs_fact_check_before_repair_count"] = sum(
        1 for item in case_results if item.get("needs_fact_check_before_repair") is True
    )
    result["needs_fact_check_after_repair_count"] = sum(
        1 for item in case_results if item.get("needs_fact_check_after_repair") is True
    )
    result["buyer_word_preservation_errors_before_repair"] = sum(
        1
        for item in case_results
        for error in (item.get("verifier_errors_before_repair") or [])
        if isinstance(error, str) and error.startswith("buyer_word_not_preserved:")
    )
    result["buyer_word_preservation_errors_after_repair"] = sum(
        1
        for item in case_results
        for error in (item.get("verifier_errors_after_repair") or [])
        if isinstance(error, str) and error.startswith("buyer_word_not_preserved:")
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
