#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from benchmark_ollama_small_live_action_models_001 import BENCHMARK_ID, BENCHMARK_REPORT_PATH, BENCHMARK_RESULT_PATH, MODE_NAMES, PRIMARY_MODELS, quality_acceptable
from local_ollama_qwen_utils_001 import (
    GENERATED_DIR,
    audit_side_effects,
    changed_files,
    mode_target_met,
    pruned_weight_files,
    read_json,
    rel,
    runtime_behavior_changed_by_files,
    tracked_model_or_adapter_files,
    utc_now,
    write_json,
    write_text,
)


VALIDATION_ID = "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-BENCHMARK-VALIDATION-001"
OUT_DIR = GENERATED_DIR / VALIDATION_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
FALSE_FLAGS = (
    "provider_calls_made",
    "openai_api_calls_made",
    "live_tts_calls_made",
    "provider_side_effects_made",
    "training_rerun",
    "actual_pruning_performed",
    "runtime_behavior_changed",
    "response_text_changed",
    "adapter_live_ready",
    "live_wiring_allowed",
    "model_weights_committed",
    "adapter_weights_committed",
    "raw_private_transcript_included",
    "raw_private_transcript_copied_to_public_evidence",
)


def false_flag(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


def validate_metrics(payload: dict[str, Any], failures: list[str]) -> None:
    metrics_by_model = payload.get("metrics_by_model_mode") if isinstance(payload.get("metrics_by_model_mode"), dict) else {}
    if payload.get("benchmark_run") is True:
        missing_models = [model for model in PRIMARY_MODELS if model not in metrics_by_model and payload.get("model_present_by_model", {}).get(model) is True]
        if missing_models:
            failures.append(f"present primary models missing metrics: {missing_models}")
        for model_name, by_mode in metrics_by_model.items():
            if not isinstance(by_mode, dict):
                failures.append(f"{model_name} metrics must be an object")
                continue
            missing_modes = [mode for mode in MODE_NAMES if mode not in by_mode]
            if missing_modes:
                failures.append(f"{model_name} missing modes: {missing_modes}")
            for mode, metrics in by_mode.items():
                if not isinstance(metrics, dict):
                    failures.append(f"{model_name}.{mode} metrics must be object")
                    continue
                expected_target = mode_target_met(metrics)
                if metrics.get("target_met") is not expected_target:
                    failures.append(f"{model_name}.{mode}.target_met dishonest: expected {expected_target}, found {metrics.get('target_met')}")
                expected_quality = quality_acceptable(metrics, str(mode))
                if metrics.get("quality_acceptable") is not expected_quality:
                    failures.append(f"{model_name}.{mode}.quality_acceptable dishonest: expected {expected_quality}, found {metrics.get('quality_acceptable')}")
                for key in ("model_present", "model_loaded", "pull_attempted", "warm_case_count", "malformed_output_count", "verifier_pass_count", "hard_block_count"):
                    if key not in metrics:
                        failures.append(f"{model_name}.{mode} missing {key}")
    else:
        if not str(payload.get("not_run_reason") or "").strip():
            failures.append("not-run benchmark needs clear not_run_reason")


def validate_side_effects(payload: dict[str, Any], failures: list[str]) -> None:
    for key in FALSE_FLAGS:
        false_flag(payload, key, failures, "benchmark")
    if "ollama_localhost_calls_made" not in payload:
        failures.append("benchmark must report ollama_localhost_calls_made separately")
    if "ollama_localhost_api_call_count" not in payload:
        failures.append("benchmark must count localhost Ollama API calls")
    if payload.get("ollama_pull_attempted") is True and payload.get("pull_allowed") is not True:
        failures.append("benchmark pulled without explicit pull allowance")
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in (
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "training_rerun",
        "actual_pruning_performed",
        "pruned_weights_created",
        "model_weights_committed",
        "adapter_files_committed",
        "raw_private_transcript_copied_to_public_evidence",
    ):
        if side_effects.get(key) is not False:
            failures.append(f"benchmark.side_effects.{key} must be false")


def main() -> int:
    failures: list[str] = []
    if not BENCHMARK_RESULT_PATH.is_file():
        failures.append(f"missing benchmark result: {rel(BENCHMARK_RESULT_PATH)}")
    if not BENCHMARK_REPORT_PATH.is_file():
        failures.append(f"missing benchmark report: {rel(BENCHMARK_REPORT_PATH)}")
    payload = read_json(BENCHMARK_RESULT_PATH)
    if payload.get("experiment_id") != BENCHMARK_ID:
        failures.append("benchmark result has wrong experiment_id")
    validate_metrics(payload, failures)
    validate_side_effects(payload, failures)

    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter/local_artifact files are forbidden: {tracked[:20]}")
    pruned = pruned_weight_files()
    if pruned:
        failures.append(f"pruned weights exist but this phase must not create them: {pruned[:20]}")
    files = changed_files()
    runtime_behavior_changed = runtime_behavior_changed_by_files(files)
    response_text_changed = any(path.startswith("runtime/dialogue") or path.startswith("runtime/responses") for path in files)
    if runtime_behavior_changed:
        failures.append("runtime behavior changed")
    if response_text_changed:
        failures.append("response text changed")

    result = {
        "experiment_id": VALIDATION_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "benchmark_result": rel(BENCHMARK_RESULT_PATH),
        "benchmark_run": payload.get("benchmark_run"),
        "models_tested": [model for model, loaded in (payload.get("model_loaded_by_model") or {}).items() if loaded],
        "ollama_localhost_calls_made": payload.get("ollama_localhost_calls_made"),
        "ollama_localhost_api_call_count": payload.get("ollama_localhost_api_call_count"),
        "changed_files": files,
        "failures": failures,
        "side_effects": audit_side_effects(
            local_model_calls_made=payload.get("local_model_calls_made") is True,
            ollama_localhost_calls_made=payload.get("ollama_localhost_calls_made") is True,
            ollama_pull_attempted=payload.get("ollama_pull_attempted") is True,
        ),
    }
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                f"# {VALIDATION_ID}",
                "",
                f"- status: {result['status']}",
                f"- benchmark_run: {str(result['benchmark_run']).lower()}",
                f"- failure_count: {len(failures)}",
                "",
                "## Failures",
                "",
                json.dumps(failures, indent=2, ensure_ascii=False),
            ]
        ),
    )
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
