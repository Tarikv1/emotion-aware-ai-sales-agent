#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from local_ollama_qwen_utils_001 import (
    GENERATED_DIR,
    TARGETS_SECONDS,
    audit_side_effects,
    changed_files,
    pruned_weight_files,
    read_json,
    rel,
    runtime_behavior_changed_by_files,
    tracked_model_or_adapter_files,
    utc_now,
    write_json,
    write_text,
)


EXPERIMENT_ID = "LOCAL-QWEN-OLLAMA-LIVE-ACTION-BENCHMARK-001"
VALIDATION_ID = "LOCAL-QWEN-OLLAMA-LIVE-ACTION-BENCHMARK-VALIDATION-001"
RESULT_PATH = GENERATED_DIR / EXPERIMENT_ID / "result.json"
REPORT_PATH = GENERATED_DIR / EXPERIMENT_ID / "report.md"
OUT_DIR = GENERATED_DIR / VALIDATION_ID
VALIDATION_RESULT_PATH = OUT_DIR / "result.json"
VALIDATION_REPORT_PATH = OUT_DIR / "report.md"
REQUIRED_MODES = {
    "minimal_live_action_prompt",
    "minimal_live_action_prompt_with_replan_context",
    "constrained_action_selector_prompt",
}


def measured_target_met(metrics: dict[str, Any]) -> bool:
    p50 = metrics.get("total_generation_latency_p50_s")
    p90 = metrics.get("total_generation_latency_p90_s")
    p99 = metrics.get("total_generation_latency_p99_s")
    return bool(
        isinstance(p50, (int, float))
        and isinstance(p90, (int, float))
        and isinstance(p99, (int, float))
        and p50 <= TARGETS_SECONDS["p50"]
        and p90 <= TARGETS_SECONDS["p90"]
        and p99 <= TARGETS_SECONDS["p99"]
    )


def false_flag(payload: dict[str, Any], key: str, failures: list[str]) -> None:
    if payload.get(key) is not False:
        failures.append(f"{key} must be false")


def main() -> int:
    failures: list[str] = []
    if not RESULT_PATH.is_file():
        failures.append(f"missing Ollama benchmark result: {rel(RESULT_PATH)}")
    if not REPORT_PATH.is_file():
        failures.append(f"missing Ollama benchmark report: {rel(REPORT_PATH)}")
    payload = read_json(RESULT_PATH)
    if payload.get("experiment_id") != EXPERIMENT_ID:
        failures.append("Ollama benchmark has wrong experiment_id")
    if payload.get("benchmark_run") is True:
        metrics = payload.get("metrics_by_mode") if isinstance(payload.get("metrics_by_mode"), dict) else {}
        missing = sorted(REQUIRED_MODES - set(metrics))
        if missing:
            failures.append(f"Ollama benchmark missing modes: {missing}")
        live_metrics = payload.get("warm_metrics_by_mode", {}).get("minimal_live_action_prompt") if isinstance(payload.get("warm_metrics_by_mode"), dict) else {}
        if not isinstance(live_metrics, dict) or not live_metrics:
            live_metrics = metrics.get("minimal_live_action_prompt") if isinstance(metrics.get("minimal_live_action_prompt"), dict) else {}
        expected = measured_target_met(live_metrics)
        if payload.get("target_met") is not expected:
            failures.append(f"Ollama benchmark target_met dishonest: expected {expected}, found {payload.get('target_met')}")
        if payload.get("local_model_calls_made") is not True:
            failures.append("benchmark_run true requires local_model_calls_made true")
        if payload.get("ollama_localhost_calls_made") is not True:
            failures.append("benchmark_run true requires ollama_localhost_calls_made true")
        if not isinstance(payload.get("ollama_local_model_call_count"), int) or payload.get("ollama_local_model_call_count") <= 0:
            failures.append("benchmark_run true requires positive ollama_local_model_call_count")
    else:
        reason = str(payload.get("not_run_reason") or "")
        if not reason:
            failures.append("not-run Ollama benchmark needs a clear blocker")
        if payload.get("local_model_calls_made") is not False:
            failures.append("not-run Ollama benchmark must not make model calls")

    for key in (
        "training_rerun",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "actual_pruning_performed",
        "runtime_behavior_changed",
        "response_text_changed",
        "adapter_live_ready",
        "live_wiring_allowed",
        "ollama_pull_attempted",
    ):
        false_flag(payload, key, failures)
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in ("provider_calls_made", "openai_api_calls_made", "live_tts_calls_made", "provider_side_effects_made", "training_rerun", "actual_pruning_performed", "pruned_weights_created"):
        if side_effects.get(key) is not False:
            failures.append(f"side_effects.{key} must be false")
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
        "benchmark_result": rel(RESULT_PATH),
        "benchmark_run": payload.get("benchmark_run"),
        "target_met": payload.get("target_met"),
        "ollama_localhost_calls_made": payload.get("ollama_localhost_calls_made"),
        "changed_files": files,
        "failures": failures,
        "side_effects": audit_side_effects(local_model_calls_made=payload.get("local_model_calls_made") is True, ollama_localhost_calls_made=payload.get("ollama_localhost_calls_made") is True),
    }
    write_json(VALIDATION_RESULT_PATH, result)
    write_text(
        VALIDATION_REPORT_PATH,
        "\n".join(
            [
                f"# {VALIDATION_ID}",
                "",
                f"- status: {result['status']}",
                f"- benchmark_run: {str(result['benchmark_run']).lower()}",
                f"- target_met: {result['target_met']}",
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
