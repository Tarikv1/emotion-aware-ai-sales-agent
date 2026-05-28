#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from local_ollama_qwen_utils_001 import (
    GENERATED_DIR,
    PRUNING_PLAN_PATH,
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


EXPERIMENT_ID = "LOCAL-QWEN7B-PRUNING-FEASIBILITY-001"
VALIDATION_ID = "LOCAL-QWEN7B-PRUNING-FEASIBILITY-VALIDATION-001"
RESULT_PATH = GENERATED_DIR / EXPERIMENT_ID / "result.json"
REPORT_PATH = GENERATED_DIR / EXPERIMENT_ID / "report.md"
OUT_DIR = GENERATED_DIR / VALIDATION_ID
VALIDATION_RESULT_PATH = OUT_DIR / "result.json"
VALIDATION_REPORT_PATH = OUT_DIR / "report.md"


def false_flag(payload: dict[str, Any], key: str, failures: list[str]) -> None:
    if payload.get(key) is not False:
        failures.append(f"{key} must be false")


def main() -> int:
    failures: list[str] = []
    if not RESULT_PATH.is_file():
        failures.append(f"missing pruning feasibility result: {rel(RESULT_PATH)}")
    if not REPORT_PATH.is_file():
        failures.append(f"missing pruning feasibility report: {rel(REPORT_PATH)}")
    if not PRUNING_PLAN_PATH.is_file():
        failures.append(f"missing pruning plan: {rel(PRUNING_PLAN_PATH)}")
    payload = read_json(RESULT_PATH)
    plan = read_json(PRUNING_PLAN_PATH)
    if payload.get("experiment_id") != EXPERIMENT_ID:
        failures.append("pruning feasibility result has wrong experiment_id")
    for key in (
        "pruning_feasible_now",
        "pruning_recommended_now",
        "recommended_pruning_type",
        "expected_latency_gain_class",
        "implementation_risk",
        "quality_risk",
        "attempt_actual_pruning_next_phase",
        "smaller_model_or_distillation_remains_recommended",
    ):
        if key not in payload:
            failures.append(f"pruning feasibility missing field: {key}")
    if payload.get("pruning_recommended_now") is False and payload.get("recommended_pruning_type") not in {"none", "", None}:
        failures.append("recommended_pruning_type must be none when pruning is not recommended")
    if payload.get("expected_latency_gain_class") not in {"low", "medium", "high", "unknown"}:
        failures.append("expected_latency_gain_class has invalid value")
    if payload.get("implementation_risk") not in {"low", "medium", "high"}:
        failures.append("implementation_risk has invalid value")
    if payload.get("quality_risk") not in {"low", "medium", "high"}:
        failures.append("quality_risk has invalid value")
    for key in (
        "training_rerun",
        "actual_pruning_performed",
        "pruned_weights_created",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "runtime_behavior_changed",
        "response_text_changed",
        "live_wiring_allowed",
        "adapter_live_ready",
        "model_or_adapter_weights_committed",
    ):
        false_flag(payload, key, failures)
    if plan.get("actual_pruning_performed") is not False or plan.get("model_weights_created") is not False:
        failures.append("pruning plan must not create or claim created weights")
    if plan.get("live_wiring_allowed") is not False or plan.get("adapter_live_ready") is not False:
        failures.append("pruning plan must keep live wiring and adapter readiness false")
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
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in ("provider_calls_made", "openai_api_calls_made", "live_tts_calls_made", "provider_side_effects_made", "training_rerun", "actual_pruning_performed", "pruned_weights_created"):
        if side_effects.get(key) is not False:
            failures.append(f"side_effects.{key} must be false")

    result = {
        "experiment_id": VALIDATION_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "pruning_result": rel(RESULT_PATH),
        "pruning_plan": rel(PRUNING_PLAN_PATH),
        "pruning_feasible_now": payload.get("pruning_feasible_now"),
        "pruning_recommended_now": payload.get("pruning_recommended_now"),
        "expected_latency_gain_class": payload.get("expected_latency_gain_class"),
        "implementation_risk": payload.get("implementation_risk"),
        "quality_risk": payload.get("quality_risk"),
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
                f"- pruning_recommended_now: {str(result['pruning_recommended_now']).lower()}",
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
