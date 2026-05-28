#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from benchmark_ollama_small_live_action_models_001 import DECISION_ID, DECISION_REPORT_PATH, DECISION_RESULT_PATH, BENCHMARK_RESULT_PATH, metric_candidates
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


VALIDATION_ID = "LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-DECISION-VALIDATION-001"
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
    "decision_local_model_calls_made",
)


def false_flag(payload: dict[str, Any], key: str, failures: list[str], prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


def expected_recommendation_id(benchmark: dict[str, Any]) -> str:
    candidates = metric_candidates(benchmark)
    valid = [item for item in candidates if item["target_met"] and item["quality_acceptable"]]
    latency_only = [item for item in candidates if item["target_met"] and not item["quality_acceptable"]]
    ultra_latency = [item for item in candidates if item["mode"] == "ultra_minimal_action_id_only" and item["target_met"]]
    say_valid = [
        item
        for item in candidates
        if item["mode"] in {"constrained_action_selector_prompt", "minimal_live_action_prompt"} and item["target_met"] and item["quality_acceptable"]
    ]
    if valid:
        return "offline_quality_benchmark_next"
    if ultra_latency and not say_valid:
        return "two_head_split_action_id_selector"
    if latency_only:
        return "latency_met_quality_weak_finetune_or_action_only"
    if not any(item["target_met"] for item in candidates):
        return "non_llm_classifier_or_backend_optimization"
    return "rerun_after_blocker"


def main() -> int:
    failures: list[str] = []
    if not BENCHMARK_RESULT_PATH.is_file():
        failures.append(f"missing benchmark result: {rel(BENCHMARK_RESULT_PATH)}")
    if not DECISION_RESULT_PATH.is_file():
        failures.append(f"missing decision result: {rel(DECISION_RESULT_PATH)}")
    if not DECISION_REPORT_PATH.is_file():
        failures.append(f"missing decision report: {rel(DECISION_REPORT_PATH)}")
    benchmark = read_json(BENCHMARK_RESULT_PATH)
    decision = read_json(DECISION_RESULT_PATH)
    if decision.get("experiment_id") != DECISION_ID:
        failures.append("decision has wrong experiment_id")
    if not str(decision.get("recommendation") or "").strip():
        failures.append("decision recommendation is missing")
    if not isinstance(decision.get("recommended_actions"), list) or not decision.get("recommended_actions"):
        failures.append("decision recommended_actions missing")
    expected_id = expected_recommendation_id(benchmark)
    if decision.get("recommendation_id") != expected_id:
        failures.append(f"decision.recommendation_id must be {expected_id}")
    if decision.get("target_met") is not (benchmark.get("target_met") is True):
        failures.append("decision.target_met must mirror benchmark target_met")
    if decision.get("quality_acceptable") is not (benchmark.get("quality_acceptable") is True):
        failures.append("decision.quality_acceptable must mirror benchmark quality_acceptable")
    if decision.get("quality_benchmark_required_before_live_wiring") is not True:
        failures.append("decision must require quality benchmark before live wiring")
    if decision.get("benchmark_local_model_calls_made") is not (benchmark.get("local_model_calls_made") is True):
        failures.append("decision.benchmark_local_model_calls_made must mirror benchmark")
    if "ollama_localhost_calls_made" not in decision:
        failures.append("decision must report localhost Ollama calls separately")
    for key in FALSE_FLAGS:
        false_flag(decision, key, failures, "decision")
    side_effects = decision.get("side_effects") if isinstance(decision.get("side_effects"), dict) else {}
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
            failures.append(f"decision.side_effects.{key} must be false")
    report_text = DECISION_REPORT_PATH.read_text(encoding="utf-8").lower() if DECISION_REPORT_PATH.is_file() else ""
    if "live_wiring_allowed: true" in report_text or "adapter_live_ready: true" in report_text:
        failures.append("decision report claims live wiring or adapter readiness")

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
        "decision_result": rel(DECISION_RESULT_PATH),
        "recommendation_id": decision.get("recommendation_id"),
        "changed_files": files,
        "failures": failures,
        "side_effects": audit_side_effects(),
    }
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                f"# {VALIDATION_ID}",
                "",
                f"- status: {result['status']}",
                f"- recommendation_id: `{result['recommendation_id']}`",
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
