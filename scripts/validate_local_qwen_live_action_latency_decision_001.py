#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.local_qwen_audit_utils_001 import (  # noqa: E402
    GENERATED_DIR,
    audit_side_effects,
    read_json,
    rel,
    runtime_behavior_changed_by_files,
    tracked_model_or_adapter_files,
    utc_now,
    write_json,
    write_text,
)


BENCHMARK_ID = "LOCAL-QWEN-LIVE-ACTION-LATENCY-BENCHMARK-001"
DECISION_ID = "LOCAL-QWEN-LIVE-ACTION-LATENCY-DECISION-001"
VALIDATION_ID = "LOCAL-QWEN-LIVE-ACTION-LATENCY-DECISION-VALIDATION-001"
BENCHMARK_RESULT_PATH = GENERATED_DIR / BENCHMARK_ID / "result.json"
BENCHMARK_REPORT_PATH = GENERATED_DIR / BENCHMARK_ID / "report.md"
DECISION_RESULT_PATH = GENERATED_DIR / DECISION_ID / "result.json"
DECISION_REPORT_PATH = GENERATED_DIR / DECISION_ID / "report.md"
OUT_DIR = GENERATED_DIR / VALIDATION_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TARGETS_SECONDS = {"p50": 2.0, "p90": 3.0, "p99": 4.0}
FALSE_FLAGS = (
    "training_rerun",
    "provider_calls_made",
    "openai_api_calls_made",
    "live_tts_calls_made",
    "provider_side_effects_made",
    "runtime_behavior_changed",
    "response_text_changed",
    "adapter_live_ready",
    "live_wiring_allowed",
    "model_redownloaded",
    "model_or_adapter_weights_committed",
)
SIDE_EFFECT_FALSE_FLAGS = (
    "provider_calls_made",
    "openai_api_calls_made",
    "live_tts_calls_made",
    "provider_side_effects_made",
    "model_download_attempted",
    "model_redownloaded",
    "model_weights_committed",
    "adapter_files_committed",
    "runtime_behavior_changed",
    "response_text_changed",
    "raw_private_transcript_copied_to_public_evidence",
)


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(["git", "--no-optional-locks", *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def changed_files() -> list[str]:
    return git_lines(["diff", "--name-only", "HEAD"])


def false_flag(payload: dict[str, Any], key: str, failures: list[str], *, prefix: str) -> None:
    if payload.get(key) is not False:
        failures.append(f"{prefix}.{key} must be false")


def side_effect_flags_false(payload: dict[str, Any], failures: list[str], *, prefix: str) -> None:
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in SIDE_EFFECT_FALSE_FLAGS:
        if side_effects.get(key) is not False:
            failures.append(f"{prefix}.side_effects.{key} must be false")


def measured_target_met(benchmark: dict[str, Any]) -> bool | None:
    if benchmark.get("benchmark_run") is not True:
        return None
    metrics = benchmark.get("metrics_by_mode") if isinstance(benchmark.get("metrics_by_mode"), dict) else {}
    live = metrics.get("minimal_live_action_prompt") if isinstance(metrics.get("minimal_live_action_prompt"), dict) else {}
    p50 = live.get("total_generation_latency_p50_s")
    p90 = live.get("total_generation_latency_p90_s")
    p99 = live.get("total_generation_latency_p99_s")
    if not all(isinstance(value, (int, float)) for value in (p50, p90, p99)):
        return False
    return bool(p50 <= TARGETS_SECONDS["p50"] and p90 <= TARGETS_SECONDS["p90"] and p99 <= TARGETS_SECONDS["p99"])


def latency_classification(benchmark: dict[str, Any]) -> str:
    expected = measured_target_met(benchmark)
    if expected is True:
        return "target_met"
    metrics = benchmark.get("metrics_by_mode") if isinstance(benchmark.get("metrics_by_mode"), dict) else {}
    live = metrics.get("minimal_live_action_prompt") if isinstance(metrics.get("minimal_live_action_prompt"), dict) else {}
    p50 = live.get("total_generation_latency_p50_s")
    p90 = live.get("total_generation_latency_p90_s")
    if isinstance(p50, (int, float)) and isinstance(p90, (int, float)) and p50 <= 4.0 and p90 <= 6.0:
        return "close_but_misses_target"
    if isinstance(p50, (int, float)) and isinstance(p90, (int, float)):
        return "far_above_target"
    return "not_measured"


def expected_recommendation_id(classification: str) -> str:
    if classification == "target_met":
        return "next_offline_quality_benchmark_for_live_action_contract"
    if classification == "close_but_misses_target":
        return "backend_optimization_before_quality_benchmark"
    if classification == "far_above_target":
        return "smaller_model_or_constrained_selector_before_live_use"
    return "rerun_benchmark_after_blocker"


def validate_benchmark(benchmark: dict[str, Any], failures: list[str]) -> None:
    if benchmark.get("experiment_id") != BENCHMARK_ID:
        failures.append("benchmark result has wrong experiment_id")
    if benchmark.get("benchmark_run") is True:
        if benchmark.get("model_loaded") is not True:
            failures.append("benchmark.model_loaded must be true when benchmark_run is true")
        if benchmark.get("adapter_loaded") is not False:
            failures.append("benchmark.adapter_loaded must be false")
        if benchmark.get("local_model_calls_made") is not True:
            failures.append("benchmark.local_model_calls_made must be true")
        if not isinstance(benchmark.get("local_model_call_count"), int) or benchmark.get("local_model_call_count") <= 0:
            failures.append("benchmark.local_model_call_count must be positive")
        metrics = benchmark.get("metrics_by_mode") if isinstance(benchmark.get("metrics_by_mode"), dict) else {}
        required_modes = {
            "current_compact_planner_prompt",
            "minimal_live_action_prompt",
            "minimal_live_action_prompt_with_replan_context",
        }
        missing = sorted(required_modes - set(metrics))
        if missing:
            failures.append(f"benchmark metrics missing mode(s): {missing}")
    else:
        if not str(benchmark.get("not_run_reason") or "").strip():
            failures.append("benchmark did not run and has no clear not_run_reason")

    expected = measured_target_met(benchmark)
    if expected is not None and benchmark.get("target_met") is not expected:
        failures.append(f"benchmark.target_met is dishonest: expected {expected}, found {benchmark.get('target_met')}")
    for key in FALSE_FLAGS:
        false_flag(benchmark, key, failures, prefix="benchmark")
    if benchmark.get("model_weights_committed") is not False:
        failures.append("benchmark.model_weights_committed must be false")
    if benchmark.get("adapter_weights_committed") is not False:
        failures.append("benchmark.adapter_weights_committed must be false")
    side_effect_flags_false(benchmark, failures, prefix="benchmark")


def validate_decision(decision: dict[str, Any], benchmark: dict[str, Any], failures: list[str]) -> None:
    if decision.get("experiment_id") != DECISION_ID:
        failures.append("decision result has wrong experiment_id")
    if not str(decision.get("recommendation") or "").strip():
        failures.append("decision recommendation is missing")
    classification = latency_classification(benchmark)
    if decision.get("latency_classification") != classification:
        failures.append(f"decision.latency_classification must be {classification}")
    expected_id = expected_recommendation_id(classification)
    if decision.get("recommendation_id") != expected_id:
        failures.append(f"decision.recommendation_id must be {expected_id}")
    if decision.get("target_met") != benchmark.get("target_met"):
        failures.append("decision.target_met must mirror benchmark.target_met")
    if decision.get("quality_benchmark_required_before_live_wiring") is not True:
        failures.append("decision must require a separate quality benchmark before live wiring")
    if decision.get("decision_local_model_calls_made") is not False:
        failures.append("decision.decision_local_model_calls_made must be false")
    if decision.get("benchmark_local_model_calls_made") != benchmark.get("local_model_calls_made"):
        failures.append("decision.benchmark_local_model_calls_made must mirror benchmark")
    for key in FALSE_FLAGS:
        false_flag(decision, key, failures, prefix="decision")
    side_effect_flags_false(decision, failures, prefix="decision")
    report_text = DECISION_REPORT_PATH.read_text(encoding="utf-8").lower() if DECISION_REPORT_PATH.is_file() else ""
    if "live_wiring_allowed: true" in report_text or "adapter_live_ready: true" in report_text:
        failures.append("decision report claims live wiring or adapter readiness")


def main() -> int:
    failures: list[str] = []
    if not BENCHMARK_RESULT_PATH.is_file():
        failures.append(f"missing benchmark result: {rel(BENCHMARK_RESULT_PATH)}")
    if not BENCHMARK_REPORT_PATH.is_file():
        failures.append(f"missing benchmark report: {rel(BENCHMARK_REPORT_PATH)}")
    if not DECISION_RESULT_PATH.is_file():
        failures.append(f"missing decision result: {rel(DECISION_RESULT_PATH)}")
    if not DECISION_REPORT_PATH.is_file():
        failures.append(f"missing decision report: {rel(DECISION_REPORT_PATH)}")

    benchmark = read_json(BENCHMARK_RESULT_PATH)
    decision = read_json(DECISION_RESULT_PATH)
    if benchmark:
        validate_benchmark(benchmark, failures)
    if decision:
        validate_decision(decision, benchmark, failures)

    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter/local_artifact files are forbidden: {tracked[:20]}")
    files_changed = changed_files()
    runtime_behavior_changed = runtime_behavior_changed_by_files(files_changed)
    response_text_changed = any(path.startswith("runtime/dialogue") or path.startswith("runtime/responses") for path in files_changed)
    if runtime_behavior_changed:
        failures.append("runtime behavior changed")
    if response_text_changed:
        failures.append("response text changed")

    result = {
        "experiment_id": VALIDATION_ID,
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "benchmark_result": rel(BENCHMARK_RESULT_PATH),
        "decision_result": rel(DECISION_RESULT_PATH),
        "benchmark_run": benchmark.get("benchmark_run"),
        "target_met": benchmark.get("target_met"),
        "recommendation_id": decision.get("recommendation_id"),
        "checks": {
            "benchmark_evidence_exists": BENCHMARK_RESULT_PATH.is_file() and BENCHMARK_REPORT_PATH.is_file(),
            "decision_evidence_exists": DECISION_RESULT_PATH.is_file() and DECISION_REPORT_PATH.is_file(),
            "benchmark_ran_or_blocker_reported": benchmark.get("benchmark_run") is True or bool(str(benchmark.get("not_run_reason") or "").strip()),
            "no_provider_openai_tts_calls": not any(
                benchmark.get(key) is True or decision.get(key) is True
                for key in ("provider_calls_made", "openai_api_calls_made", "live_tts_calls_made", "provider_side_effects_made")
            ),
            "no_training": benchmark.get("training_rerun") is False and decision.get("training_rerun") is False,
            "no_model_or_adapters_committed": not tracked,
            "runtime_behavior_changed": runtime_behavior_changed,
            "response_text_changed": response_text_changed,
            "live_wiring_allowed": False,
            "adapter_live_ready": False,
            "target_met_reported_honestly": measured_target_met(benchmark) in {None, benchmark.get("target_met")},
            "decision_recommendation_exists": bool(str(decision.get("recommendation") or "").strip()),
        },
        "changed_files": files_changed,
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
                f"- benchmark_run: {str(result['benchmark_run']).lower()}",
                f"- target_met: {result['target_met']}",
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
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
