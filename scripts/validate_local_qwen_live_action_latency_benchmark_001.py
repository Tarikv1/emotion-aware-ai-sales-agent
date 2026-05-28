#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
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
    rel,
    runtime_behavior_changed_by_files,
    tracked_model_or_adapter_files,
)


EXPERIMENT_ID = "LOCAL-QWEN-LIVE-ACTION-LATENCY-BENCHMARK-001"
RESULT_PATH = GENERATED_DIR / EXPERIMENT_ID / "result.json"
REPORT_PATH = GENERATED_DIR / EXPERIMENT_ID / "report.md"
VALIDATION_RESULT_PATH = GENERATED_DIR / EXPERIMENT_ID / "validation_result.json"
VALIDATION_REPORT_PATH = GENERATED_DIR / EXPERIMENT_ID / "validation_report.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(["git", "--no-optional-locks", *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def changed_files() -> list[str]:
    return git_lines(["diff", "--name-only", "HEAD"])


def false_flag(payload: dict[str, Any], key: str, failures: list[str]) -> None:
    if payload.get(key) is not False:
        failures.append(f"{key} must be false")


def validate_not_run(payload: dict[str, Any], failures: list[str]) -> None:
    if payload.get("benchmark_run") is not False:
        failures.append("not_run benchmark evidence must have benchmark_run false")
    reason = str(payload.get("not_run_reason") or "")
    if not reason:
        failures.append("not_run benchmark evidence must include not_run_reason")
    gates = payload.get("env_gates") if isinstance(payload.get("env_gates"), dict) else {}
    if gates.get("ENABLE_LOCAL_LLM_BRAIN_EXPERIMENT") is True and gates.get("LOCAL_LLM_ENABLED") is True:
        failures.append("not_run is only accepted here when env gates are disabled")
    if payload.get("local_model_calls_made") is not False:
        failures.append("not_run benchmark must not make local model calls")


def validate_run(payload: dict[str, Any], failures: list[str]) -> None:
    if payload.get("benchmark_run") is not True:
        failures.append("run benchmark evidence must have benchmark_run true")
    metrics = payload.get("metrics_by_mode") if isinstance(payload.get("metrics_by_mode"), dict) else {}
    required_modes = {
        "current_compact_planner_prompt",
        "minimal_live_action_prompt",
        "minimal_live_action_prompt_with_replan_context",
    }
    missing = sorted(required_modes - set(metrics))
    if missing:
        failures.append(f"benchmark metrics missing mode(s): {missing}")
    live_metrics = metrics.get("minimal_live_action_prompt") if isinstance(metrics.get("minimal_live_action_prompt"), dict) else {}
    for key in (
        "prompt_token_count_total",
        "generated_token_count_total",
        "first_output_latency_p50_s",
        "total_generation_latency_p50_s",
        "total_generation_latency_p90_s",
        "malformed_output_count",
        "verifier_pass_count",
        "replan_required_count",
        "internal_language_count",
        "loop_risk_count",
    ):
        if key not in live_metrics:
            failures.append(f"live benchmark metric missing: {key}")
    if payload.get("target_met") is not True and payload.get("adapter_live_ready") is True:
        failures.append("adapter_live_ready cannot be true when latency target was not met")
    if payload.get("quality_gate_passed") is not True and payload.get("live_wiring_allowed") is True:
        failures.append("live_wiring_allowed cannot be true when quality gate did not pass")


def main() -> int:
    failures: list[str] = []
    if not RESULT_PATH.is_file():
        failures.append(f"missing benchmark result: {rel(RESULT_PATH)}")
    if not REPORT_PATH.is_file():
        failures.append(f"missing benchmark report: {rel(REPORT_PATH)}")
    payload = read_json(RESULT_PATH)
    if payload.get("experiment_id") != EXPERIMENT_ID:
        failures.append("benchmark result has wrong experiment_id")
    if payload.get("benchmark_run") is True:
        validate_run(payload, failures)
    else:
        validate_not_run(payload, failures)

    for key in (
        "training_rerun",
        "provider_calls_made",
        "openai_api_calls_made",
        "live_tts_calls_made",
        "provider_side_effects_made",
        "runtime_behavior_changed",
        "response_text_changed",
        "adapter_live_ready",
        "live_wiring_allowed",
    ):
        false_flag(payload, key, failures)
    side_effects = payload.get("side_effects") if isinstance(payload.get("side_effects"), dict) else {}
    for key in (
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
    ):
        if side_effects.get(key) is not False:
            failures.append(f"side_effects.{key} must be false")

    tracked = tracked_model_or_adapter_files()
    if tracked:
        failures.append(f"tracked model/adapter/local_artifact files are forbidden: {tracked[:20]}")
    files_changed = changed_files()
    runtime_behavior_changed = runtime_behavior_changed_by_files(files_changed)
    if runtime_behavior_changed:
        failures.append("runtime behavior changed outside approved offline live-action architecture files")
    response_text_changed = any(path.startswith("runtime/dialogue") or path.startswith("runtime/responses") for path in files_changed)
    if response_text_changed:
        failures.append("response text changed")

    result = {
        "experiment_id": f"{EXPERIMENT_ID}-VALIDATION",
        "validated_at": utc_now(),
        "status": "pass" if not failures else "fail",
        "benchmark_result": rel(RESULT_PATH),
        "benchmark_run": payload.get("benchmark_run"),
        "target_met": payload.get("target_met"),
        "local_model_calls_made": payload.get("local_model_calls_made"),
        "provider_calls_made": payload.get("provider_calls_made"),
        "openai_api_calls_made": payload.get("openai_api_calls_made"),
        "live_tts_calls_made": payload.get("live_tts_calls_made"),
        "runtime_behavior_changed": runtime_behavior_changed,
        "response_text_changed": response_text_changed,
        "model_or_adapter_weights_committed": bool(tracked),
        "changed_files": files_changed,
        "failures": failures,
        "side_effects": audit_side_effects(),
    }
    VALIDATION_RESULT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    VALIDATION_REPORT_PATH.write_text(
        "\n".join(
            [
                f"# {EXPERIMENT_ID} Validation",
                "",
                f"- status: {result['status']}",
                f"- benchmark_run: {str(result['benchmark_run']).lower()}",
                f"- target_met: {result['target_met']}",
                f"- local_model_calls_made: {str(result['local_model_calls_made']).lower()}",
                "",
                "## Failures",
                "",
                json.dumps(failures, indent=2, ensure_ascii=False),
            ]
        ).rstrip()
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "failures": failures}, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
