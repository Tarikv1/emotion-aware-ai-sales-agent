#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from local_ollama_qwen_utils_001 import (
    GENERATED_DIR,
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


EXPERIMENT_ID = "LOCAL-QWEN7B-BACKEND-PRUNING-DECISION-001"
VALIDATION_ID = "LOCAL-QWEN7B-BACKEND-PRUNING-DECISION-VALIDATION-001"
RESULT_PATH = GENERATED_DIR / EXPERIMENT_ID / "result.json"
REPORT_PATH = GENERATED_DIR / EXPERIMENT_ID / "report.md"
PRUNING_RESULT_PATH = GENERATED_DIR / "LOCAL-QWEN7B-PRUNING-FEASIBILITY-001" / "result.json"
OLLAMA_BENCHMARK_PATH = GENERATED_DIR / "LOCAL-QWEN-OLLAMA-LIVE-ACTION-BENCHMARK-001" / "result.json"
OUT_DIR = GENERATED_DIR / VALIDATION_ID
VALIDATION_RESULT_PATH = OUT_DIR / "result.json"
VALIDATION_REPORT_PATH = OUT_DIR / "report.md"


def false_flag(payload: dict[str, Any], key: str, failures: list[str]) -> None:
    if payload.get(key) is not False:
        failures.append(f"{key} must be false")


def main() -> int:
    failures: list[str] = []
    if not RESULT_PATH.is_file():
        failures.append(f"missing backend/pruning decision result: {rel(RESULT_PATH)}")
    if not REPORT_PATH.is_file():
        failures.append(f"missing backend/pruning decision report: {rel(REPORT_PATH)}")
    decision = read_json(RESULT_PATH)
    pruning = read_json(PRUNING_RESULT_PATH)
    ollama = read_json(OLLAMA_BENCHMARK_PATH)
    if decision.get("experiment_id") != EXPERIMENT_ID:
        failures.append("backend/pruning decision has wrong experiment_id")
    if not str(decision.get("backend_pruning_decision") or "").strip():
        failures.append("backend/pruning decision missing backend_pruning_decision")
    if not str(decision.get("recommendation") or "").strip():
        failures.append("backend/pruning decision missing recommendation")
    if decision.get("pruning_recommended_now") != pruning.get("pruning_recommended_now"):
        failures.append("decision pruning_recommended_now must mirror pruning audit")
    if decision.get("ollama_benchmark_run") != ollama.get("benchmark_run"):
        failures.append("decision ollama_benchmark_run must mirror Ollama benchmark")
    if decision.get("quality_benchmark_required_before_live_wiring") is not True:
        failures.append("decision must require quality benchmark before live wiring")
    for key in (
        "live_wiring_allowed",
        "adapter_live_ready",
        "training_rerun",
        "actual_pruning_performed",
        "pruned_weights_created",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        false_flag(decision, key, failures)
    if decision.get("backend_pruning_decision") == "actual_pruning_experiment_next" and pruning.get("expected_latency_gain_class") != "high":
        failures.append("actual pruning experiment requires high expected latency gain")
    if decision.get("backend_pruning_decision") == "ollama_backend_quality_benchmark_next":
        if decision.get("ollama_target_met") is not True or decision.get("ollama_quality_acceptable") is not True:
            failures.append("Ollama quality benchmark recommendation requires latency target and verifier quality")
    side_effects = decision.get("side_effects") if isinstance(decision.get("side_effects"), dict) else {}
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
        "decision_result": rel(RESULT_PATH),
        "backend_pruning_decision": decision.get("backend_pruning_decision"),
        "ollama_benchmark_run": decision.get("ollama_benchmark_run"),
        "pruning_recommended_now": decision.get("pruning_recommended_now"),
        "smaller_model_or_distillation_remains_recommended": decision.get("smaller_model_or_distillation_remains_recommended"),
        "changed_files": files,
        "failures": failures,
        "side_effects": audit_side_effects(),
    }
    write_json(VALIDATION_RESULT_PATH, result)
    write_text(
        VALIDATION_REPORT_PATH,
        "\n".join(
            [
                f"# {VALIDATION_ID}",
                "",
                f"- status: {result['status']}",
                f"- backend_pruning_decision: `{result['backend_pruning_decision']}`",
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
